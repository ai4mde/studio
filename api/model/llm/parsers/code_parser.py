from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Optional

from .base import OutputParser, ParseResult


_PYTHON_FENCE_PATTERN = re.compile(
    r"```(?:python|py)\s*(.*?)```", re.IGNORECASE | re.DOTALL
)
_GENERIC_FENCE_PATTERN = re.compile(r"```\s*(.*?)```", re.DOTALL)


@dataclass(frozen=True)
class CodeBlock:
    code: str
    language: Optional[str] = None
    is_valid_python: Optional[bool] = None


class CodeOutputParser(OutputParser[CodeBlock]):
    def __init__(self, language: str = "python", validate_syntax: bool = True):
        self.language = language
        self.validate_syntax = validate_syntax

    def parse(self, raw_response: str) -> ParseResult[CodeBlock]:
        if raw_response is None or not raw_response.strip():
            return ParseResult.fail(
                code="EMPTY_RESPONSE",
                message="Response is empty; expected Python code.",
                raw_response=raw_response or "",
            )

        code = self._extract_code(raw_response)
        if code is None or not code.strip():
            return ParseResult.fail(
                code="CODE_NOT_FOUND",
                message="No code found in response.",
                raw_response=raw_response,
            )

        if self._is_short_plain_text(code):
            return ParseResult.fail(
                code="SHORT_RESPONSE",
                message="Response is too short to be treated as code.",
                raw_response=raw_response,
                data=CodeBlock(code=code, language=self.language, is_valid_python=False),
            )

        if self.validate_syntax and self.language.lower() in {"python", "py"}:
            try:
                ast.parse(code)
            except SyntaxError as exc:
                return ParseResult.fail(
                    code="PYTHON_SYNTAX_ERROR",
                    message="Extracted code is not valid Python.",
                    raw_response=raw_response,
                    data=CodeBlock(code=code, language=self.language, is_valid_python=False),
                    details={
                        "line": exc.lineno,
                        "offset": exc.offset,
                        "text": exc.text.strip() if exc.text else None,
                        "message": exc.msg,
                    },
                )

            return ParseResult.ok(
                data=CodeBlock(code=code, language=self.language, is_valid_python=True),
                raw_response=raw_response,
            )

        return ParseResult.ok(
            data=CodeBlock(code=code, language=self.language, is_valid_python=None),
            raw_response=raw_response,
        )

    def _extract_code(self, text: str) -> str | None:
        python_match = _PYTHON_FENCE_PATTERN.search(text)
        if python_match:
            return python_match.group(1).strip()

        generic_match = _GENERIC_FENCE_PATTERN.search(text)
        if generic_match:
            return generic_match.group(1).strip()

        raw_code = text.strip()
        return raw_code if raw_code else None

    def _is_short_plain_text(self, code: str) -> bool:
        stripped = code.strip()
        if "\n" in stripped:
            return False
        return stripped.isalpha() and len(stripped) < 12
