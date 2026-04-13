from __future__ import annotations

import json
import re
from typing import Generic, Type, TypeVar

from pydantic import BaseModel, ValidationError

from .base import OutputParser, ParseResult


T = TypeVar("T", bound=BaseModel)

_JSON_FENCE_PATTERN = re.compile(r"```(?:json)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)


class JsonOutputParser(OutputParser[T], Generic[T]):
    def __init__(self, schema: Type[T]):
        self.schema = schema

    def parse(self, raw_response: str) -> ParseResult[T]:
        if raw_response is None or not raw_response.strip():
            return ParseResult.fail(
                code="EMPTY_RESPONSE",
                message="Response is empty; expected JSON output.",
                raw_response=raw_response or "",
            )

        candidates = self._extract_json_candidates(raw_response)
        if not candidates:
            return ParseResult.fail(
                code="JSON_NOT_FOUND",
                message="No JSON object/array found in response.",
                raw_response=raw_response,
            )

        decode_errors: list[dict] = []
        validation_errors: list[dict] = []
        for candidate_index, candidate in enumerate(candidates):
            try:
                payload = json.loads(candidate)
            except json.JSONDecodeError as exc:
                decode_errors.append(
                    {
                        "message": str(exc),
                        "line": exc.lineno,
                        "column": exc.colno,
                        "position": exc.pos,
                    }
                )
                continue

            try:
                validated = self.schema.model_validate(payload)
                return ParseResult.ok(data=validated, raw_response=raw_response)
            except ValidationError as exc:
                validation_errors.append(
                    {
                        "candidate_index": candidate_index,
                        "errors": exc.errors(),
                    }
                )
                continue

        if validation_errors:
            last_validation_error = validation_errors[-1]
            return ParseResult.fail(
                code="SCHEMA_VALIDATION_ERROR",
                message="JSON parsed but failed schema validation.",
                raw_response=raw_response,
                details={
                    "errors": last_validation_error["errors"],
                    "validation_errors": validation_errors,
                },
            )

        return ParseResult.fail(
            code="JSON_DECODE_ERROR",
            message="Found JSON-like content but could not decode valid JSON.",
            raw_response=raw_response,
            details={"decode_errors": decode_errors},
        )

    def _extract_json_candidates(self, text: str) -> list[str]:
        candidates: list[str] = []
        seen: set[str] = set()

        def add_candidate(value: str) -> None:
            candidate = value.strip()
            if candidate and candidate not in seen:
                candidates.append(candidate)
                seen.add(candidate)

        add_candidate(text)

        for match in _JSON_FENCE_PATTERN.finditer(text):
            add_candidate(match.group(1))

        brace_index = text.find("{")
        bracket_index = text.find("[")
        candidate_starts = sorted(
            idx for idx in (brace_index, bracket_index) if idx != -1
        )

        for start_index in candidate_starts[:1]:
            end_index = self._find_balanced_json_end(text, start_index)
            if end_index is not None:
                add_candidate(text[start_index:end_index])

        return candidates

    def _find_balanced_json_end(self, text: str, start_index: int) -> int | None:
        opening_to_closing = {"{": "}", "[": "]"}

        stack: list[str] = []
        in_string = False
        escaped = False

        for index in range(start_index, len(text)):
            char = text[index]

            if escaped:
                escaped = False
                continue

            if in_string:
                if char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
                continue

            if char in opening_to_closing:
                stack.append(opening_to_closing[char])
                continue

            if stack and char == stack[-1]:
                stack.pop()
                if not stack:
                    return index + 1

        return None
