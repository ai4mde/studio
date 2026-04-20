from typing import List
import sys
from utils.definitions.model import Model, Attribute, AttributeType, CustomMethod, define_cardinality
from utils.file_generation import generate_output_file
import json
from utils.sanitization import model_name_sanitization, attribute_name_sanitization, project_name_sanitization, custom_method_name_sanitization
from utils.loading_json_utils import (
    _classifier_lookup,
    _edge_relation_data,
    _edge_source_ref,
    _edge_target_ref,
    _node_classifier_data,
    _relation_lookup,
    _relation_record_lookup,
    get_apps,
    get_enum_literals,
)
from utils.metadata_input import resolve_metadata_arg


def retrieve_class_name_by_id(node_id: str, diagram: dict, classifiers_by_id: dict[str, dict]) -> str | None:
    """Function that finds a 'node' in 'diagram' by id and builds a foreign model attribute for it"""
    for node in diagram["nodes"]:
        if node["id"] != node_id:
            continue
        node_data = _node_classifier_data(node, classifiers_by_id)
        if node_data.get("type") == "class":
            return model_name_sanitization(node_data["name"])
        return None
    return None


# TODO: implement different type of foreign models for differnt type of associations
def retrieve_foreign_models(
    node: dict,
    diagram: dict,
    classifiers_by_id: dict[str, dict],
    relations_by_id: dict[str, dict],
    relation_records_by_id: dict[str, dict],
) -> List[Attribute]:
    """Function that retrieves relations from 'node' to other nodes in 'diagram'
    and builds foreign model attributes for these relations"""
    out = []
    for edge in diagram["edges"]:
        edge_data = _edge_relation_data(edge, relations_by_id)
        edge_type = edge_data.get("type")
        if edge_type not in ("association", "composition"):
            continue

        source_ref = _edge_source_ref(edge, relation_records_by_id)
        target_ref = _edge_target_ref(edge, relation_records_by_id)

        if source_ref == node["id"]:
            foreign_model = Attribute(
                retrieve_class_name_by_id(target_ref, diagram, classifiers_by_id),
                AttributeType.FOREIGN_MODEL,
                enum_literals=None,
                cardinality=define_cardinality(edge_data["multiplicity"]["source"], edge_data["multiplicity"]["target"], node_is_source=True),
                derived=False,
                body=None,

            )
            if foreign_model.name:
                out.append(foreign_model)

        if target_ref == node["id"]:
            foreign_model = Attribute(
                retrieve_class_name_by_id(source_ref, diagram, classifiers_by_id),
                AttributeType.FOREIGN_MODEL,
                enum_literals=None,
                cardinality=define_cardinality(edge_data["multiplicity"]["target"], edge_data["multiplicity"]["source"], node_is_source=False),
                derived=False,
                body=None,
            )
            if foreign_model.name:
                out.append(foreign_model)
    return out


def retrieve_model_attributes(metadata: str, node: dict, classifiers_by_id: dict[str, dict]) -> List[Attribute]:
    """Function that parses the attributes of a class node from JSON to a Python objects"""
    out = []
    node_data = _node_classifier_data(node, classifiers_by_id)

    for attribute in node_data.get("attributes", []):
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
        elif attribute["type"] == "date":
            att_type = AttributeType.DATE
        elif attribute["type"] == "datetime":
            att_type = AttributeType.DATETIME
        elif attribute["type"] == "text":
            att_type = AttributeType.TEXT
        elif attribute["type"] == "float":
            att_type = AttributeType.FLOAT
        elif attribute["type"] == "email":
            att_type = AttributeType.EMAIL
        
        att = Attribute(
            name = attribute_name_sanitization(attribute["name"]),
            type = att_type,
            enum_literals = enum_literals,
            cardinality = None,
            derived = attribute.get("derived", False),
            body = attribute.get("body")
        )
        out.append(att)

    return out


def retrieve_model_custom_methods(node: dict, classifiers_by_id: dict[str, dict]) -> List[CustomMethod]:
    """Function that parses the custom methods of a class node from JSON to a Python objects"""
    out = []
    node_data = _node_classifier_data(node, classifiers_by_id)
    for custom_method in node_data.get("methods", []):
        mtd = CustomMethod(
            name = custom_method_name_sanitization(custom_method["name"]),
            body = custom_method["body"]
        )
        out.append(mtd)
    
    return out
 

def retrieve_models(metadata: str) -> List[Model]:
    """Function that parses the class nodes of a class diagram from JSON to Python objects"""
    if metadata in ["", None]:
        raise Exception("Failed to retrieve models from metadata: metadata is empty")

    out = []
    try:
        if metadata:
            metadata_json = json.loads(metadata)
            classifiers_by_id = _classifier_lookup(metadata_json)
            relations_by_id = _relation_lookup(metadata_json)
            relation_records_by_id = _relation_record_lookup(metadata_json)

            # First pass: collect generalization (inheritance) edges
            # generalization source = child, target = parent
            parent_map: dict[str, str] = {}  # child_node_id -> parent_class_name
            for diagram in metadata_json["diagrams"]:
                if diagram["type"] != "classes":
                    continue
                for edge in diagram["edges"]:
                    edge_data = _edge_relation_data(edge, relations_by_id)
                    if edge_data.get("type") != "generalization":
                        continue
                    source_ref = _edge_source_ref(edge, relation_records_by_id)
                    target_ref = _edge_target_ref(edge, relation_records_by_id)
                    parent_name = retrieve_class_name_by_id(target_ref, diagram, classifiers_by_id)
                    if parent_name:
                        parent_map[source_ref] = parent_name

            for diagram in metadata_json["diagrams"]:
                if diagram["type"] != "classes":
                    continue
                for node in diagram["nodes"]:
                    node_data = _node_classifier_data(node, classifiers_by_id)
                    if node_data.get("type") != "class":
                        continue
                    cls = Model(
                        name = model_name_sanitization(node_data["name"]),
                        attributes = retrieve_model_attributes(metadata, node, classifiers_by_id) + retrieve_foreign_models(node, diagram, classifiers_by_id, relations_by_id, relation_records_by_id),
                        custom_methods = retrieve_model_custom_methods(node, classifiers_by_id),
                        parent_class = parent_map.get(node["id"]),
                    )
                    out.append(cls)

            # Sort models: parents before children for correct Django inheritance
            name_set = {m.name for m in out}
            sorted_out: list[Model] = []
            remaining = list(out)
            added = set()
            while remaining:
                progress = False
                for m in list(remaining):
                    if m.parent_class is None or m.parent_class in added or m.parent_class not in name_set:
                        sorted_out.append(m)
                        added.add(m.name)
                        remaining.remove(m)
                        progress = True
                if not progress:
                    # Break cycles by adding remaining as-is
                    sorted_out.extend(remaining)
                    break
            out = sorted_out
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