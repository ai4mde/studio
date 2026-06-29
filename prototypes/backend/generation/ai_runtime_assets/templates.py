"""M01 Template-Driven Prompt Construction - vendored subset (pure Python, no Django).
Extracted from Studio api/model/llm/templates/{registry,renderer}.py: the two modules are
merged and their relative imports removed; logic unchanged. Registry reduced to the Library
entry (A-lite)."""
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound


@dataclass(frozen=True)
class TemplateEntry:
    prompt_name: str
    filename: str


TEMPLATE_DIR = Path(__file__).resolve().parent / "prompt_templates"

TEMPLATE_REGISTRY = {
    "library_late_risk_v1": TemplateEntry(
        prompt_name="library_late_risk_v1",
        filename="library_late_risk_v1.j2",
    ),
}


def get_template_entry(prompt_name: str) -> TemplateEntry:
    entry = TEMPLATE_REGISTRY.get(prompt_name)
    if entry is None:
        available = ", ".join(sorted(TEMPLATE_REGISTRY.keys()))
        raise ValueError(f"Invalid prompt name: {prompt_name}. Available: {available}")
    return entry


_environment = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    undefined=StrictUndefined,
    autoescape=False,
    keep_trailing_newline=True,
)


def render_prompt(prompt_name: str, context: Mapping[str, Any]) -> str:
    if context is None:
        raise ValueError("No input data given")
    entry = get_template_entry(prompt_name)
    try:
        template = _environment.get_template(entry.filename)
    except TemplateNotFound as exc:
        raise FileNotFoundError(f"Template file not found: {entry.filename}") from exc
    return template.render(**context)
