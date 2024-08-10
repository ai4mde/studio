#this file contains getter functions that act on the section table

#classes
def get_models_per_app_name(table, app_name):
    """NEW FUNCTION, only compound section models on page!
    returns the list of classes accessed by an app as a dict per page_name
    returns Dict[page_name : str, model_names : list[str]]
    """
    models_per_page = {}
    for page_name in table.section_components_per_app_and_page[app_name]:
        page_list = []
        for section_component in table.section_components_per_app_and_page[app_name][page_name]:
            page_list.append(section_component.model)
            if "parent_model" not in section_component.__dict__:
                continue 
            for parent_model in section_component.parent_models:
                page_list.append(parent_model)
        models_per_page[page_name] = page_list
    return models_per_page

def get_class_name_from_table_with_class_id(table, class_id):
    for class_name in table.class_data_per_name:
        if table.class_data_per_name[class_name]["id"] == class_id:
            return class_name
    raise Exception("class with id: "+class_id + " not found on table")

def get_model_from_table(table, section_name = "", section_id = "", model_name = "", model_id = ""):
    """Looks in table if model name is known and returns model data. 
    If no model name is given, looks for model of section with name or id instead.
    If only a subset of attributes of model are in attributes on section, return model data with only those attributes.
    NOTE: returns None if no table is given"""
    if "class_data_per_name" not in table.__dict__:
        raise Exception("Class data is missing from table") 
    
    if model_id != "":
        for found_model_name in table.class_data_per_name:
            if table.class_data_per_name[found_model_name]["id"] == model_id:
                model_name = found_model_name
    if model_name in table.class_data_per_name:
        return table.class_data_per_name[model_name]

    for section in table.table:
        if "model" not in section.__dict__:
            raise Exception("section " + str(section) + " lacks model")

        if not ("attributes" in section.__dict__ and "attribute_types" in section.__dict__ and "id" in section.__dict__):
            raise Exception("Important attributes of " + str(section) + " are not set")
        
        if (section_id == "" and "name" in section.__dict__ and section.name == section_name 
        ) or section.id == section_id:
            return section.attribute_types
    raise Exception("in none of the sections on table, model:  -" + str(model_name) + "- was found")


def get_child_models_of_model_from_table_with_model_id(table, model_id) -> list[str]:
    model = get_model_from_table(table=table,model_id=model_id)
    child_models = []
    if "adjacency_list" not in model:
        raise Exception("adjacency_list for model with id:  " + str(model_id) + " could be found")
    for child_id in model["adjacency_list"]:
        child_models.append(get_class_name_from_table_with_class_id(table,child_id))
    return child_models

def get_parent_models_of_model_from_table_with_model_name(table, model_name) -> list[str]:
    model = get_model_from_table(table=table,model_name=model_name)
    if "parent_models" not in model:
        raise Exception("No parent models loaded yet for model: "+ str(model))
    return model["parent_models"]

#home pages and entries
def get_home_entry_for_app_from_table(table, app_name : str):
    """Looks in home_entries dictionary with key: @param app_name and returns value: home entry. 
    Or blank if appname == authentication"""
    if app_name == "authentication" or app_name == "Authentication":
        return ""
    try:
        return table.home_entries[app_name]
    except (TypeError, AttributeError, KeyError) as err:
        # pass
        #homepage not loaded yet
        raise err

#actors and apps
def get_actors_from_table(table):
    return table.actors

def get_applications_from_table(table):
    """returns a list of app_names. looking for app_components? try get_application_components"""
    return table.app_names

def get_user_types_from_table(table):
    """returns user_types list, which is a list of app_names for which there exists a class of the same name. 
    """
    user_types = []
    for app_name in table.app_names:
        if app_name in table.class_names:
            user_types.append(app_name)
    return user_types

def get_application_component_from_table_with_name(table, appname):
    """returns the application component corresponding to app with appname"""
    for app in table.application_components:
        if app["name"] == appname:
            return app
    raise Exception("no application component on table with name = "+ appname)

#pages
def get_page_names_on_app_from_table(table,app_name) -> list:
    return list(table.page_data_per_app[app_name].keys())

def get_data_all_pages_for_app_from_table(table,app_name) -> dict:
    return table.page_data_per_app[app_name]

def get_page_data_per_app_from_table_with_name(table,app_name,page_name):
    pages = table.page_data_per_app[app_name]
    for page_data in pages:
        if page_data["name"] == page_name:
            return page_data

def get_pages_names_from_table(table):
    """returns a list of all pages"""
    pages_names = []
    for app_dict in table.application_components:
        if app_dict["name"] == "authentication" or app_dict["name"] == "Authentication":
            continue
        for page_data in app_dict["content"]["pages"]:
            pages_names.append(page_data["name"]) 
    return pages_names

def get_pages_from_table(table):
    """returns a list of all pages"""
    pages = []
    for app_dict in table.application_components:
        if app_dict["name"] == "authentication" or app_dict["name"] == "Authentication":
            continue
        for page_data in app_dict["content"]["pages"]:
            pages.append(page_data) 
    return pages

def get_page_name_per_id(table,page_id) -> str:
    pages = get_pages_from_table(table)
    for page in pages:
        if page["id"] == page_id:
            return page["name"]
    raise Exception("no page with id: "+ str(page_id) + " could be found")

def get_section_components_on_page_from_table(table,app_name,page_name):
    """returns the sections of a page"""
    try:
        return table.section_components_per_app_and_page[app_name][page_name]
    except (Exception, AttributeError, KeyError, ValueError ):
        raise Exception("no sections on app_name: "+ app_name+ " page_name: "+ page_name)

from .table_utils import get_name_or_entire_object

#section components
def get_sections_components_page_dict_with_app_name_from_table(table, app_name) -> dict[str, list]:
    """returns the compound sections list as a dict per page_name and section name in lower case"""
    compound_sections = {}
    for page_name in table.section_components_per_app_and_page[app_name]:
        page_list = []
        for section_component in table.section_components_per_app_and_page[app_name][page_name]:
            section_component.name = section_component.name.lower()
            page_list.append(section_component)
        compound_sections[page_name] = page_list
    return compound_sections

def get_list_of_section_components_on_app_from_table_with_app_name(table, app_name) -> list:
    """returns all sections of app with names in lower case"""
    compound_sections = []
    for page_name in table.section_components_per_app_and_page[app_name]:
        for section_component in table.section_components_per_app_and_page[app_name][page_name]:
            section_component.name = section_component.name.lower()
            compound_sections.append(section_component)
    return compound_sections

def get_section_component_from_table(table, id = "", name= "", app = "", page = "", col = -1, row = -1):
    """Returns the first section component object that matches @param id, name, or app-page-row-col combination.
    Ignores section components without names or ids.
    TODO change name to id for dict on table. add validation for col and row on params of page."""
    
    for sec in table.section_components:
        if "id" not in sec.__dict__ or "name" not in sec.__dict__:
            #weird section component object
            continue 
        if "app" in sec.__dict__ and "page" in sec.__dict__:
            if not (col > 0 and row > 0): #add more validation and move to data_validation_utils
                pass #weird call
            else:
                for page_section in table.section_components_per_app_and_page[app][page]:            
                    if "col" not in sec.__dict__ or "row" not in sec.__dict__:
                        #weird section component object
                        continue 
                    if page_section.col == col and page_section.row == row:
                        if id != "":
                            if page_section.id != id:
                                raise Exception("There are two sections at (r"+ str(row) +",c" + str(col) +") on "+ app + " "+ page +": "+
                                                    get_name_or_entire_object(sec) + " and " +  get_name_or_entire_object(page_section) )
                        else: 
                            id = page_section.id
        if sec.id == id or sec.name == name:
            return sec

def get_section_component_metadata_from_table_with_id(table,section_id) -> str:
    if section_id in table.section_component_data_per_id:
        return table.section_component_data_per_id[section_id]
    raise Exception("No section component found in metadata with id: "+ str(section_id))

def get_section_components_from_table(table):
    return table.section_components