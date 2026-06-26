from .uml_mapping.metadata_context import _actor_name_from_context, _fetch_system_context_data
from .section_utils import (
    _ensure_workflow_pages,
    _normalize_activity_action_sections,
    _normalize_chrome_sections,
)
from .token_normalizer import _as_list
from .uml_mapping.usecase_workflow import _build_usecase_navigation


def _workflow_system_context(system_id: str | None, system_context: dict | None) -> dict | None:
    if system_context is not None:
        return system_context
    if system_id:
        return _fetch_system_context_data(system_id)
    return None


def _workflow_model_attrs(system_context: dict) -> dict:
    model_attrs = {}
    for c in _as_list(system_context.get("classifiers"), "classifiers"):
        cdata = c.get("data") or {}
        cname = cdata.get("name")
        if cname:
            model_attrs[cname] = {
                a.get("name")
                for a in cdata.get("attributes", [])
                if a.get("name")
            }
    return model_attrs


def _workflow_navigation(system_context: dict, actor_id: str | None, usecase_navigation: dict | None) -> dict:
    if usecase_navigation is not None:
        return usecase_navigation
    actor_name = _actor_name_from_context(system_context, actor_id)
    return _build_usecase_navigation(system_context, str(actor_id or ""), actor_name)


def _apply_builtin_workflow_logic(
    interface_data: dict,
    system_id: str | None,
    actor_id: str | None,
    *,
    system_context: dict | None = None,
    usecase_navigation: dict | None = None,
    model_attrs: dict | None = None,
) -> dict:
    """Apply UML-derived workflow pages and sections to interface data."""
    data = dict(interface_data or {})
    pages = list(data.get("pages") or [])
    sections = list(data.get("sections") or [])

    system_context = _workflow_system_context(system_id, system_context)
    if system_context:
        model_attrs = model_attrs if model_attrs is not None else _workflow_model_attrs(system_context)
        usecase_navigation = _workflow_navigation(system_context, actor_id, usecase_navigation)
        workflow_steps = usecase_navigation.get("workflow_steps") or []
        pages, sections = _ensure_workflow_pages(
            pages, sections, workflow_steps, model_attrs, usecase_navigation
        )

    sections = _normalize_chrome_sections(
        _normalize_activity_action_sections(pages, sections)
    )
    data["pages"] = pages
    data["sections"] = sections
    return data
