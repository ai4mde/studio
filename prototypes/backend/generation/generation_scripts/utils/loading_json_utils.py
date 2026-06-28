from typing import List, Dict
from utils.sanitization import app_name_sanitization, model_name_sanitization, category_name_sanitization, attribute_name_sanitization, page_name_sanitization
from utils.definitions.application_component import ApplicationComponent
from utils.definitions.section_component import SectionComponent, SectionAttribute, SectionCustomMethod
from utils.definitions.page import Page
from utils.definitions.category import Category
from utils.definitions.model import AttributeType, Model, Cardinality, define_cardinality
from utils.definitions.styling import Styling, StyleType
from utils.definitions.settings import Settings
import json
import os
from pathlib import Path
import re
import tempfile
from uuid import uuid4


def normalize_section_operations(operations) -> dict:
    select_terms = {"select", "choose", "pick", "bulk_select", "multi_select", "batch_select"}
    false_terms = {"", "0", "false", "no", "none", "null", "off"}

    def enabled(value) -> bool:
        if isinstance(value, str):
            return value.strip().lower() not in false_terms
        return bool(value)

    if isinstance(operations, dict):
        return {
            "create": any(enabled(operations.get(term, False)) for term in ("create", "add")),
            "update": any(enabled(operations.get(term, False)) for term in ("update", "edit")),
            "delete": any(enabled(operations.get(term, False)) for term in ("delete", "remove")),
            "select": any(enabled(operations.get(term, False)) for term in select_terms),
        }
    if isinstance(operations, str):
        operations = re.split(r"[\s,;|]+", operations)
    if isinstance(operations, list):
        values = {str(value).strip().lower() for value in operations}
        return {
            "create": bool({"create", "add"} & values),
            "update": bool({"update", "edit"} & values),
            "delete": bool({"delete", "remove"} & values),
            "select": bool(select_terms & values),
        }
    return {"create": False, "update": False, "delete": False, "select": False}


def _safe_metadata_path(path: str) -> Path:
    metadata_path = Path(path).resolve()
    allowed_roots = {
        Path(os.environ.get("PROTOTYPE_TEMP_DIR", "/usr/src/prototypes/tmp")).resolve(),
        Path(tempfile.gettempdir()).resolve(),
        Path.cwd().resolve(),
    }
    if not metadata_path.is_file():
        raise ValueError("Metadata file does not exist")
    if not any(metadata_path == root or root in metadata_path.parents for root in allowed_roots):
        raise ValueError("Metadata file path is outside allowed directories")
    return metadata_path


def resolve_metadata_arg(metadata: str) -> str:
    if isinstance(metadata, str) and metadata.startswith("@"):
        with _safe_metadata_path(metadata[1:]).open("r", encoding="utf-8") as f:
            return f.read()
    return metadata


def get_apps(metadata: str) -> str:
    '''Returns a string with all application component names, and spaces inbetween'''
    metadata = resolve_metadata_arg(metadata)
    apps = []
    
    try:
        if metadata:
            for interface in json.loads(metadata)["interfaces"]:
                apps.append(app_name_sanitization(interface["value"]["name"]))
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
    for diagram in json.loads(metadata)["diagrams"]:
        if diagram["type"] != "classes":
            continue
        for node in diagram["nodes"]:
            cls = node.get("cls", {})
            cls_data = cls.get("data", cls) if isinstance(cls, dict) else {}
            if node["cls_ptr"] == class_id and cls_data.get("type") == "enum":
                for literal in cls_data.get("literals", []):
                    out.append(str(literal))
                return out
    return []


def find_model_by_class_ptr(metadata: str, class_id: str) -> str | None:
    metadata_json = json.loads(metadata)
    for diagram in metadata_json["diagrams"]:
        if diagram["type"] != "classes":
            continue
        for node in diagram["nodes"]:
            node_cls_ptr = node.get("cls_ptr") or node.get("id")
            if str(node_cls_ptr) == str(class_id):
                cls = node.get("cls", {})
                cls_data = cls.get("data", cls) if isinstance(cls, dict) else {}
                name = cls_data.get("name")
                return model_name_sanitization(name) if name else None
    # Fallback: resolve from flat classifiers list added during generation
    for classifier in metadata_json.get("classifiers", []):
        if str(classifier["id"]) == str(class_id):
            name = classifier.get("data", {}).get("name")
            if name:
                return model_name_sanitization(name)
    return None


def find_class_ptr_by_model_name(metadata: str, model_name: str) -> str | None:
    """Resolve an Interface Metadata primary_model name to the underlying classifier id."""
    if not model_name:
        return None
    target = model_name_sanitization(str(model_name))
    metadata_json = json.loads(metadata)
    for diagram in metadata_json.get("diagrams", []):
        if diagram.get("type") != "classes":
            continue
        for node in diagram.get("nodes", []):
            cls = node.get("cls", {})
            cls_data = cls.get("data", cls) if isinstance(cls, dict) else {}
            if cls_data.get("type") == "class" and model_name_sanitization(cls_data.get("name", "")) == target:
                return str(node.get("cls_ptr") or node.get("id") or "")
    for classifier in metadata_json.get("classifiers", []):
        data = classifier.get("data", {})
        if data.get("type") == "class" and model_name_sanitization(data.get("name", "")) == target:
            return str(classifier.get("id") or "")
    return None


def find_model_by_id(metadata: str, class_id: str) -> str | None:
    for diagram in json.loads(metadata)["diagrams"]:
        if diagram["type"] != "classes":
            continue
        for node in diagram["nodes"]:
            cls = node.get("cls", {})
            cls_data = cls.get("data", cls) if isinstance(cls, dict) else {}
            if node["id"] == class_id and cls_data.get("type") == "class":
                return model_name_sanitization(cls_data.get("name", ""))
    return None


def find_model_id_by_class_ptr(metadata: str, class_ptr: str) -> str:
    for diagram in json.loads(metadata)["diagrams"]:
        if diagram["type"] != "classes":
            continue
        for node in diagram["nodes"]:
            node_cls_ptr = node.get("cls_ptr") or node.get("id")
            if str(node_cls_ptr) == str(class_ptr):
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
    primary_class_id = find_model_id_by_class_ptr(metadata, primary_class_class_ptr)

    for diagram in json.loads(metadata)["diagrams"]:
        if diagram["type"] != "classes":
            continue
        if "edges" not in diagram:
            return []
        for edge in diagram["edges"]:
            rel = edge.get("rel", {})
            if not isinstance(rel, dict):
                continue
            rel_data = rel.get("data", rel)
            if rel_data.get("type") != "association":
                continue
            if edge["source_ptr"] == primary_class_id:
                multiplicity = rel_data.get("multiplicity", {})
                cardinality = define_cardinality(multiplicity.get("source", ""), multiplicity.get("target", ""), node_is_source=True)
                model_name = find_model_by_id(metadata, edge["target_ptr"])
                if model_name and cardinality in SOURCE_ACCEPTABLE_CARDINALITIES:
                    out.append(model_name_sanitization(model_name))
            if edge["target_ptr"] == primary_class_id:
                multiplicity = rel_data.get("multiplicity", {})
                cardinality = define_cardinality(multiplicity.get("source", ""), multiplicity.get("target", ""), node_is_source=False)
                model_name = find_model_by_id(metadata, edge["source_ptr"])
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


def resolve_page_reference(metadata: str, application_name: str, page_ref: str) -> str | None:
    if not page_ref:
        return None
    ref = str(page_ref)
    ref_sanitized = page_name_sanitization(ref)
    try:
        for application_component in json.loads(metadata)["interfaces"]:
            if app_name_sanitization(application_component["label"]) != application_name:
                continue
            for page in application_component.get("value", {}).get("data", {}).get("pages", []):
                page_name = page.get("name", "")
                page_sanitized = page_name_sanitization(page_name)
                if ref in (str(page.get("id")), page_name, page_sanitized) or ref_sanitized == page_sanitized:
                    return page_sanitized
    except Exception:
        return None
    return None


def normalize_field_action(metadata: str, application_name: str, action: dict) -> dict:
    action = dict(action or {"type": "none"})
    if action.get("type") == "navigate":
        page_ref = action.get("targetPage") or action.get("targetPageId") or action.get("page")
        resolved_page = resolve_page_reference(metadata, application_name, page_ref)
        if resolved_page:
            action["targetPage"] = resolved_page
            action.pop("targetPageId", None)
        elif page_ref:
            action["type"] = "none"
            action["invalidTargetPage"] = page_ref
    return action


def infer_attribute_type_from_name(attr_name: str) -> AttributeType | None:
    low = str(attr_name or "").lower()
    if any(token in low for token in ("image", "img", "photo", "avatar", "thumbnail", "thumb", "poster", "cover", "logo")):
        return AttributeType.IMAGE
    if any(token in low for token in ("video", "trailer", "media_url")):
        return AttributeType.VIDEO
    return None


def retrieve_section_attributes(metadata: str, section: str, application_name: str = "") -> List[SectionAttribute]:
    if not section:
        return []
    if "attributes" not in section:
        return []
    
    out = []
    for attribute in section["attributes"]:
        attribute_type = AttributeType.STRING
        enum_literals = None
        derived = False
        is_link = False
        render_as = "text"
        action = {"type": "none"}
        readonly = False
        source = "primary"
        
        if isinstance(attribute, str):
            attr_name = attribute
            if "." in attr_name:
                source = "related"
                readonly = True
            inferred_attribute_type = infer_attribute_type_from_name(attr_name)
            if inferred_attribute_type:
                attribute_type = inferred_attribute_type
        else:
            attr_name = attribute["name"]
            derived = attribute.get("derived", False)
            source = attribute.get("source") or ("related" if "." in attr_name else "primary")
            readonly = bool(attribute.get("readonly", False)) or source == "related"
            is_link = attribute.get("is_link", False)
            render_config = attribute.get("render") or {}
            render_as = render_config.get("as") or attribute.get("render_as") or ("link" if is_link else "text")
            is_link = is_link or render_as == "link"
            action = normalize_field_action(
                metadata,
                application_name,
                attribute.get("action") or ({"type": "navigate"} if is_link else {"type": "none"})
            )
            if attribute.get("type") == "str":
                attribute_type  = AttributeType.STRING
            elif attribute.get("type") == "int":
                attribute_type  = AttributeType.INTEGER
            elif attribute.get("type") == "bool":
                attribute_type  = AttributeType.BOOLEAN
            elif attribute.get("type") == "enum":
                attribute_type  = AttributeType.ENUM
                enum_literals = get_enum_literals(metadata, attribute.get("enum"))
            elif attribute.get("type") == "image":
                attribute_type  = AttributeType.IMAGE
            elif attribute.get("type") == "video":
                attribute_type  = AttributeType.VIDEO
            else:
                inferred_attribute_type = infer_attribute_type_from_name(attr_name)
                if inferred_attribute_type:
                    attribute_type = inferred_attribute_type

        att = SectionAttribute(
            name = attribute_name_sanitization(attr_name),
            type = attribute_type,
            enum_literals = enum_literals,
            updatable = not readonly,
            derived = derived,
            is_link = is_link,
            render_as = render_as,
            action = action,
            readonly = readonly,
            source = source
        )
        out.append(att)

    return out


def retrieve_section_custom_methods(section: str, field: str = "methods") -> List[str]:
    if not section:
        return []
    if field not in section:
        return []
    
    out = []
    for custom_method in section[field]:
        if isinstance(custom_method, str):
            custom_method = {"name": custom_method, "label": custom_method.replace("_", " ")}
        if not isinstance(custom_method, dict):
            continue
        mtd = SectionCustomMethod(
            name = custom_method["name"],
            body = custom_method.get("body"),
            parameters = custom_method.get("parameters", []),
            action = custom_method.get("action"),
            target_model = custom_method.get("target_model"),
            target_page = custom_method.get("target_page") or custom_method.get("targetPage"),
            call_name = custom_method.get("call_name"),
            label = custom_method.get("label"),
        )
        out.append(mtd)
    
    return out


def make_activity_action_section(application_name: str, page_name: str, label: str, section: dict | None = None) -> SectionComponent:
    section = section or {}
    raw_style = section.get("style") or {}
    raw_workflow = section.get("workflow") or {}
    variant = raw_style.get("variant", "button")
    if variant not in ("button", "link", "fab", "wizard_next", "auto"):
        variant = "button"
    workflow_action = raw_workflow.get("action") or section.get("workflow_action") or "complete"
    target_page = (
        raw_workflow.get("target_page")
        or raw_workflow.get("targetPage")
        or section.get("target_page")
        or section.get("targetPage")
    )

    return SectionComponent(
        id=section.get("id", str(uuid4())),
        name=section.get("name", "activity_action"),
        application=application_name,
        page=page_name,
        primary_model=None,
        parent_models=[],
        attributes=[],
        text="",
        has_create_operation=False,
        has_delete_operation=False,
        has_update_operation=False,
        custom_methods=[],
        layout="activity_action",
        style={
            "variant": variant,
            "size": raw_style.get("size", "lg"),
            "align": raw_style.get("align", "right"),
        },
        col_span=int(section.get("col_span", 12)),
        position=section.get("position", "main"),
        component_type="activity_action",
        label=label or section.get("label") or "Complete",
        workflow={
            "action": workflow_action,
            **({"target_page": page_name_sanitization(target_page)} if target_page else {}),
        },
    )


def sanitize_page_targets(pages: List[Page]) -> None:
    valid_page_names = {page.name for page in pages}

    for page in pages:
        for section_component in page.section_components:
            if section_component.item_click_target_page and section_component.item_click_target_page not in valid_page_names:
                section_component.item_click_target_page = None
                if isinstance(section_component.behavior, dict):
                    item_click = section_component.behavior.get("item_click")
                    if isinstance(item_click, dict):
                        item_click["type"] = "none"
                        item_click.pop("target_page", None)
                        item_click.pop("targetPage", None)

            if section_component.workflow_target_page and section_component.workflow_target_page not in valid_page_names:
                section_component.workflow_target_page = None
                if isinstance(section_component.workflow, dict):
                    section_component.workflow.pop("target_page", None)
                    section_component.workflow.pop("targetPage", None)


def make_activity_start_section(application_name: str, page_name: str, section: dict | None = None) -> SectionComponent:
    section = section or {}
    raw_style = section.get("style") or {}
    return SectionComponent(
        id=section.get("id", str(uuid4())),
        name=section.get("name") or section.get("label") or "activity_start",
        application=application_name,
        page=page_name,
        primary_model=None,
        parent_models=[],
        attributes=[],
        text="",
        has_create_operation=False,
        has_delete_operation=False,
        has_update_operation=False,
        custom_methods=[],
        layout="activity_start",
        style={
            "card_style": raw_style.get("card_style", "elevated"),
            "columns": str(raw_style.get("columns", "3")),
            "align": raw_style.get("align", "left"),
            "cta_label": raw_style.get("cta_label", "Start"),
        },
        col_span=int(section.get("col_span", 12)),
        position=section.get("position", "main"),
        component_type="activity_start",
        label=section.get("label") or section.get("name") or "Start a Process",
    )


def make_activity_tasks_section(application_name: str, page_name: str, section: dict | None = None) -> SectionComponent:
    section = section or {}
    raw_style = section.get("style") or {}
    return SectionComponent(
        id=section.get("id", str(uuid4())),
        name=section.get("name") or section.get("label") or "activity_tasks",
        application=application_name,
        page=page_name,
        primary_model=None,
        parent_models=[],
        attributes=[],
        text="",
        has_create_operation=False,
        has_delete_operation=False,
        has_update_operation=False,
        custom_methods=[],
        layout="activity_tasks",
        style={
            "card_style": raw_style.get("card_style", "elevated"),
            "columns": str(raw_style.get("columns", "3")),
        },
        col_span=int(section.get("col_span", 12)),
        position=section.get("position", "main"),
        component_type="activity_tasks",
        label=section.get("label") or section.get("name") or "My Tasks",
    )


def retrieve_section_components(application_name: str, page_name: str, metadata: str) -> List[SectionComponent]:
    '''Function that retrieves the section components corresponding to page_name from
    metadata and returns a list of SectionComponent objects.'''
    if metadata in ["", None]:
        raise Exception("Failed to retrieve section components from metadata: metadata is empty")
    
    out = []
    try:
        for application_component in json.loads(metadata)["interfaces"]:
            if app_name_sanitization(application_component["label"]) != application_name:
                continue
            
            if "pages" not in application_component["value"]["data"]: # no pages in interface
                return []

            for page in application_component["value"]["data"]["pages"]:
                if page["name"] != page_name:
                    continue

                page_sections = list(page.get("sections", []))
                page_section_ids = {
                    str(page_section.get("value"))
                    for page_section in page_sections
                    if isinstance(page_section, dict) and page_section.get("value")
                }
                for application_section in application_component["value"]["data"].get("sections", []):
                    section_position = application_section.get("position", "main")
                    section_id = str(application_section.get("id", ""))
                    section_is_activity_action = (
                        application_section.get("type") == "activity_action"
                        or application_section.get("layout") == "activity_action"
                    )
                    if (
                        section_position in ("header", "footer", "sidebar")
                        and not section_is_activity_action
                        and section_id
                        and section_id not in page_section_ids
                    ):
                        page_sections.append({"value": section_id})
                        page_section_ids.add(section_id)

                for page_section in page_sections:
                    section = None
                    page_section_id = page_section["value"] if isinstance(page_section, dict) else str(page_section)
                    for application_section in application_component["value"]["data"]["sections"]:
                        if application_section["id"] == page_section_id:
                            section = application_section
                    
                    if not section:
                        continue

                    if section.get("type") == "activity_action" or section.get("layout") == "activity_action":
                        out.append(make_activity_action_section(
                            application_name=application_name,
                            page_name=page_name,
                            label=section.get("label") or section.get("name", "Complete"),
                            section=section,
                        ))
                        continue

                    if section.get("type") == "activity_start" or section.get("layout") == "activity_start":
                        out.append(make_activity_start_section(
                            application_name=application_name,
                            page_name=page_name,
                            section=section,
                        ))
                        continue

                    if section.get("type") == "activity_tasks" or section.get("layout") == "activity_tasks":
                        out.append(make_activity_tasks_section(
                            application_name=application_name,
                            page_name=page_name,
                            section=section,
                        ))
                        continue

                    declared_primary_model = section.get("primary_model") or section.get("object") or ""
                    raw_section_class = section.get("class")
                    if raw_section_class and find_model_by_class_ptr(metadata, raw_section_class):
                        section_class = raw_section_class
                    else:
                        section_class = find_class_ptr_by_model_name(
                            metadata,
                            raw_section_class or declared_primary_model,
                        )
                    primary_model = find_model_by_class_ptr(metadata, section_class) if section_class else None
                    operations = normalize_section_operations(section.get("operations"))
                    query = dict(section.get("query") or {})
                    relationship = section.get("relationship") or {}
                    if "limit" not in query and relationship.get("limit") is not None:
                        query["limit"] = relationship.get("limit")
                    if "exclude_source" not in query and relationship.get("exclude_source") is not None:
                        query["exclude_source"] = relationship.get("exclude_source")

                    behavior = section.get("behavior") if isinstance(section.get("behavior"), dict) else {}
                    section_layout = section.get("layout", "table")
                    section_position = section.get("position", "main")
                    sec = SectionComponent(
                        id = section["id"],
                        name = section.get("name") or section.get("id", ""),
                        application = application_name,
                        page = page_name,
                        primary_model = primary_model,
                        parent_models = find_parent_models_by_id(metadata, section_class) if section_class else [],
                        attributes = retrieve_section_attributes(metadata, section, application_name),
                        has_create_operation = bool(operations.get("create", False)),
                        has_delete_operation = bool(operations.get("delete", False)),
                        has_update_operation = bool(operations.get("update", False)),
                        has_select_operation = bool(operations.get("select", False)),
                        custom_methods = retrieve_section_custom_methods(section),
                        text = section.get("text", ""),
                        layout = section_layout,
                        style = section.get("style", None),
                        related_to_section_id = section.get("related_to", None),
                        relation_field = section.get("relation_field", None),
                        query = query,
                        col_span = int(section.get("col_span", 12)),
                        min_height = section.get("min_height"),
                        position = section_position,
                        component_type = section.get("type", "data"),
                        label = section.get("label"),
                        workflow = section.get("workflow"),
                        component = section.get("component"),
                        role = section.get("role"),
                        field_layout = section.get("field_layout") if isinstance(section.get("field_layout"), dict) else {},
                        behavior = behavior,
                    )
                    out.append(sec)
            return out
    except Exception as _e:
        import logging as _log
        _log.exception("retrieve_section_components error")
        raise ValueError(f"Failed to retrieve section components from metadata: parsing error - {_e}") from _e

    return out


def retrieve_categories(application_name: str, metadata: str) -> List[Category]:
    '''Function that retrieves the categories corresponding to application_name from
    metadata and returns a list of Category objects.'''
    
    if metadata in ["", None]:
        raise Exception("Failed to retrieve pages from metadata: metadata is empty")
    
    out = []

    try:
        for application_component in json.loads(metadata)["interfaces"]:
            if "categories" not in application_component["value"]["data"]: # empty interface
                continue
            if app_name_sanitization(application_component["label"]) != application_name:
                continue

            for category in application_component["value"]["data"]["categories"]:
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
            if "pages" not in application_component["value"]["data"]: # empty interface
                continue
            sanitized_application_label = app_name_sanitization(application_component["label"])
            if sanitized_application_label != application_name:
                continue

            for page in application_component["value"]["data"]["pages"]:
                category = None
                if page.get("category") is not None:
                    category = page["category"]["value"]["name"]

                layout_field = page.get("layout")
                if isinstance(layout_field, dict):
                    page_layout = {**layout_field, "value": layout_field.get("value") or "vertical"}
                else:
                    page_layout = layout_field or "vertical"

                gap_field = page.get("gap")
                page_gap = gap_field.get("value") if isinstance(gap_field, dict) else gap_field
                if not page_gap:
                    page_gap = "normal"

                type_field = page.get("type")
                if isinstance(type_field, dict):
                    page_type = type_field.get("value", "normal")
                elif type_field:
                    page_type = str(type_field)
                else:
                    page_type = "normal"
                activity_name = page['action']['label'] if page.get('action') else None
                section_components = retrieve_section_components(
                    application_name=application_name,
                    page_name=page["name"],
                    metadata=metadata,
                )
                if page_type == "activity" and not any(sc.component_type == "activity_action" for sc in section_components):
                    section_components.append(make_activity_action_section(
                        application_name=application_name,
                        page_name=page["name"],
                        label=activity_name or page["name"],
                    ))

                pg = Page(
                    id = page["id"],
                    name = page["name"],
                    application = sanitized_application_label,
                    category = category,
                    activity_name = activity_name,
                    type = page_type,
                    section_components = section_components,
                    layout = page_layout,
                    gap = str(page_gap),
                )
                out.append(pg)
    except Exception as _e:
        import logging as _log
        _log.exception("retrieve_pages error")
        raise ValueError(f"Failed to retrieve pages from metadata: parsing error - {_e}") from _e

    # Deduplicate by name: activity type takes precedence over normal.
    # This prevents a duplicate nav link when the same page appears as both
    # normal and activity (activity URL requires active_process_node_id, so
    # the normal variant would generate a broken {% url %} with no param).
    seen: dict[str, Page] = {}
    for pg in out:
        existing = seen.get(pg.name)
        if existing is None or pg.type == "activity":
            seen[pg.name] = pg
    out = list(seen.values())

    return out


def retrieve_models_on_pages(application_component: ApplicationComponent) -> dict[Page, Dict[str, List[Model]]]:
    '''Function that returns all primary models & foreign/parent models on pages inside
    application_component'''
    out: dict[Page, Dict[str, List[Model]]] = {}

    for page in application_component.pages:
        if page not in out:
            out[page] = {'primary_models': [], 'parent_models': []}
        for section_component in page.section_components:
            if section_component.primary_model:
                out[page]['primary_models'].append(section_component.primary_model)
            for parent_model in section_component.parent_models:
                out[page]['parent_models'].append(parent_model)
    return out


def retrieve_styling(application_name: str, metadata: str)  -> Styling:
    if metadata in ["", None]:
        raise Exception("Failed to retrieve styling from metadata: metadata is empty")
    
    style_type = None
    radius = None
    background_color = None
    accent_color = None
    text_color = None
    
    try:
        for application_component in json.loads(metadata)["interfaces"]:
            if app_name_sanitization(application_component["label"]) != application_name:
                continue
            if "styling" not in application_component["value"]["data"]: # empty interface
                return Styling() # return default object
            
            styling = application_component["value"]["data"]["styling"]
            if "selectedStyle" not in styling:
                style_type = StyleType.BASIC
            elif styling["selectedStyle"] == "basic":
                style_type = StyleType.BASIC
            elif styling["selectedStyle"] == "abstract":
                style_type = StyleType.ABSTRACT
            elif styling["selectedStyle"] == "modern":
                style_type = StyleType.MODERN

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
                radius = radius,
                text_color = text_color,
                accent_color = accent_color,
                background_color = background_color,
                font_family = styling.get("fontFamily", "inter"),
                page_max_width = styling.get("pageMaxWidth", "xl"),
                button_style = styling.get("buttonStyle", "solid"),
                card_hover = styling.get("cardHover", "lift"),
                image_ratio = styling.get("imageRatio", "4:3"),
                divider = styling.get("divider", "none"),
            )
    except:
        return Styling()

def retrieve_settings(application_name: str, metadata: str) -> Settings:
    if metadata in ["", None]:
        raise Exception("Failed to retrieve styling from metadata: metadata is empty")
    
    manager_access = False
    try:
        for application_component in json.loads(metadata)["interfaces"]:
            if app_name_sanitization(application_component["label"]) != application_name:
                continue
            if "settings" not in application_component['value']['data']:
                return Settings(manager_access=manager_access)
            settings = application_component["value"]["data"]["settings"]
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
        if "settings" not in application_component['value']['data']:
            continue
        settings = application_component["value"]["data"]["settings"]
        if "managerAccess" not in settings or not settings["managerAccess"]:
            continue
        manager_roles.append(app_name_sanitization(application_component["label"]))
    return manager_roles


def get_application_component(project_name: str, application_name: str, metadata: str, authentication_present: bool) -> ApplicationComponent:
    '''Function that builds an ApplicationComponent object for application_name
    from metadata.'''
    pages = retrieve_pages(application_name=application_name, metadata=metadata)
    sanitize_page_targets(pages)
    categories = retrieve_categories(application_name=application_name, metadata=metadata)
    settings = retrieve_settings(application_name=application_name, metadata=metadata)
    styling = retrieve_styling(application_name=application_name, metadata=metadata)
    tokens = {}
    for application_component in json.loads(metadata)["interfaces"]:
        if app_name_sanitization(application_component["label"]) == application_name:
            data = (application_component["value"].get("data") or {})
            tokens = dict(data.get("tokens") or {})
            # Pull dot-notation styling keys (e.g. "region.header.bg_hex") into tokens
            # so prototype CSS variables match the preview render path (_apply_styling_tokens).
            styling_raw = data.get("styling") or {}
            if isinstance(styling_raw, dict):
                for k, v in styling_raw.items():
                    if "." in str(k) and v not in (None, ""):
                        tokens.setdefault(str(k), v)
                accent_secondary = styling_raw.get("accentSecondary")
                if accent_secondary:
                    tokens.setdefault("color.secondary.hex", accent_secondary)
            break

    return ApplicationComponent(
        id = uuid4(), # TODO: retrieve frontend id from metadata
        project = project_name,
        name = application_name,
        categories = categories,
        pages = pages,
        settings = settings,
        styling = styling,
        tokens = tokens,
        authentication_present = authentication_present
    )
