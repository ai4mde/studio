"""M04 runtime chaining with explicit step input, validation, and fail-stop semantics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Type

from pydantic import BaseModel

from .execution import PromptBudgetExceeded, prompt_record, safe_error
from .parsers import JsonOutputParser, ParseError
from .templates import render_prompt


@dataclass(frozen=True)
class ChainStep:
    prompt_name: str
    output_schema: Type[BaseModel]
    output_key: str
    name: str | None = None
    description: str = ""
    validate_context: Callable | None = None


@dataclass(frozen=True)
class ChainResult:
    success: bool
    outputs: dict[str, Any] = field(default_factory=dict)
    failed_step: str | None = None
    error: ParseError | None = None
    step_details: list[dict[str, Any]] = field(default_factory=list)


class ChainRunner:
    def __init__(self, steps: list[ChainStep], llm_caller: Callable[[str, ChainStep], str]):
        self.steps = steps
        self.llm_caller = llm_caller

    def run(self, initial_context: Mapping[str, Any]) -> ChainResult:
        context = dict(initial_context or {})
        outputs, details = {}, []
        for index, step in enumerate(self.steps, start=1):
            name = step.name or f"step_{index}"
            detail = {"step": name, "prompt_name": step.prompt_name, "output_key": step.output_key, "success": False}
            details.append(detail)

            def failed(code, message):
                detail["error"] = {"code": code, "message": message}
                return ChainResult(False, outputs, name, ParseError(code=code, message=message), details)

            try:
                prompt = render_prompt(step.prompt_name, context)
                detail.update(prompt_record(step.prompt_name, prompt))
            except PromptBudgetExceeded as exc:
                return failed(exc.code, str(exc))
            except Exception as exc:
                return failed("TEMPLATE_RENDER_ERROR", safe_error(exc)["message"])
            try:
                raw = self.llm_caller(prompt, step)
                detail["raw_response"] = raw
            except Exception as exc:
                return failed("LLM_CALL_ERROR", safe_error(exc)["message"])
            parsed = JsonOutputParser(step.output_schema).parse(raw)
            if not parsed.success or parsed.data is None:
                return failed(parsed.error.code, parsed.error.message)
            try:
                if step.validate_context:
                    step.validate_context(parsed.data, context)
            except (ValueError, TypeError, KeyError) as exc:
                return failed("CHAIN_CONTEXT_ERROR", str(exc))
            normalized = parsed.data.model_dump()
            detail["success"], detail["parsed_output"] = True, normalized
            outputs[step.output_key] = parsed.data
            context[step.output_key] = normalized
        return ChainResult(True, outputs=outputs, step_details=details)
