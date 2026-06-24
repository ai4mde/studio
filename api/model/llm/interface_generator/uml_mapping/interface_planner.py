"""
Interface Planner
Takes extracted UML intelligence and generates a concrete interface plan:
  - pages (one per actor-accessible model/use-case grouping)
  - sections (collection, detail, form, filter, child_collection, workflow stepper)
  - semantic_decisions (layout/component questions for the LLM to resolve)
"""

import re
from collections import defaultdict

from ..token_normalizer import _sid


# ─── helpers ─────────────────────────────────────────────────────────────────


def _plural(model: str) -> str:
    """Pluralize value."""
    base = _sid(model or "items")
    if base.endswith("y") and not base.endswith(("ay", "ey", "oy", "uy")):
        return f"{base[:-1]}ies"
    if base.endswith("s"):
        return base
    return f"{base}s"


def _title(page_id: str) -> str:
    """Title-case value."""
    return page_id.replace("_", " ").title()


# ─── field selection ─────────────────────────────────────────────────────────

# Semantic categories derived from field name patterns; first match wins.
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

# Category priority order per section role.
_ROLE_CATEGORY_ORDER: dict[str, list[str]] = {
    "object_collection": ["image", "video", "name", "status", "code", "category", "metric", "temporal", "flag"],
    "object_detail":     ["image", "video", "name", "describe", "status", "metric", "contact", "category", "temporal"],
    "object_form":       ["name", "describe", "category", "status", "metric", "contact", "address", "temporal"],
    "child_collection":  ["name", "code", "metric", "status"],
    "filter":            ["name", "status", "category", "metric", "temporal", "flag"],
}

# System/audit fields excluded from editable forms.
_EXCLUDED_FORM = frozenset({
    "id", "uuid", "slug",
    "created_at", "updated_at", "created_on", "updated_on", "deleted_at",
})


def _field_category(field_name: str) -> str | None:
    """Classify a model field for ordering and layout decisions."""
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
    """Shared field-selection algorithm used by both interface_planner and navigation_planner."""
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


def _pick_fields(model_info: dict, role: str, limit: int = 8) -> list[str]:
    """Pick fields."""
    attrs = model_info.get("attributes") or []
    attr_names = [a["name"] for a in attrs if a.get("name")]
    if role == "object_form":
        attr_names = [f for f in attr_names if f.lower() not in _EXCLUDED_FORM]
    else:
        attr_names = [f for f in attr_names if f.lower() != "id"]
    return _pick_fields_by_names(attr_names, role, _ROLE_CATEGORY_ORDER, limit)


# ─── component selection ─────────────────────────────────────────────────────

_MODEL_PERSON   = re.compile(r"user|person|people|customer|client|patient|doctor|member|staff|employee|contact|vendor|seller|supplier|student|teacher|author|owner|passenger|operator|admin|applicant|borrower|officer|analyst|reviewer", re.I)
_MODEL_DOCUMENT = re.compile(r"report|document|record|contract|invoice|receipt|statement|transcript|certificate|permit|license|policy|agreement", re.I)
_MODEL_CATEGORY = re.compile(r"categor|genre|collection|group|class|tag|label", re.I)

_FORM_ADDRESS   = re.compile(r"address|shipping|delivery|mailing", re.I)
_FORM_PAYMENT   = re.compile(r"payment|checkout|billing|charge|subscription", re.I)
_FORM_REVIEW    = re.compile(r"review|rating|feedback|assessment|evaluation|testimonial", re.I)


def _collection_component(model: str, layout: str) -> str:
    """Select the collection component type for a model and page role."""
    if layout == "timeline":
        return "TimelineList"
    if layout == "map":
        return "MapView"
    if layout == "table":
        return "DataTable"
    if layout == "gallery":
        m = model.lower()
        if _MODEL_CATEGORY.search(m):
            return "CategoryTileGrid"
        if _MODEL_PERSON.search(m):
            return "PersonCardGrid"
        return "CardGrid"
    return "ObjectList"


def _detail_component(model: str) -> str:
    """Select the detail component type for a model and page role."""
    m = model.lower()
    if _MODEL_DOCUMENT.search(m):
        return "DocumentPanel"
    if _MODEL_PERSON.search(m):
        return "ProfilePanel"
    return "DetailPanel"


def _form_component(model: str, page_id: str) -> str:
    """Select the form component type for a form-oriented page role."""
    m = (model + " " + page_id).lower()
    if _FORM_ADDRESS.search(m):
        return "AddressForm"
    if _FORM_PAYMENT.search(m):
        return "PaymentMethodForm"
    if _FORM_REVIEW.search(m):
        return "ReviewForm"
    return "ObjectForm"


def _child_component(model: str, page_id: str) -> str:
    """Select the component type for a related child collection section."""
    m = (model + " " + page_id).lower()
    if any(t in m for t in ("item", "line", "cart", "basket")):
        return "LineItemList"
    return "RelatedObjectList"


# ─── layout selection ────────────────────────────────────────────────────────

def _pick_layout(model_info: dict, page_role: str, semantic_override: str | None = None, model: str = "") -> str:
    """Select layout for a collection page based on scoring and semantic decision."""
    if page_role in {"detail_workspace", "object_workspace"}:
        return "detail"
    if page_role == "workflow_entry":
        return "detail"
    if semantic_override:
        return semantic_override

    score = model_info.get("layout_score") or {}
    model_l = str(model or model_info.get("name") or "").lower()
    attr_names = {str(a.get("name") or "").lower() for a in model_info.get("attributes", []) if isinstance(a, dict)}
    attr_count = len(attr_names)

    # Prefer semantically distinct layouts before falling back to generic table scoring.
    if _MODEL_PERSON.search(model_l):
        return "gallery"
    if re.search(r"appointment|booking|reservation|schedule|event|meeting|slot", model_l):
        return "list"
    if re.search(r"admission|application|loan|case|incident|ticket|request", model_l):
        if score.get("timeline", 0) > 0 or any(a in attr_names for a in {"status", "state", "created_at", "updated_at", "start_date", "end_date"}):
            return "timeline"
        return "list"
    if _MODEL_DOCUMENT.search(model_l) or re.search(r"bill|payment|prescription|medication|lab|test|room|department", model_l):
        return "list" if attr_count <= 10 else "table"

    candidates = [
        ("gallery",  score.get("gallery",  0)),
        ("table",    score.get("table",    0)),
        ("list",     score.get("list",     0)),
        ("timeline", score.get("timeline", 0)),
        ("map",      score.get("map",      0)),
    ]
    # Only consider special layouts if score is high enough
    special = [(l, s) for l, s in candidates if l not in {"table", "list", "gallery"} and s > 0.6]
    if special:
        return max(special, key=lambda x: x[1])[0]
    if attr_count <= 8 and score.get("table", 0) <= 0.7:
        return "list"
    standard = [(l, s) for l, s in candidates if l in {"gallery", "table", "list"}]
    return max(standard, key=lambda x: x[1])[0]


def _activity_layout_from_action(action: str, hint: str) -> tuple[str, str, str] | None:
    """Rule fallback for activity steps when no LLM semantic override is available."""
    text = str(action or "").lower()
    if any(w in text for w in ("review", "consult", "monitor", "analyze", "analyse", "assess", "verify", "inspect")):
        return "detail", "object_detail", "DetailPanel"
    if any(w in text for w in ("notify", "notification", "unavailable", "alert", "message")):
        return "detail", "object_detail", "SummaryPanel"
    if any(w in text for w in ("confirm", "summary", "check", "approve", "reject", "discharge")):
        return "detail", "object_detail", "SummaryPanel"
    if any(w in text for w in ("select", "choose", "pick", "browse", "compare")):
        return "list", "object_collection", "ObjectList"
    if hint == "DetailPanel":
        return "detail", "object_detail", "DetailPanel"
    if hint == "SelectionList":
        return "list", "object_collection", "ObjectList"
    return None


def _activity_form_operations(action: str) -> list[str]:
    """Build activity form operations."""
    text = str(action or "").lower()
    create_terms = ("create", "add", "new", "record", "submit", "register", "enter", "request", "apply", "book", "schedule", "reserve")
    update_terms = ("update", "edit", "change", "set", "mark", "renew", "return")
    if any(term in text for term in update_terms) and not any(term in text for term in create_terms):
        return ["update"]
    return ["create"]


def _is_create_like_activity(action: str) -> bool:
    """Detect workflow steps that should render as create-style activity pages."""
    text = str(action or "").lower()
    return any(term in text for term in ("request", "apply", "submit", "book", "schedule", "reserve", "create", "register", "enter"))


def _merge_field_names(*groups: list[str]) -> list[str]:
    """Merge field names."""
    out = []
    for group in groups:
        for field in group or []:
            if field and field not in out:
                out.append(field)
    return out


def _semantic_section_attrs(step_attrs: list[dict], readonly: list[str], editable: list[str]) -> list[dict]:
    """Merge semantic field hints into ordered section attribute descriptors."""
    attr_by_name = {attr.get("name"): dict(attr) for attr in step_attrs or [] if attr.get("name")}
    out = []
    for field in _merge_field_names(readonly, editable):
        attr = dict(attr_by_name.get(field) or {"name": field})
        attr["readonly"] = field not in set(editable or [])
        out.append(attr)
    return out


def _workflow_semantics_payload(workflow_semantic: dict, readonly: list[str], editable: list[str]) -> dict:
    """Build workflow semantics payload."""
    payload = {
        key: workflow_semantic.get(key)
        for key in ("intent", "context_model", "target_model", "context_binding", "condition", "true_next", "false_next")
        if workflow_semantic.get(key)
    }
    if readonly:
        payload["readonly_fields"] = readonly
    if editable:
        payload["editable_fields"] = editable
    return payload


_ACTOR_MODEL_SCOPES = {"self_profile", "collection", "assigned", "hidden"}


def _actor_model_scope(actor_name: str, model: str, semantic_overrides: dict | None = None) -> str:
    """Return validated actor-to-model scope; fall back to strict identity matching."""
    scopes = (semantic_overrides or {}).get("actor_model_scopes") or {}
    scope = scopes.get(model)
    if scope in _ACTOR_MODEL_SCOPES:
        return scope
    return "self_profile" if _is_actor_self_model(actor_name, model) else "collection"


def _is_actor_self_scope(actor_name: str, model: str, semantic_overrides: dict | None = None) -> bool:
    """True only when mapping semantics say the model is the actor's own identity record."""
    return _actor_model_scope(actor_name, model, semantic_overrides) == "self_profile"


def _actor_owned_data_scope(actor_name: str, model: str, semantic_overrides: dict | None = None) -> dict:
    """Return an explicit section data scope when the section represents the current actor's own record."""
    if not actor_name or not model:
        return {}
    if not _is_actor_self_scope(actor_name, model, semantic_overrides):
        return {}
    return {
        "mode": "actor_owned",
        "source": "current_actor",
        "model": model,
    }


def _is_actor_self_model(actor_name: str, model: str) -> bool:
    """True when a model represents the current actor's own identity record."""
    return bool(actor_name and model and _sid(actor_name) == _sid(model))


def _parent_page_data_scope(page_primary_model: str, parent_model: str) -> dict:
    """Return a parent_page_instance scope when a section FK points to the current page's primary model."""
    if not page_primary_model or not parent_model:
        return {}
    if _sid(page_primary_model) == _sid(parent_model):
        return {
            "mode": "parent_page_instance",
            "source": "page_context",
            "model": parent_model,
        }
    return {}


def _relation_data_scopes(
    actor_name: str,
    parent_models: list[str],
    semantic_overrides: dict | None = None,
    page_primary_model: str | None = None,
) -> dict:
    """Mark parent relations that should be resolved from the current actor or page context."""
    scopes = {}
    for parent_model in parent_models or []:
        scope = _actor_owned_data_scope(actor_name, parent_model, semantic_overrides)
        if not scope and page_primary_model:
            scope = _parent_page_data_scope(page_primary_model, parent_model)
        if scope:
            scopes[parent_model] = scope
    return scopes


def _model_relation_data_scopes(
    actor_name: str,
    model_info: dict,
    semantic_overrides: dict | None = None,
    page_primary_model: str | None = None,
) -> dict:
    """Infer relation scopes for foreign-key style fields on a section's model.

    page_primary_model: the primary model of the page this section lives on.
    FKs pointing to that model are marked parent_page_instance so the view
    generator can auto-fill them from the URL's instance_id_ parameter instead
    of showing a generic dropdown.
    """
    parent_models = []
    for attr in model_info.get("attributes") or []:
        if isinstance(attr, dict) and attr.get("model"):
            parent_models.append(attr["model"])
    for assoc in model_info.get("associations") or []:
        if isinstance(assoc, dict) and assoc.get("model"):
            parent_models.append(assoc["model"])
    return _relation_data_scopes(actor_name, parent_models, semantic_overrides, page_primary_model)


def _should_add_filter(layout: str, model_info: dict, page_role: str) -> bool:
    """Decide whether a generated collection page should include a filter section."""
    if layout not in {"table", "list"} or page_role != "collection_workspace":
        return False
    attr_names = {str(a.get("name") or "").lower() for a in model_info.get("attributes", []) if isinstance(a, dict)}
    return len(attr_names) > 8 or bool(attr_names & {"status", "state", "category", "type", "specialization"})


# ─── Plan builder ─────────────────────────────────────────────────────────────

def _section_data_role(role: str, layout: str, operations: list[str], style: dict | None = None) -> str:
    """Classify what a section does with data; rendering and workflow logic consume this."""
    ops = set(operations or [])
    workflow_intent = str(((style or {}).get("workflow_semantics") or {}).get("intent") or "").lower()
    if "notify" in workflow_intent:
        return "notify_summary"
    if "check" in workflow_intent or "decision" in workflow_intent:
        return "decision_check"
    if "select" in ops and not ops.intersection({"create", "update", "delete"}):
        return "select_existing"
    if "create" in ops and layout == "form":
        return "create_record"
    if "update" in ops and layout == "form":
        return "update_record"
    if layout == "detail" or role in {"object_detail", "object_summary"}:
        return "show_record"
    return "display_records"


def _section_fields(model: str, visible: list[str], editable: list[str], attributes: list[dict] | None, data_role: str) -> list[dict]:
    """Return explicit field semantics without replacing legacy attributes."""
    editable_set = set(editable or [])
    attr_names = [
        attr.get("name")
        for attr in (attributes or [])
        if isinstance(attr, dict) and attr.get("name")
    ]
    names = _merge_field_names(visible or [], editable or []) or attr_names
    fields = []
    for name in names:
        if not name:
            continue
        field_model = model
        field_name = name
        source = "primary"
        if "." in str(name):
            field_model, field_name = str(name).split(".", 1)
            source = "related"
        mode = "editable" if name in editable_set else "display"
        if source == "related" or (data_role in {"show_record", "decision_check", "notify_summary"} and name not in editable_set):
            mode = "readonly"
        elif data_role == "display_records" and name not in editable_set:
            mode = "display"
        fields.append({
            "model": field_model,
            "name": field_name,
            "mode": mode,
            "source": source,
        })
    return fields


def _section_actions(model: str, data_role: str, operations: list[str]) -> list[dict]:
    """Expose user-facing actions separately from CRUD permissions."""
    if data_role == "display_records":
        return [{"type": "navigate", "label": "View", "target_page": f"{model} Detail"}] if model else []
    if data_role == "select_existing":
        return [{"type": "select", "label": "Select", "target_model": model}] if model else []
    if data_role in {"create_record", "update_record"}:
        label = "Create" if data_role == "create_record" else "Save"
        return [{"type": "submit", "label": label, "operations": operations or []}]
    if data_role == "decision_check":
        return [{"type": "complete_step", "label": "Continue"}]
    if data_role == "notify_summary":
        return [{"type": "complete_step", "label": "Mark done"}]
    return []


def _section(
    page_id: str,
    section_id: str,
    role: str,
    name: str,
    layout: str,
    component: str,
    model: str,
    visible: list[str],
    editable: list[str],
    operations: list[str],
    attributes: list[dict] | None = None,
    **extra,
) -> dict:
    """Build section value."""
    style_override = extra.pop("style", None)
    data_scope = extra.pop("data_scope", None)
    relation_data_scopes = extra.pop("relation_data_scopes", None)
    sec = {
        "id": section_id,
        "page_id": page_id,
        "role": role,
        "name": name,
        "layout": layout,
        "component": component,
        "primary_model": model,
        "class": model,
        "attributes": attributes or [],
        "visible_fields": visible,
        "editable_fields": editable,
        "related_visible_fields": [],
        "field_layout": {},
        "operations": operations,
        "query": {},
        "style": {
            "color": "accent",
            "density": "compact" if layout in {"table", "list"} else "normal",
            "shadow": "sm",
            "border": "light",
            "bg": "white",
        },
        "col_span": 12,
    }
    if isinstance(style_override, dict):
        sec["style"].update(style_override)
    if isinstance(data_scope, dict) and data_scope:
        sec["style"]["data_scope"] = data_scope
    if isinstance(relation_data_scopes, dict) and relation_data_scopes:
        sec["style"]["relation_data_scopes"] = relation_data_scopes
    data_role = extra.pop("data_role", None) or _section_data_role(role, layout, operations, sec.get("style") or {})
    sec["data_role"] = data_role
    sec["fields"] = extra.pop("fields", None) or _section_fields(model, visible, editable, sec["attributes"], data_role)
    sec["actions"] = extra.pop("actions", None) or _section_actions(model, data_role, operations)
    sec.update(extra)
    return sec


# ─── subordinate model detection ─────────────────────────────────────────────

_ASSET_SUFFIXES = frozenset({
    "image", "photo", "picture", "video", "media", "file", "attachment",
    "option", "variant", "spec", "config", "setting", "detail",
    "tag", "label", "price", "pricing",
})


def _subordinate_parent(model_name: str, model_graph: dict, accessible: set[str]) -> str | None:
    """
    Returns the parent model name if this model should be a SECTION on the parent's detail page
    rather than a standalone page.

    A model is subordinate when:
    (a) Its name starts with a parent model name AND ends in an asset-like suffix
        e.g. ProductImage → Product (image suffix)
    (b) All its associations point to exactly ONE other accessible model AND
        the model name contains an asset-like word anywhere
    """
    m = model_name.lower()
    info = model_graph.get(model_name) or {}
    assoc_models = {a["model"] for a in (info.get("associations") or [])}

    # (a) name prefix match
    for parent in sorted(accessible, key=len, reverse=True):
        p = parent.lower()
        if len(p) >= 3 and m.startswith(p) and m != p:
            suffix = m[len(p):]
            if any(suf in suffix for suf in _ASSET_SUFFIXES):
                return parent

    # (b) single-parent association + asset-like name
    accessible_assocs = assoc_models & accessible
    if len(accessible_assocs) == 1 and any(suf in m for suf in _ASSET_SUFFIXES):
        return next(iter(accessible_assocs))

    return None


# ─── child sections from associations ────────────────────────────────────────

_SKIP_CHILD_ASSOCS = frozenset({
    # Models that appear as "many" side but are not meaningful sub-lists on a detail page
    "cart", "cartitem", "address",
})


def _add_association_sections(
    page_id: str,
    model: str,
    model_info: dict,
    model_graph: dict,
    accessible: set[str],
    subordinate_models: set[str],
    existing_section_ids: set[str],
    add_section_fn,
    max_sections: int = 3,
) -> None:
    """
    Add child_collection sections for 1:many and many:many associations on a detail page.
    Prioritises: composition_owned > 1-many associations > many-many.
    Skips models that already have standalone pages.
    """
    added = 0

    # 1. Composition children (strongest relationship)
    for comp in model_info.get("compositions_owned") or []:
        if added >= max_sections:
            break
        child = comp["model"]
        child_info = model_graph.get(child) or {}
        child_fields = _pick_fields(child_info, "child_collection", 6)
        sec_id = f"{page_id}_{_sid(child)}_child_collection"
        if sec_id not in existing_section_ids:
            add_section_fn(_section(
                page_id=page_id, section_id=sec_id,
                role="child_collection", name=f"{child}",
                layout="list", component=_child_component(child, page_id),
                model=child, visible=child_fields, editable=[],
                operations=["read", "update", "delete"],
                attributes=child_info.get("attributes", []),
            ))
            added += 1

    # 2. Subordinate models (e.g., ProductImage → Product)
    #    These are ONLY placed here, never as standalone pages.
    for sub_model in sorted(subordinate_models):
        if added >= max_sections:
            break
        sub_parent = _subordinate_parent(sub_model, model_graph, {model})
        if sub_parent != model:
            continue
        sub_info = model_graph.get(sub_model) or {}
        sub_fields = _pick_fields(sub_info, "child_collection", 5)
        sec_id = f"{page_id}_{_sid(sub_model)}_child_collection"
        if sec_id not in existing_section_ids:
            add_section_fn(_section(
                page_id=page_id, section_id=sec_id,
                role="child_collection", name=f"{sub_model}",
                layout="list", component=_child_component(sub_model, page_id),
                model=sub_model, visible=sub_fields, editable=[],
                operations=["read"],
                attributes=sub_info.get("attributes", []),
            ))
            added += 1

    # 3. 1:many associations (model owns many of the related)
    for assoc in model_info.get("associations") or []:
        if added >= max_sections:
            break
        rel_model = assoc["model"]
        cardinality = assoc.get("cardinality", "")
        if cardinality != "1-many":
            continue
        if rel_model.lower() in _SKIP_CHILD_ASSOCS:
            continue
        if rel_model not in accessible:
            continue
        if rel_model in subordinate_models:
            continue  # handled above
        rel_info = model_graph.get(rel_model) or {}
        rel_fields = _pick_fields(rel_info, "child_collection", 5)
        sec_id = f"{page_id}_{_sid(rel_model)}_related"
        if sec_id not in existing_section_ids:
            add_section_fn(_section(
                page_id=page_id, section_id=sec_id,
                role="child_collection", name=f"{rel_model}",
                layout="list", component=_child_component(rel_model, page_id),
                model=rel_model, visible=rel_fields, editable=[],
                operations=["read"],
                attributes=rel_info.get("attributes", []),
            ))
            added += 1


def generate_interface_plan(
    uml_intelligence: dict,
    semantic_overrides: dict | None = None,
) -> dict:
    """
    Generate pages + sections from extracted UML intelligence.

    semantic_overrides: {model_name: {"layout": "table", "component": "DataTable"}}
    These come from the LLM resolving the semantic_decisions.
    """
    semantic_overrides = semantic_overrides or {}
    model_graph: dict = uml_intelligence.get("model_graph") or {}
    actor_intel: dict = uml_intelligence.get("actor_intel") or {}
    workflow_intel: dict = uml_intelligence.get("workflow_intel") or {}
    current_actor_name = (uml_intelligence.get("actor_name") or actor_intel.get("actor_name") or "").strip()

    target_permissions: dict[str, list] = actor_intel.get("target_permissions") or {}
    target_use_cases: list[dict] = actor_intel.get("target_use_cases") or []
    accessible: set[str] = set(target_permissions.keys())

    # ── Pre-compute subordinate models ───────────────────────────────────────
    # These models should appear as sections on their parent's detail page, not as standalone pages.
    subordinate_to: dict[str, str] = {}  # child_model → parent_model
    for model in accessible:
        parent = _subordinate_parent(model, model_graph, accessible - {model})
        if parent:
            subordinate_to[model] = parent
    subordinate_models: set[str] = set(subordinate_to.keys())

    pages: list[dict] = []
    sections: list[dict] = []
    page_sections: dict[str, list] = defaultdict(list)
    existing_page_ids: set[str] = set()
    existing_section_ids: set[str] = set()

    def add_section(sec: dict) -> None:
        """Provide a local helper for generate_interface_plan."""
        if sec["id"] not in existing_section_ids:
            sections.append(sec)
            page_sections[sec["page_id"]].append(sec["id"])
            existing_section_ids.add(sec["id"])

    def add_page(pg: dict) -> None:
        """Provide a local helper for generate_interface_plan."""
        if pg["id"] not in existing_page_ids:
            pages.append(pg)
            existing_page_ids.add(pg["id"])

    # ── Step 1: derive page entries from use cases ────────────────────────────

    page_map: dict[str, dict] = {}
    workflow_collection_models: dict[str, set] = defaultdict(set)

    for uc in target_use_cases:
        role = uc.get("page_role") or "object_workspace"
        original_role = role
        model = uc.get("primary_model") or ""
        perms = set(uc.get("permissions") or [])
        actor_model_scope = _actor_model_scope(current_actor_name, model, semantic_overrides)
        is_actor_self = actor_model_scope == "self_profile"
        if model and (original_role == "workflow_entry" or uc.get("has_workflow")):
            workflow_collection_models[model].update(perms or {"read"})
        if uc.get("has_workflow") and model and role == "workflow_entry":
            # Activity diagrams produce the step-by-step task pages below. Keep a
            # separate object workspace for the model so actors still get normal
            # browse/detail UI instead of only task forms.
            role = "object_workspace"
        if actor_model_scope == "collection" and role == "object_workspace":
            role = "collection_workspace"
        if is_actor_self and role in {"collection_workspace", "object_workspace"}:
            role = "detail_workspace"

        if role == "workflow_entry":
            page_id = f"{_sid(model or uc['name'])}_workflow" if model else _sid(uc["name"])
        elif role == "collection_workspace":
            page_id = _plural(model) if model else _sid(uc["name"])
        elif role == "detail_workspace":
            page_id = f"{_sid(model)}_detail" if model else _sid(uc["name"])
        else:
            page_id = _sid(model or uc["name"])

        if page_id not in page_map:
            page_map[page_id] = {"id": page_id, "role": role, "model": model,
                                  "permissions": set(), "use_cases": [], "has_workflow": False}
        page_map[page_id]["permissions"].update(perms)
        page_map[page_id]["use_cases"].append(uc["name"])
        if uc.get("has_workflow"):
            page_map[page_id]["has_workflow"] = True
        role_priority = {"collection_workspace": 3, "object_workspace": 2, "detail_workspace": 1, "workflow_entry": 0}
        existing_role = page_map[page_id]["role"]
        if role_priority.get(role, 0) > role_priority.get(existing_role, 0):
            page_map[page_id]["role"] = role
        if not page_map[page_id]["model"] and model:
            page_map[page_id]["model"] = model

    # ── Step 2: ensure standalone accessible models have a page ──────────────
    # Skip subordinate models — they'll appear as sections, not pages.

    for model, perms in target_permissions.items():
        if model in subordinate_models:
            continue  # will appear as a section on parent's detail page
        has_page = any(v["model"] == model for v in page_map.values())
        if not has_page:
            if _is_actor_self_scope(current_actor_name, model, semantic_overrides):
                page_id = f"{_sid(model)}_detail"
                role = "detail_workspace"
            else:
                page_id = _plural(model)
                role = "collection_workspace"
            page_map[page_id] = {"id": page_id, "role": role, "model": model,
                                  "permissions": set(perms), "use_cases": [], "has_workflow": False}
        else:
            for v in page_map.values():
                if v["model"] == model:
                    v["permissions"].update(perms)

    # Workflow-start use cases such as "Fill in application" or "Book appointment"
    # need both a task entry and a way to see existing/started instances. If the
    # workflow model only produced a detail/workflow page, add a collection page
    # for tracking without forcing unrelated subordinate models into navigation.
    for model, perms in workflow_collection_models.items():
        if model in subordinate_models or _is_actor_self_scope(current_actor_name, model, semantic_overrides):
            continue
        page_id = _plural(model)
        if page_id in page_map:
            page_map[page_id]["permissions"].update(perms)
            continue
        page_map[page_id] = {
            "id": page_id,
            "role": "collection_workspace",
            "model": model,
            "permissions": set(perms or target_permissions.get(model) or ["read"]),
            "use_cases": ["Track existing workflow items"],
            "has_workflow": True,
        }

    # ── Step 3: build pages and sections ─────────────────────────────────────

    for page_id, pm in page_map.items():
        model = pm["model"]
        page_role = pm["role"]
        permissions = list(pm["permissions"])
        model_info = model_graph.get(model) or {}

        override = (semantic_overrides.get("models") or {}).get(model) or semantic_overrides.get(model) or {}
        layout = _pick_layout(model_info, page_role, override.get("layout"), model)
        is_collection = layout in {"gallery", "table", "list", "timeline", "map"}
        is_detail = layout == "detail"

        add_page({
            "id": page_id,
            "name": _title(page_id),
            "primary_model": model,
            "role": page_role,
            "nav": page_role in {"collection_workspace", "object_workspace"} or _is_actor_self_scope(current_actor_name, model, semantic_overrides),
            "sections": [],
        })

        if not model:
            continue

        can_create = "create" in permissions
        can_update = "update" in permissions

        if is_collection:
            component = override.get("component") or _collection_component(model, layout)
            visible = _pick_fields(model_info, "object_collection")
            add_section(_section(
                page_id=page_id,
                section_id=f"{page_id}_{_sid(model)}_object_collection",
                role="object_collection", name=f"{model} {layout.title()}",
                layout=layout, component=component, model=model,
                visible=visible, editable=[],
                operations=[p for p in ("create", "read", "update", "delete") if p in permissions or p == "read"],
                attributes=model_info.get("attributes", []),
                data_scope=_actor_owned_data_scope(current_actor_name, model, semantic_overrides),
                relation_data_scopes=_model_relation_data_scopes(current_actor_name, model_info, semantic_overrides, page_primary_model=model),
            ))
            filter_fields = _pick_fields(model_info, "filter", 5)
            if filter_fields and _should_add_filter(layout, model_info, page_role):
                add_section(_section(
                    page_id=page_id,
                    section_id=f"{page_id}_{_sid(model)}_filter",
                    role="filter", name=f"Search {model}",
                    layout="filter", component="FilterPanel",
                    model=model, visible=filter_fields, editable=filter_fields,
                    operations=["read"],
                    attributes=model_info.get("attributes", []),
                    data_scope=_actor_owned_data_scope(current_actor_name, model, semantic_overrides),
                    relation_data_scopes=_model_relation_data_scopes(current_actor_name, model_info, semantic_overrides, page_primary_model=model),
                    style={"color": "neutral", "density": "compact", "shadow": "none",
                           "border": "none", "bg": "surface", "col_span": 12},
                ))

        elif is_detail:
            component = override.get("component") or _detail_component(model)
            visible = _pick_fields(model_info, "object_detail")
            add_section(_section(
                page_id=page_id,
                section_id=f"{page_id}_{_sid(model)}_object_detail",
                role="object_detail", name=f"{model} Detail",
                layout="detail", component=component, model=model,
                visible=visible, editable=[], operations=["read"],
                attributes=model_info.get("attributes", []),
                data_scope=_actor_owned_data_scope(current_actor_name, model, semantic_overrides),
                relation_data_scopes=_model_relation_data_scopes(current_actor_name, model_info, semantic_overrides, page_primary_model=model),
            ))
            if can_create or can_update:
                form_fields = _pick_fields(model_info, "object_form", 10)
                if form_fields:
                    add_section(_section(
                        page_id=page_id,
                        section_id=f"{page_id}_{_sid(model)}_object_form",
                        role="object_form", name=f"Edit {model}",
                        layout="form", component=_form_component(model, page_id),
                        model=model, visible=form_fields, editable=form_fields,
                        operations=[p for p in ("create", "update") if p in permissions],
                        attributes=model_info.get("attributes", []),
                        data_scope=_actor_owned_data_scope(current_actor_name, model, semantic_overrides),
                        relation_data_scopes=_model_relation_data_scopes(current_actor_name, model_info, semantic_overrides, page_primary_model=model),
                    ))
            # Add child sections from composition + subordinates + 1:many associations
            _add_association_sections(
                page_id, model, model_info, model_graph,
                accessible, subordinate_models, existing_section_ids, add_section,
            )

    # ── Step 4: auto-infer detail pages for collection models with update/create ──

    for col_pid, col_pm in [(pid, pm) for pid, pm in page_map.items()
                            if pm["role"] == "collection_workspace"]:
        model = col_pm["model"]
        if not model or model in subordinate_models:
            continue
        perms = list(target_permissions.get(model) or [])
        if not any(p in perms for p in ("create", "update")):
            continue
        detail_id = f"{_sid(model)}_detail"
        if detail_id in existing_page_ids:
            continue

        model_info = model_graph.get(model) or {}
        override = (semantic_overrides.get("models") or {}).get(model) or semantic_overrides.get(model) or {}

        add_page({"id": detail_id, "name": f"{model} Detail", "primary_model": model,
                  "role": "detail_workspace", "nav": False, "sections": []})

        visible = _pick_fields(model_info, "object_detail")
        add_section(_section(
            page_id=detail_id,
            section_id=f"{detail_id}_{_sid(model)}_object_detail",
            role="object_detail", name=f"{model} Detail",
            layout="detail", component=override.get("detail_component") or _detail_component(model),
            model=model, visible=visible, editable=[], operations=["read"],
            attributes=model_info.get("attributes", []),
            data_scope=_actor_owned_data_scope(current_actor_name, model, semantic_overrides),
            relation_data_scopes=_model_relation_data_scopes(current_actor_name, model_info, semantic_overrides),
        ))
        form_fields = _pick_fields(model_info, "object_form", 10)
        if form_fields:
            add_section(_section(
                page_id=detail_id,
                section_id=f"{detail_id}_{_sid(model)}_object_form",
                role="object_form", name=f"Edit {model}",
                layout="form", component=_form_component(model, detail_id),
                model=model, visible=form_fields, editable=form_fields,
                operations=[p for p in ("create", "update") if p in perms],
                attributes=model_info.get("attributes", []),
                data_scope=_actor_owned_data_scope(current_actor_name, model, semantic_overrides),
                relation_data_scopes=_model_relation_data_scopes(current_actor_name, model_info, semantic_overrides, page_primary_model=model),
            ))
        _add_association_sections(
            detail_id, model, model_info, model_graph,
            accessible, subordinate_models, existing_section_ids, add_section,
        )

    # ── Step 5: workflow activity pages (one page per step) ───────────────────

    _FORM_HINTS = {"PaymentMethodForm", "AddressForm", "ReviewForm", "ObjectForm", "FileUpload"}
    _DETAIL_HINTS = {"DetailPanel"}
    _LIST_HINTS = {"SelectionList"}

    current_actor_name_l = current_actor_name.lower()

    for wf in workflow_intel.get("workflows") or []:
        if not wf.get("is_multi_step"):
            continue
        wf_id = _sid(wf.get("name") or "workflow")

        for i, step in enumerate(wf.get("steps") or []):
            action = step.get("action") or f"Step {i + 1}"
            step_model = step.get("model") or ""
            hint = step.get("component_hint") or "ObjectForm"
            step_page_id = f"{wf_id}_step{i + 1}_{_sid(action)}"
            step_override = (
                (semantic_overrides.get("activity_steps") or {}).get(action)
                or (semantic_overrides.get("activity_steps") or {}).get(step_page_id)
                or {}
            )
            workflow_semantic = (
                (semantic_overrides.get("workflow_steps") or {}).get(action)
                or (semantic_overrides.get("workflow_steps") or {}).get(step_page_id)
                or {}
            )
            step_intent = workflow_semantic.get("intent") or ""
            if not step_intent and _is_create_like_activity(action):
                step_intent = "create_record"
                workflow_semantic = {
                    **workflow_semantic,
                    "intent": step_intent,
                    "target_model": workflow_semantic.get("target_model") or step_model,
                }

            is_automatic_step = bool(step.get("is_automatic"))

            # Swim lane filter: only generate pages for steps in this actor's lane.
            step_actor = (step.get("actor_node_name") or "").strip().lower()
            actor_lane_assigned = bool(step_actor and current_actor_name_l and step_actor == current_actor_name_l)
            if step_actor and current_actor_name_l and step_actor != current_actor_name_l:
                continue

            override_model = step_override.get("model")
            if not override_model:
                override_model = workflow_semantic.get("target_model") or workflow_semantic.get("context_model")
            if override_model in model_graph and (actor_lane_assigned or override_model in accessible):
                step_model = override_model

            # Per-step model filter: skip steps whose model is inaccessible to this actor.
            if step_model and not actor_lane_assigned and step_model not in accessible:
                continue

            if step_page_id in existing_page_ids:
                continue

            step_model_info = model_graph.get(step_model) or {}
            step_attrs = step_model_info.get("attributes", [])
            valid_step_fields = {
                attr.get("name")
                for attr in step_attrs
                if attr.get("name")
            }
            override_editable = [
                field
                for field in (step_override.get("editable_fields") or [])
                if field in valid_step_fields
            ]
            semantic_readonly = [
                field
                for field in (workflow_semantic.get("readonly_fields") or step_override.get("readonly_fields") or [])
                if field in valid_step_fields
            ]
            semantic_editable = [
                field
                for field in (workflow_semantic.get("editable_fields") or override_editable or [])
                if field in valid_step_fields
            ]

            # Pick layout and component from LLM semantic override first; fall back
            # to rule-based component_hint when no valid override is provided.
            override_layout = step_override.get("layout")
            override_component = step_override.get("component")
            override_role = step_override.get("role")
            rule_layout = _activity_layout_from_action(action, hint)
            if step_intent == "check":
                layout, role, component = "detail", "object_detail", "SummaryPanel"
                condition = workflow_semantic.get("condition") or {}
                condition_field = condition.get("field")
                visible = semantic_readonly or ([condition_field] if condition_field in valid_step_fields else _pick_fields(step_model_info, "object_detail", 6))
                editable = []
                ops = ["read"]
            elif step_intent == "notify":
                layout, role, component = "detail", "object_detail", "SummaryPanel"
                visible = semantic_readonly or _pick_fields(step_model_info, "object_detail", 6)
                editable = []
                ops = ["read"]
            elif step_intent == "select_existing":
                layout, role = "list", "object_collection"
                component = _collection_component(step_model, "list") if step_model else "ObjectList"
                visible = semantic_readonly or _pick_fields(step_model_info, "object_collection", 6)
                editable = []
                ops = ["read", "select"]
            elif step_intent == "create_record":
                layout, role, component = "form", "object_form", "ObjectForm"
                editable = semantic_editable or override_editable or _pick_fields(step_model_info, "object_form", 8)
                readonly = semantic_readonly or [
                    field for field in _pick_fields(step_model_info, "object_detail", 4)
                    if field not in set(editable)
                ]
                visible = _merge_field_names(readonly, editable)
                ops = ["create"]
            elif step_intent == "update_record":
                layout, role, component = "form", "object_form", "ObjectForm"
                editable = semantic_editable or _pick_fields(step_model_info, "object_form", 2)
                readonly = semantic_readonly or [
                    field for field in _pick_fields(step_model_info, "object_detail", 6)
                    if field not in set(editable)
                ]
                visible = _merge_field_names(readonly, editable)
                ops = ["update"]
            elif override_layout in {"form", "list", "detail"} and override_component:
                layout = override_layout
                component = override_component
                if override_role in {"object_form", "object_collection", "object_detail"}:
                    role = override_role
                else:
                    role = "object_form" if layout == "form" else ("object_collection" if layout == "list" else "object_detail")
                if layout == "form":
                    ops = _activity_form_operations(action)
                    editable = semantic_editable or override_editable or _pick_fields(step_model_info, "object_form", 8)
                    editable_set = set(editable)
                    readonly = semantic_readonly or [
                        field for field in _pick_fields(step_model_info, "object_detail", 6)
                        if field not in editable_set
                    ]
                    visible = _merge_field_names(readonly, editable) if ops == ["update"] else editable
                elif layout == "list":
                    visible = _pick_fields(step_model_info, "object_collection", 6)
                    editable = []
                    ops = ["read", "select"]
                else:
                    visible = _pick_fields(step_model_info, "object_detail", 8)
                    editable = []
                    ops = ["read"]
            elif rule_layout:
                layout, role, component = rule_layout
                if layout == "list":
                    visible = _pick_fields(step_model_info, "object_collection", 6)
                    editable = []
                    ops = ["read", "select"]
                else:
                    visible = _pick_fields(step_model_info, "object_detail", 8)
                    editable = []
                    ops = ["read"]
            elif hint in _FORM_HINTS:
                layout, role = "form", "object_form"
                component = hint if hint != "FileUpload" else "ObjectForm"
                ops = _activity_form_operations(action)
                editable = semantic_editable or override_editable or _pick_fields(step_model_info, "object_form", 8)
                readonly = semantic_readonly or [
                    field for field in _pick_fields(step_model_info, "object_detail", 6)
                    if field not in set(editable)
                ]
                visible = _merge_field_names(readonly, editable) if ops == ["update"] else editable
            elif hint in _LIST_HINTS:
                layout, role = "list", "object_collection"
                component = _collection_component(step_model, "list") if step_model else "ObjectList"
                visible = _pick_fields(step_model_info, "object_collection", 6)
                editable = []
                ops = ["read", "select"]
            else:  # DetailPanel, confirm, summary
                layout, role = "detail", "object_detail"
                component = "SummaryPanel" if any(w in action.lower() for w in ("confirm", "summary", "review", "check")) else "DetailPanel"
                visible = _pick_fields(step_model_info, "object_detail", 8)
                editable = []
                ops = ["read"]

            add_page({
                "id": step_page_id,
                "name": action,
                "primary_model": step_model,
                "role": "workflow_entry",
                "type": {"value": "activity", "label": "Activity"},
                "nav": False,
                "sections": [],
            })

            # Content section — always emit; confirmation/summary steps get a
            # SummaryPanel even with no model so the page has something to render.
            # Steps owned by another actor are skipped above; rendered steps use their own operations.
            _is_confirm = any(w in action.lower() for w in ("confirm", "summary", "check", "complete", "finish", "approve", "submit", "review"))
            effective_ops = ops
            effective_editable = editable
            effective_readonly = [
                field for field in visible or []
                if field not in set(effective_editable or [])
            ]
            rendered_step_attrs = [
                attr
                for attr in step_attrs
                if attr.get("name") in set(visible or effective_editable or [])
            ] or step_attrs
            semantic_attrs = _semantic_section_attrs(step_attrs, effective_readonly, effective_editable)
            if semantic_attrs:
                rendered_step_attrs = semantic_attrs
            section_style = {
                "color": "accent",
                "density": "normal",
                "shadow": "sm",
                "border": "light",
                "bg": "white",
            }
            semantic_payload = _workflow_semantics_payload(workflow_semantic, effective_readonly, effective_editable)
            if semantic_payload:
                section_style["workflow_semantics"] = semantic_payload
            data_scope = _actor_owned_data_scope(current_actor_name, step_model, semantic_overrides)
            if data_scope:
                section_style["data_scope"] = data_scope
            relation_scopes = _model_relation_data_scopes(current_actor_name, step_model_info, semantic_overrides)
            if relation_scopes:
                section_style["relation_data_scopes"] = relation_scopes
            if visible or step_model:
                add_section(_section(
                    page_id=step_page_id,
                    section_id=f"{step_page_id}_content",
                    role=role,
                    name=action,
                    layout=layout,
                    component=component,
                    model=step_model,
                    visible=visible,
                    editable=effective_editable,
                    operations=effective_ops,
                    attributes=rendered_step_attrs,
                    style=section_style,
                ))
            elif _is_confirm or is_automatic_step:
                add_section(_section(
                    page_id=step_page_id,
                    section_id=f"{step_page_id}_content",
                    role="object_detail",
                    name=action,
                    layout="detail",
                    component="SummaryPanel",
                    model="",
                    visible=[], editable=[],
                    operations=["read"],
                    attributes=[],
                ))

            add_section(_section(
                page_id=step_page_id,
                section_id=f"{step_page_id}_action",
                role="activity_action",
                name=action,
                layout="activity_action",
                component="WorkflowActionButton",
                model=step_model,
                visible=[],
                editable=[],
                operations=[],
                style={"variant": "button", "align": "right", "size": "lg"},
                workflow={"action": "complete"},
            ))

    # ── Finalize page.sections lists ─────────────────────────────────────────

    for page in pages:
        page["sections"] = page_sections.get(page["id"], [])

    return {
        "pages": pages,
        "sections": sections,
        "summary": {
            "page_count": len(pages),
            "section_count": len(sections),
        },
    }
