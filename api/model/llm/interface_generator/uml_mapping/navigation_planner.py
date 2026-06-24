import re
from collections import defaultdict

from .interface_planner import (
    _MODEL_PERSON, _MODEL_DOCUMENT, _MODEL_CATEGORY,
    _FORM_ADDRESS, _FORM_PAYMENT, _FORM_REVIEW,
    _field_category, _pick_fields_by_names, _ROLE_CATEGORY_ORDER, _EXCLUDED_FORM,
)


DATA_SECTION_ROLES = {
    "object_collection",
    "object_detail",
    "object_summary",
    "child_collection",
    "object_form",
}

_ACTIVITY_FORM_TERMS = re.compile(
    r"\b(enter|fill|provide|submit|create|update|edit|write|upload|add|register|confirm|book|pay|record|input)\b",
    re.I,
)
_ACTIVITY_LIST_TERMS = re.compile(
    r"\b(list|browse|manage|track|monitor|search|select|choose|review|approve|check|verify|pick|items)\b",
    re.I,
)
_ACTIVITY_SELECT_TERMS = re.compile(r"\b(search|select|choose|pick|browse)\b", re.I)


def _section_id(name: str) -> str:
    """Convert a free-form label into a stable section id."""
    s = re.sub(r"[^a-zA-Z0-9]+", "_", str(name or "").strip()).strip("_").lower()
    return s or "section"


def _page_name(page_id: str) -> str:
    """Convert a free-form label into the generated page class/name format."""
    return str(page_id or "Page").replace("_", " ").title().replace(" ", "_")


def _is_strict_child_collection_model(model_name: str) -> bool:
    """Detect models that should only appear as child collections."""
    name_l = str(model_name or "").lower()
    return any(term in name_l for term in ("item", "line", "entry", "row", "detail", "selection", "option"))


_ROLE_CATEGORY_ORDER_OOUI = {
    **_ROLE_CATEGORY_ORDER,
    "object_summary": ["status", "metric", "temporal"],
}


def _pick_fields(model_attrs: dict, model: str, role: str, limit: int = 8) -> list[str]:
    """Pick fields."""
    all_attrs = [f for f in (model_attrs.get(model) or []) if f]
    excluded = _EXCLUDED_FORM if role == "object_form" else frozenset({"id"})
    attr_names = [f for f in all_attrs if f.lower() not in excluded]
    return _pick_fields_by_names(attr_names, role, _ROLE_CATEGORY_ORDER_OOUI, limit, fallback=all_attrs)


def _layout_for_page_role(page: dict) -> str:
    """Choose a section layout from a generated page role."""
    roles = set(page.get("roles") or [])
    page_id = str(page.get("id") or page.get("page_id") or "").lower()

    if "detail_workspace" in roles or "workflow_entry" in roles:
        return "detail"
    if "collection_workspace" in roles:
        if any(t in page_id for t in ("catalog", "browse", "gallery", "photo", "image", "product")):
            return "gallery"
        if any(t in page_id for t in ("order", "invoice", "log", "history", "queue", "cart")):
            return "list"
        return "table"
    if "object_workspace" in roles:
        return "detail"
    return "card"


def _operations_for_model(model: str, actor_permissions: dict) -> list[str]:
    """Return CRUD operations allowed for a model by actor permissions."""
    permissions = set(actor_permissions.get(model) or [])
    operations = ["view"]
    for operation in ("create", "update", "delete"):
        if operation in permissions:
            operations.append(operation)
    return operations


def _operations_for_page(model: str, actor_permissions: dict, page: dict) -> list[str]:
    """Return CRUD operations allowed for the page role and model."""
    roles = set(page.get("roles") or [])
    page_text = f"{page.get('id') or page.get('page_id') or ''} {page.get('name') or page.get('page_name') or ''}".lower()
    operation_kind = str(page.get("operation_kind") or page.get("kind") or "").lower()
    if "collection_workspace" in roles and (
        operation_kind in {"view_collection", "select_existing"} or _ACTIVITY_SELECT_TERMS.search(page_text)
    ):
        operations = ["view"]
        if operation_kind == "select_existing" or _ACTIVITY_SELECT_TERMS.search(page_text):
            operations.append("select")
        return operations
    return _operations_for_model(model, actor_permissions)


def _editable_fields_for_model(model_attrs: dict, model: str, role: str, operations: list[str]) -> list[str]:
    """Choose fields that should be editable for the page role and operations."""
    if not ({"create", "update"} & set(operations)):
        return []
    excluded = {"id", f"{_section_id(model)}_id", "created_at", "updated_at", "created_on", "updated_on"}
    return [field for field in _pick_fields(model_attrs, model, "object_form", 10) if field.lower() not in excluded]


_CHILD_LINE_ITEM = re.compile(r"item|line|cart|basket|order|invoice|receipt", re.I)


def _component_for_section(role: str, layout: str, model: str = "", page_id: str = "") -> str:
    """Choose the component type for a generated section role and layout."""
    model_l = str(model or "").lower()
    ctx = f"{model_l} {page_id or ''}".lower()

    if role == "child_collection":
        return "LineItemList" if _CHILD_LINE_ITEM.search(ctx) else "RelatedObjectList"
    if role == "object_summary":
        return "SummaryPanel"
    if role == "object_detail":
        if _MODEL_DOCUMENT.search(model_l):
            return "DocumentPanel"
        if _MODEL_PERSON.search(model_l):
            return "ProfilePanel"
        return "DetailPanel"
    if role == "object_form":
        if _FORM_ADDRESS.search(ctx):
            return "AddressForm"
        if _FORM_PAYMENT.search(ctx):
            return "PaymentMethodForm"
        if _FORM_REVIEW.search(ctx):
            return "ReviewForm"
        return "ObjectForm"
    if layout == "gallery":
        if _MODEL_CATEGORY.search(model_l):
            return "CategoryTileGrid"
        if _MODEL_PERSON.search(model_l):
            return "PersonCardGrid"
        return "CardGrid"
    if layout == "table":
        return "DataTable"
    if layout == "list":
        return "ObjectList"
    if layout == "form":
        return "ObjectForm"
    if layout == "filter":
        return "FilterPanel"
    return "CardGrid" if layout == "card" else "SectionPanel"


def _field_layout_for_component(component: str, attrs: list[str], related_attrs: list[str] | None = None) -> dict:
    """Build the field-layout slots expected by a section component."""
    related_attrs = related_attrs or []
    all_attrs = attrs + related_attrs

    def first(*names: str) -> str:
        """Provide a local helper for _field_layout_for_component."""
        for name in names:
            if name in all_attrs:
                return name
        return ""

    if component in {"ProductCardGrid", "CardGrid", "CategoryTileGrid", "PersonCardGrid"}:
        return {
            "image": first("image_url", "photo_url", "avatar_url", "thumbnail_url"),
            "video": first("video_url", "trailer_url", "media_url"),
            "title": first("name", "title", "full_name"),
            "subtitle": first("brand", "category", "role", "description"),
            "primary": first("price", "total", "status"),
            "secondary": [field for field in all_attrs if field not in {first("image_url", "photo_url", "avatar_url", "thumbnail_url"), first("video_url", "trailer_url", "media_url"), first("name", "title", "full_name"), first("brand", "category", "role", "description"), first("price", "total", "status")}][:3],
        }
    if component in {"DataTable", "ObjectList", "LineItemList", "RelatedObjectList"}:
        return {"columns": [{"field": field, "label": field.replace("_", " ").title()} for field in all_attrs[:8]]}
    if component in {"DetailPanel", "ProductDetailPanel", "SummaryPanel"}:
        return {
            "hero": first("image_url", "photo_url", "thumbnail_url"),
            "video": first("video_url", "trailer_url", "media_url"),
            "title": first("name", "title"),
            "description": first("description", "summary"),
            "facts": [field for field in all_attrs if field not in {first("image_url", "photo_url", "thumbnail_url"), first("video_url", "trailer_url", "media_url"), first("name", "title"), first("description", "summary")}][:6],
        }
    if component.endswith("Form") or component == "ObjectForm":
        return {"groups": [{"title": "Details", "fields": attrs[:8]}], "submit_label": "Save"}
    return {}


def _section_for_page(page: dict, model_attrs: dict, actor_permissions: dict | None = None) -> dict | None:
    """Build section for page."""
    model = page.get("primary_model") or ""
    if not model:
        return None
    actor_permissions = actor_permissions or {}
    page_id = page.get("id") or page.get("page_id")
    roles = set(page.get("roles") or [])
    layout = _layout_for_page_role(page)
    role = "object_detail" if layout == "detail" else "object_collection"
    if "workflow_entry" in roles:
        role = "object_summary"
    operations = _operations_for_page(model, actor_permissions, page)
    style = {
        "color": "accent",
        "density": "compact" if layout in {"list", "table"} else "normal",
        "shadow": "sm",
        "border": "light",
        "bg": "white",
    }
    if layout in {"gallery", "card"}:
        style.update({"display_mode": "grid", "columns": "3", "card_style": "product" if model.lower() == "product" else "default"})
    if layout == "list":
        style["list_style"] = "default"
    visible_fields = _pick_fields(model_attrs, model, role)
    component = _component_for_section(role, layout, model, page_id)
    return {
        "id": f"{page_id}_{_section_id(model)}_{role}",
        "page_id": page_id,
        "role": role,
        "name": f"{page.get('name') or page.get('page_name') or _page_name(page_id)} {model}",
        "layout": layout,
        "component": component,
        "primary_model": model,
        "visible_fields": visible_fields,
        "editable_fields": _editable_fields_for_model(model_attrs, model, role, operations),
        "related_visible_fields": [],
        "field_layout": _field_layout_for_component(component, visible_fields),
        "operations": operations,
        "query": {},
        "style": style,
        "col_span": 12,
    }


def _child_section(page_id: str, model: str, model_attrs: dict, label: str = "", related_models: list[str] | None = None) -> dict:
    """Build a related child collection section for a generated page."""
    style = {
        "color": "accent",
        "density": "compact",
        "shadow": "sm",
        "border": "light",
        "bg": "white",
        "list_style": "cart-item" if any(term in f"{page_id} {model}".lower() for term in ("cart", "basket", "item", "line")) else "default",
    }
    editable = [field for field in ("quantity", "status") if field in (model_attrs.get(model) or set())]
    visible_fields = _pick_fields(model_attrs, model, "child_collection")
    related_visible = []
    for related_model in related_models or []:
        if related_model == model or related_model not in model_attrs:
            continue
        related_attrs = model_attrs.get(related_model) or set()
        if related_model.lower() == "product":
            related_visible.extend([f"{related_model}.{field}" for field in ("name", "image_url", "video_url", "price") if field in related_attrs])
        elif related_model.lower() in model.lower() or model.lower() in related_model.lower():
            continue
    return {
        "id": f"{page_id}_{_section_id(model)}_child_collection",
        "page_id": page_id,
        "role": "child_collection",
        "name": label or f"{model} Items",
        "layout": "list",
        "component": _component_for_section("child_collection", "list", model, page_id),
        "primary_model": model,
        "visible_fields": visible_fields,
        "editable_fields": editable,
        "related_visible_fields": related_visible,
        "field_layout": _field_layout_for_component(
            _component_for_section("child_collection", "list", model, page_id),
            visible_fields,
            related_visible,
        ),
        "operations": ["view", "update", "delete"],
        "data_source": {"mode": "query", "from": {"model": model}, "joins": []} if related_visible else {},
        "query": {},
        "style": style,
        "col_span": 12,
    }


def _activity_layout(step_name: str) -> str:
    """Build activity layout."""
    if _ACTIVITY_LIST_TERMS.search(step_name):
        return "list"
    if _ACTIVITY_FORM_TERMS.search(step_name):
        return "form"
    return "detail"


def _sections_for_activity_step(step: dict, model_attrs: dict, workflow_entries: list | None = None) -> list[dict]:
    """Build sections for activity step."""
    known = set(model_attrs.keys())
    page_id = step.get("page_id") or _section_id(step.get("page_name") or "workflow")

    models = [m for m in (step.get("classes") or []) if m in known]
    if not models and workflow_entries:
        related: list[str] = []
        for entry in workflow_entries:
            related.extend(entry.get("pre_workflow_collections") or [])
            related.extend(entry.get("related_models") or [])
            if entry.get("primary_model"):
                related.append(entry["primary_model"])
        models = [m for m in dict.fromkeys(related) if m in known][:1]

    result = []
    for model in models[:2]:
        layout = _activity_layout(step.get("activity_node_name", ""))
        is_select_step = bool(_ACTIVITY_SELECT_TERMS.search(step.get("activity_node_name", "")))
        if layout == "form":
            role = "object_form"
        elif layout in {"list", "table", "card", "gallery"}:
            role = "object_collection"
        else:
            role = "object_detail"
        visible = _pick_fields(model_attrs, model, role)
        component = _component_for_section(role, layout, model, page_id)
        style: dict = {
            "color": "accent",
            "density": "compact" if layout in {"list", "table"} else "normal",
            "shadow": "sm", "border": "light", "bg": "white",
        }
        if layout == "form":
            style["form_style"] = "step"
        result.append({
            "id": f"{page_id}_{_section_id(model)}_activity_action",
            "page_id": page_id,
            "role": role,
            "name": f"{step.get('activity_node_name') or 'Task'} — {model}",
            "layout": layout,
            "component": component,
            "primary_model": model,
            "visible_fields": visible,
            "editable_fields": visible if layout == "form" else [],
            "related_visible_fields": [],
            "field_layout": _field_layout_for_component(component, visible),
            "operations": {
                "create": layout == "form" and not is_select_step,
                "update": layout in {"form", "list", "table", "detail"} and not is_select_step,
                "delete": layout in {"list", "table"},
                "select": is_select_step,
            },
            "style": style,
            "col_span": 12,
        })
    return result


def build_navigation_plan(usecase_navigation: dict, model_attrs: dict | None = None, workflow_steps: list | None = None) -> dict:
    """Build navigation plan."""
    model_attrs = model_attrs or {}
    actor_permissions = usecase_navigation.get("actor_permissions") or {}
    pages = []
    sections = []
    operations = []
    workflows = []
    page_sections = defaultdict(list)

    for page in usecase_navigation.get("pages") or []:
        normalized = {
            "id": page.get("page_id"),
            "name": page.get("page_name") or _page_name(page.get("page_id")),
            "role": (page.get("roles") or ["object_workspace"])[0],
            "roles": page.get("roles") or [],
            "primary_model": page.get("primary_model", ""),
            "operation_kind": page.get("operation_kind") or page.get("kind") or "",
            "usecases": page.get("usecases") or [],
            "nav": page.get("page_id") in set(usecase_navigation.get("nav_bar_pages") or []),
            "sections": [],
        }
        main_section = _section_for_page(normalized, model_attrs, actor_permissions)
        if main_section:
            sections.append(main_section)
            page_sections[normalized["id"]].append(main_section["id"])
        pages.append(normalized)

    for entry in usecase_navigation.get("workflow_entry_points") or []:
        page_id = entry.get("page_id")
        if not page_id:
            continue
        related_models = [m for m in entry.get("related_models") or [] if m in model_attrs]
        for model in entry.get("pre_workflow_collections") or []:
            if model not in model_attrs:
                continue
            if not _is_strict_child_collection_model(model):
                continue
            page_stem = re.sub(r"[^a-z0-9]", "", page_id.lower())
            model_stem = re.sub(r"[^a-z0-9]", "", model.lower())
            if page_stem and not model_stem.startswith(page_stem):
                continue
            section = _child_section(page_id, model, model_attrs, related_models=related_models)
            if section["id"] not in {s["id"] for s in sections}:
                sections.append(section)
                page_sections[page_id].append(section["id"])
        workflow_section = {
            "id": f"{page_id}_workflow_entry",
            "page_id": page_id,
            "role": "workflow_entry",
            "name": entry.get("label") or "Start Workflow",
            "layout": "activity_start",
            "component": "StartWorkflowButton",
            "primary_model": "",
            "visible_fields": [],
            "editable_fields": [],
            "related_visible_fields": [],
            "field_layout": {},
            "behavior": {"type": "start_workflow", "target_activity_node_id": entry.get("starts_activity_node_id", "")},
            "operations": ["start_workflow"],
            "label": entry.get("button_label") or entry.get("label") or "Start",
            "style": {"cta_label": entry.get("button_label") or entry.get("label") or "Start"},
            "col_span": 12,
        }
        sections.append(workflow_section)
        page_sections[page_id].append(workflow_section["id"])
        workflows.append({
            "entry_page": page_id,
            "entry_label": workflow_section["label"],
            "starts_activity_node_id": entry.get("starts_activity_node_id", ""),
            "starts_activity_name": entry.get("starts_activity_name", ""),
        })

    for usecase in usecase_navigation.get("usecases") or []:
        mapping = usecase.get("ui_mapping") or {}
        if mapping.get("role") == "inline_operation":
            operations.append({
                "usecase": usecase.get("name"),
                "kind": mapping.get("operation_kind", "object_operation"),
                "page_id": mapping.get("page_id"),
                "source_model": mapping.get("page_model") or usecase.get("primary_model"),
                "target_model": mapping.get("target_model", ""),
            })

    # Activity pages — one page + content sections per workflow step
    workflow_entries = usecase_navigation.get("workflow_entry_points") or []
    existing_section_ids = {s["id"] for s in sections}
    existing_page_ids = {p["id"] for p in pages}
    for step in (workflow_steps or []):
        page_id = step.get("page_id")
        if not page_id:
            continue
        if page_id not in existing_page_ids:
            pages.append({
                "id": page_id,
                "name": step.get("page_name") or _page_name(page_id),
                "role": "activity_action",
                "roles": ["activity_action"],
                "primary_model": next((m for m in (step.get("classes") or []) if m in model_attrs), ""),
                "usecases": [],
                "nav": False,
                "sections": [],
            })
            existing_page_ids.add(page_id)
        for sec in _sections_for_activity_step(step, model_attrs, workflow_entries):
            if sec["id"] not in existing_section_ids:
                sections.append(sec)
                page_sections[page_id].append(sec["id"])
                existing_section_ids.add(sec["id"])

    for page in pages:
        page["sections"] = page_sections.get(page["id"], [])

    return {
        "pages": pages,
        "sections": sections,
        "operations": operations,
        "workflows": workflows,
        "_note": "OOUI plan: pages are object workspaces; sections have one primary_model; activity pages have form/list/detail sections per workflow step.",
    }
