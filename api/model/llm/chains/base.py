from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Type

from pydantic import BaseModel

from llm.parsers.base import ParseError
from llm.parsers.json_parser import JsonOutputParser
from llm.templates.renderer import render_prompt


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
                error = ParseError(
                    code="TEMPLATE_RENDER_ERROR",
                    message="Failed to render chain step prompt.",
                    details={"step": step_name, "prompt_name": step.prompt_name, "reason": str(exc)},
                )
                return ChainResult(
                    success=False,
                    outputs=outputs,
                    failed_step=step_name,
                    error=error,
                    step_details=step_details,
                )

            try:
                raw_response = self.llm_caller(prompt)
            except Exception as exc:  # noqa: BLE001
                error = ParseError(
                    code="LLM_CALL_ERROR",
                    message="Failed to call LLM for chain step.",
                    details={"step": step_name, "prompt_name": step.prompt_name, "reason": str(exc)},
                )
                return ChainResult(
                    success=False,
                    outputs=outputs,
                    failed_step=step_name,
                    error=error,
                    step_details=step_details,
                )

            parser = JsonOutputParser(schema=step.output_schema)
            parse_result = parser.parse(raw_response)

            step_details.append(
                {
                    "step": step_name,
                    "prompt_name": step.prompt_name,
                    "output_key": step.output_key,
                    "success": parse_result.success,
                    "error": parse_result.error,
                    "raw_response": parse_result.raw_response,
                }
            )

            if not parse_result.success or parse_result.data is None:
                error = parse_result.error or ParseError(
                    code="PARSE_ERROR",
                    message="Failed to parse chain step response.",
                )
                return ChainResult(
                    success=False,
                    outputs=outputs,
                    failed_step=step_name,
                    error=error,
                    step_details=step_details,
                )

            outputs[step.output_key] = parse_result.data
            if isinstance(parse_result.data, BaseModel):
                context[step.output_key] = parse_result.data.model_dump()
            else:
                context[step.output_key] = parse_result.data

        return ChainResult(
            success=True,
            outputs=outputs,
            step_details=step_details,
        )
