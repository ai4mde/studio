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
PREVIEW_TEMPLATE = "page_preview.html.jinja2"

DEFAULT_SECTION_STYLE = {
    "color": "blue",
    "density": "normal",
    "radius": "xl",
    "columns": "3",
    "card_style": "elevated",
}

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
                 layout="table", style=None):
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

    def __str__(self):
        return self.name


class _Page:
    def __init__(self, name, display_name, type_, activity_name, category, section_components):
        self.name = name
        self.display_name = display_name
        self.type = type_
        self.activity_name = activity_name
        self.category = category
        self.section_components = section_components

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


def render_layout(
    interface_data: Dict,
    classifiers: List[Dict],
    layout_config: Optional[Dict],
    interface_name: str = "interface",
    inject_click_handlers: bool = False,
) -> List[Dict]:
    """
    Render layout templates from interface.data using per-section layout/style.
    Returns a list of {path, content, type} dicts.
    """
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

            cls_data = classifier_map.get(str(s_raw.get("class", "")), {})
            primary_model = _sanitize(cls_data.get("name", "item")) if cls_data else "item"

            attributes = []
            for attr_raw in s_raw.get("attributes", []):
                type_str = attr_raw.get("type", "str")
                if type_str == "int":
                    attr_type = AttributeType.INTEGER
                elif type_str == "bool":
                    attr_type = AttributeType.BOOLEAN
                elif type_str == "enum":
                    attr_type = AttributeType.ENUM
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

            # Per-section layout/style — override with layout_config if provided (legacy global mode)
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
                parent_models=[],
                attributes=attributes,
                has_create_operation=bool(ops.get("create", False)),
                has_update_operation=bool(ops.get("update", False)),
                has_delete_operation=bool(ops.get("delete", False)),
                text=_parse_text(s_raw.get("text", "")),
                layout=sec_layout,
                style=sec_style,
            ))

        type_field = p_raw.get("type")
        page_type = type_field.get("value", "normal") if isinstance(type_field, dict) else (str(type_field) if type_field else "normal")

        action_field = p_raw.get("action")
        activity_name = action_field.get("label") if isinstance(action_field, dict) else None

        pages.append(_Page(
            name=_sanitize(p_raw.get("name", "")),
            display_name=p_raw.get("name", ""),
            type_=page_type,
            activity_name=activity_name,
            category=None,
            section_components=section_components,
        ))

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
) -> List[Dict]:
    """
    Render standalone preview HTML (with mock data) for iframe display in AgentDesign.
    Returns a list of {path, content, type} dicts — one per page.
    Unlike render_layout(), the output is complete HTML (not Django templates).
    """
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

            cls_data = classifier_map.get(str(s_raw.get("class", "")), {})
            primary_model = _sanitize(cls_data.get("name", "item")) if cls_data else "item"

            attributes = []
            for attr_raw in s_raw.get("attributes", []):
                type_str = attr_raw.get("type", "str")
                if type_str == "int":
                    attr_type = AttributeType.INTEGER
                elif type_str == "bool":
                    attr_type = AttributeType.BOOLEAN
                elif type_str == "enum":
                    attr_type = AttributeType.ENUM
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
            sec_style["columns"] = str(sec_style.get("columns", "3"))

            section_components.append(_SectionComponent(
                id=s_raw.get("id", ""),
                name=_sanitize(s_raw.get("name", "")),
                display_name=s_raw.get("name", ""),
                primary_model=primary_model,
                parent_models=[],
                attributes=attributes,
                has_create_operation=bool(ops.get("create", False)),
                has_update_operation=bool(ops.get("update", False)),
                has_delete_operation=bool(ops.get("delete", False)),
                text=_parse_text(s_raw.get("text", "")),
                layout=sec_layout,
                style=sec_style,
            ))

        type_field = p_raw.get("type")
        page_type = type_field.get("value", "normal") if isinstance(type_field, dict) else (str(type_field) if type_field else "normal")
        action_field = p_raw.get("action")
        activity_name = action_field.get("label") if isinstance(action_field, dict) else None

        pages.append(_Page(
            name=_sanitize(p_raw.get("name", "")),
            display_name=p_raw.get("name", ""),
            type_=page_type,
            activity_name=activity_name,
            category=None,
            section_components=section_components,
        ))

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(PREVIEW_TEMPLATE)

    output_files = []
    for page in pages:
        rendered = template.render(
            page=page,
            AttributeType=AttributeType,
        )
        output_files.append({
            "path": f"preview/{app_name}_{page.name}.html",
            "content": rendered,
            "type": "html",
        })

    return output_files
