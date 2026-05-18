"""
In-memory Jinja2 renderer that converts interface.data + system classifiers
into rendered HTML files with per-section layout/style and click-to-select support.
"""
import re
from enum import IntEnum
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader

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
  document.querySelectorAll('[data-section-id]').forEach(function(el) {
    el.addEventListener('click', function(e) {
      document.querySelectorAll('[data-section-id]').forEach(function(x){x.classList.remove('si-selected')});
      el.classList.add('si-selected');
      window.parent.postMessage({type:'section-selected',id:el.dataset.sectionId,name:el.dataset.sectionName},'*');
    });
  });
})();
</script>
"""


class AttributeType(IntEnum):
    INTEGER = 1
    STRING = 2
    BOOLEAN = 3
    ENUM = 4
    IMAGE = 5


class _Attribute:
    def __init__(self, name, type_, enum_literals, updatable, derived):
        self.name = name
        self.type = type_
        self.enum_literals = enum_literals
        self.updatable = updatable
        self.derived = derived

    def __str__(self):
        return self.name


class _SectionComponent:
    def __init__(self, id, name, display_name, primary_model, parent_models, attributes,
                 has_create_operation, has_update_operation, has_delete_operation, text,
                 layout="table", style=None, custom_methods=None, col_span=12, view_detail_page=None,
                 related_to_section_id=None, relation_field=None, query=None, position="main"):
        self.id = id
        self.name = name
        self.display_name = display_name
        self.primary_model = primary_model
        self.parent_models = parent_models
        self.attributes = attributes
        self.has_create_operation = has_create_operation
        self.has_update_operation = has_update_operation
        self.has_delete_operation = has_delete_operation
        self.text = text
        self.layout = layout or "table"
        self.style = {**DEFAULT_SECTION_STYLE, **(style or {})}
        self.style["columns"] = str(self.style.get("columns", "3"))
        self.custom_methods = custom_methods or []
        self.col_span = col_span if col_span in (3, 4, 6, 12) else 12
        self.view_detail_page = view_detail_page
        self.related_to_section_id = related_to_section_id
        self.relation_field = relation_field
        self.query = query or {}
        self.position = position or "main"

    def __str__(self):
        return self.name


class _Page:
    def __init__(self, name, display_name, type_, activity_name, category, section_components, layout="vertical", gap="normal", single_record=False):
        self.name = name
        self.display_name = display_name
        self.type = type_
        self.activity_name = activity_name
        self.category = category
        self.section_components = section_components
        self.layout = layout or "vertical"
        self.gap = gap or "normal"
        self.single_record = single_record

    def __str__(self):
        return self.name


def _sanitize(name: str) -> str:
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name.lower()


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

    sections_raw = interface_data.get("sections", [])
    section_by_id: Dict[str, Dict] = {s["id"]: s for s in sections_raw}

    app_name = _sanitize(interface_name)

    pages = []
    for p_raw in interface_data.get("pages", []):
        section_components = []
        for ref in p_raw.get("sections", []):
            sec_id = ref.get("value") if isinstance(ref, dict) else str(ref)
            s_raw = section_by_id.get(sec_id)
            if not s_raw:
                continue

            # Skip sections that are explicitly hidden
            if s_raw.get("visible") is False:
                continue

            cls_data = classifier_map.get(str(s_raw.get("class", "")), {})
            primary_model = _sanitize(cls_data.get("name", "item")) if cls_data else "item"
            parent_models = _infer_parent_models(str(s_raw.get("class", "")), classifiers, relations)

            attributes = []
            for attr_raw in s_raw.get("attributes", []):
                type_str = attr_raw.get("type", "str")
                if type_str == "int":
                    attr_type = AttributeType.INTEGER
                elif type_str == "bool":
                    attr_type = AttributeType.BOOLEAN
                elif type_str == "enum":
                    attr_type = AttributeType.ENUM
                elif type_str == "image":
                    attr_type = AttributeType.IMAGE
                else:
                    attr_type = AttributeType.STRING

                enum_literals = []
                if attr_type == AttributeType.ENUM and attr_raw.get("enum"):
                    enum_cls = classifier_map.get(str(attr_raw["enum"]), {})
                    enum_literals = [str(lit) for lit in enum_cls.get("literals", [])]

                attributes.append(_Attribute(
                    name=_sanitize(attr_raw.get("name", "")),
                    type_=attr_type,
                    enum_literals=enum_literals,
                    updatable=True,
                    derived=bool(attr_raw.get("derived", False)),
                ))

            ops = s_raw.get("operations", {})

            sec_layout = s_raw.get("layout", "table")
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
                text=_parse_text(s_raw.get("text", "")),
                layout=sec_layout,
                style=sec_style,
                custom_methods=_parse_custom_methods(s_raw),
                col_span=int(s_raw.get("col_span", 12)),
                view_detail_page=s_raw.get("view_detail_page"),
                related_to_section_id=s_raw.get("related_to"),
                relation_field=s_raw.get("relation_field"),
                query=_parse_query(s_raw),
                position=s_raw.get("position", "main"),
            ))

        type_field = p_raw.get("type")
        page_type = type_field.get("value", "normal") if isinstance(type_field, dict) else (str(type_field) if type_field else "normal")

        layout_field = p_raw.get("layout")
        page_layout = layout_field.get("value", "vertical") if isinstance(layout_field, dict) else (str(layout_field) if layout_field else "vertical")

        gap_field = p_raw.get("gap")
        page_gap = gap_field.get("value", "normal") if isinstance(gap_field, dict) else (str(gap_field) if gap_field else "normal")

        action_field = p_raw.get("action")
        activity_name = action_field.get("label") if isinstance(action_field, dict) else None

        pages.append(_Page(
            name=_sanitize(p_raw.get("name", "")),
            display_name=p_raw.get("name", ""),
            type_=page_type,
            activity_name=activity_name,
            category=None,
            section_components=section_components,
            layout=page_layout,
            gap=page_gap,
            single_record=bool(p_raw.get("single_record", False)),
        ))

    return app_name, pages


def render_layout(
    interface_data: Dict,
    classifiers: List[Dict],
    layout_config: Optional[Dict],
    interface_name: str = "interface",
    inject_click_handlers: bool = False,
    relations: Optional[List[Dict]] = None,
) -> List[Dict]:
    app_name, pages = _parse_pages(interface_data, classifiers, interface_name, layout_config, relations)

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(UNIFIED_TEMPLATE)

    output_files = []
    for page in pages:
        rendered = template.render(
            application_name=app_name,
            page=page,
            AttributeType=AttributeType,
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
    app_name, pages = _parse_pages(interface_data, classifiers, interface_name, relations=relations)
    tokens = interface_data.get("tokens", {})

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(UNIFIED_TEMPLATE)

    output_files = []
    for page in pages:
        rendered = template.render(
            page=page,
            AttributeType=AttributeType,
            preview_mode=True,
            tokens=tokens,
        )
        output_files.append({
            "path": f"preview/{app_name}_{page.name}.html",
            "content": rendered,
            "type": "html",
        })

    return output_files
