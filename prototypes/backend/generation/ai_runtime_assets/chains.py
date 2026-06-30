"""M04 Prompt Chaining - vendored subset (pure Python, no Django).
Extracted from Studio api/model/llm/chains/base.py: imports rewritten to ai_runtime.*, and the
single `django.conf.settings` read replaced by an env flag. Logic unchanged: per step
render_prompt (M01) -> llm_caller (M06) -> JsonOutputParser (M03), threading outputs forward."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Type

from pydantic import BaseModel

from ai_runtime.parsers import JsonOutputParser, ParseError
from ai_runtime.templates import render_prompt


@dataclass(frozen=True)
class ChainStep:
    prompt_name: str
    output_schema: Type[BaseModel]
    output_key: str
    name: str | None = None
    description: str = ""


@dataclass(frozen=True)
class ChainResult:
    success: bool
    outputs: dict[str, Any] = field(default_factory=dict)
    failed_step: str | None = None
    error: ParseError | None = None
    step_details: list[dict[str, Any]] = field(default_factory=list)


def _store_trace() -> bool:
    return os.environ.get("LLM_STORE_CHAIN_TRACE", "1") != "0"


class ChainRunner:
    def __init__(self, steps: list[ChainStep], llm_caller: Callable[[str], str]):
        self.steps = steps
        self.llm_caller = llm_caller

    def run(self, initial_context: Mapping[str, Any]) -> ChainResult:
        context = dict(initial_context or {})
        outputs: dict[str, Any] = {}
        step_details: list[dict[str, Any]] = []
        for index, step in enumerate(self.steps, start=1):
            step_name = step.name or f"step_{index}"
            try:
                prompt = render_prompt(prompt_name=step.prompt_name, context=context)
            except Exception as exc:  # noqa: BLE001
                return ChainResult(success=False, outputs=outputs, failed_step=step_name,
                                   error=ParseError(code="TEMPLATE_RENDER_ERROR", message=str(exc)),
                                   step_details=step_details)
            try:
                raw_response = self.llm_caller(prompt)
            except Exception as exc:  # noqa: BLE001
                return ChainResult(success=False, outputs=outputs, failed_step=step_name,
                                   error=ParseError(code="LLM_CALL_ERROR", message=str(exc)),
                                   step_details=step_details)
            parse_result = JsonOutputParser(schema=step.output_schema).parse(raw_response)
            if _store_trace():
                step_details.append({"step": step_name, "prompt_name": step.prompt_name,
                                     "output_key": step.output_key, "success": parse_result.success,
                                     "raw_response": parse_result.raw_response})
            else:
                step_details.append({"step": step_name, "success": parse_result.success})
            if not parse_result.success or parse_result.data is None:
                return ChainResult(success=False, outputs=outputs, failed_step=step_name,
                                   error=parse_result.error or ParseError(code="PARSE_ERROR", message="parse failed"),
                                   step_details=step_details)
            outputs[step.output_key] = parse_result.data
            context[step.output_key] = (parse_result.data.model_dump()
                                        if isinstance(parse_result.data, BaseModel) else parse_result.data)
        return ChainResult(success=True, outputs=outputs, step_details=step_details)
