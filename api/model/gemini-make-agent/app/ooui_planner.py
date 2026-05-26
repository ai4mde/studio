import re
from collections import defaultdict


DATA_SECTION_ROLES = {
    "object_collection",
    "object_detail",
    "object_summary",
    "child_collection",
    "object_form",
}


def _section_id(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", str(name or "").strip()).strip("_").lower()
    return s or "section"


def _page_name(page_id: str) -> str:
    return str(page_id or "Page").replace("_", " ").title().replace(" ", "_")


def _is_child_collection_model(model_name: str, page_terms: str = "") -> bool:
    name_l = str(model_name or "").lower()
    terms_l = str(page_terms or "").lower()
    if any(term in name_l for term in ("item", "line", "entry", "row", "detail", "selection")):
        return True
    return any(term in terms_l for term in ("cart", "basket", "checkout", "order", "request", "application")) and any(
        term in name_l for term in ("product", "service", "option")
    )


def _is_strict_child_collection_model(model_name: str) -> bool:
    name_l = str(model_name or "").lower()
    return any(term in name_l for term in ("item", "line", "entry", "row", "detail", "selection", "option"))


def _pick_fields(model_attrs: dict, model: str, role: str, limit: int = 8) -> list[str]:
    attrs = list(model_attrs.get(model) or [])
    preferred_by_role = {
        "object_collection": ["image_url", "video_url", "name", "title", "price", "status", "rating", "created_at"],
        "object_detail": ["image_url", "video_url", "name", "title", "description", "price", "status", "rating"],
        "object_summary": ["status", "total", "total_price", "item_count", "created_at"],
        "child_collection": ["name", "title", "quantity", "unit_price", "price", "subtotal", "status"],
        "object_form": ["name", "title", "address", "street", "city", "postcode", "method", "status"],
    }
    selected = [field for field in preferred_by_role.get(role, []) if field in attrs]
    selected.extend([field for field in attrs if field and field not in selected and field.lower() != "id"])
    return selected[:limit] or attrs[:limit]


def _layout_for_page_role(page: dict) -> str:
    roles = set(page.get("roles") or [])
    page_id = str(page.get("id") or page.get("page_id") or "").lower()
    model = str(page.get("primary_model") or "").lower()
    if "detail_workspace" in roles:
        return "detail"
    if "workflow_entry" in roles:
        return "detail"
    if any(term in page_id for term in ("catalog", "product", "browse", "search")):
        return "gallery"
    if any(term in page_id or term in model for term in ("order", "cart", "list")):
        return "list"
    return "detail" if "object_workspace" in roles else "card"


def _operations_for_model(model: str, actor_permissions: dict) -> list[str]:
    permissions = set(actor_permissions.get(model) or [])
    operations = ["view"]
    for operation in ("create", "update", "delete"):
        if operation in permissions:
            operations.append(operation)
    return operations


def _editable_fields_for_model(model_attrs: dict, model: str, role: str, operations: list[str]) -> list[str]:
    if not ({"create", "update"} & set(operations)):
        return []
    excluded = {"id", f"{_section_id(model)}_id", "created_at", "updated_at", "created_on", "updated_on"}
    return [field for field in _pick_fields(model_attrs, model, "object_form", 10) if field.lower() not in excluded]


def _component_for_section(role: str, layout: str, model: str = "", page_id: str = "") -> str:
    model_l = str(model or "").lower()
    page_l = str(page_id or "").lower()
    if role == "child_collection":
        return "LineItemList" if any(term in f"{model_l} {page_l}" for term in ("item", "line", "cart", "order")) else "RelatedObjectList"
    if role == "object_summary":
        return "SummaryPanel"
    if role == "object_detail":
        if model_l == "product":
            return "ProductDetailPanel"
        return "DetailPanel"
    if role == "object_form":
        if "payment" in model_l or "payment" in page_l:
            return "PaymentMethodForm"
        if "address" in model_l or "address" in page_l:
            return "AddressForm"
        if "review" in model_l or "review" in page_l:
            return "ReviewForm"
        return "ObjectForm"
    if layout == "gallery":
        if model_l == "product":
            return "ProductCardGrid"
        if "category" in model_l:
            return "CategoryTileGrid"
        if any(term in model_l for term in ("user", "customer", "seller", "employee", "doctor", "agent", "member")):
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
    related_attrs = related_attrs or []
    all_attrs = attrs + related_attrs

    def first(*names: str) -> str:
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
    operations = _operations_for_model(model, actor_permissions)
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


def build_ooui_plan_from_navigation(usecase_navigation: dict, model_attrs: dict | None = None) -> dict:
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
            if page_id == "cart" and model.lower() not in {"cartitem", "cart item"}:
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

    for page in pages:
        page["sections"] = page_sections.get(page["id"], [])

    return {
        "pages": pages,
        "sections": sections,
        "operations": operations,
        "workflows": workflows,
        "_note": "OOUI plan: pages are object workspaces; sections have one primary_model; related fields are read-only; inline operations attach to object sections.",
    }
