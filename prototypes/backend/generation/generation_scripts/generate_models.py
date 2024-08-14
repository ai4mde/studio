from typing import List
import sys
from utils.definitions.model import Model, Attribute, AttributeType
from utils.file_generation import generate_output_file
import json
from utils.sanitization import model_name_sanitization, attribute_name_sanitization, project_name_sanitization


def retrieve_class_by_id(node_id: str, diagram: str) -> Attribute:
    """Function that finds a 'node' in 'diagram' by id and builds a foreign model attribute for it"""
    for node in diagram["nodes"]:
        if node["id"] != node_id:
            continue
        return Attribute(
            name = model_name_sanitization(node["cls"]["name"]),
            type = AttributeType.FOREIGN_MODEL
        )


# TODO: implement different type of foreign models for differnt type of associations
def retrieve_foreign_models(node: str, diagram: str) -> List[Attribute]:
    """Function that retrieves relations from 'node' to other nodes in 'diagram'
    and builds foreign model attributes for these relations"""
    out = []
    for association in diagram["edges"]:
        if association["source_ptr"] == node["id"]:
            foreign_model = retrieve_class_by_id(association["target_ptr"], diagram)
            out.append(foreign_model)
            
        if association["target_ptr"] == node["id"]:
            foreign_model = retrieve_class_by_id(association["source_ptr"], diagram)
            out.append(foreign_model)

    return out


def retrieve_attributes(node: str) -> List[Attribute]:
    """Function that parses the attributes of a class node from JSON to a Python objects"""
    out = []

    for attribute in node["cls"]["attributes"]:
        att_type = AttributeType.NONE
        if attribute["type"] == "str":
            att_type = AttributeType.STRING
        elif attribute["type"] == "bool":
            att_type = AttributeType.BOOLEAN
        elif attribute["type"] == "int":
            att_type = AttributeType.INTEGER
        
        att = Attribute(
            name = attribute_name_sanitization(attribute["name"]),
            type = att_type
        )
        out.append(att)

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
                    cls = Model(
                        name = model_name_sanitization(node["cls"]["name"]),
                        attributes = retrieve_attributes(node) + retrieve_foreign_models(node, diagram),
                        custom_methods = [] # TODO
                    )
                    out.append(cls)
    except:
        raise Exception("Failed to retrieve models from metadata: parsing error")
    
    return out


def main():
    if (len(sys.argv) != 3):
        raise Exception("Invalid number of system arguments.")
    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/models.py.jinja2"
    OUTPUT_FILE_PATH = "/usr/src/prototypes/generated_prototypes/" + project_name_sanitization(sys.argv[1]) + "/shared_models/models.py"
    data = {
        "project_name": sys.argv[1],
        "app_name": "shared_models",
        "models": retrieve_models(sys.argv[2]),
        "user_types": [], # TODO
    }
    if generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        return True
    
    raise Exception("Failed to generate shared_models/models.py")


if __name__ == "__main__":
    main()