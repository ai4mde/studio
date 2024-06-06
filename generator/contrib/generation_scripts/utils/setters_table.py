#this file contains setter functions that act on the section table. 
#Functions for extracting information from diagrams are found in the utils file of the corresponding diagram.

from utils.UI_utils import extract_section_components
from utils.activity_utils import get_data_of_action_with_id_from_dict
from utils.section_component import  SectionComponent
from utils.section_component_utils import CustomMethod, Link, determine_attribute_types_from_metadata
from utils.usecase_utils import get_data_of_use_case_with_id_from_dict
from .class_utils import build_adjacency_dicts_from_class_dicts, sanitize_models
from .loading_json_utils import get_metadata_all_diagrams
from .getters_table import get_child_models_of_model_from_table_with_model_id, get_model_from_table, get_page_name_per_id, get_section_component_metadata_from_table_with_id
from .data_validation_utils import app_name_sanitizer, attribute_name_sanitizer, check_section_component_with_model, class_data_sanitizer, class_name_sanitizer, page_name_sanitizer, section_component_name_sanitizer

#diagrams
def set_metadata_of_diagrams_on_table(table, metadata_all_diagrams = get_metadata_all_diagrams()) -> None:
    """loads the metadata from tests/cs3_metadata_hacked.json and stores it on table"""
    table.metadata_all_diagrams = metadata_all_diagrams

def set_class_names_and_metadata_on_table(table, class_dicts) -> None:
    """adds classes to the table"""
    for cls_metadata in class_dicts["nodes"]["class"]:
        new_class_name = class_name_sanitizer(cls_metadata["name"])
        cls_metadata["name"] = new_class_name
        table.class_names.append(new_class_name)
        for attribute_data in cls_metadata["attributes"]:
            attribute_data["name"] = attribute_name_sanitizer(attribute_data["name"])
        table.class_data_per_name[new_class_name] = cls_metadata

def extend_class_data_on_table_with_adjacency_lists(table, class_adjacency_lists) -> None:
    """First extends classes with adjacency list and then extends all classes with parent and child models using it"""
    parent_model_buffer = {}
    for class_name in table.class_data_per_name:
        class_id = table.class_data_per_name[class_name]["id"]
        parent_model_buffer[class_id] = []

    #set adjacency list for all class_ids and build parent models
    for class_name in table.class_data_per_name:
        class_id = table.class_data_per_name[class_name]["id"]
        adjacent_classes = class_adjacency_lists[class_id]
        for outgoing_class in adjacent_classes:
            parent_model_buffer[outgoing_class].append(class_name)
        table.class_data_per_name[class_name]["adjacency_list"] = adjacent_classes

    for class_name in table.class_data_per_name:
        class_id = table.class_data_per_name[class_name]["id"]
        adjacent_classes = class_adjacency_lists[class_id]
        table.class_data_per_name[class_name]["child_models"] = get_child_models_of_model_from_table_with_model_id(table, model_id=class_id)
        table.class_data_per_name[class_name]["parent_models"] = parent_model_buffer[class_id]
        table.class_data_per_name[class_name].pop("adjacency_list", None) #not necessary but cleans up nicely
        

def set_class_data_on_table(table, class_dicts) -> None:
    """Sets class_data of table. Like all known relations and attributes (their types and defaults)
    NOTE: No support for multiplicities yet"""
    set_class_names_and_metadata_on_table(table, class_dicts)
    class_adjacency_lists = build_adjacency_dicts_from_class_dicts(class_dicts)
    extend_class_data_on_table_with_adjacency_lists(table, class_adjacency_lists)

    #update parent models and attributes
    for cls_name in table.class_data_per_name:
        table.class_data_per_name[cls_name] = class_data_sanitizer(table.class_data_per_name[cls_name])
    
    sanitize_models(table)

#applications
def set_app_names_on_table(table, app_names : list[str]):
    table.app_names = app_names

#pages
def set_page_data_per_app_and_santize_page_names(table) -> None:
    """Creates a dict with page data per app. 
    The pages are themselves dicts with their own names as keys in the app dict.
    Pages are extracted here for the first time from the metadata so their names are sanitized.
    Assumes application_components are extracted"""
    pagesPerApp = {}
    for app in table.application_components:
        app_name =app["name"]
        #initialize pagesPerApp
        if app["name"] not in pagesPerApp:
            pagesPerApp[app["name"]] = {}
            
        if app["name"] == "authentication" or app["name"] == "Authentication": 
            continue
        for page in app["content"]["pages"]:
            page["name"] = page_name_sanitizer(page["name"]+ app_name_sanitizer(app_name).lower())
            pagesPerApp[app["name"]][page["name"]] = page
    table.page_data_per_app = pagesPerApp

def create_render_for_page_on_table(table,app_name,page_name) -> None:
    """makes new render functions on table and sets up how to handle generation"""
    rendername = "render_" + page_name
    rendername = page_name_sanitizer(rendername)
    match page_name:
        case "home":
            table.render_per_app_and_page[app_name][page_name] = rendername
            #do something different here for default handling
            pass
        case ["login", "authentication"]:
            table.render_per_app_and_page[app_name][page_name] = rendername
            pass
        case _:
            if page_name not in table.render_per_app_and_page[app_name]:
                table.render_per_app_and_page[app_name][page_name] = rendername
    return rendername

def set_page_renders_on_table(table) -> None:
    """Sets the render_per_app_and_page dict on table.
    calls function to creates renders.
    Assumes application component has been extracted"""
    for app in table.application_components:
        app_name = app["name"]
        if app_name not in table.render_per_app_and_page:
            table.render_per_app_and_page[app_name] = {}
            
        if app_name == "authentication" or app_name == "Authentication":
            continue
        for page in app["content"]["pages"]:
            table.render_per_app_and_page[app_name][page["name"]] = create_render_for_page_on_table(table,app_name,page["name"])

def set_home_render_on_table(table,app_name,page_name):
    """Creates home_render for page_name for and and sets table.home_renders[app_name]"""
    set_render = create_render_for_page_on_table(table,app_name,page_name)
    table.home_renders[app_name] = set_render

def set_home_pages_and_renders(table):
    """Sets the first page found as homepage if none of them with name "home" is found
    Unused bandaid for now. Can use activity data alongside UI to create initial homepage, 
    todo unless authentication is turned on.
    """
    for app in table.application_components:
        app_name = app["name"]
        
        if app_name == "authentication" or app_name == "Authentication":
            table.home_pages[app_name] = ""
            set_home_render_on_table(table,app_name,"")
            continue

        set_page_name = app["content"]["pages"][-1]["name"] #start at back so not all are home
        for page in app["content"]["pages"]:
            page_name = page["name"] 
            if page_name == "home":
                set_page_name = "home"
                break
        table.home_pages[app_name] = set_page_name
        set_home_render_on_table(table,app_name,page_name)

#section_components
def set_section_component_data_on_table(table, section_components_metadata) -> None:
    """ Sets section_component_data_per_id dict on table with metadata as value"""
    for section_component_data in section_components_metadata:
        section_component_data["name"] = section_component_name_sanitizer(section_component_data["name"])
        table.section_component_data_per_id[section_component_data["id"]] = section_component_data

def set_default_model_on_section_component_object(table,new_section_component_object) -> None:
    """Looks at the first model in classes that is also in name and sets model as that one
    Also sets parent models of found model"""
    for model_id in new_section_component_object.classes:
        model_data = get_model_from_table(table,model_id=model_id)
        new_model_name = model_data["name"]
        
        #find model or overwrite with first model name of given classes mentioned in section name
        if new_model_name in new_section_component_object.name:
            position_new_model_name = new_section_component_object.name.find(new_model_name)
            position_other_model_name = -1
            if "model" in  new_section_component_object.__dict__ and new_section_component_object.model != None and new_section_component_object.model != "":
                position_other_model_name = new_section_component_object.name.find(new_section_component_object.model)
            if position_other_model_name == -1 or position_new_model_name <= position_other_model_name:
                setattr(new_section_component_object, "model", new_model_name)
                setattr(new_section_component_object, "parent_models", model_data["parent_models"]) #NOTE: only sets parent model of primary model
                setattr(new_section_component_object, "derived_attributes", model_data["derived_attributes"]) #NOTE: only sets parent model of primary model

def exend_section_component_with_custom_methods_from_class_data(table, new_section_component_object):
    """delete the iterable custom methods not on section"""
    model_data = get_model_from_table(table,model_name=new_section_component_object.model)
    new_model_name = model_data["name"]
    new_custom_methods = []
    for iterable_custom_method_data in new_section_component_object.custom_methods:
        new_custom_method = CustomMethod(iterable_custom_method_data["name"], new_model_name, True)
        if new_custom_method.method_name not in [method.method_name for method in new_custom_methods]:    
            new_custom_methods.append(new_custom_method)
    setattr(new_section_component_object, "custom_methods", new_custom_methods)

    #set model methods
    if "custom_methods" in model_data:
        for cust_meth in model_data["custom_methods"]:
            new_custom_method = CustomMethod(cust_meth, new_model_name, False)
            if new_custom_method.method_name not in [method.method_name for method in new_custom_methods]:
                new_custom_methods.append(new_custom_method)
    setattr(new_section_component_object, "custom_methods", new_custom_methods)

def extend_section_with_class_data(table,new_section_component_object) -> None:
    """Updates section_component objects on table with class data"""
    #set model and parent model
    if "model" not in new_section_component_object.__dict__ or not new_section_component_object.model:
        set_default_model_on_section_component_object(table,new_section_component_object)
    elif new_section_component_object.model not in table.class_names:
        model_name = get_model_from_table(table,model_id=new_section_component_object.model)["name"]
        setattr(new_section_component_object, "model", model_name) 
    
    model_data = get_model_from_table(table,model_name=new_section_component_object.model)
    model_attributes = [attr_name for attr_name in model_data["attributes"]]

    #set new custom_method object
    exend_section_component_with_custom_methods_from_class_data(table, new_section_component_object)

    #setup attributes, attributes_types, updateable_attributes
    if new_section_component_object.attributes == []:
        setattr(new_section_component_object, "attributes", model_attributes )
        setattr(new_section_component_object, "attribute_types", model_data["attributes"])

    #add attribute types for all attributes aleady known
    new_attributes = []
    new_attribute_types = {}
    new_updateable_attributes = {}
    new_derived_attributes = model_data["derived_attributes"]

    for class_id in new_section_component_object.classes:
        if class_id == model_data["id"]: #skip self
            continue
        relation_model_data = get_model_from_table(table,model_id=class_id)
        new_attributes.append(relation_model_data["name"])
        new_attribute_types[relation_model_data["name"]] = "model"
    
    for attribute_from_metadata in new_section_component_object.attributes:
        if isinstance(attribute_from_metadata,dict):
            if attribute_from_metadata["class_id"] != model_data["id"] or attribute_from_metadata["name"] not in model_data["attributes"]: 
                continue #skip the attribute because it should have been removed (it's a remnant from editor, old class or changed attribute)
                # raise Exception("class_id("+str(attribute_from_metadata["class_id"])+") on "+str(attribute_from_metadata["name"])+" does not match model of attribute: "+ str(model_data))
            if attribute_from_metadata["name"] not in new_attributes:
                new_attributes.append(attribute_from_metadata["name"])
                new_attribute_types[attribute_from_metadata["name"]] = model_data["attributes"][attribute_from_metadata["name"]]
                new_updateable_attributes[attribute_from_metadata["name"]] = True
        if attribute_from_metadata not in model_attributes:
            continue
        if attribute_from_metadata not in new_attributes:
            new_attributes.append(attribute_from_metadata)
            new_attribute_types[attribute_from_metadata] = model_data["attributes"][attribute_from_metadata]
            new_updateable_attributes[attribute_from_metadata] = True

    new_attribute_types = determine_attribute_types_from_metadata(new_attribute_types)

    setattr(new_section_component_object, "attributes", new_attributes)
    setattr(new_section_component_object, "attribute_types", new_attribute_types) #overwrites with first model name found in section name
    setattr(new_section_component_object, "updateable_attributes", new_updateable_attributes) 
    setattr(new_section_component_object, "derived_attributes", new_derived_attributes)

    if not new_section_component_object.hasUpdate:
        for attr in new_section_component_object.updateable_attributes:
            new_section_component_object.updateable_attributes[attr] = False
    check_section_component_with_model(table, new_section_component_object)

def extend_section_with_links(table,new_section_component_object) -> None:
    """set new link object"""
    new_links = []
    for link_data in new_section_component_object.links:
        new_link = Link(text=link_data["text"], page_name_out=get_page_name_per_id(table,link_data["link"]), app_name_out=new_section_component_object.app)
        new_links.append(new_link)
    setattr(new_section_component_object, "links", new_links)


#TODO change dict keys to id instead of name
def set_section_component_objects_on_table(table, page_name, page_data, app_name) -> None:
    """Creates and sets section_component objects for generation and also fills section_components_per_app_and_page dict on table.
    Loads all section_component_data from @param page_data
    Extend (with @param page_name on @param app_name and functionalities) and sets section_component objects on table.
    Also extends dicts on table and functionalities to with section objects."""
    #Load section data and create objects
    for section_component_id in page_data["sections"]:
        new_section_component = SectionComponent()
        try:
            section_component_data = get_section_component_metadata_from_table_with_id(table,section_component_id)
        except Exception:
            continue

        #extend section_components with data
        new_section_component.extend_with_all_data( section_component_data,
                                                    page_data=page_name, 
                                                    app_data=app_name)
        #Extends attributes and custom methods
        extend_section_with_class_data(table,new_section_component)

        #Extends links
        extend_section_with_links(table,new_section_component)
        
        #set on table
        table.section_components_per_app_and_page[app_name][page_name].append(new_section_component)
        table.section_components.append(new_section_component)

def combine_UI_data_on_table(table) -> None:
    """Innitializes and fills the dictionaries about UI data for generation.
    Loads apps and pages and initializes section_components_per_app_and_page dict and section_components_per_app_and_page list.
    Calls set_section_component_objects_on_table to create and set objects.
    Assumes application_components have been set, app_names, page_data_per_app, section_components_per_id."""
    for app in table.application_components:
        app_name = app["name"]
        table.section_components_per_app_and_page[app_name] = {}
        
        if app_name == "authentication" or app_name == "Authentication":
            continue

        for page_name in table.page_data_per_app[app_name]:
            page_data = table.page_data_per_app[app_name][page_name]
            table.section_components_per_app_and_page[app_name][page_name] = []

            #Create and set section component objects on table
            set_section_component_objects_on_table(table, page_name, page_data, app_name)

def set_UI_data_on_table(table, application_components) -> None:
    """Adds application_components, pages, sections and functionalities to the table.
    Creates section_component objects and functionality objects.
    Adds functionalities to section_component objects and those to pages and apps.
    NOTE: Only section components found on pages are created as objects, but section component data is always stored"""
    table.application_components = application_components
    set_app_names_on_table(table, [app["name"] for app in application_components])
    set_page_data_per_app_and_santize_page_names(table)
    set_section_component_data_on_table(table, extract_section_components(application_components))
    set_page_renders_on_table(table)
    combine_UI_data_on_table(table)

    
def extend_section_objects_with_behavioural_data_on_table(table, activity_diagram_dict, use_case_diagram_dict) -> None:
    """Sets the matching usecases and actions on a section
    Looks through sections to find sections with a action and a usecase, and matches their names 
    todo unless authentication is turned on.
    """
    
    for app_data_key in table.section_components_per_app_and_page:
        if app_data_key == "authentication" or app_data_key == "Authentication":
            continue
        for page_data_key in table.section_components_per_app_and_page[app_data_key]:
            
            for sec_object in table.section_components_per_app_and_page[app_data_key][page_data_key]:
                for action_id in sec_object.actions:
                    action_name = get_data_of_action_with_id_from_dict(activity_diagram_dict, action_id, "name")
                    for use_case_id in sec_object.use_cases:
                        use_case_name = get_data_of_use_case_with_id_from_dict(use_case_diagram_dict,use_case_id, "name")
                        if use_case_name and use_case_name == action_name:
                            # print("found match for "+ str(action_name))
                            # print("  ids: action:" + action_id + " and use case:" + use_case_id + " on page: "+page_data_key + " section: " + sec_object.name)
                            # print()
                            pass
                            #TODO
                            # create_query(sec_object,action_id)
    raise Exception("unimplemented")