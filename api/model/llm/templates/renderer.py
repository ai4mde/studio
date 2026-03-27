from typing import Any, Mapping

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound

from .registry import TEMPLATE_DIR, get_template_entry


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
