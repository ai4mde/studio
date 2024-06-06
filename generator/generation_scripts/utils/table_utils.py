#This file includes functions and tools that are necessary to build the functionality table during prototype generation.
#The focus here lies on general functions which are necessary for each diagram.

from enum import Enum

class TableSpec:
    '''
    This class specifies the section table format.
    '''
    def __init__(self):
        self.headers = [
            "name",
            "section_component", #from this, the next 5 should be derived
            "app", #appname for now
            "page", #pagename for now
            "sectionrow",
            "sectioncolumn",
            "page_out", #on succes url
            "type",    #         class FunctionalityType(Enum):
                                    # CREATE_OBJECT = 1
                                    # READ_MULT_ATTRIBUTE = 2
                                    # READ_ONE_ATTRIBUTE = 3
                                    # UPDATE_MULT_ATTRIBUTE = 4
                                    # UPDATE_ONE_ATTRIBUTE = 5
                                    # DELETE_OBJECT = 6 
                                    # QUERY_MULT_ATTRIBUTE = 7
                                    # QUERY_ONE_ATTRIBUTE = 8
            # "class", #primary model that is acted upon
            "model", #primary model that is acted upon
            "parent_models", #list of parent models (e.g. for creation of child model, on delete=CASCADE)
            "attributes", #all attributes acted on by section
            "attribute_types", #all attributes acted on by section and its type
            "query_condition", # str. query condition for query types
            "order", # int. linear order in SectionComponent on page render
            "action", #if this section has a linked action, we note it here
            "usecase" #if this section has a linked usecase, we note it here
            ]
        # self.projectname = "default projectname"
        # self.app_names = []
        # self.application_components = [] #contains all data 
        # self.table = tableData # contains all loaded functionalities
        # self.class_names = []
        # self.class_data = [] #including all attributes and linked classes
        # self.home_pages = {}, # helpers for render functions (example: call on landing page)
        # self.home_entries = {}, # 
        # self.view_entry_out_per_app_page ={}, #to find entry out quickly


def get_name_or_entire_object(from_this) -> str:
    """If possible name, else entire object."""
    if from_this == None:
        return ""
    if isinstance(from_this, str):
        return from_this
    elif isinstance(from_this, int):
        return str(from_this)
    elif isinstance(from_this, list):
        return strorlenlist(from_this)
    elif isinstance(from_this, dict): 
        if "name" in from_this:
            return str(from_this["name"])
    elif isinstance(from_this, Enum): #useful for funct types 
        return str(from_this)[18:]
    elif isinstance(from_this, object):
        if "name" in from_this.__dict__:
            return str(getattr(from_this,"name"))
    return "ERR: "+ str(from_this)+" is unnamed object or dict"

def strorlenlist(stringorlist):
    """Returns a string with info about the list and its content
    or name of an object
    or just a plain string if it's neither of the above"""
    if isinstance(stringorlist, list): 
        if stringorlist:
            print_content = str("[1/"+ str(len(stringorlist))+"]:")
            for thing in stringorlist:
                print_content += str(thing) + ", "
            return  print_content[:-2]+"."
    elif isinstance(stringorlist, object):
        return get_name_or_entire_object(stringorlist)
    return str(stringorlist)

#specification of fields for attributes of model 
class AttributeType(Enum):
    STRING = 1
    BOOLEAN = 2
    INTEGER = 3
    MODEL = 4   # used for parent models in FunctionalityType.CREATE_OBJECT
    
def main():
    
    #for debugging
    return

if __name__ == "__main__":
    main()