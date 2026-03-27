from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Generic, Optional, TypeVar


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
    def fail(
        cls,
        *,
        code: str,
        message: str,
        raw_response: str,
        details: Optional[Dict[str, Any]] = None,
        data: Optional[T] = None,
    ) -> "ParseResult[T]":
        return cls(
            success=False,
            data=data,
            error=ParseError(code=code, message=message, details=details or {}),
            raw_response=raw_response,
        )


class OutputParser(Generic[T]):
    def parse(self, raw_response: str) -> ParseResult[T]:
        raise NotImplementedError
