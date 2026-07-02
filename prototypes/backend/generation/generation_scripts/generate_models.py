from typing import List
import sys
from utils.definitions.model import Model, Attribute, AttributeType, CustomMethod, Cardinality, define_cardinality
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


def _id_reference_model(attribute_name: str, current_model: str, model_names: set[str]) -> str | None:
    """Resolve patient_id-style fields to an existing related model name."""
    raw = attribute_name_sanitization(attribute_name or "").lower()
    candidates = []
    if raw.endswith("_id") and len(raw) > 3:
        candidates.append(raw[:-3])
    elif raw.endswith("id") and len(raw) > 2:
        candidates.append(raw[:-2].rstrip("_"))
    current = model_name_sanitization(current_model or "").lower()
    for candidate in candidates:
        if not candidate or candidate == current:
            continue
        for model_name in model_names:
            if model_name.lower() == candidate:
                return model_name
    return None


def _dedupe_attributes(attributes: List[Attribute]) -> List[Attribute]:
    out = []
    seen = set()
    for attribute in attributes:
        key = str(attribute.name)
        if key in seen:
            continue
        seen.add(key)
        out.append(attribute)
    return out


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


def _resolve_attr_type_and_literals(attribute: dict, metadata: str) -> tuple:
    """Return (att_type, enum_literals) for a class attribute descriptor."""
    type_str = attribute.get("type", "")
    if type_str == "str":
        return AttributeType.STRING, None
    if type_str == "bool":
        return AttributeType.BOOLEAN, None
    if type_str == "int":
        return AttributeType.INTEGER, None
    if type_str == "enum":
        enum_ref = attribute.get("enum")
        if not enum_ref:
            return AttributeType.ENUM, []
        return AttributeType.ENUM, get_enum_literals(metadata, enum_ref)
    if type_str == "image":
        return AttributeType.IMAGE, None
    if type_str == "video":
        return AttributeType.VIDEO, None
    return AttributeType.NONE, None


def retrieve_model_attributes(metadata: str, node: str, model_names: set[str] | None = None) -> List[Attribute]:
    """Function that parses the attributes of a class node from JSON to a Python objects"""
    out = []
    model_names = model_names or set()
    node_cls = node.get("cls") or {}
    current_model = model_name_sanitization(node_cls.get("name", ""))

    for attribute in node_cls.get("attributes", []):
        relation_model = _id_reference_model(attribute.get("name", ""), current_model, model_names)
        if relation_model:
            out.append(Attribute(
                name=relation_model,
                type=AttributeType.FOREIGN_MODEL,
                enum_literals=None,
                cardinality=Cardinality.ZERO_MANY_TO_ONE,
                derived=False,
                body=None,
            ))
            continue
        att_type, enum_literals = _resolve_attr_type_and_literals(attribute, metadata)
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
            for method_field in ("methods",):
                for custom_method in section.get(method_field, []) or []:
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
        data = json.loads(metadata)
        model_names = {
            model_name_sanitization(node.get("cls", {}).get("name", ""))
            for diagram in data.get("diagrams", [])
            if diagram.get("type") == "classes"
            for node in diagram.get("nodes", [])
            if isinstance(node.get("cls"), dict)
            if node.get("cls", {}).get("type") == "class" and node.get("cls", {}).get("name")
        }
        model_names.update({
            model_name_sanitization((classifier.get("data") or {}).get("name", ""))
            for classifier in data.get("classifiers", [])
            if (classifier.get("data") or {}).get("type") == "class" and (classifier.get("data") or {}).get("name")
        })
        if metadata:
            for diagram in data["diagrams"]:
                if diagram["type"] != "classes":
                    continue
                for node in diagram["nodes"]:
                    # cls may be a UUID string (ExportNode format) — skip; handled by classifiers fallback
                    if not isinstance(node.get("cls"), dict):
                        continue
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
                        attributes = _dedupe_attributes(retrieve_model_attributes(metadata, node, model_names) + retrieve_foreign_models(node, diagram)),
                        custom_methods = deduped_methods
                    )
                    out.append(cls)
    except:
        raise Exception("Failed to retrieve models from metadata: parsing error")

    # Fallback: generate models from flat classifiers list not already covered by a diagram node.
    # The API enriches the metadata with system classifiers on generation.
    try:
        data_parsed = json.loads(metadata)
        seen_names = {m.name for m in out}
        all_model_names = {
            model_name_sanitization((classifier.get("data") or {}).get("name", ""))
            for classifier in data_parsed.get("classifiers", [])
            if (classifier.get("data") or {}).get("type") == "class" and (classifier.get("data") or {}).get("name")
        } | seen_names
        for flat_cls in data_parsed.get("classifiers", []):
            cls_data = flat_cls.get("data", {})
            if cls_data.get("type") != "class":
                continue
            name = model_name_sanitization(cls_data.get("name", ""))
            if not name or name in seen_names:
                continue
            attrs_out = []
            for attribute in cls_data.get("attributes", []):
                relation_model = _id_reference_model(attribute.get("name", ""), name, all_model_names)
                if relation_model:
                    attrs_out.append(Attribute(
                        name=relation_model,
                        type=AttributeType.FOREIGN_MODEL,
                        enum_literals=None,
                        cardinality=Cardinality.ZERO_MANY_TO_ONE,
                        derived=attribute.get("derived", False),
                        body=attribute.get("body"),
                    ))
                    continue
                att_type = AttributeType.NONE
                if attribute.get("type") == "str":
                    att_type = AttributeType.STRING
                elif attribute.get("type") == "bool":
                    att_type = AttributeType.BOOLEAN
                elif attribute.get("type") == "int":
                    att_type = AttributeType.INTEGER
                elif attribute.get("type") == "image":
                    att_type = AttributeType.IMAGE
                elif attribute.get("type") == "video":
                    att_type = AttributeType.VIDEO
                attrs_out.append(Attribute(
                    name=attribute_name_sanitization(attribute.get("name", "")),
                    type=att_type,
                    enum_literals=None,
                    cardinality=None,
                    derived=attribute.get("derived", False),
                    body=attribute.get("body"),
                ))
            custom_methods = []
            seen_method_names = set()
            for method_data in cls_data.get("methods", []):
                if not method_data.get("body") and not method_data.get("action"):
                    continue
                call_name = method_data.get("call_name") or custom_method_name_sanitization(method_data.get("name", ""))
                if call_name in seen_method_names:
                    continue
                seen_method_names.add(call_name)
                custom_methods.append(CustomMethod(
                    name=custom_method_name_sanitization(method_data.get("name", "")),
                    body=method_data.get("body"),
                    action=method_data.get("action"),
                    target_model=method_data.get("target_model"),
                    parameters=method_data.get("parameters", []),
                    call_name=call_name,
                ))
            for m in retrieve_section_custom_methods_for_model(metadata, name):
                if m.call_name not in seen_method_names:
                    seen_method_names.add(m.call_name)
                    custom_methods.append(m)
            out.append(Model(
                name=name,
                attributes=_dedupe_attributes(attrs_out),
                custom_methods=custom_methods,
            ))
            seen_names.add(name)
    except Exception:
        pass

    return out


def main():
    if (len(sys.argv) != 5):
        raise Exception("Invalid number of system arguments.")
    project_name_arg = str(sys.argv[1])
    metadata_arg = str(sys.argv[2])
    authentication_arg = str(sys.argv[3])
    system_id_arg = str(sys.argv[4])
    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/models.py.jinja2"
    OUTPUT_FILE_PATH = "/usr/src/prototypes/generated_prototypes/" + system_id_arg + "/" + project_name_sanitization(project_name_arg) + "/shared_models/models.py"

    metadata = resolve_metadata_arg(metadata_arg)
    application_names = get_apps(metadata).split()

    data = {
        "project_name": project_name_arg,
        "app_name": "shared_models",
        "models": retrieve_models(metadata),
        "authentication_present": authentication_arg == "True",
        "user_types": application_names
    }
    if generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        return True
    
    raise Exception("Failed to generate shared_models/models.py")


if __name__ == "__main__":
    main()
