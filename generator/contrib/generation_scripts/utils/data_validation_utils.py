#This file includes all tools to check our assumptions of the data so generation works as intended

def check_orders_on_section(table,section_component):
    """Walks through objects on section to validate lineair order through links and text"""
    raise Exception("unimplemented")
    #look if order on section is okay

#class
def check_models_on_table(table):
    """checks if User model is defined when Auth is toggled"""
    for app_name in table.app_names:
        if app_name == "authentication" or app_name == "Authentication":
            if "User" not in table.class_names:
                raise Exception("User model not in known class_names, but required for Auth") 
    return

#todo just act on models not on entire data
def sanitize_data_models(data):
    """Removes unneccessary "data" attribute from model and sanitizes names.
    Assumes data attribute is in data, else this function does nothing"""
    updatedmodels = data["models"]
    updateddata = data

    for model in data["models"]:
        if not "data" in model:
            continue
        for updatedmodel in updatedmodels:
            if updatedmodel["id"] == model["id"]:
                for attribute in model["data"]:
                    insertvalue = model["data"][attribute]
                    if attribute == "name":
                        insertvalue = class_name_sanitizer(insertvalue)
                    #sanitize attribute names
                    elif attribute == "attributes":
                        new_attributes = []
                        for attribute_data in insertvalue:
                            if isinstance(attribute_data, dict):
                                new_attribute_data_dict = attribute_data 
                                new_attribute_data_dict["name"] = attribute_name_sanitizer(attribute_data["name"]) 
                                new_attributes.append(new_attribute_data_dict)
                            elif isinstance(attribute_data, str): #old style with attributes passed just as strings of their name
                                new_attributes.append(attribute_name_sanitizer(attribute_data))
                            else:
                                raise Exception("unknown format for attributes: "+ str(attribute_data))
                        insertvalue = new_attributes
                    updatedmodel[attribute] = insertvalue
                updatedmodel.pop("data")

    updateddata["models"] = updatedmodels
    return updateddata

import re
from utils.getters_table import get_model_from_table
from utils.table_utils import AttributeType

def determine_attribute_types_from_model(attribute_types_model) -> None:
    """returns the attribute_types in correct format"""
    new_attribute_types = {}
    for attribute_type in attribute_types_model:
        new_attribute_type = attribute_type 
        match attribute_types_model[attribute_type]:
            case "str": 
                overwrite_with_attribute = AttributeType.STRING
            case "bool": 
                overwrite_with_attribute = AttributeType.BOOLEAN
            case "int": 
                overwrite_with_attribute = AttributeType.INTEGER
            case "model": 
                overwrite_with_attribute = AttributeType.MODEL
            case None:
                overwrite_with_attribute = AttributeType.STRING #default
            case _ :
                overwrite_with_attribute = attribute_types_model[attribute_type]
        new_attribute_types[new_attribute_type] = overwrite_with_attribute
    return new_attribute_types

def class_data_sanitizer(class_dict : dict ) -> dict:
    """also sets derived attributes"""
    new_class_dict = class_dict
    new_class_dict["derived_attributes"] = []
    new_class_dict["custom_methods"] = []
    if "attributes" in class_dict:
        new_attribute_types = {}
        for old_attribute_type in class_dict["attributes"]:
            old_attribute_name = attribute_name_sanitizer(old_attribute_type["name"])
            if "derived" in old_attribute_type:
                new_class_dict["derived_attributes"].append(old_attribute_name)
            new_attribute_types[old_attribute_name] = old_attribute_type["type"]
        new_class_dict["attributes"] = determine_attribute_types_from_model(new_attribute_types)
    if "methods" in class_dict:
        for old_method in class_dict["methods"]:        
            new_custom_method = {}
            new_custom_method = custom_method_name_sanitizer(old_method["name"])
            new_class_dict["custom_methods"].append(new_custom_method)
        # new_class_dict["methods"].pop()
    return new_class_dict

#names
def generic_name_sanitizer(name : str, source : str = "any") -> str:
    error_name = "name"
    if source != "any":
        error_name = error_name + " of " + source
    if name == None: return "unknown "+ error_name
    return re.sub(r'[^a-zA-Z0-9_]', '', name)

def custom_method_name_sanitizer(custom_method_name : str):
    if custom_method_name.lower() in [
        "ceate",
        "create_popup"
        "delete",
        "update",
        "update_popup",
    ]:
        raise Exception("Tried to create a CustomMethod object with an invalid custom_method_name")
    return generic_name_sanitizer(custom_method_name, "custom method")

def app_name_sanitizer(name : str) -> str:
    if name == "Authentication" or name == "authentication":
        name = "authentication"
    return generic_name_sanitizer(name, "app")

def class_name_sanitizer(name : str) -> str:
    return generic_name_sanitizer(name, "class")

def attribute_name_sanitizer(name : str) -> str:
    return generic_name_sanitizer(name, "attribute")

def page_name_sanitizer(name : str) -> str:
    return generic_name_sanitizer(name, "page").lower()

def section_component_name_sanitizer(name : str) -> str:
    return generic_name_sanitizer(name, "section_component")#.lower()

def is_valid_uuid(uuid):
    #source https://stackoverflow.com/questions/11384589/what-is-the-correct-regex-for-matching-values-generated-by-uuid-uuid4-hex
    regex = re.compile('^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z', re.I)
    match = regex.match(uuid)
    return bool(match)

def check_page_id(page_id : str) -> bool:
    return is_valid_uuid(page_id)

def check_section_component_with_model(table, section_component_object):
    """Checks if data on section_component_object matches data in table.
    Loads model_data on section component from table and checks if attributes are valid"""
    check_model_of_section_component(section_component_object, table)
    
def check_model_of_section_component(section_component_object,table):
        model = get_model_from_table(table=table,model_name=section_component_object.model) #moet een dict zijn
        section_component_attribute_types = section_component_object.attribute_types
        
        model_attribute_names = [model_attr for model_attr in model["attributes"]]
        for section_component_attribute_name in section_component_attribute_types:
            if section_component_attribute_name not in model_attribute_names and section_component_attribute_name not in table.class_names:
                raise Exception("ERR: "+str(section_component_attribute_name)+" attribute does not exist in model "+str(model_attribute_names))
            for attr_name in model["attributes"]:
                if attr_name == section_component_attribute_name and not (section_component_attribute_types[section_component_attribute_name] == model["attributes"][attr_name]):
                    raise Exception("ERR: "+str(section_component_attribute_name) + " has a different type than allowed : "+str(
                    section_component_attribute_types[section_component_attribute_name])+" != "+ str(model["attributes"][attr_name]) +" in model ")#+str(model))

def main():
    raise Exception("unimplemented")


if __name__ == "__main__":
    main()
