import re
from collections import defaultdict


_FIELD_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("image",    re.compile(r"(image|photo|avatar|picture|thumbnail|banner|cover|logo|icon)(_url|_src|_path)?$", re.I)),
    ("video",    re.compile(r"(video|clip|recording)(_url|_src)?$", re.I)),
    ("name",     re.compile(r"^(name|title|full_name|display_name|label|heading|caption|subject)$", re.I)),
    ("status",   re.compile(r"^(status|state|phase|stage)$", re.I)),
    ("flag",     re.compile(r"^(is|has|can|allow|enable)_|^(active|enabled|visible|featured|verified|published|archived)$", re.I)),
    ("code",     re.compile(r"^(sku|code|ref|barcode|serial|number|identifier)$", re.I)),
    ("category", re.compile(r"^(category|type|kind|genre|group|class|tier|level|tag|section)$", re.I)),
    ("metric",   re.compile(r"^(price|amount|total|subtotal|cost|fee|tax|discount|quantity|qty|count|rating|score|stock|balance|weight|size|duration)$", re.I)),
    ("describe", re.compile(r"^(description|bio|summary|overview|notes|content|body|details|info|about|message|text|comment|remarks)$", re.I)),
    ("contact",  re.compile(r"^(email|phone|mobile|tel|fax|website)$", re.I)),
    ("address",  re.compile(r"^(address|street|city|state|province|postcode|postal_code|zip|country|region|district|location)$", re.I)),
    ("temporal", re.compile(r"(_at|_date|_time|_on)$", re.I)),
]

_ROLE_CATEGORY_ORDER: dict[str, list[str]] = {
    "object_collection": ["image", "video", "name", "status", "code", "category", "metric", "temporal", "flag"],
    "object_detail":     ["image", "video", "name", "describe", "status", "metric", "contact", "category", "temporal"],
    "object_form":       ["name", "describe", "category", "status", "metric", "contact", "address", "temporal"],
    "child_collection":  ["name", "code", "metric", "status"],
    "filter":            ["name", "status", "category", "metric", "temporal", "flag"],
}

_EXCLUDED_FORM = frozenset({
    "id", "uuid", "slug",
    "created_at", "updated_at", "created_on", "updated_on", "deleted_at",
})


def _field_category(field_name: str) -> str | None:
    for category, pattern in _FIELD_PATTERNS:
        if pattern.search(field_name):
            return category
    return None


def _pick_fields_by_names(
    attr_names: list[str],
    role: str,
    category_order: dict,
    limit: int = 8,
    fallback: list[str] | None = None,
) -> list[str]:
    order = category_order.get(role, [])
    buckets: dict[str, list[str]] = {cat: [] for cat in order}
    tail: list[str] = []
    for field in attr_names:
        cat = _field_category(field)
        if cat and cat in buckets:
            buckets[cat].append(field)
        else:
            tail.append(field)
    result: list[str] = []
    seen: set[str] = set()
    for cat in order:
        for f in buckets[cat]:
            if f not in seen:
                result.append(f)
                seen.add(f)
    for f in tail:
        if f not in seen:
            result.append(f)
            seen.add(f)
    return result[:limit] or (fallback or [])[:limit]


_MODEL_PERSON = re.compile(
    r"user|person|people|customer|client|patient|doctor|member|staff|employee|"
    r"contact|vendor|seller|supplier|student|teacher|author|owner|passenger|"
    r"operator|admin|applicant|borrower|officer|analyst|reviewer",
    re.I,
)
_MODEL_DOCUMENT = re.compile(r"report|document|record|contract|invoice|receipt|statement|transcript|certificate|permit|license|policy|agreement", re.I)
_MODEL_CATEGORY = re.compile(r"categor|genre|collection|group|class|tag|label", re.I)

_FORM_ADDRESS = re.compile(r"address|shipping|delivery|mailing", re.I)
_FORM_PAYMENT = re.compile(r"payment|checkout|billing|charge|subscription", re.I)
_FORM_REVIEW  = re.compile(r"review|rating|feedback|assessment|evaluation|testimonial", re.I)


DATA_SECTION_ROLES = {
    "object_collection",
    "object_detail",
    "object_summary",
    "child_collection",
    "object_form",
    "filter",
    "workflow_action",
    "workflow_history",
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
        "query": _query_for_section(
            "child_collection", model, visible_fields,
            parent_model=(related_models or [""])[0],
        ),
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


def _filter_section_for_model(
    page_id: str,
    model: str,
    model_attrs: dict,
) -> dict:
    """Build a FilterPanel section for a collection page."""
    filter_fields = _pick_fields(model_attrs, model, "filter", limit=5)
    return {
        "id": f"{page_id}_{_section_id(model)}_filter",
        "page_id": page_id,
        "role": "filter",
        "name": f"Search {model}",
        "layout": "filter",
        "component": "FilterPanel",
        "primary_model": model,
        "visible_fields": filter_fields,
        "editable_fields": filter_fields,
        "related_visible_fields": [],
        "field_layout": {},
        "operations": {"create": False, "update": False, "delete": False, "select": False},
        "query": _query_for_section("filter", model, filter_fields),
        "style": {"color": "accent", "density": "compact", "shadow": "none", "border": "light", "bg": "light"},
        "col_span": 12,
    }


def _collection_section_for_model(
    page_id: str,
    page: dict,
    model: str,
    model_attrs: dict,
    actor_permissions: dict,
    is_select: bool = False,
    layout_override: str = "",
    component_override: str = "",
) -> dict:
    """Build the primary data-collection section for a collection/browse page."""
    layout = layout_override or _layout_for_page_role(page)
    if layout == "detail":
        layout = "table"
    role = "object_collection"
    visible_fields = _pick_fields(model_attrs, model, role)
    component = component_override or _component_for_section(role, layout, model, page_id)
    operations = _operations_for_page(model, actor_permissions, page)
    style: dict = {
        "color": "accent",
        "density": "compact" if layout in {"list", "table"} else "normal",
        "shadow": "sm",
        "border": "light",
        "bg": "white",
    }
    if layout in {"gallery", "card"}:
        style.update({"display_mode": "grid", "columns": "3"})
    if layout == "list":
        style["list_style"] = "default"
    return {
        "id": f"{page_id}_{_section_id(model)}_object_collection",
        "page_id": page_id,
        "role": role,
        "name": f"{page.get('name') or _page_name(page_id)} {model}",
        "layout": layout,
        "component": component,
        "primary_model": model,
        "visible_fields": visible_fields,
        "editable_fields": _editable_fields_for_model(model_attrs, model, role, operations) if not is_select else [],
        "related_visible_fields": [],
        "field_layout": _field_layout_for_component(component, visible_fields),
        "operations": {
            "create": not is_select and "create" in operations,
            "update": not is_select and "update" in operations,
            "delete": not is_select and "delete" in operations,
            "select": is_select,
        },
        "query": _query_for_section("object_collection", model, visible_fields),
        "style": style,
        "col_span": 12,
    }


def _detail_section_for_model(
    page_id: str,
    model: str,
    model_attrs: dict,
    actor_permissions: dict,
    label: str = "",
    editable: bool = True,
) -> dict:
    """Build an ObjectDetail section."""
    role = "object_detail"
    visible_fields = _pick_fields(model_attrs, model, role)
    component = _component_for_section(role, "detail", model, page_id)
    return {
        "id": f"{page_id}_{_section_id(model)}_object_detail",
        "page_id": page_id,
        "role": role,
        "name": label or f"{model} Details",
        "layout": "detail",
        "component": component,
        "primary_model": model,
        "visible_fields": visible_fields,
        "editable_fields": _editable_fields_for_model(model_attrs, model, role, list(actor_permissions.get(model) or ["view", "update"])) if editable else [],
        "related_visible_fields": [],
        "field_layout": _field_layout_for_component(component, visible_fields),
        "operations": {"create": False, "update": editable, "delete": editable, "select": False},
        "query": _query_for_section("object_detail", model, visible_fields),
        "style": {"color": "accent", "density": "normal", "shadow": "sm", "border": "none", "bg": "white"},
        "col_span": 12,
    }


# ---------------------------------------------------------------------------
# UI Pattern → Section Composition
# ---------------------------------------------------------------------------
# Pattern table (Interaction Profile → OOUI UI Pattern → Section list):
#
#   collection_workspace + Search/StateTransition   → FilterPanel + DataCollection
#   collection_workspace (Lookup/simple)            → FilterPanel + DataList
#   detail_workspace                                → ObjectDetail + ChildCollections
#   workflow_entry                                  → SummaryPanel + WorkflowStart
#   object_workspace (profile/settings)             → ObjectDetail
#   select_existing (operation_kind)                → FilterPanel + DataCollection (select)
#   form / create                                   → ObjectForm
# ---------------------------------------------------------------------------

def _query_for_section(
    role: str,
    model: str,
    visible_fields: list[str] | None = None,
    parent_model: str = "",
    operation_kind: str = "",
) -> dict:
    """Auto-generate a query descriptor for a section based on its role.

    Generates interface-metadata-compatible query objects:
      object_collection  → list query with filter placeholder + ordering
      object_detail      → single-object lookup by $params.id
      object_form        → same as detail (edit form pre-populates)
      object_summary     → same as detail (context panel)
      child_collection   → related list filtered by parent FK
      filter             → filter-form descriptor pointing at the collection
      workflow_*         → empty (driven by workflow engine)
    """
    fields = list(visible_fields or [])
    if role == "object_collection":
        q: dict = {"model": model, "filter": {}, "limit": 20}
        # Auto-detect ordering: prefer created_at, status, id
        order_candidates = ["created_at", "updated_at", "name", "id"]
        for f in order_candidates:
            if f in fields:
                q["order_by"] = [f"-{f}" if f in {"created_at", "updated_at"} else f]
                break
        if "search_fields" not in q and fields:
            # Text fields for search
            text_fields = [f for f in fields if any(t in f for t in ("name", "title", "label", "code", "description"))]
            if text_fields:
                q["search_fields"] = text_fields[:3]
        return q
    if role in {"object_detail", "object_form", "object_summary"}:
        return {"model": model, "lookup": {"id": "$params.id"}}
    if role == "child_collection":
        # FK is parent_model_id on child table
        fk = f"{parent_model.lower()}_id" if parent_model else "parent_id"
        return {"model": model, "filter": {fk: "$params.id"}, "order_by": ["id"]}
    if role == "filter":
        # Describes the filter-form itself; not a data query
        filter_fields = [f for f in fields if any(
            t in f for t in ("status", "type", "category", "name", "date", "created")
        )]
        return {"type": "filter_form", "filter_fields": filter_fields or fields[:4]}
    return {}


def _resolve_dynamic(value: str, role: str, layout: str, model: str, page_id: str) -> str:
    """Resolve $-prefixed dynamic values in section_composition pattern fields."""
    if value == "$entity_layout":
        return layout
    if value == "$collection_component":
        return _component_for_section(role or "object_collection", layout, model, page_id)
    if value == "$detail_component":
        return _component_for_section("object_detail", "detail", model, page_id)
    return value


def _match_composition_pattern(
    pattern: dict,
    page_roles: set,
    intents: set,
    n_attrs: int,
    workflow_intents: set | None = None,
    activity_node_name: str = "",
) -> bool:
    """Return True if a section_composition YAML pattern matches the page + entity profile.

    Conditions (all must pass):
      page_roles            — at least one role must match
      intents_any/all       — entity intent conditions
      min_attrs             — attribute count threshold
      workflow_intents_any  — at least one workflow intent (Decision/StateTransition/…) from activity diagram
      activity_terms_any    — regex alternatives matched against activity action node name
    """
    pattern_roles = set(pattern.get("page_roles") or [])
    if not (pattern_roles & page_roles):
        return False
    intents_any = set(pattern.get("intents_any") or [])
    if intents_any and not (intents_any & intents):
        return False
    intents_all = set(pattern.get("intents_all") or [])
    if intents_all and not intents_all.issubset(intents):
        return False
    min_attrs = pattern.get("min_attrs")
    if min_attrs and n_attrs < min_attrs:
        return False
    wi_any = set(pattern.get("workflow_intents_any") or [])
    if wi_any and not (wi_any & (workflow_intents or set())):
        return False
    at_any_raw = pattern.get("activity_terms_any") or ""
    if at_any_raw:
        # YAML may give a single string or a list — join list items with | so they
        # become regex alternatives; never pass a list directly to re.search().
        if isinstance(at_any_raw, list):
            at_any = "|".join(str(x) for x in at_any_raw)
        else:
            at_any = str(at_any_raw)
        try:
            if not re.search(at_any, activity_node_name, re.I):
                return False
        except re.error:
            pass
    return True


def _build_section_from_pattern_entry(
    entry: dict,
    page: dict,
    model: str,
    model_attrs: dict,
    model_graph: dict,
    actor_permissions: dict,
    page_id: str,
    base_layout: str,
    is_select: bool,
) -> list[dict]:
    """Build one or more section dicts from a single section_composition pattern entry."""
    role = str(entry.get("role") or "")
    layout_spec = str(entry.get("layout") or base_layout)
    layout = _resolve_dynamic(layout_spec, role, base_layout, model, page_id)
    comp_spec = str(entry.get("component") or "")
    component = _resolve_dynamic(comp_spec, role, layout, model, page_id) or _component_for_section(role, layout, model, page_id)
    col_span = int(entry.get("col_span") or 12)

    # for_each: expand one section per 1:N child model
    if entry.get("for_each") == "compositions_1n":
        results = []
        model_info = model_graph.get(model) or {}
        seen: set[str] = set()
        for rel_key in ("compositions_owned", "aggregations_owned", "associations"):
            for assoc in model_info.get(rel_key) or []:
                child = assoc.get("model") or ""
                if child and child not in seen and child != model and child in model_attrs and assoc.get("cardinality") == "1-many":
                    results.append(_child_section(page_id, child, model_attrs, related_models=[model]))
                    seen.add(child)
        return results

    # Standard single section builders
    if role == "filter":
        return [_filter_section_for_model(page_id, model, model_attrs)]

    if role == "object_collection":
        # Pass layout/component from the YAML pattern if they are literal (not dynamic $-refs)
        lo = layout if not layout_spec.startswith("$") else ""
        co = component if not comp_spec.startswith("$") else ""
        return [_collection_section_for_model(
            page_id, page, model, model_attrs, actor_permissions,
            is_select=is_select, layout_override=lo, component_override=co,
        )]

    if role == "object_detail":
        return [_detail_section_for_model(page_id, model, model_attrs, actor_permissions)]

    if role == "object_summary":
        vis = _pick_fields(model_attrs, model, "object_summary")
        return [{
            "id": f"{page_id}_{_section_id(model)}_object_summary",
            "page_id": page_id,
            "role": "object_summary",
            "name": f"{model} Summary",
            "layout": "detail",
            "component": component,
            "primary_model": model,
            "visible_fields": vis,
            "editable_fields": [],
            "related_visible_fields": [],
            "field_layout": _field_layout_for_component(component, vis),
            "operations": {"create": False, "update": False, "delete": False, "select": False},
            "query": _query_for_section("object_summary", model, vis),
            "style": {"color": "accent", "density": "compact", "shadow": "sm", "border": "light", "bg": "white"},
            "col_span": col_span,
        }]

    if role == "object_form":
        vis = _pick_fields(model_attrs, model, "object_form")
        return [{
            "id": f"{page_id}_{_section_id(model)}_object_form",
            "page_id": page_id,
            "role": "object_form",
            "name": f"{model} Settings",
            "layout": "form",
            "component": component,
            "primary_model": model,
            "visible_fields": vis,
            "editable_fields": vis,
            "related_visible_fields": [],
            "field_layout": _field_layout_for_component(component, vis),
            "operations": {"create": False, "update": True, "delete": False, "select": False},
            "query": _query_for_section("object_form", model, vis),
            "style": {"color": "accent", "density": "normal", "shadow": "sm", "bg": "white", "form_style": "default"},
            "col_span": col_span,
        }]

    if role == "workflow_action":
        # Approve / Reject / Complete buttons panel for decision steps
        return [{
            "id": f"{page_id}_workflow_action",
            "page_id": page_id,
            "role": "workflow_action",
            "name": "Actions",
            "layout": layout or "action_panel",
            "component": component or "WorkflowActionPanel",
            "primary_model": model,
            "visible_fields": [],
            "editable_fields": [],
            "related_visible_fields": [],
            "field_layout": {},
            "operations": {"create": False, "update": True, "delete": False, "select": False},
            "query": {},
            "style": {"color": "accent", "density": "normal", "shadow": "none", "bg": "white", "button_layout": "horizontal"},
            "col_span": col_span,
        }]

    if role == "workflow_history":
        # Timeline of previous workflow steps for result/share pages
        return [{
            "id": f"{page_id}_workflow_history",
            "page_id": page_id,
            "role": "workflow_history",
            "name": "Workflow History",
            "layout": layout or "timeline",
            "component": component or "WorkflowTimeline",
            "primary_model": model,
            "visible_fields": [],
            "editable_fields": [],
            "related_visible_fields": [],
            "field_layout": {},
            "operations": {"create": False, "update": False, "delete": False, "select": False},
            "query": {},
            "style": {"color": "accent", "density": "compact", "shadow": "sm", "bg": "white"},
            "col_span": col_span,
        }]

    return []


def _compose_page_sections(
    page: dict,
    model_attrs: dict,
    model_graph: dict,
    actor_permissions: dict,
    semantic_profiles: dict | None = None,
    section_composition: dict | None = None,
) -> tuple[str | None, list[dict]]:
    """Return (pattern_name, sections) for a page, driven by YAML section_composition rules.

    Pipeline:
        TKB intent_rules  →  semantic_profiles  →  section_composition patterns
        (YAML rule)           (engine output)        (YAML config, read here)

    pattern_name: the `pattern:` field from the matched YAML entry, or None.
    The candidate generation phase later only varies layout/component/tokens
    within each section — it does not add or remove sections.
    """
    model = page.get("primary_model") or ""
    page_id = str(page.get("id") or page.get("page_id") or "")
    roles = set(page.get("roles") or [])
    operation_kind = str(page.get("operation_kind") or page.get("kind") or "").lower()

    if not model or not page_id:
        return []

    # ── Intents from TKB engine (YAML intent_rules), not Python heuristics ──
    profile = (semantic_profiles or {}).get(model) or {}
    intents: set[str] = set(profile.get("intents") or ["CRUD"])

    is_select = (
        operation_kind in {"select_existing", "select"}
        or _ACTIVITY_SELECT_TERMS.search(f"{page_id} {page.get('name', '')}") is not None
    )
    if is_select:
        roles = roles | {"select_existing"}

    # ── Role augmentation: operation_kind and page-name heuristics ───────────
    # Many UseCase names ("Products", "Manage Orders") don't trigger the YAML
    # role_keywords, so they land on object_workspace (the default).  Upgrade
    # the role here so the right YAML section_composition pattern is matched.
    if "collection_workspace" not in roles and "detail_workspace" not in roles and "activity_action" not in roles:
        if operation_kind in {"view_collection", "select_existing"}:
            roles = roles | {"collection_workspace"}
        elif operation_kind == "view_detail":
            roles = roles | {"detail_workspace"}
        elif operation_kind in {"manage_object", ""}:
            # Plain plural model name → collection ("products", "orders", "customers")
            pid_clean = page_id.replace("_", "").lower()
            m_clean = model.lower()
            if pid_clean in {m_clean, m_clean + "s", m_clean + "es",
                              "manage" + m_clean, "manage" + m_clean + "s",
                              "list" + m_clean + "s", "all" + m_clean + "s"}:
                roles = roles | {"collection_workspace"}
            # "Product Detail", "Order Detail" etc. → detail
            elif any(kw in page_id for kw in ("_detail", "_profile", "_info", "_overview", "_view")):
                roles = roles | {"detail_workspace"}

    n_attrs = len(model_attrs.get(model) or [])
    base_layout = _layout_for_page_role(page)
    workflow_intents: set[str] = set(page.get("workflow_intents") or [])
    activity_node_name: str = str(page.get("activity_node_name") or page.get("name") or "")

    # ── Match first applicable YAML section_composition pattern ─────────────
    patterns = (section_composition or {}).get("patterns") or []
    for pattern in patterns:
        if not _match_composition_pattern(
            pattern, roles, intents, n_attrs,
            workflow_intents=workflow_intents,
            activity_node_name=activity_node_name,
        ):
            continue
        if model not in model_attrs:
            break
        pattern_name: str | None = pattern.get("pattern") or None
        sections: list[dict] = []
        for entry in pattern.get("sections") or []:
            sections.extend(_build_section_from_pattern_entry(
                entry, page, model, model_attrs, model_graph,
                actor_permissions, page_id, base_layout, is_select,
            ))
        return pattern_name, sections

    # ── Fallback: single section (old behaviour) if no pattern matched ───────
    main = _section_for_page(page, model_attrs, actor_permissions)
    return None, ([main] if main else [])


def build_navigation_plan(
    usecase_navigation: dict,
    model_attrs: dict | None = None,
    workflow_steps: list | None = None,
    model_graph: dict | None = None,
    semantic_profiles: dict | None = None,
    section_composition: dict | None = None,
) -> dict:
    """Build navigation plan driven by YAML section_composition patterns.

    semantic_profiles: name-keyed dict of {intents: [...]} from TKB engine
    section_composition: the section_composition config block from the YAML rules file
    model_graph: 1:N relation data for child_collection expansion
    """
    model_attrs = model_attrs or {}
    semantic_profiles = semantic_profiles or {}
    section_composition = section_composition or {}
    model_graph = model_graph or {}
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
            "name_slugs": page.get("name_slugs") or [],
            "sections": [],
        }
        pattern_name, composed = _compose_page_sections(
            normalized, model_attrs, model_graph, actor_permissions,
            semantic_profiles=semantic_profiles,
            section_composition=section_composition,
        )
        if pattern_name:
            normalized["pattern"] = pattern_name
        name_slugs = normalized["name_slugs"]
        for sec in composed:
            sec["name_slugs"] = name_slugs
            sections.append(sec)
            page_sections[normalized["id"]].append(sec["id"])
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
        step_model = next((m for m in (step.get("classes") or []) if m in model_attrs), "")
        # The nav_plan page_id has a "Workflow_" prefix (e.g. "workflow_view_cart") but the
        # DB activity page is indexed by the plain activity-node name slug ("view_cart").
        # Store that slug in name_slugs so _materialize_nav_plan_sections can find the DB page.
        node_name_slug = _section_id(step.get("activity_node_name") or step.get("page_name") or "")
        step_name_slugs = [node_name_slug] if node_name_slug and node_name_slug != page_id else []
        if page_id not in existing_page_ids:
            # Build a normalized page dict so _compose_page_sections can pattern-match
            # using the activity-diagram context (workflow_intents, activity_node_name).
            pages.append({
                "id": page_id,
                "name": step.get("page_name") or _page_name(page_id),
                "role": "activity_action",
                "roles": ["activity_action"],
                "primary_model": step_model,
                "activity_node_name": step.get("activity_node_name") or step.get("page_name") or "",
                "workflow_intents": step.get("workflow_intents") or [],
                "usecases": [],
                "nav": False,
                "sections": [],
            })
            existing_page_ids.add(page_id)
        if step_model:
            # Use YAML-driven pattern selection instead of the old hardcoded function
            step_page = {
                "id": page_id,
                "roles": ["activity_action"],
                "primary_model": step_model,
                "activity_node_name": step.get("activity_node_name") or step.get("page_name") or "",
                "workflow_intents": step.get("workflow_intents") or [],
            }
            step_pattern, step_composed = _compose_page_sections(
                step_page, model_attrs, model_graph, actor_permissions,
                semantic_profiles=semantic_profiles,
                section_composition=section_composition,
            )
            if step_pattern:
                for p in pages:
                    if p["id"] == page_id:
                        p["pattern"] = step_pattern
                        break
            for sec in step_composed:
                if sec["id"] not in existing_section_ids:
                    sec["name_slugs"] = step_name_slugs
                    sections.append(sec)
                    page_sections[page_id].append(sec["id"])
                    existing_section_ids.add(sec["id"])
        else:
            # No model known for this step — fall back to old logic
            for sec in _sections_for_activity_step(step, model_attrs, workflow_entries):
                if sec["id"] not in existing_section_ids:
                    sec["name_slugs"] = step_name_slugs
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
