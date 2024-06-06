#This file is used to generate the html templates in the correct styling and format as indicated by the UI json

from enum import Enum

#Sections data
class SectionTextTag(Enum):
    P = 0
    H1 = 1
    H2 = 2
    H3 = 3
    H4 = 4
    H5 = 5
    H6 = 6

def determine_section_text_tag_from_metadata(text_tag_metadata : str) -> None:
    """translates metadata of tag into SectionText Enum"""
    match text_tag_metadata:
        case "P": return SectionTextTag.P
        case "H1" | "h1": return SectionTextTag.H1
        case "H2" | "h2": return SectionTextTag.H2
        case "H3" | "h3": return SectionTextTag.H3
        case "H4" | "h4": return SectionTextTag.H4
        case "H5" | "h5": return SectionTextTag.H5
        case "H6" | "h6": return SectionTextTag.H6
        case _: raise Exception("unknown text tag: "+ text_tag_metadata)

class SectionText():
    def __init__(self, 
                 content : str, 
                 tag : str,
                 order : int):
        self.content = content
        self.tag = determine_section_text_tag_from_metadata(tag)
        self.order = order

class SectionComponentType(Enum):
    FunctionalityList = 1
    READ = 2

class Link():
    def __init__(self, text : str = None, 
                 app_name_out : str = None, 
                 page_name_out : str = None):
        if text in [None, ""]:
            self.text = "Go to " + page_name_out
        else:
            self.text = text
        self.app_name_out = app_name_out
        self.page_name_out = page_name_out

from utils.data_validation_utils import custom_method_name_sanitizer, is_valid_uuid, section_component_name_sanitizer

class CustomMethod():
    def __init__(self,
                 method_name : str = None,
                 primary_model_name : str = None,
                 iterable : bool = True # True: button for each object, False: one global button
                 ):
        if primary_model_name in [None, ""] or method_name in [None, ""]:
            raise Exception("Tried to create an invalid CustomMethod object")
        self.method_name = custom_method_name_sanitizer(method_name)
        self.primary_model_name = primary_model_name
        self.iterable = iterable

    def isIterable(self) -> bool:
        return self.iterable == True

from .table_utils import AttributeType

def determine_attribute_types_from_metadata(attribute_types_metadata) -> None:
    """changes attribute_types to be of ENUM instead of string.
    Used the first time when parsing sections and when updating them.
    Returns the attribute_types in correct format"""
    new_attribute_types = {}
    for attribute_name in attribute_types_metadata:
        new_attribute_type = attribute_types_metadata[attribute_name] 
        match new_attribute_type:
            case "str": 
                new_attribute_type = AttributeType.STRING
            case "bool": 
                new_attribute_type = AttributeType.BOOLEAN
            case "int": 
                new_attribute_type = AttributeType.INTEGER
            case "model": 
                new_attribute_type = AttributeType.MODEL
            case None:
                new_attribute_type = AttributeType.STRING #default
        new_attribute_types[attribute_name] = new_attribute_type
    return new_attribute_types

def translate_and_set_section_component_object_attribute(section_component, attribute_name, data_value, data_type = dict):
    """This function is used to set specific values of sections that are sometimes named differently like model == class == op_class"""
    if data_value == "" or  data_value == []:
        return

    #change some values to expected names
    match attribute_name:
        case "text" : #section components can have text classes but it might be useful anyways
            if data_type != object:
                list_of_texts = []
                for text_metadata_instance in data_value:
                    list_of_texts.append( SectionText(text_metadata_instance["content"], text_metadata_instance["tag"], text_metadata_instance["order"]))
                data_value = list_of_texts
        #these should all set the value to their name TODO -> id instead
        #todo actions and usecases could be multiple
        case "section_component" | "section_component_name" | "section_component_data" :
            if "name" in section_component.__dict__ and section_component.name:
                raise Exception("Tried to name section component " + str(data_value) +" but it already has name: "+ section_component.name)
            attribute_name = "name"
        case "app" | "app_name" | "app_data" :
            attribute_name = "app"
        case "op_class" | "primary_model" | "model" :
            attribute_name = "model"
        case "page" | "page_data" | "page_name":
            attribute_name = "page"
        case "usecase" | "usecases" | "use_cases" | "usecase_name" | "usecase_data" | "use_case" | "use_case_name" | "use_case_data" :
            attribute_name = "use_cases"
        case "action" | "actions" | "activity" | "activities" | "actions_data" | "action_data" | "action_name" :
            attribute_name = "actions"
        case "class" | "classes" | "class_name" | "class_names" | "models" | "model" | "model_names" | "model_name" :
            attribute_name = "classes"
        case "col" | "sectioncolumn" | "sectioncol" | "section_column" | "section_col" | "column" | "pagecol" | "page_column" | "page_col":
            attribute_name = "col"
            data_value = int(data_value)
        case "row" | "sectionrow" | "sectionrow" | "section_row" | "section_row" | "row" | "pagerow" | "page_row" | "page_row":
            attribute_name = "row"
            data_value = int(data_value)
        case "custom_method":
            #note: max of one custom function is passed
            attribute_name="custom_methods"
            if data_value == None or data_value == [] or data_value == "" or data_value["name"] == "":
                return
            data_value=[data_value]
        case "query_value":
            attribute_name="query_condition"
        case "crud":
            print_string =" "
            for crudd_type in data_value:
                if data_value[crudd_type] == True:
                    match crudd_type:
                        case "is_custom":
                            continue
                        case "is_query":
                            attribute_name = "isQuery"
                        case "has_update":
                            attribute_name = "hasUpdate"
                        case "has_create":
                            attribute_name = "hasCreate"
                        case "has_delete":
                            attribute_name = "hasDelete"
                    print_string = print_string + (" " + str(crudd_type) + ",")
                    setattr(section_component, attribute_name, data_value[crudd_type])
            return
        case "name":
            data_value = section_component_name_sanitizer(data_value) 
        case "id":
                if not is_valid_uuid(data_value):
                    raise Exception("invalid id: "+ data_value)
        case _:
            pass

    setattr(section_component, attribute_name, data_value)

def main():
    return

if __name__ == "__main__":
    main()