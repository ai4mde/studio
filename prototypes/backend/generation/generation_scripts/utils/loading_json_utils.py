from typing import List, Dict
from utils.sanitization import app_name_sanitization, model_name_sanitization, category_name_sanitization, attribute_name_sanitization
from utils.definitions.application_component import ApplicationComponent
from utils.definitions.section_component import SectionComponent, SectionAttribute, SectionCustomMethod
from utils.definitions.page import Page
from utils.definitions.category import Category
from utils.definitions.model import AttributeType, Model, Cardinality, define_cardinality
from utils.definitions.styling import Styling, StyleType, LayoutType
from utils.definitions.settings import Settings
import json
import re
from uuid import uuid4


_TAILWIND_HEX = {
    "slate": {50: "#f8fafc", 100: "#f1f5f9", 200: "#e2e8f0", 300: "#cbd5e1", 400: "#94a3b8", 500: "#64748b", 600: "#475569", 700: "#334155", 800: "#1e293b", 900: "#0f172a", 950: "#020617"},
    "gray": {50: "#f9fafb", 100: "#f3f4f6", 200: "#e5e7eb", 300: "#d1d5db", 400: "#9ca3af", 500: "#6b7280", 600: "#4b5563", 700: "#374151", 800: "#1f2937", 900: "#111827", 950: "#030712"},
    "zinc": {50: "#fafafa", 100: "#f4f4f5", 200: "#e4e4e7", 300: "#d4d4d8", 400: "#a1a1aa", 500: "#71717a", 600: "#52525b", 700: "#3f3f46", 800: "#27272a", 900: "#18181b", 950: "#09090b"},
    "neutral": {50: "#fafafa", 100: "#f5f5f5", 200: "#e5e5e5", 300: "#d4d4d4", 400: "#a3a3a3", 500: "#737373", 600: "#525252", 700: "#404040", 800: "#262626", 900: "#171717", 950: "#0a0a0a"},
    "stone": {50: "#fafaf9", 100: "#f5f5f4", 200: "#e7e5e4", 300: "#d6d3d1", 400: "#a8a29e", 500: "#78716c", 600: "#57534e", 700: "#44403c", 800: "#292524", 900: "#1c1917", 950: "#0c0a09"},
    "red": {50: "#fef2f2", 100: "#fee2e2", 200: "#fecaca", 300: "#fca5a5", 400: "#f87171", 500: "#ef4444", 600: "#dc2626", 700: "#b91c1c", 800: "#991b1b", 900: "#7f1d1d", 950: "#450a0a"},
    "orange": {50: "#fff7ed", 100: "#ffedd5", 200: "#fed7aa", 300: "#fdba74", 400: "#fb923c", 500: "#f97316", 600: "#ea580c", 700: "#c2410c", 800: "#9a3412", 900: "#7c2d12", 950: "#431407"},
    "amber": {50: "#fffbeb", 100: "#fef3c7", 200: "#fde68a", 300: "#fcd34d", 400: "#fbbf24", 500: "#f59e0b", 600: "#d97706", 700: "#b45309", 800: "#92400e", 900: "#78350f", 950: "#451a03"},
    "yellow": {50: "#fefce8", 100: "#fef9c3", 200: "#fef08a", 300: "#fde047", 400: "#facc15", 500: "#eab308", 600: "#ca8a04", 700: "#a16207", 800: "#854d0e", 900: "#713f12", 950: "#422006"},
    "lime": {50: "#f7fee7", 100: "#ecfccb", 200: "#d9f99d", 300: "#bef264", 400: "#a3e635", 500: "#84cc16", 600: "#65a30d", 700: "#4d7c0f", 800: "#3f6212", 900: "#365314", 950: "#1a2e05"},
    "green": {50: "#f0fdf4", 100: "#dcfce7", 200: "#bbf7d0", 300: "#86efac", 400: "#4ade80", 500: "#22c55e", 600: "#16a34a", 700: "#15803d", 800: "#166534", 900: "#14532d", 950: "#052e16"},
    "emerald": {50: "#ecfdf5", 100: "#d1fae5", 200: "#a7f3d0", 300: "#6ee7b7", 400: "#34d399", 500: "#10b981", 600: "#059669", 700: "#047857", 800: "#065f46", 900: "#064e3b", 950: "#022c22"},
    "teal": {50: "#f0fdfa", 100: "#ccfbf1", 200: "#99f6e4", 300: "#5eead4", 400: "#2dd4bf", 500: "#14b8a6", 600: "#0d9488", 700: "#0f766e", 800: "#115e59", 900: "#134e4a", 950: "#042f2e"},
    "cyan": {50: "#ecfeff", 100: "#cffafe", 200: "#a5f3fc", 300: "#67e8f9", 400: "#22d3ee", 500: "#06b6d4", 600: "#0891b2", 700: "#0e7490", 800: "#155e75", 900: "#164e63", 950: "#083344"},
    "sky": {50: "#f0f9ff", 100: "#e0f2fe", 200: "#bae6fd", 300: "#7dd3fc", 400: "#38bdf8", 500: "#0ea5e9", 600: "#0284c7", 700: "#0369a1", 800: "#075985", 900: "#0c4a6e", 950: "#082f49"},
    "blue": {50: "#eff6ff", 100: "#dbeafe", 200: "#bfdbfe", 300: "#93c5fd", 400: "#60a5fa", 500: "#3b82f6", 600: "#2563eb", 700: "#1d4ed8", 800: "#1e40af", 900: "#1e3a8a", 950: "#172554"},
    "indigo": {50: "#eef2ff", 100: "#e0e7ff", 200: "#c7d2fe", 300: "#a5b4fc", 400: "#818cf8", 500: "#6366f1", 600: "#4f46e5", 700: "#4338ca", 800: "#3730a3", 900: "#312e81", 950: "#1e1b4b"},
    "violet": {50: "#f5f3ff", 100: "#ede9fe", 200: "#ddd6fe", 300: "#c4b5fd", 400: "#a78bfa", 500: "#8b5cf6", 600: "#7c3aed", 700: "#6d28d9", 800: "#5b21b6", 900: "#4c1d95", 950: "#2e1065"},
    "purple": {50: "#faf5ff", 100: "#f3e8ff", 200: "#e9d5ff", 300: "#d8b4fe", 400: "#c084fc", 500: "#a855f7", 600: "#9333ea", 700: "#7e22ce", 800: "#6b21a8", 900: "#581c87", 950: "#3b0764"},
    "fuchsia": {50: "#fdf4ff", 100: "#fae8ff", 200: "#f5d0fe", 300: "#f0abfc", 400: "#e879f9", 500: "#d946ef", 600: "#c026d3", 700: "#a21caf", 800: "#86198f", 900: "#701a75", 950: "#4a044e"},
    "pink": {50: "#fdf2f8", 100: "#fce7f3", 200: "#fbcfe8", 300: "#f9a8d4", 400: "#f472b6", 500: "#ec4899", 600: "#db2777", 700: "#be185d", 800: "#9d174d", 900: "#831843", 950: "#500724"},
    "rose": {50: "#fff1f2", 100: "#ffe4e6", 200: "#fecdd3", 300: "#fda4af", 400: "#fb7185", 500: "#f43f5e", 600: "#e11d48", 700: "#be123c", 800: "#9f1239", 900: "#881337", 950: "#4c0519"},
}

_ROUNDING_TO_RADIUS = {
    "rounded-none": 0,
    "rounded-sm": 2,
    "rounded": 4,
    "rounded-md": 6,
    "rounded-lg": 8,
    "rounded-xl": 12,
    "rounded-2xl": 16,
    "rounded-3xl": 24,
    "rounded-full": 999,
}

_SHADOW_MAP = {
    "shadow-sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
    "shadow": "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)",
    "shadow-md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)",
    "shadow-lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)",
    "shadow-xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)",
    "shadow-2xl": "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
    "shadow-none": "none",
}

_FONT_MAP = {
    "font-sans": "Arial, sans-serif",
    "font-serif": "Georgia, serif",
    "font-mono": "'Courier New', Courier, monospace",
}


_TAILWIND_SPECIAL = {
    "white": "#ffffff",
    "black": "#000000",
    "transparent": "transparent",
    "inherit": "inherit",
    "current": "currentColor",
}

def _tailwind_token_to_hex(token: str) -> str | None:
    # Try arbitrary value: bg-[#hex], text-[#hex], etc.
    arb = re.search(r"(?:bg|text|border|ring|from|to|via)-\[(#[0-9a-fA-F]{3,8})\]", token)
    if arb:
        return arb.group(1)
    # Special single-word colours: text-white, bg-black, etc.
    special = re.search(r"(?:bg|text|border|ring|from|to|via)-(white|black|transparent|inherit|current)\b", token)
    if special:
        return _TAILWIND_SPECIAL.get(special.group(1))
    # Standard Tailwind palette
    match = re.search(r"(?:bg|text|border|ring|from|to|via)-([a-z]+)-(50|100|200|300|400|500|600|700|800|900|950)\b", token)
    if not match:
        return None
    return _TAILWIND_HEX.get(match.group(1), {}).get(int(match.group(2)))


def _extract_first_hex(raw: str, prefixes: tuple[str, ...]) -> str | None:
    if not raw:
        return None
    for cls in raw.split():
        if cls.startswith(prefixes):
            value = _tailwind_token_to_hex(cls)
            if value:
                return value
    return None


def _extract_radius(raw: str) -> int | None:
    if not raw:
        return None
    for cls in raw.split():
        if cls in _ROUNDING_TO_RADIUS:
            return _ROUNDING_TO_RADIUS[cls]
    return None


def _extract_shadow(raw: str) -> str | None:
    if not raw:
        return None
    for cls in raw.split():
        if cls in _SHADOW_MAP:
            return _SHADOW_MAP[cls]
    return None


def _extract_font_family(raw: str) -> str | None:
    if not raw:
        return None
    for cls in raw.split():
        if cls in _FONT_MAP:
            return _FONT_MAP[cls]
    return None


def _interface_label(component: dict) -> str:
    value = component.get("value")
    if isinstance(value, dict) and value.get("name"):
        return value["name"]
    return component.get("label") or component.get("name") or ""


def _interface_data(component: dict) -> dict:
    value = component.get("value")
    if isinstance(value, dict):
        data = value.get("data")
        if isinstance(data, dict):
            return data
    data = component.get("data")
    return data if isinstance(data, dict) else {}


def _classifier_lookup(metadata_json: dict) -> dict[str, dict]:
    return {
        classifier.get("id", ""): classifier.get("data", {})
        for classifier in metadata_json.get("classifiers", [])
        if isinstance(classifier, dict)
    }


def _relation_lookup(metadata_json: dict) -> dict[str, dict]:
    return {
        relation.get("id", ""): relation.get("data", {})
        for relation in metadata_json.get("relations", [])
        if isinstance(relation, dict)
    }


def _relation_record_lookup(metadata_json: dict) -> dict[str, dict]:
    return {
        relation.get("id", ""): relation
        for relation in metadata_json.get("relations", [])
        if isinstance(relation, dict)
    }


def _node_classifier_data(node: dict, classifiers_by_id: dict[str, dict]) -> dict:
    cls = node.get("cls")
    if isinstance(cls, dict):
        return cls
    if isinstance(cls, str):
        return classifiers_by_id.get(cls, {})
    cls_ptr = node.get("cls_ptr")
    if isinstance(cls_ptr, str):
        return classifiers_by_id.get(cls_ptr, {})
    return {}


def _node_classifier_ref(node: dict) -> str | None:
    cls = node.get("cls")
    if isinstance(cls, str):
        return cls
    cls_ptr = node.get("cls_ptr")
    if isinstance(cls_ptr, str):
        return cls_ptr
    return None


def _edge_relation_data(edge: dict, relations_by_id: dict[str, dict]) -> dict:
    rel = edge.get("rel")
    if isinstance(rel, dict):
        return rel
    if isinstance(rel, str):
        return relations_by_id.get(rel, {})
    rel_ptr = edge.get("rel_ptr")
    if isinstance(rel_ptr, str):
        return relations_by_id.get(rel_ptr, {})
    return {}


def _edge_source_ref(edge: dict, relation_records_by_id: dict[str, dict]) -> str | None:
    source_ptr = edge.get("source_ptr")
    if isinstance(source_ptr, str):
        return source_ptr
    rel = edge.get("rel")
    if isinstance(rel, str):
        relation = relation_records_by_id.get(rel, {})
        source = relation.get("source")
        if isinstance(source, str):
            return source
    rel_ptr = edge.get("rel_ptr")
    if isinstance(rel_ptr, str):
        relation = relation_records_by_id.get(rel_ptr, {})
        source = relation.get("source")
        if isinstance(source, str):
            return source
    return None


def _edge_target_ref(edge: dict, relation_records_by_id: dict[str, dict]) -> str | None:
    target_ptr = edge.get("target_ptr")
    if isinstance(target_ptr, str):
        return target_ptr
    rel = edge.get("rel")
    if isinstance(rel, str):
        relation = relation_records_by_id.get(rel, {})
        target = relation.get("target")
        if isinstance(target, str):
            return target
    rel_ptr = edge.get("rel_ptr")
    if isinstance(rel_ptr, str):
        relation = relation_records_by_id.get(rel_ptr, {})
        target = relation.get("target")
        if isinstance(target, str):
            return target
    return None


def get_apps(metadata: str) -> str:
    '''Returns a string with all application component names, and spaces inbetween'''
    apps = []
    
    try:
        if metadata:
            for interface in json.loads(metadata)["interfaces"]:
                label = _interface_label(interface)
                if label:
                    apps.append(app_name_sanitization(label))
    except:
        raise Exception("Failed to retrieve names of interfaces")
    return " ".join(apps)


def authentication_is_present(metadata: str) -> bool:
    '''Returns true if authentication is enabled in the metadata'''

    if metadata in ["", None]:
        raise Exception("Metadata is empty")
    
    metadata_json = json.loads(metadata)
    if "useAuthentication" in metadata_json:
        return metadata_json["useAuthentication"]
    
    return False

def get_enum_literals(metadata: str, class_id: str) -> List[str]:
    out = []
    metadata_json = json.loads(metadata)
    classifiers_by_id = _classifier_lookup(metadata_json)
    for diagram in metadata_json["diagrams"]:
        if diagram["type"] != "classes":
            continue
        for node in diagram["nodes"]:
            node_data = _node_classifier_data(node, classifiers_by_id)
            if _node_classifier_ref(node) == class_id and node_data.get("type") == "enum":
                for literal in node_data.get("literals", []):
                    out.append(str(literal))
                return out
    return []


def find_model_by_class_ptr(metadata: str, class_id: str) -> str | None:
    metadata_json = json.loads(metadata)
    classifiers_by_id = _classifier_lookup(metadata_json)
    for diagram in metadata_json["diagrams"]:
        if diagram["type"] != "classes":
            continue
        for node in diagram["nodes"]:
            if _node_classifier_ref(node) == class_id:
                node_data = _node_classifier_data(node, classifiers_by_id)
                return model_name_sanitization(node_data["name"])
    return None


def find_model_by_id(metadata: str, class_id: str) -> str | None:
    metadata_json = json.loads(metadata)
    classifiers_by_id = _classifier_lookup(metadata_json)
    for diagram in metadata_json["diagrams"]:
        if diagram["type"] != "classes":
            continue
        for node in diagram["nodes"]:
            node_data = _node_classifier_data(node, classifiers_by_id)
            if node["id"] == class_id and node_data.get("type") == "class":
                return model_name_sanitization(node_data["name"])
    return None


def find_model_id_by_class_ptr(metadata: str, class_ptr: str) -> str:
    metadata_json = json.loads(metadata)
    classifiers_by_id = _classifier_lookup(metadata_json)
    for diagram in metadata_json["diagrams"]:
        if diagram["type"] != "classes":
            continue
        for node in diagram["nodes"]:
            if _node_classifier_ref(node) == class_ptr:
                node_data = _node_classifier_data(node, classifiers_by_id)
                if node_data.get("type") == "class":
                    return node["id"]
                return node["id"]
    return None

SOURCE_ACCEPTABLE_CARDINALITIES = [
    Cardinality.ZERO_MANY_TO_ONE,
    Cardinality.ONE_MANY_TO_ONE
    # TODO: maybe more?
]
TARGET_ACCEPTABLE_CARDINALITIES = [
    Cardinality.ONE_TO_ZERO_MANY,
    Cardinality.ONE_TO_ONE_MANY
    # TODO: maybe more?
]


def find_parent_models_by_id(metadata: str, primary_class_class_ptr: str) -> List[str]:
    out = []
    metadata_json = json.loads(metadata)
    relations_by_id = _relation_lookup(metadata_json)
    relation_records_by_id = _relation_record_lookup(metadata_json)
    primary_class_id = find_model_id_by_class_ptr(metadata, primary_class_class_ptr)
    primary_refs = {ref for ref in [primary_class_class_ptr, primary_class_id] if ref}

    for diagram in metadata_json["diagrams"]:
        if diagram["type"] != "classes":
            continue
        if "edges" not in diagram:
            return []
        for edge in diagram["edges"]:
            edge_data = _edge_relation_data(edge, relations_by_id)
            if edge_data.get("type") != "association":
                continue
            source_ref = _edge_source_ref(edge, relation_records_by_id)
            target_ref = _edge_target_ref(edge, relation_records_by_id)
            if source_ref in primary_refs:
                multiplicity = edge_data.get("multiplicity", {})
                cardinality = define_cardinality(multiplicity.get("source"), multiplicity.get("target"), node_is_source=True)
                model_name = find_model_by_class_ptr(metadata, target_ref) or find_model_by_id(metadata, target_ref)
                if model_name and cardinality in SOURCE_ACCEPTABLE_CARDINALITIES:
                    out.append(model_name_sanitization(model_name))
            if target_ref in primary_refs:
                multiplicity = edge_data.get("multiplicity", {})
                cardinality = define_cardinality(multiplicity.get("source"), multiplicity.get("target"), node_is_source=False)
                model_name = find_model_by_class_ptr(metadata, source_ref) or find_model_by_id(metadata, source_ref)
                if model_name and cardinality in TARGET_ACCEPTABLE_CARDINALITIES:
                    out.append(model_name_sanitization(model_name))
    return out


# TODO: redundant
def filter_section_components_by_application(section_components: List[SectionComponent], application: str) -> List[SectionComponent]:
    out = []
    for section_component in section_components:
        if section_component.application == application:
            out.append(section_component)
    return out


# TODO: redundant
def filter_pages_by_application(pages: List[Page], application: str) -> List[Page]:
    out = []
    for page in pages:
        if page.application == application:
            out.append(page)
    return out


def retrieve_section_attributes(metadata: str, section: str) -> List[SectionAttribute]:
    if not section:
        return []
    if "attributes" not in section:
        return []
    
    out = []
    for attribute in section["attributes"]:
        attribute_type = None
        enum_literals = None
        if attribute["type"] == "str":
            attribute_type  = AttributeType.STRING
        elif attribute["type"] == "int":
            attribute_type  = AttributeType.INTEGER
        elif attribute["type"] == "bool":
            attribute_type  = AttributeType.BOOLEAN
        elif attribute["type"] == "enum":
            attribute_type  = AttributeType.ENUM
            enum_literals = get_enum_literals(metadata, attribute["enum"])
        elif attribute["type"] == "date":
            attribute_type  = AttributeType.DATE
        elif attribute["type"] == "datetime":
            attribute_type  = AttributeType.DATETIME
        elif attribute["type"] == "text":
            attribute_type  = AttributeType.TEXT
        elif attribute["type"] == "float":
            attribute_type  = AttributeType.FLOAT
        elif attribute["type"] == "email":
            attribute_type  = AttributeType.EMAIL

        att = SectionAttribute(
            name = attribute_name_sanitization(attribute["name"]),
            type = attribute_type,
            enum_literals = enum_literals,
            updatable = True, # TODO: frontend management of updatable attributes
            derived = attribute["derived"]
        )
        out.append(att)

    return out


def retrieve_section_custom_methods(section: str) -> List[str]:
    if not section:
        return []
    if "methods" not in section:
        return []
    
    out = []
    for custom_method in section["methods"]:
        mtd = SectionCustomMethod(
            name = custom_method["name"],
            body = custom_method["body"]
        )
        out.append(mtd)
    
    return out


def retrieve_section_components(application_name: str, page_name: str, metadata: str) -> List[SectionComponent]:
    '''Function that retrieves the section components corresponding to page_name from
    metadata and returns a list of SectionComponent objects.'''
    if metadata in ["", None]:
        raise Exception("Failed to retrieve section components from metadata: metadata is empty")
    
    out = []
    try:
        for application_component in json.loads(metadata)["interfaces"]:
            component_label = _interface_label(application_component)
            component_data = _interface_data(application_component)
            if app_name_sanitization(component_label) != application_name:
                continue
            
            if "pages" not in component_data: # no pages in interface
                return []

            for page in component_data["pages"]:
                if page["name"] != page_name:
                    continue

                for page_section in page["sections"]:
                    section = None
                    page_section_id = page_section["value"]
                    for application_section in component_data.get("sections", []):
                        if application_section["id"] == page_section_id:
                            section = application_section
                    
                    if not section:
                        continue

                    sec = SectionComponent(
                        id = section["id"],
                        name = section["name"],
                        application = application_name,
                        page = page_name,
                        primary_model = find_model_by_class_ptr(metadata, section["class"]), # TODO: there might be a quicker method than this
                        parent_models = find_parent_models_by_id(metadata, section["class"]), # TODO: quicker method?
                        attributes = retrieve_section_attributes(metadata, section),
                        has_create_operation = section["operations"]["create"],
                        has_delete_operation = section["operations"]["delete"],
                        has_update_operation = section["operations"]["update"],
                        custom_methods = retrieve_section_custom_methods(section),
                        text = section["text"]
                    )
                    out.append(sec)
            return out
    except:
        raise Exception("Failed to retrieve section components from metadata: parsing error")

    return out


def retrieve_categories(application_name: str, metadata: str) -> List[Category]:
    '''Function that retrieves the categories corresponding to application_name from
    metadata and returns a list of Category objects.'''
    
    if metadata in ["", None]:
        raise Exception("Failed to retrieve pages from metadata: metadata is empty")
    
    out = []

    try:
        for application_component in json.loads(metadata)["interfaces"]:
            component_data = _interface_data(application_component)
            if "categories" not in component_data: # empty interface
                continue
            if app_name_sanitization(_interface_label(application_component)) != application_name:
                continue

            for category in component_data["categories"]:
                cat = Category(
                    id = category["id"],
                    name = category["name"],
                )
                out.append(cat)
    except:
        raise Exception("Failed to retrieve pages from metadata: parsing error")

    return out



def retrieve_pages(application_name: str, metadata: str) -> List[Page]:
    '''Function that retrieves the pages corresponding to application_name from
    metadata and returns a list of Page objects.'''
    
    if metadata in ["", None]:
        raise Exception("Failed to retrieve pages from metadata: metadata is empty")
    
    out = []

    try:
        for application_component in json.loads(metadata)["interfaces"]:
            component_data = _interface_data(application_component)
            if "pages" not in component_data: # empty interface
                continue
            sanitized_application_label = app_name_sanitization(_interface_label(application_component))
            if sanitized_application_label != application_name:
                continue

            component_schema_pages = {
                p.get("page_id", ""): p
                for p in ((component_data.get("componentSchema") or {}).get("pages") or [])
                if isinstance(p, dict)
            }

            for page in component_data["pages"]:
                category = None
                if page["category"] != None:
                    category = page["category"]["value"]["name"]
                component_schema_page = component_schema_pages.get(page.get("id", ""), {})
                pg = Page(
                    id = page["id"],
                    name = page["name"],
                    application = sanitized_application_label,
                    category = category,
                    activity_name = page['action']['label'] if page.get('action') else None,
                    type = page["type"]['value'] if page.get('type') else 'normal',
                    section_components = retrieve_section_components(application_name=application_name, page_name=page["name"], metadata=metadata),
                    render_ast = page.get("renderAst") or page.get("ast") or component_schema_page.get("renderAst") or component_schema_page.get("ast") or [],
                    semantic_ast = page.get("semanticAst") or component_schema_page.get("semanticAst") or {},
                )
                out.append(pg)
    except:
        raise Exception("Failed to retrieve pages from metadata: parsing error")

    return out


def retrieve_models_on_pages(application_component: ApplicationComponent) -> dict[Page, Dict[str, List[Model]]]:
    '''Function that returns all primary models & foreign/parent models on pages inside
    application_component'''
    out: dict[Page, Dict[str, List[Model]]] = {}

    for page in application_component.pages:
        if page not in out:
            out[page] = {'primary_models': [], 'parent_models': []}
        for section_component in page.section_components:
            out[page]['primary_models'].append(section_component.primary_model)
            for parent_model in section_component.parent_models:
                out[page]['parent_models'].append(parent_model)
    return out


def retrieve_styling(application_name: str, metadata: str)  -> Styling:
    if metadata in ["", None]:
        raise Exception("Failed to retrieve styling from metadata: metadata is empty")
    
    style_type = None
    layout_type = None
    radius = None
    background_color = None
    accent_color = None
    text_color = None
    
    try:
        for application_component in json.loads(metadata)["interfaces"]:
            component_data = _interface_data(application_component)
            if app_name_sanitization(_interface_label(application_component)) != application_name:
                continue
            if "styling" not in component_data: # empty interface
                return Styling() # return default object
            
            styling = component_data["styling"]

            style_map = {
                "basic": StyleType.BASIC,
                "modern": StyleType.MODERN,
                "abstract": StyleType.ABSTRACT,
                "elegant": StyleType.ELEGANT,
                "brutalist": StyleType.BRUTALIST,
                "glassmorphism": StyleType.GLASSMORPHISM,
                "dark": StyleType.DARK,
            }
            style_type = style_map.get(styling.get("selectedStyle", ""), StyleType.BASIC)

            layout_map = {
                "sidebar_left": LayoutType.SIDEBAR_LEFT,
                "sidebar_right": LayoutType.SIDEBAR_RIGHT,
                "top_nav": LayoutType.TOP_NAV,
                "top_nav_sidebar": LayoutType.TOP_NAV_SIDEBAR,
            }
            layout_type = layout_map.get(styling.get("selectedLayout", ""), LayoutType.SIDEBAR_LEFT)

            if "radius" not in styling:
                radius = 10
            else:
                radius = styling["radius"]
            if "backgroundColor" not in styling:
                background_color = "#FFFFFF"
            else:
                background_color = styling["backgroundColor"]
            if "accentColor" not in styling:
                accent_color = "#777777"
            else:
                accent_color = styling["accentColor"]
            if "textColor" not in styling:
                text_color = "#000000"
            else:
                text_color = styling["textColor"]

            return Styling(
                style_type = style_type,
                layout_type = layout_type,
                radius = radius,
                text_color = text_color,
                accent_color = accent_color,
                background_color = background_color
            )
    except:
        return Styling()


def retrieve_theme(application_name: str, metadata: str) -> dict:
    if metadata in ["", None]:
        raise Exception("Failed to retrieve theme from metadata: metadata is empty")

    try:
        for application_component in json.loads(metadata)["interfaces"]:
            if app_name_sanitization(_interface_label(application_component)) != application_name:
                continue
            data = _interface_data(application_component)
            theme = data.get("theme")
            return theme if isinstance(theme, dict) else {}
    except:
        return {}

    return {}


def retrieve_theme_summary(application_name: str, metadata: str) -> dict:
    theme = retrieve_theme(application_name, metadata)
    tokens = theme.get("tokens") or {}

    page_body = tokens.get("page.body", "")
    page_surface = tokens.get("page.surface", "")
    button_primary = tokens.get("component.button.primary") or tokens.get("element.button.primary") or ""
    input_default = tokens.get("component.input.default") or tokens.get("element.input.default") or ""
    radius = _extract_radius(button_primary) or _extract_radius(input_default) or _extract_radius(page_surface)

    return {
        "font_family": _extract_font_family(page_body),
        "background_color": _extract_first_hex(page_body, ("bg-", "from-", "via-", "to-")),
        "text_color": _extract_first_hex(page_body, ("text-",)),
        "surface_color": _extract_first_hex(page_surface, ("bg-",)),
        "surface_text_color": _extract_first_hex(page_surface, ("text-",)),
        "border_color": _extract_first_hex(page_surface, ("border-",)),
        "surface_shadow": _extract_shadow(page_surface),
        "accent_color": _extract_first_hex(button_primary, ("bg-", "border-", "ring-", "from-", "to-", "via-")),
        "button_text_color": _extract_first_hex(button_primary, ("text-",)),
        "button_radius": _extract_radius(button_primary),
        "input_background_color": _extract_first_hex(input_default, ("bg-",)),
        "input_text_color": _extract_first_hex(input_default, ("text-",)),
        "input_border_color": _extract_first_hex(input_default, ("border-", "ring-")),
        "input_radius": _extract_radius(input_default),
        "radius": radius,
    }


def retrieve_global_layout(application_name: str, metadata: str) -> dict:
    """Retrieve the LLM-generated global layout elements (navbar/sidebar HTML) from metadata."""
    if metadata in ["", None]:
        return {}

    try:
        for application_component in json.loads(metadata)["interfaces"]:
            if app_name_sanitization(_interface_label(application_component)) != application_name:
                continue
            data = _interface_data(application_component)
            layout = data.get("layout") or {}
            selected = layout.get("selected")
            return selected if isinstance(selected, dict) else {}
    except:
        return {}

    return {}


def retrieve_settings(application_name: str, metadata: str) -> Settings:
    if metadata in ["", None]:
        raise Exception("Failed to retrieve styling from metadata: metadata is empty")
    
    manager_access = False
    try:
        for application_component in json.loads(metadata)["interfaces"]:
            component_data = _interface_data(application_component)
            if app_name_sanitization(_interface_label(application_component)) != application_name:
                continue
            if "settings" not in component_data:
                return Settings(manager_access=manager_access)
            settings = component_data["settings"]
            return Settings(
                manager_access=settings['managerAccess']
                if 'managerAccess' in settings else False
            )
    except:
        return Settings(manager_access=manager_access)
    

def retrieve_manager_roles(metadata: str) -> List[str]:
    if metadata in ["", None]:
        raise Exception("Failed to retrieve manager roles from metadata: metadata is empty")
    manager_roles = []
    for application_component in json.loads(metadata)["interfaces"]:
        component_data = _interface_data(application_component)
        if "settings" not in component_data:
            continue
        settings = component_data["settings"]
        if "managerAccess" not in settings or not settings["managerAccess"]:
            continue
        manager_roles.append(app_name_sanitization(_interface_label(application_component)))
    return manager_roles


def get_application_component(project_name: str, application_name: str, metadata: str, authentication_present: bool) -> ApplicationComponent:
    '''Function that builds an ApplicationComponent object for application_name
    from metadata.'''
    pages = retrieve_pages(application_name=application_name, metadata=metadata)
    categories = retrieve_categories(application_name=application_name, metadata=metadata)
    settings = retrieve_settings(application_name=application_name, metadata=metadata)
    styling = retrieve_styling(application_name=application_name, metadata=metadata)
    theme = retrieve_theme(application_name=application_name, metadata=metadata)
    theme_summary = retrieve_theme_summary(application_name=application_name, metadata=metadata)
    global_layout = retrieve_global_layout(application_name=application_name, metadata=metadata)

    return ApplicationComponent(
        id = uuid4(), # TODO: retrieve frontend id from metadata
        project = project_name,
        name = application_name,
        categories = categories,
        pages = pages,
        styling = styling,
        theme = theme,
        theme_summary = theme_summary,
        settings = settings,
        authentication_present = authentication_present,
        global_layout = global_layout,
    )