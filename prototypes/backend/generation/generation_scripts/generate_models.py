from typing import List
import sys
from utils.definitions.model import Model, Attribute, AttributeType, CustomMethod, define_cardinality
from utils.file_generation import generate_output_file
import json
from utils.sanitization import model_name_sanitization, attribute_name_sanitization, project_name_sanitization, custom_method_name_sanitization
from utils.loading_json_utils import resolve_metadata_arg
from utils.loading_json_utils import get_apps, get_enum_literals


def retrieve_class_name_by_id(node_id: str, diagram: str) -> str:
    """Function that finds a 'node' in 'diagram' by id and builds a foreign model attribute for it"""
    for node in diagram["nodes"]:
        if node["id"] != node_id:
            continue
        if node["cls"]["type"] == "class":
            return model_name_sanitization(node["cls"]["name"])
        return None


# TODO: implement different type of foreign models for differnt type of associations
def retrieve_foreign_models(node: str, diagram: str) -> List[Attribute]:
    """Function that retrieves relations from 'node' to other nodes in 'diagram'
    and builds foreign model attributes for these relations"""
    out = []
    for edge in diagram["edges"]:
        if edge["rel"]["type"] != "association":
            continue

        if edge["source_ptr"] == node["id"] :
            foreign_model = Attribute(
                retrieve_class_name_by_id(edge["target_ptr"], diagram),
                AttributeType.FOREIGN_MODEL,
                enum_literals=None,
                cardinality=define_cardinality(edge["rel"]["multiplicity"]["source"], edge["rel"]["multiplicity"]["target"], node_is_source=True),
                derived=False,
                body=None,

            )
            if foreign_model:
                out.append(foreign_model)

        if edge["target_ptr"] == node["id"] :
            foreign_model = Attribute(
                retrieve_class_name_by_id(edge["source_ptr"], diagram),
                AttributeType.FOREIGN_MODEL,
                enum_literals=None,
                cardinality=define_cardinality(edge["rel"]["multiplicity"]["target"], edge["rel"]["multiplicity"]["source"], node_is_source=False),
                derived=False,
                body=None,

            )
            if foreign_model:
                out.append(foreign_model)
    return out


def retrieve_model_attributes(metadata: str, node: str) -> List[Attribute]:
    """Function that parses the attributes of a class node from JSON to a Python objects"""
    out = []

    for attribute in node["cls"]["attributes"]:
        att_type = AttributeType.NONE
        enum_literals = None
        if attribute["type"] == "str":
            att_type = AttributeType.STRING
        elif attribute["type"] == "bool":
            att_type = AttributeType.BOOLEAN
        elif attribute["type"] == "int":
            att_type = AttributeType.INTEGER
        elif attribute["type"] == "enum":
            att_type = AttributeType.ENUM
            if "enum" not in attribute:
                enum_literals = []
            elif not attribute["enum"]:
                enum_literals = []
            else:
                enum_literals = get_enum_literals(metadata, attribute["enum"])
        
        att = Attribute(
            name = attribute_name_sanitization(attribute["name"]),
            type = att_type,
            enum_literals = enum_literals,
            cardinality = None,
            derived = attribute["derived"],
            body = attribute["body"]
        )
        out.append(att)

    return out


def retrieve_model_custom_methods(node: str) -> List[CustomMethod]:
    """Function that parses the custom methods of a class node from JSON to a Python objects"""
    out = []
    for custom_method in node["cls"]["methods"]:
        mtd = CustomMethod(
            name = custom_method_name_sanitization(custom_method["name"]),
            body = custom_method.get("body"),
            action = custom_method.get("action"),
            target_model = custom_method.get("target_model"),
            parameters = custom_method.get("parameters", []),
            call_name = custom_method.get("call_name") or custom_method_name_sanitization(custom_method["name"]),
        )
        out.append(mtd)
    
    return out


def retrieve_section_custom_methods_for_model(metadata: str, model_name: str) -> List[CustomMethod]:
    """Collect section-level custom method bodies for the model they act on."""
    out = []
    seen_bodies = set()
    data = json.loads(metadata)
    class_ids = {}
    for diagram in data.get("diagrams", []):
        if diagram.get("type") != "classes":
            continue
        for node in diagram.get("nodes", []):
            cls = node.get("cls", {})
            if cls.get("type") == "class":
                class_ids[model_name_sanitization(cls.get("name", ""))] = str(node.get("cls_ptr") or node.get("id"))
    for classifier in data.get("classifiers", []):
        cls_data = classifier.get("data", {})
        if cls_data.get("type") == "class":
            class_ids.setdefault(model_name_sanitization(cls_data.get("name", "")), str(classifier.get("id")))

    class_id = class_ids.get(model_name)
    if not class_id:
        return out

    for interface in data.get("interfaces", []):
        sections = interface.get("value", {}).get("data", {}).get("sections", [])
        for section in sections:
            if section.get("class") != class_id:
                continue
            for custom_method in section.get("methods", []) or []:
                body = custom_method.get("body")
                action = custom_method.get("action")
                dedupe_key = body or f"{custom_method.get('call_name') or custom_method.get('name')}:{action}"
                if not (body or action) or dedupe_key in seen_bodies:
                    continue
                seen_bodies.add(dedupe_key)
                out.append(
                    CustomMethod(
                        name=custom_method_name_sanitization(custom_method.get("name", "")),
                        body=body,
                        action=custom_method.get("action"),
                        target_model=custom_method.get("target_model"),
                        parameters=custom_method.get("parameters", []),
                        call_name=custom_method.get("call_name") or custom_method_name_sanitization(custom_method.get("name", "")),
                    )
                )
    return out
 

def retrieve_models(metadata: str) -> List[Model]:
    """Function that parses the class nodes of a class diagram from JSON to Python objects"""
    if metadata in ["", None]:
        raise Exception("Failed to retrieve models from metadata: metadata is empty")

    out = []
    try:
        if metadata:
            for diagram in json.loads(metadata)["diagrams"]:
                if diagram["type"] != "classes":
                    continue
                for node in diagram["nodes"]:
                    if node["cls"]["type"] != "class":
                        continue
                    custom_methods = retrieve_model_custom_methods(node) + retrieve_section_custom_methods_for_model(
                        metadata,
                        model_name_sanitization(node["cls"]["name"]),
                    )
                    deduped_methods = []
                    seen_method_names = set()
                    for custom_method in custom_methods:
                        key = custom_method.call_name
                        if key in seen_method_names:
                            continue
                        seen_method_names.add(key)
                        deduped_methods.append(custom_method)
                    cls = Model(
                        name = model_name_sanitization(node["cls"]["name"]),
                        attributes = retrieve_model_attributes(metadata, node) + retrieve_foreign_models(node, diagram),
                        custom_methods = deduped_methods
                    )
                    out.append(cls)
    except:
        raise Exception("Failed to retrieve models from metadata: parsing error")
    
    return out


def main():
    if (len(sys.argv) != 5):
        raise Exception("Invalid number of system arguments.")
    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/models.py.jinja2"
    OUTPUT_FILE_PATH = "/usr/src/prototypes/generated_prototypes/" + sys.argv[4] + "/" + project_name_sanitization(sys.argv[1]) + "/shared_models/models.py"

    metadata = resolve_metadata_arg(sys.argv[2])
    application_names = get_apps(metadata).split()

    data = {
        "project_name": sys.argv[1],
        "app_name": "shared_models",
        "models": retrieve_models(metadata),
        "authentication_present": sys.argv[3] == "True",
        "user_types": application_names
    }
    if generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        return True
    
    raise Exception("Failed to generate shared_models/models.py")


if __name__ == "__main__":
    main()
