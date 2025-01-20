from typing import List, Dict
from utils.sanitization import app_name_sanitization, model_name_sanitization, category_name_sanitization, attribute_name_sanitization
from utils.definitions.application_component import ApplicationComponent
from utils.definitions.section_component import SectionComponent, SectionAttribute, SectionCustomMethod
from utils.definitions.page import Page
from utils.definitions.category import Category
from utils.definitions.model import AttributeType, Model, Cardinality, define_cardinality
from utils.definitions.styling import Styling, StyleType
import json
from uuid import uuid4


def get_apps(metadata: str) -> str:
    '''Returns a string with all application component names, and spaces inbetween'''
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
            if node["cls_ptr"] == class_id and node["cls"]["type"] == "enum":
                for literal in node["cls"]["literals"]:
                    out.append(str(literal))
                return out
    return []


def find_model_by_class_ptr(metadata: str, class_id: str) -> str | None:
    for diagram in json.loads(metadata)["diagrams"]:
        if diagram["type"] != "classes":
            continue
        for node in diagram["nodes"]:
            if node["cls_ptr"] == class_id:
                return model_name_sanitization(node["cls"]["name"])
    return None


def find_model_by_id(metadata: str, class_id: str) -> str | None:
    for diagram in json.loads(metadata)["diagrams"]:
        if diagram["type"] != "classes":
            continue
        for node in diagram["nodes"]:
            if node["id"] == class_id and node["cls"]["type"] == "class":
                return model_name_sanitization(node["cls"]["name"])
    return None


def find_model_id_by_class_ptr(metadata: str, class_ptr: str) -> str:
    for diagram in json.loads(metadata)["diagrams"]:
        if diagram["type"] != "classes":
            continue
        for node in diagram["nodes"]:
            if node["cls_ptr"] == class_ptr:
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
            if edge["rel"]["type"] != "association":
                continue
            if edge["source_ptr"] == primary_class_id:
                cardinality = define_cardinality(edge["rel"]["multiplicity"]["source"], edge["rel"]["multiplicity"]["target"], node_is_source=True)
                model_name = find_model_by_id(metadata, edge["target_ptr"])
                if model_name and cardinality in SOURCE_ACCEPTABLE_CARDINALITIES:
                    out.append(model_name_sanitization(model_name))
            if edge["target_ptr"] == primary_class_id:
                cardinality = define_cardinality(edge["rel"]["multiplicity"]["source"], edge["rel"]["multiplicity"]["target"], node_is_source=False)
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
            if application_component["label"] != application_name:
                continue
            
            if "pages" not in application_component["value"]["data"]: # no pages in interface
                return []

            for page in application_component["value"]["data"]["pages"]:
                if page["name"] != page_name:
                    continue

                for page_section in page["sections"]:
                    section = None
                    page_section_id = page_section["value"]
                    for application_section in application_component["value"]["data"]["sections"]:
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
                        custom_methods = retrieve_section_custom_methods(section)
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
            if "categories" not in application_component["value"]["data"]: # empty interface
                continue
            if application_component["label"] != application_name:
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
            if application_component["label"] != application_name:
                continue

            for page in application_component["value"]["data"]["pages"]:
                category = None
                if page["category"] != None:
                    category = page["category"]["value"]["name"]
                pg = Page(
                    id = page["id"],
                    name = page["name"],
                    application = application_component["label"],
                    category = category,
                    section_components = retrieve_section_components(application_name=application_name, page_name=page["name"], metadata=metadata)
                )
                out.append(pg)
    except:
        raise Exception("Failed to retrieve pages from metadata: parsing error")

    return out


def retrieve_models_on_pages(application_component: ApplicationComponent) -> Dict[Page, List[Model]]:
    '''Function that returns all primary models & foreign/parent models on pages inside
    application_component'''
    out: Dict[Page, List[Model]] = {}

    for page in application_component.pages:
        if page not in out:
            out[page] = []
        for section_component in page.section_components:
            out[page].append(section_component.primary_model)
            for parent_model in section_component.parent_models:
                out[page].append(parent_model)
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
            if application_component["label"] != application_name:
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
                background_color = background_color
            )
    except:
        return Styling()


def get_application_component(project_name: str, application_name: str, metadata: str, authentication_present: bool) -> ApplicationComponent:
    '''Function that builds an ApplicationComponent object for application_name
    from metadata.'''
    pages = retrieve_pages(application_name=application_name, metadata=metadata)
    categories = retrieve_categories(application_name=application_name, metadata=metadata)
    return ApplicationComponent(
        id = uuid4(), # TODO: retrieve frontend id from metadata
        project = project_name,
        name = application_name,
        categories = categories,
        pages = pages,
        styling = retrieve_styling(application_name, metadata),
        authentication_present = authentication_present
    )