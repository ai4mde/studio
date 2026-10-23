"""Explicit runtime results; a skipped/error result is never an implicit write."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class HistoryOutcome:
    rows: list[dict] = field(default_factory=list)
    diagnostics: dict = field(default_factory=dict)
    skip_reason: str | None = None


@dataclass
class ContextOutcome:
    context: dict = field(default_factory=dict)
    diagnostics: dict = field(default_factory=dict)
    skip_reason: str | None = None


@dataclass
class RunOutcome:
    invocation_id: str = field(default_factory=lambda: str(uuid4()))
    evaluated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "success"
    value: str | None = None
    should_write: bool = False
    skip_reason: str | None = None
    reason: str | None = None
    mode: str | None = None
    error: dict | None = None
    failed_step: str | None = None
    step_details: list[dict] = field(default_factory=list)
    diagnostics: dict = field(default_factory=dict)
    context: dict = field(default_factory=dict)
    raw_output: str = ""
    parsed_output: Any = None
    prompts: list[dict] = field(default_factory=list)
    calls: list[dict] = field(default_factory=list)
