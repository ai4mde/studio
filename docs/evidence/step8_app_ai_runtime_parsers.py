"""M03 Structured Output Parsing - vendored subset (pure Python, no Django).
Extracted from Studio api/model/llm/parsers/{base,json_parser}.py: merged, relative import
removed; logic unchanged. Strips json code fences, extracts balanced JSON, validates against a
pydantic schema."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T")


@dataclass(frozen=True)
class ParseError:
    code: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ParseResult(Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[ParseError] = None
    raw_response: str = ""

    @classmethod
    def ok(cls, data: T, raw_response: str) -> "ParseResult[T]":
        return cls(success=True, data=data, raw_response=raw_response)

    @classmethod
    def fail(cls, *, code: str, message: str, raw_response: str,
             details: Optional[Dict[str, Any]] = None, data: Optional[T] = None) -> "ParseResult[T]":
        return cls(success=False, data=data,
                   error=ParseError(code=code, message=message, details=details or {}),
                   raw_response=raw_response)


class OutputParser(Generic[T]):
    def parse(self, raw_response: str) -> ParseResult[T]:
        raise NotImplementedError


TModel = TypeVar("TModel", bound=BaseModel)
_JSON_FENCE_PATTERN = re.compile(r"```(?:json)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)


class JsonOutputParser(OutputParser[TModel], Generic[TModel]):
    def __init__(self, schema: Type[TModel]):
        self.schema = schema

    def parse(self, raw_response: str) -> ParseResult[TModel]:
        if raw_response is None or not raw_response.strip():
            return ParseResult.fail(code="EMPTY_RESPONSE",
                                    message="Response is empty; expected JSON output.",
                                    raw_response=raw_response or "")
        candidates = self._extract_json_candidates(raw_response)
        if not candidates:
            return ParseResult.fail(code="JSON_NOT_FOUND",
                                    message="No JSON object/array found in response.",
                                    raw_response=raw_response)
        decode_errors: list[dict] = []
        validation_errors: list[dict] = []
        for candidate_index, candidate in enumerate(candidates):
            try:
                payload = json.loads(candidate)
            except json.JSONDecodeError as exc:
                decode_errors.append({"message": str(exc), "line": exc.lineno,
                                      "column": exc.colno, "position": exc.pos})
                continue
            try:
                validated = self.schema.model_validate(payload)
                return ParseResult.ok(data=validated, raw_response=raw_response)
            except ValidationError as exc:
                validation_errors.append({"candidate_index": candidate_index, "errors": exc.errors()})
                continue
        if validation_errors:
            return ParseResult.fail(code="SCHEMA_VALIDATION_ERROR",
                                    message="JSON parsed but failed schema validation.",
                                    raw_response=raw_response,
                                    details={"errors": validation_errors[-1]["errors"],
                                             "validation_errors": validation_errors})
        return ParseResult.fail(code="JSON_DECODE_ERROR",
                                message="Found JSON-like content but could not decode valid JSON.",
                                raw_response=raw_response, details={"decode_errors": decode_errors})

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
        candidate_starts = sorted(idx for idx in (brace_index, bracket_index) if idx != -1)
        for start_index in candidate_starts[:1]:
            end_index = self._find_balanced_json_end(text, start_index)
            if end_index is not None:
                add_candidate(text[start_index:end_index])
        return candidates

    def _find_balanced_json_end(self, text: str, start_index: int) -> Optional[int]:
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
