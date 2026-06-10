"""
In-memory Jinja2 renderer that converts interface.data + system classifiers
into rendered HTML files with per-section layout/style and click-to-select support.
"""
import re
from enum import IntEnum
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader

from llm.interface_generator.section_utils import _normalize_select_existing_sections

TEMPLATE_DIR = "/usr/src/templates"
UNIFIED_TEMPLATE = "page_unified.html.jinja2"

DEFAULT_SECTION_STYLE = {
    "color": "blue",
    "density": "normal",
    "radius": "xl",
    "columns": "3",
    "card_style": "elevated",
    "image_position": "top",
    "image_size": "md",
}

SOURCE_PARENT_MULTIPLICITIES = {("*", "1"), ("1..*", "1")}
TARGET_PARENT_MULTIPLICITIES = {("1", "*"), ("1", "1..*")}

CLICK_SCRIPT = """
<script>
(function() {
  var style = document.createElement('style');
  style.textContent = '[data-section-id]{cursor:pointer;transition:outline 0.15s}[data-section-id]:hover{outline:2px dashed #93c5fd;outline-offset:6px}[data-section-id].si-selected{outline:2px solid #3b82f6;outline-offset:6px}';
  document.head.appendChild(style);
  document.addEventListener('click', function(e) {
    var link = e.target.closest && e.target.closest('a[href]');
    if (link) { e.preventDefault(); }
    var el = e.target.closest && e.target.closest('[data-section-id]');
    if (!el) return;
    e.stopPropagation();
    document.querySelectorAll('[data-section-id]').forEach(function(x){x.classList.remove('si-selected')});
    el.classList.add('si-selected');
    window.parent.postMessage({type:'section-selected',id:el.dataset.sectionId,name:el.dataset.sectionName},'*');
  }, true);
})();
</script>
"""


class AttributeType(IntEnum):
    INTEGER = 1
    STRING = 2
    BOOLEAN = 3
    ENUM = 4
    IMAGE = 5
    VIDEO = 6


class _Attribute:
    def __init__(self, name, type_, enum_literals, updatable, derived, is_link=False, render_as="text", action=None, readonly=False, source="primary"):
        self.name = name
        self.type = type_
        self.enum_literals = enum_literals
        self.updatable = updatable
        self.derived = derived
        self.is_link = is_link
        self.render_as = render_as
        self.action = action or {"type": "none"}
        self.readonly = readonly
        self.source = source or "primary"

    def __str__(self):
        return self.name


ACTIVITY_ACTION_VARIANTS = {"button", "link", "fab", "row_action", "wizard_next", "auto"}


class _SectionComponent:
    def __init__(self, id, name, display_name, primary_model, parent_models, attributes,
                 has_create_operation, has_update_operation, has_delete_operation, has_select_operation, text,
                 layout="table", style=None, custom_methods=None, col_span=12,
                 related_to_section_id=None, relation_field=None, query=None, position="main",
                 component_type="data", label=None, workflow=None, min_height=None,
                 component=None, role=None, field_layout=None, behavior=None):
        self.id = id
        self.name = name
        self.display_name = display_name
        self.primary_model = primary_model
        self.parent_models = parent_models
        self.attributes = attributes
        self.has_create_operation = has_create_operation
        self.has_update_operation = has_update_operation
        self.has_delete_operation = has_delete_operation
        self.has_select_operation = has_select_operation
        self.text = text
        self.layout = layout or "table"
        self.component = component or ""
        self.role = role or ""
        self.field_layout = field_layout or {}
        self.behavior = behavior or {}
        self.style = {**DEFAULT_SECTION_STYLE, **(style or {})}
        self.style["columns"] = str(self.style.get("columns", "3"))
        self.custom_methods = custom_methods or []
        self.col_span = col_span if col_span in (3, 4, 6, 12) else 12
        self.related_to_section_id = related_to_section_id
        self.relation_field = relation_field
        self.query = query or {}
        self.position = position or "main"
        self.component_type = component_type  # "data" | "activity_action"
        self.label = label  # used by activity_action
        self.success_page = (style or {}).get("success_page")
        self.workflow = workflow or {}
        self.workflow_action = self.workflow.get("action", "complete")
        workflow_target_page = self.workflow.get("target_page") or self.workflow.get("targetPage")
        self.workflow_target_page = _sanitize(workflow_target_page) if workflow_target_page else None
        item_click = self.behavior.get("item_click") if isinstance(self.behavior.get("item_click"), dict) else {}
        item_click_target_page = (
            item_click.get("target_page") or item_click.get("targetPage")
            if item_click.get("type") == "navigate"
            else None
        )
        self.item_click_target_page = _sanitize(item_click_target_page) if item_click_target_page else None
        self.min_height = int(min_height) if min_height else None

    def __str__(self):
        return self.name


def _make_activity_start_section(s_raw: dict = None) -> "_SectionComponent":
    s = s_raw or {}
    return _SectionComponent(
        id=s.get("id", "activity-start"),
        name="activity_start",
        display_name=s.get("name") or s.get("label") or "Start a Process",
        primary_model="", parent_models=[], attributes=[],
        has_create_operation=False, has_update_operation=False, has_delete_operation=False, has_select_operation=False,
        text="",
        col_span=int(s.get("col_span", 12)),
        position=s.get("position", "main"),
        style={
            "card_style": (s.get("style") or {}).get("card_style", "elevated"),
            "columns": str((s.get("style") or {}).get("columns", "3")),
            "align": (s.get("style") or {}).get("align", "left"),
            "cta_label": (s.get("style") or {}).get("cta_label", "Start"),
            "process_label": (s.get("style") or {}).get("process_label", ""),
        },
        component_type="activity_start",
        label=s.get("label") or s.get("name") or "Start a Process",
    )


def _make_activity_tasks_section(s_raw: dict = None) -> "_SectionComponent":
    s = s_raw or {}
    return _SectionComponent(
        id=s.get("id", "activity-tasks"),
        name="activity_tasks",
        display_name=s.get("name") or s.get("label") or "My Tasks",
        primary_model="", parent_models=[], attributes=[],
        has_create_operation=False, has_update_operation=False, has_delete_operation=False, has_select_operation=False,
        text="",
        col_span=int(s.get("col_span", 12)),
        position=s.get("position", "main"),
        style={
            "card_style": (s.get("style") or {}).get("card_style", "elevated"),
            "columns": str((s.get("style") or {}).get("columns", "3")),
        },
        component_type="activity_tasks",
        label=s.get("label") or s.get("name") or "My Tasks",
    )


def _make_activity_action_section(label: str, s_raw: dict = None) -> "_SectionComponent":
    s = s_raw or {}
    raw_style = s.get("style") or {}
    raw_workflow = s.get("workflow") or {}
    variant = raw_style.get("variant", "button")
    if variant not in ACTIVITY_ACTION_VARIANTS:
        variant = "button"
    workflow_action = raw_workflow.get("action") or s.get("workflow_action") or "complete"
    target_page = (
        raw_workflow.get("target_page")
        or raw_workflow.get("targetPage")
        or s.get("target_page")
        or s.get("targetPage")
    )
    return _SectionComponent(
        id=s.get("id", "activity-action"),
        name="activity_action",
        display_name=label,
        primary_model="", parent_models=[], attributes=[],
        has_create_operation=False, has_update_operation=False, has_delete_operation=False, has_select_operation=False,
        text="",
        col_span=int(s.get("col_span", 12)),
        position=s.get("position", "main"),
        style={"variant": variant, "size": raw_style.get("size", "lg"), "align": raw_style.get("align", "right")},
        component_type="activity_action",
        label=label,
        workflow={
            "action": workflow_action,
            **({"target_page": _sanitize(target_page)} if target_page else {}),
        },
    )


class _Page:
    def __init__(self, name, display_name, type_, activity_name, category, section_components, layout="vertical", gap="normal", is_task_page=False):
        self.name = name
        self.display_name = display_name
        self.type = type_
        self.activity_name = activity_name
        self.category = category
        self.section_components = section_components
        self.layout = layout or "vertical"
        self.gap = gap or "normal"
        self.is_task_page = is_task_page

    def __str__(self):
        return self.name


def _make_task_home_page(chrome_sections=None) -> "_Page":
    sections = [
        _make_activity_start_section({
            "id": "task-home-activity-start",
            "name": "Processes you can start",
            "label": "Processes you can start",
            "col_span": 6,
            "style": {"columns": "1", "card_style": "elevated", "cta_label": "Start"},
        }),
        _make_activity_tasks_section({
            "id": "task-home-activity-tasks",
            "name": "Tasks to complete",
            "label": "Tasks to complete",
            "col_span": 6,
            "style": {"columns": "1", "card_style": "elevated"},
        }),
    ]
    sections.extend(chrome_sections or [])
    return _Page(
        name="task",
        display_name="Task",
        type_="normal",
        activity_name=None,
        category=None,
        section_components=sections,
        layout="vertical",
        gap="normal",
        is_task_page=True,
    )


def _sanitize(name: str) -> str:
    name = str(name or "")
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name.lower()


def _id_reference_model(field_name: str, current_model: str, model_names: set[str]) -> Optional[str]:
    """Return the related model for fields like patient_id when that model exists."""
    raw = _sanitize(field_name)
    candidates = []
    if raw.endswith("_id") and len(raw) > 3:
        candidates.append(raw[:-3])
    elif raw.endswith("id") and len(raw) > 2:
        candidates.append(raw[:-2].rstrip("_"))
    current = _sanitize(current_model)
    for candidate in candidates:
        if not candidate or candidate == current:
            continue
        for model in model_names:
            if _sanitize(model) == candidate:
                return model
    return None

_LAYOUT_ALIASES = {
    "nav": "nav-links",
    "navigation": "nav-links",
    "navbar": "nav-links",
    "side-nav": "nav-links",
    "top-nav": "nav-links",
    "footer-links": "link-grid",
    "footer-brand": "brand-strip",
    "service-strip": "service-bar",
}

def _normalize_layout_alias(layout) -> str:
    value = str(layout or "").strip()
    return _LAYOUT_ALIASES.get(value, value)

def _attrs_for_section_render(section_raw: Dict, cls_data: Dict, layout: str) -> List:
    raw_attrs = section_raw.get("attributes") or []
    if raw_attrs:
        return raw_attrs
    if not cls_data or layout not in {"card", "list", "table", "detail", "gallery", "filter", "form"}:
        return []
    attrs = [
        attr for attr in (cls_data.get("attributes") or [])
        if isinstance(attr, dict) and attr.get("name") and str(attr.get("name")).lower() not in {"id", "pk"}
    ]
    preferred = ["name", "title", "status", "amount", "price", "total", "email", "phone", "date", "description"]
    selected = []
    for key in preferred:
        selected.extend([attr for attr in attrs if key in str(attr.get("name", "")).lower() and attr not in selected])
    selected.extend([attr for attr in attrs if attr not in selected])
    return selected[:8]


def _parse_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'##### (.+)', r'<h5>\1</h5>', text)
    text = re.sub(r'#### (.+)', r'<h4>\1</h4>', text)
    text = re.sub(r'### (.+)', r'<h3>\1</h3>', text)
    text = re.sub(r'## (.+)', r'<h2>\1</h2>', text)
    text = re.sub(r'# (.+)', r'<h1>\1</h1>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    text = text.replace("\n", "<br>")
    return text


def _parse_custom_methods(section_raw: Dict) -> List[str]:
    methods = []
    for method_raw in section_raw.get("methods", []) or []:
        if isinstance(method_raw, dict):
            method_name = method_raw.get("name") or method_raw.get("label") or method_raw.get("value")
            if method_name:
                methods.append(str(method_name))
        elif method_raw:
            methods.append(str(method_raw))
    return methods


def _parse_query(section_raw: Dict) -> Dict:
    query = dict(section_raw.get("query") or {})
    relationship = section_raw.get("relationship") or {}
    if "limit" not in query and relationship.get("limit") is not None:
        query["limit"] = relationship.get("limit")
    if "exclude_source" not in query and relationship.get("exclude_source") is not None:
        query["exclude_source"] = relationship.get("exclude_source")
    return query


def _parse_operations(raw) -> Dict:
    select_terms = {"select", "choose", "pick", "bulk_select", "multi_select", "batch_select"}
    false_terms = {"", "0", "false", "no", "none", "null", "off"}

    def enabled(value) -> bool:
        if isinstance(value, str):
            return value.strip().lower() not in false_terms
        return bool(value)

    if isinstance(raw, dict):
        return {
            "create": any(enabled(raw.get(term, False)) for term in ("create", "add")),
            "update": any(enabled(raw.get(term, False)) for term in ("update", "edit")),
            "delete": any(enabled(raw.get(term, False)) for term in ("delete", "remove")),
            "select": any(enabled(raw.get(term, False)) for term in select_terms),
        }
    if isinstance(raw, str):
        raw = re.split(r"[\s,;|]+", raw)
    if isinstance(raw, list):
        values = {str(value).strip().lower() for value in raw}
        return {
            "create": bool({"create", "add"} & values),
            "update": bool({"update", "edit"} & values),
            "delete": bool({"delete", "remove"} & values),
            "select": bool(select_terms & values),
        }
    return {"create": False, "update": False, "delete": False, "select": False}


def _default_enum_literals_for_attr(attr_name: str) -> List[str]:
    name = _sanitize(attr_name)
    if name in {"status", "state", "phase", "stage"} or name.endswith("_status") or name.endswith("_state"):
        return ["pending", "active", "completed", "cancelled"]
    return []


def _relation_data(relation: Dict) -> Dict:
    return relation.get("data", relation)


def _relation_endpoint(relation: Dict, key: str) -> Optional[str]:
    value = relation.get(key)
    if isinstance(value, dict):
        return str(value.get("id")) if value.get("id") else None
    return str(value) if value else None


def _infer_parent_models(class_id: str, classifiers: List[Dict], relations: Optional[List[Dict]]) -> List[str]:
    if not class_id or not relations:
        return []

    classifier_names = {
        str(c["id"]): _sanitize(c.get("data", {}).get("name", ""))
        for c in (classifiers or [])
    }

    out = []
    for relation in relations:
        data = _relation_data(relation)
        if data.get("type") != "association":
            continue

        source_id = _relation_endpoint(relation, "source")
        target_id = _relation_endpoint(relation, "target")
        multiplicity = data.get("multiplicity") or {}
        source_mult = str(multiplicity.get("source", ""))
        target_mult = str(multiplicity.get("target", ""))

        parent_id = None
        if source_id == str(class_id) and (source_mult, target_mult) in SOURCE_PARENT_MULTIPLICITIES:
            parent_id = target_id
        elif target_id == str(class_id) and (source_mult, target_mult) in TARGET_PARENT_MULTIPLICITIES:
            parent_id = source_id

        parent_name = classifier_names.get(str(parent_id)) if parent_id else None
        if parent_name and parent_name not in out:
            out.append(parent_name)

    return out


def _parse_pages(interface_data: Dict, classifiers: List[Dict], interface_name: str, layout_config: Optional[Dict] = None, relations: Optional[List[Dict]] = None):
    classifier_map: Dict[str, Dict] = {
        str(c["id"]): c.get("data", {}) for c in (classifiers or [])
    }
    classifier_name_map: Dict[str, Dict] = {
        _sanitize(c.get("data", {}).get("name", "")): c.get("data", {})
        for c in (classifiers or [])
        if c.get("data", {}).get("name")
    }
    model_names = {
        _sanitize(c.get("data", {}).get("name", ""))
        for c in (classifiers or [])
        if c.get("data", {}).get("type") == "class" and c.get("data", {}).get("name")
    }

    sections_raw = interface_data.get("sections", [])
    section_by_id: Dict[str, Dict] = {s["id"]: s for s in sections_raw}
    _activity_section_types = {"activity_action", "activity_start", "activity_tasks"}
    layout_region_section_ids = [
        str(s.get("id"))
        for s in sections_raw
        if s.get("id") and s.get("position") in ("header", "footer", "sidebar")
        and s.get("type") not in _activity_section_types
        and s.get("layout") not in _activity_section_types
    ]

    app_name = _sanitize(interface_name)

    pages = []
    for p_raw in interface_data.get("pages", []):
        section_components = []
        page_section_refs = list(p_raw.get("sections", []))
        page_section_ids = {
            str(ref.get("value") if isinstance(ref, dict) else ref)
            for ref in page_section_refs
        }
        for region_section_id in layout_region_section_ids:
            if region_section_id not in page_section_ids:
                page_section_refs.append({"value": region_section_id})

        for ref in page_section_refs:
            sec_id = ref.get("value") if isinstance(ref, dict) else str(ref)
            s_raw = section_by_id.get(sec_id)
            if not s_raw:
                continue

            # Skip sections that are explicitly hidden
            if s_raw.get("visible") is False:
                continue

            # activity_action section — render as workflow completion button
            if s_raw.get("type") == "activity_action" or s_raw.get("layout") == "activity_action":
                section_components.append(_make_activity_action_section(
                    label=s_raw.get("label") or s_raw.get("name", ""),
                    s_raw=s_raw,
                ))
                continue

            # activity_start section — show available processes to start
            if s_raw.get("type") == "activity_start" or s_raw.get("layout") == "activity_start":
                section_components.append(_make_activity_start_section(s_raw=s_raw))
                continue

            # activity_tasks section — show active tasks to complete
            if s_raw.get("type") == "activity_tasks" or s_raw.get("layout") == "activity_tasks":
                section_components.append(_make_activity_tasks_section(s_raw=s_raw))
                continue

            class_ref = str(s_raw.get("class", "") or "")
            cls_data = classifier_map.get(class_ref, {}) or classifier_name_map.get(_sanitize(class_ref), {})
            declared_primary_model = str(s_raw.get("primary_model") or s_raw.get("object") or "")
            if not cls_data and declared_primary_model:
                cls_data = classifier_name_map.get(_sanitize(declared_primary_model), {})
            primary_model = _sanitize(cls_data.get("name", "")) if cls_data else ""
            parent_models = _infer_parent_models(str(s_raw.get("class", "")), classifiers, relations)
            sec_layout = _normalize_layout_alias(s_raw.get("layout", "table"))

            attributes = []
            classifier_attr_types = {
                _sanitize(attr.get("name", "")): str(attr.get("type", "str")).lower()
                for attr in cls_data.get("attributes", [])
                if isinstance(attr, dict)
            }
            for attr_raw in _attrs_for_section_render(s_raw, cls_data, sec_layout):
                if isinstance(attr_raw, str):
                    attr_data = {"name": attr_raw}
                else:
                    attr_data = attr_raw or {}

                attr_name = _sanitize(attr_data.get("name", ""))
                reference_model = _id_reference_model(attr_name, primary_model, model_names)
                if reference_model:
                    if reference_model not in parent_models:
                        parent_models.append(reference_model)
                    continue
                inferred_type = classifier_attr_types.get(attr_name)
                if not inferred_type and any(token in attr_name.lower() for token in ("image", "img", "photo", "thumbnail", "thumb", "avatar", "poster", "cover", "logo")):
                    inferred_type = "image"
                if not inferred_type and any(token in attr_name.lower() for token in ("video", "trailer", "media_url")):
                    inferred_type = "video"
                explicit_enum_literals = (
                    attr_data.get("enum_values")
                    or attr_data.get("options")
                    or attr_data.get("choices")
                    or []
                )
                type_str = attr_data.get("type") or inferred_type or "str"
                if explicit_enum_literals and str(type_str).lower() in {"str", "string", "enum"}:
                    type_str = "enum"
                if type_str == "int":
                    attr_type = AttributeType.INTEGER
                elif type_str == "bool":
                    attr_type = AttributeType.BOOLEAN
                elif type_str == "enum":
                    attr_type = AttributeType.ENUM
                elif _default_enum_literals_for_attr(attr_name):
                    attr_type = AttributeType.ENUM
                elif type_str == "image":
                    attr_type = AttributeType.IMAGE
                elif type_str == "video":
                    attr_type = AttributeType.VIDEO
                else:
                    attr_type = AttributeType.STRING

                enum_literals = []
                if attr_type == AttributeType.ENUM and explicit_enum_literals:
                    enum_literals = [str(lit) for lit in explicit_enum_literals if str(lit)]
                elif attr_type == AttributeType.ENUM and attr_data.get("enum"):
                    enum_cls = classifier_map.get(str(attr_data["enum"]), {})
                    enum_literals = [str(lit) for lit in enum_cls.get("literals", [])]
                elif attr_type == AttributeType.ENUM:
                    enum_literals = _default_enum_literals_for_attr(attr_name)

                render_config = attr_data.get("render") or {}
                render_as = render_config.get("as") or attr_data.get("render_as") or ("link" if attr_data.get("is_link") else "text")
                action = attr_data.get("action") or ({"type": "navigate"} if attr_data.get("is_link") else {"type": "none"})
                readonly = bool(attr_data.get("readonly", False))
                attributes.append(_Attribute(
                    name=_sanitize(attr_data.get("name", "")),
                    type_=attr_type,
                    enum_literals=enum_literals,
                    updatable=not readonly,
                    derived=bool(attr_data.get("derived", False)),
                    is_link=bool(attr_data.get("is_link")) or render_as == "link",
                    render_as=render_as,
                    action=action,
                    readonly=readonly,
                    source=attr_data.get("source") or ("related" if "." in str(attr_data.get("name", "")) else "primary"),
                ))

            ops = _parse_operations(s_raw.get("operations", {}))

            sec_style = {**DEFAULT_SECTION_STYLE, **(s_raw.get("style") or {})}
            if layout_config and not s_raw.get("layout"):
                sec_layout = layout_config.get("layout", sec_layout)
                sec_style = {**sec_style, **layout_config.get("style", {})}
            sec_style["columns"] = str(sec_style.get("columns", "3"))

            section_components.append(_SectionComponent(
                id=s_raw.get("id", ""),
                name=_sanitize(s_raw.get("name", "")),
                display_name=s_raw.get("name", ""),
                primary_model=primary_model,
                parent_models=parent_models,
                attributes=attributes,
                has_create_operation=bool(ops.get("create", False)),
                has_update_operation=bool(ops.get("update", False)),
                has_delete_operation=bool(ops.get("delete", False)),
                has_select_operation=bool(ops.get("select", False)),
                text=_parse_text(s_raw.get("text", "")),
                layout=sec_layout,
                style=sec_style,
                custom_methods=_parse_custom_methods(s_raw),
                col_span=int(s_raw.get("col_span", 12)),
                min_height=s_raw.get("min_height"),
                related_to_section_id=s_raw.get("related_to"),
                relation_field=s_raw.get("relation_field"),
                query=_parse_query(s_raw),
                position=s_raw.get("position", "main"),
                component=s_raw.get("component"),
                role=s_raw.get("role"),
                field_layout=s_raw.get("field_layout") if isinstance(s_raw.get("field_layout"), dict) else {},
                behavior=s_raw.get("behavior") if isinstance(s_raw.get("behavior"), dict) else {},
            ))

        type_field = p_raw.get("type")
        page_type = type_field.get("value", "normal") if isinstance(type_field, dict) else (str(type_field) if type_field else "normal")

        layout_field = p_raw.get("layout")
        if isinstance(layout_field, dict):
            page_layout = {**layout_field, "value": layout_field.get("value", "vertical")}
        else:
            page_layout = str(layout_field) if layout_field else "vertical"

        gap_field = p_raw.get("gap")
        page_gap = gap_field.get("value", "normal") if isinstance(gap_field, dict) else (str(gap_field) if gap_field else "normal")

        action_field = p_raw.get("action")
        activity_name = action_field.get("label") if isinstance(action_field, dict) else None

        # Auto-inject activity_action section if page is activity type and none defined
        if page_type == "activity" and not any(s.component_type == "activity_action" for s in section_components):
            section_components.append(_make_activity_action_section(
                label=activity_name or p_raw.get("name", "Complete"),
            ))

        pages.append(_Page(
            name=_sanitize(p_raw.get("name", "")),
            display_name=p_raw.get("name", "").replace("_", " ").replace("-", " ").strip(),
            type_=page_type,
            activity_name=activity_name,
            category=None,
            section_components=section_components,
            layout=page_layout,
            gap=page_gap,
        ))

    if not any(page.name == "task" for page in pages):
        chrome_sections = []
        seen_chrome = set()
        for page in pages:
            for section in page.section_components:
                if section.position in ("header", "footer") and section.id not in seen_chrome:
                    seen_chrome.add(section.id)
                    chrome_sections.append(section)
        pages.insert(0, _make_task_home_page(chrome_sections))

    return app_name, pages


_FONT_CDN = {
    "inter":            "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
    "roboto":           "https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap",
    "poppins":          "https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap",
    "playfair":         "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&display=swap",
    "playfair display": "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&display=swap",
    "mono":             "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap",
    "jetbrains mono":   "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap",
    "geist":            "https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&display=swap",
    "dm sans":          "https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap",
    "lato":             "https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap",
    "montserrat":       "https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap",
    "nunito":           "https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700&display=swap",
    "raleway":          "https://fonts.googleapis.com/css2?family=Raleway:wght@400;500;600;700&display=swap",
    "source sans pro":  "https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap",
    "source sans 3":    "https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap",
    "open sans":        "https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;500;600;700&display=swap",
    "ubuntu":           "https://fonts.googleapis.com/css2?family=Ubuntu:wght@400;500;700&display=swap",
    "noto sans":        "https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;500;600;700&display=swap",
}

_FONT_CSS_NAME = {
    "inter": "Inter", "roboto": "Roboto", "poppins": "Poppins",
    "playfair": "'Playfair Display'", "mono": "'JetBrains Mono'", "geist": "Geist",
}

_MAX_WIDTH_CLASS = {
    "sm": "max-w-3xl", "md": "max-w-4xl", "lg": "max-w-5xl",
    "xl": "max-w-6xl", "2xl": "max-w-7xl", "full": "max-w-full",
}

def normalize_interface_schema(interface_data: Dict) -> Dict:
    """Return the canonical schema consumed by both preview and generated live templates."""
    raw = dict(interface_data or {})
    canonical = raw.get("canonical_schema")
    if isinstance(canonical, dict):
        merged = dict(raw)
        for key in ("pages", "sections", "tokens", "styling", "prompt_intent"):
            if key in canonical:
                merged[key] = canonical[key]
        raw = merged

    pages = []
    for page in raw.get("pages") or []:
        if not isinstance(page, dict):
            continue
        page = dict(page)
        layout = page.get("layout") or {}
        if isinstance(layout, str):
            layout = {"value": layout}
        elif not isinstance(layout, dict):
            layout = {}
        layout.setdefault("value", "vertical")
        layout.setdefault("main_width", "contained")
        layout.setdefault("header_width", "contained")
        layout.setdefault("hero_width", "contained")
        layout.setdefault("footer_width", "contained")
        page["layout"] = layout

        refs = []
        for ref in page.get("sections") or []:
            if isinstance(ref, dict):
                value = ref.get("value") or ref.get("id")
                if value:
                    refs.append({**ref, "value": value})
            elif isinstance(ref, str):
                refs.append({"value": ref})
        page["sections"] = refs
        pages.append(page)

    sections = []
    for section in raw.get("sections") or []:
        if not isinstance(section, dict):
            continue
        section = dict(section)
        section.setdefault("position", "main")
        section.setdefault("style", {})
        section.setdefault("operations", {"create": False, "update": False, "delete": False, "select": False})
        if not isinstance(section.get("style"), dict):
            section["style"] = {}
        section["operations"] = _parse_operations(section.get("operations"))
        if section.get("field_layout") is None:
            section["field_layout"] = {}
        sections.append(section)

    normalized = dict(raw)
    sections = _normalize_select_existing_sections(pages, sections)
    normalized["pages"] = pages
    normalized["sections"] = sections
    normalized["tokens"] = dict(raw.get("tokens") or {})
    normalized["styling"] = dict(raw.get("styling") or {})
    normalized["canonical_schema"] = {
        "version": 1,
        "pages": pages,
        "sections": sections,
        "tokens": normalized["tokens"],
        "styling": normalized["styling"],
        **({"prompt_intent": raw.get("prompt_intent")} if raw.get("prompt_intent") else {}),
    }
    return normalized


def _apply_styling_tokens(tokens: dict, styling: dict, interface_name: str) -> None:
    """Merge styling dict into tokens in-place. Tokens already set take priority."""
    tokens.setdefault("brand.name", interface_name)
    default_blues = {"", None, "#2563eb", "#0000a4", "var(--accent)"}
    styling_accent = styling.get("accentColor", "")
    current_accent = tokens.get("accent.hex")
    if styling_accent and current_accent in default_blues:
        tokens["accent.hex"] = styling_accent
    accent = tokens.get("accent.hex")
    if accent:
        if "region.header.bg" not in tokens:
            tokens["region.header.bg"] = f"bg-[{accent}]"
            tokens["page.header.text"] = "text-white"

    bg = styling.get("backgroundColor", "")
    if bg and "page.body.bg" not in tokens:
        tokens["page.body.bg"] = f"bg-[{bg}]"

    text = styling.get("textColor", "")
    if text and "page.body.text" not in tokens:
        tokens["page.body.text"] = f"text-[{text}]"

    font = styling.get("fontFamily", "inter")
    tokens.setdefault("page.font.family", _FONT_CSS_NAME.get(font, "Inter"))
    if "page.font.cdn" not in tokens:
        # Prefer CDN matched to the already-resolved font family (e.g. from MD spec)
        _PROPRIETARY_FONTS = {
            "airbnb cereal", "airbnb cereal vf", "sf pro", "sf pro display", "sf pro text",
            "circular", "circular std", "gt walsheim", "gt america", "basier circle",
            "neue haas grotesk", "helvetica neue", "helvetica", "neue montreal",
        }
        family_lower = tokens.get("page.font.family", "Inter").lower().strip("'\" ")
        cdn = _FONT_CDN.get(family_lower) or _FONT_CDN.get(font)
        if cdn is None:
            for key, url in _FONT_CDN.items():
                if key in family_lower or family_lower.startswith(key):
                    cdn = url
                    break
        # Only fall through to Inter default — don't auto-generate URLs that may 404
        tokens["page.font.cdn"] = cdn or (
            "" if any(p in family_lower for p in _PROPRIETARY_FONTS)
            else _FONT_CDN["inter"]
        )

    radius = styling.get("radius", 8)
    tokens.setdefault("page.radius.px", str(radius))

    max_w = styling.get("pageMaxWidth", "xl")
    tokens.setdefault("page.container.class", _MAX_WIDTH_CLASS.get(max_w, "max-w-6xl"))

    tokens.setdefault("theme.button.style", styling.get("buttonStyle", "solid"))
    tokens.setdefault("theme.card.hover", styling.get("cardHover", "lift"))
    tokens.setdefault("theme.image.ratio", styling.get("imageRatio", "4:3"))
    tokens.setdefault("theme.divider", styling.get("divider", "none"))

    accent_hex = tokens.get("accent.hex")
    if accent_hex:
        for key in ("region.header.bg_hex", "region.footer.bg_hex", "button.primary.bg_hex", "button.primary.border_hex", "input.border_focus_hex"):
            if tokens.get(key) in default_blues:
                tokens[key] = accent_hex
        tokens.setdefault("region.header.text_hex", "#ffffff")
        tokens.setdefault("region.footer.text_hex", "#ffffff")


def render_layout(
    interface_data: Dict,
    classifiers: List[Dict],
    layout_config: Optional[Dict],
    interface_name: str = "interface",
    inject_click_handlers: bool = False,
    relations: Optional[List[Dict]] = None,
    preview_mode: bool = True,
) -> List[Dict]:
    interface_data = normalize_interface_schema(interface_data)
    app_name, pages = _parse_pages(interface_data, classifiers, interface_name, layout_config, relations)

    tokens = dict(interface_data.get("tokens", {}))
    styling = interface_data.get("styling", {})
    _apply_styling_tokens(tokens, styling, app_name)

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(UNIFIED_TEMPLATE)

    output_files = []
    for page in pages:
        rendered = template.render(
            application_name=app_name,
            application_namespace=app_name,
            page=page,
            pages=pages,
            all_pages=pages,
            AttributeType=AttributeType,
            preview_mode=preview_mode,
            tokens=tokens,
            styling=styling,
        )
        if inject_click_handlers:
            rendered = rendered.replace("</body>", CLICK_SCRIPT + "</body>")
        output_files.append({
            "path": f"templates/{app_name}_{page.name}.html",
            "content": rendered,
            "type": "html",
        })

    return output_files


def render_preview(
    interface_data: Dict,
    classifiers: List[Dict],
    interface_name: str = "interface",
    relations: Optional[List[Dict]] = None,
) -> List[Dict]:
    interface_data = normalize_interface_schema(interface_data)
    app_name, pages = _parse_pages(interface_data, classifiers, interface_name, relations=relations)
    tokens = dict(interface_data.get("tokens", {}))
    styling = interface_data.get("styling", {})
    _apply_styling_tokens(tokens, styling, app_name)

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(UNIFIED_TEMPLATE)

    output_files = []
    for page in pages:
        rendered = template.render(
            application_name=app_name,
            application_namespace=app_name,
            page=page,
            pages=pages,
            all_pages=pages,
            AttributeType=AttributeType,
            preview_mode=True,
            tokens=tokens,
            styling=styling,
        )
        output_files.append({
            "path": f"preview/{app_name}_{page.name}.html",
            "content": rendered,
            "type": "html",
        })

    return output_files
