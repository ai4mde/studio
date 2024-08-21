from typing import List, Dict
from utils.sanitization import app_name_sanitization, model_name_sanitization, category_name_sanitization, attribute_name_sanitization
from utils.definitions.application_component import ApplicationComponent
from utils.definitions.section_component import SectionComponent, SectionAttribute
from utils.definitions.page import Page
from utils.definitions.category import Category
from utils.definitions.model import AttributeType, Model
from utils.definitions.styling import Styling, StyleType
import json
from uuid import uuid4


def get_apps(metadata: str) -> List[str]:
    '''Returns a list of all application component names'''
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


def find_model_by_id(metadata: str, class_id: str) -> str | None:
    for diagram in json.loads(metadata)["diagrams"]:
        if diagram["type"] != "classes":
            continue
        for node in diagram["nodes"]:
            if node["cls_ptr"] == class_id:
                return model_name_sanitization(node["cls"]["name"])
    return None


def find_category_by_id(metadata: str, category_id: str) -> str | None:
    for interface in json.loads(metadata)["interfaces"]:
        if "categories" not in interface["value"]["data"]:
            continue # Empty interface

        for category in interface["value"]["data"]["categories"]:
            if category["id"] == category_id:
                return category_name_sanitization(category["name"])
    return None


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


def retrieve_section_attributes(section: str) -> List[SectionAttribute]:
    if not section:
        return []
    if "attributes" not in section:
        return []
    
    out = []
    for attribute in section["attributes"]:
        attribute_type = None
        if attribute["type"] == "str":
            attribute_type  = AttributeType.STRING
        elif attribute["type"] == "int":
            attribute_type  = AttributeType.INTEGER
        elif attribute["type"] == "bool":
            attribute_type  = AttributeType.BOOLEAN

        # TODO: retrieve foreign models (also TODO in frontend)

        att = SectionAttribute(
            name = attribute_name_sanitization(attribute["name"]),
            type = attribute_type,
            updatable = True # TODO: frontend management of updatable attributes
        )
        out.append(att)

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

                for section in page["sections"]:
                    sec = SectionComponent(
                        id = section["id"],
                        name = section["name"],
                        application = application_name,
                        page = page_name,
                        primary_model = find_model_by_id(metadata, section["class"]), # TODO: there might be a quicker method than this
                        parent_models = [], # TODO
                        attributes = retrieve_section_attributes(section),
                        has_create_operation = section["operations"]["create"],
                        has_delete_operation = section["operations"]["delete"],
                        has_update_operation = section["operations"]["update"],

                    )
                    out.append(sec)
            return out
    except:
        raise Exception("Failed to retrieve section components from metadata: parsing error")

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
                pg = Page(
                    id = page["id"],
                    name = page["name"],
                    application = application_component["label"],
                    category = find_category_by_id(metadata, page["category"]), # TODO: there might be a quicker method than this
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
    return ApplicationComponent(
        id = uuid4(), # TODO: retrieve frontend id from metadata
        project = project_name,
        name = application_name,
        pages = pages,
        styling = retrieve_styling(application_name, metadata),
        authentication_present = authentication_present
    )