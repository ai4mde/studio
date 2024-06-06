#this file contains all the general functions which are used to extract information out of the json metadata
#example: opening json files or parsing general diagrams

from glom import glom
import json

from utils.data_validation_utils import app_name_sanitizer, class_name_sanitizer

def get_metadata_all_diagrams(pre_path_to_runtime_dir = "../",filename = "./tests/runtime.json") -> dict: #cs3
    """Reads all diagrams and application component metadata from filename.
    Looks in dir above first, then the dir above that one and finally in filename so we can use this funciton from different dirs like utils during debugging"""

    with open(pre_path_to_runtime_dir+filename, "r") as json_file:
        metadata_all_diagrams = json.load(json_file)
    return metadata_all_diagrams

def extract_data(metadata_all_diagrams, diagram_type) -> dict:
    """Calls the general extract function with the specific diagram type name"""
    run_data = metadata_all_diagrams["diagram"][diagram_type] 
    return run_data

def get_user_types_from_metadata(metadata_all_diagrams = get_metadata_all_diagrams()) -> list:
    """returns user_types list, which is a list of app_names for which there exists a class of the same name."""
    user_types = []
    for app_name in get_apps(metadata_all_diagrams):
        if app_name in get_models(metadata_all_diagrams):
            user_types.append(app_name)
    return user_types

def get_apps(metadata_all_diagrams = get_metadata_all_diagrams()) -> list:
    """returns a list of all application names found in app components"""
    apps = []
    dicts = get_dict_from_metadata("UI", metadata_all_diagrams)
    for appdict in dicts:
        apps.append(app_name_sanitizer(appdict["name"]))
    return apps

def get_models(metadata_all_diagrams = get_metadata_all_diagrams()) -> list:
    """returns a list of all class names found in class diagram"""
    classes = []
    dicts = get_dict_from_metadata("class", metadata_all_diagrams)
    for class_dict in dicts["nodes"]["class"]:
        classes.append(class_name_sanitizer(class_dict["name"]))
    return classes

def build_parent_models_dict_from_metadata_for_class_with_node_id(node_id, metadata_all_diagrams) -> dict:
    """Looks for composition or association or generalization in class diagram and returns dict with parent model info. 
    key: parent_model_id value: class diagram metadata of parent model.
    EXAMPLE: (from) Customer is parent of (to) Shopping Cart.
    (for generalization it's reversed) User (to) is parent of Customer (from)"""
    parent_model_dict = {}
    for edge in metadata_all_diagrams["diagram"]["class"]["edges"]:
        parent_id = ""
        if (edge["type"] == "composition" or edge["type"] == "association") and node_id == edge["data"]["to"]:
            parent_id = edge["data"]["from"]
            parent_model_dict[parent_id] = extract_node_data_from_diagram_metadata_with_id(metadata_all_diagrams["diagram"]["class"],parent_id)
        elif edge["type"] == "generalization" and node_id == edge["data"]["from"]:
            parent_id = edge["data"]["to"]
            parent_model_dict[parent_id] = extract_node_data_from_diagram_metadata_with_id(metadata_all_diagrams["diagram"]["class"],parent_id)
    return parent_model_dict

def get_parent_models_of_model(class_name, metadata_all_diagrams = get_metadata_all_diagrams()) ->list:
    """returns a list of class names found in class diagram which are parent models of @param class_name"""
    parent_models = []
    parent_model_ids = []
    class_dicts = get_dict_from_metadata("class", metadata_all_diagrams)
    for class_dict in class_dicts["nodes"]["class"]:
        if class_name_sanitizer(class_dict["name"]) == class_name:
            parent_model_ids = [parent_id for parent_id in build_parent_models_dict_from_metadata_for_class_with_node_id(class_dict["id"],metadata_all_diagrams)]
    for parent_model_dict in class_dicts["nodes"]["class"]:
        if parent_model_dict["id"] in parent_model_ids:
            parent_models.append(class_name_sanitizer(parent_model_dict["name"]))
    return parent_models

def get_models_without_parents(metadata_all_diagrams = get_metadata_all_diagrams()) -> list:
    """returns a list of all models without parent models in class diagram"""
    classes = []
    dicts = get_dict_from_metadata("class", metadata_all_diagrams)
    for class_dict in dicts["nodes"]["class"]:
        if get_parent_models_of_model(class_name_sanitizer(class_dict["name"]), metadata_all_diagrams) == []:
            classes.append(class_name_sanitizer(class_dict["name"])) 
    return classes

def get_child_models_of_model(class_name, metadata_all_diagrams = get_metadata_all_diagrams()) -> list:
    """returns a list of all child models of model with @param class_name found in class diagram"""
    child_models = []
    child_ids = []
    class_dicts = get_dict_from_metadata("class", metadata_all_diagrams)
    class_adjacency_dicts = build_adjacency_dicts_from_class_dicts(class_dicts)
    for class_dict in class_dicts["nodes"]["class"]:
        if class_name_sanitizer(class_dict["name"]) == class_name:
            child_ids = [ child_ids for child_ids in class_adjacency_dicts[class_dict["id"]] ]
    for child_model_dict in class_dicts["nodes"]["class"]:
        if child_model_dict["id"] in child_ids:
            child_models.append(class_name_sanitizer(child_model_dict["name"]))
    return child_models

def get_app_components(metadata_all_diagrams = get_metadata_all_diagrams()) -> list[dict]:
    """Sanitizes app_names and returns a list of all application components dicts based on spec in UI_data."""
    new_dicts = [] 
    old_dicts = get_dict_from_metadata("UI", metadata_all_diagrams)
    for app in old_dicts:
        new_app = app
        new_app["name"] = app_name_sanitizer(app["name"]) 
        new_dicts.append(new_app)
    return new_dicts

def get_app_dict(appname, metadata_all_diagrams= get_metadata_all_diagrams()) -> dict:
    """returns a dict of app component with appname from UI_data"""
    dicts = get_dict_from_metadata("UI", metadata_all_diagrams)
    for appdict in dicts:
        if (app_name_sanitizer(appdict["name"]) == appname):
            return appdict
    raise Exception("appname: " + appname+ " is not in known apps: "+ str(get_apps()))

def get_styling_from_metadata(appname, metadata_all_diagrams = get_metadata_all_diagrams()) -> dict:    
    """returns a list of all styling found in app component with name = appname. Should also use applicaions_data ideally"""
    #Load modern by default
    AI4MDE_logo = "data:image/png;base64,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"
    styling = {
                "logo": AI4MDE_logo,
				"type": "modern",
				"radius": "10",
				"text-color": "#1E3F5A",
				"accent-color": "#000000",
				"text-alignment": "left",
				"background-color": "#FFFFFF"
    }
    if appname != "authentication" and appname != "Authentication" :
        if appname in get_apps(metadata_all_diagrams):
            styling = get_app_dict(appname, metadata_all_diagrams)["styling"]
            if "logo" not in styling: 
                styling["logo"] = AI4MDE_logo
        else:
            print("is appname: " + appname+ " in known apps? : "+ str(get_apps(metadata_all_diagrams)))
    return styling

def add_edges(run_classes, diag_edges):
    for edge in diag_edges:
        from_class_id = edge["data"].get("from")
        to_class_id = edge["data"].get("to")

        from_class = next((cls for cls in run_classes if cls.get("id") == from_class_id), None)
        to_class = next((cls for cls in run_classes if cls.get("id") == to_class_id), None)

        if from_class and to_class:
            if "associations" not in to_class:
                to_class["associations"] = []

            to_class["associations"].append({"id": from_class_id})

    return run_classes

def get_run_cls(pre_path_to_run = "../", metadata_all_diagrams = {}) -> dict:
    """Gets the class metadata in the old style"""
    if metadata_all_diagrams == {}:
        metadata_all_diagrams = get_metadata_all_diagrams(pre_path_to_run)
    diagram_type = "class"
    run_data = metadata_all_diagrams["diagram"]["class"]["nodes"]
    run_data = add_edges(
        run_data,
        glom(metadata_all_diagrams, "diagram."+diagram_type+".edges", default=[])
    )
    return run_data

def extract_data_attribute_from_node_metadata(node, attribute, nested_under = "data") -> any:
    """Returns a value of attribute on node (which might be) under nested_under variable.
    Node is a part of metadata from diagrams. 
    EXAMPLE: node["data"]["attribute"] """
    value = ""
    if attribute in node:
        value = node[attribute]
    elif nested_under in node:
        value = node[nested_under][attribute]
    return value

def extract_node_data_from_diagram_metadata_with_id(diagram_metadata,node_id, data_attribute="") -> any:
    """returns the data_attribute of the node in diagram with a node_id. 
    Defaults to "": returns entire dict of node.
    EXAMPLE:  diagram_metadata = activity: { "nodes": [ {"name": "action1", "id": 12 ...} ]} , node_id = "12", data_attribute="all"
    result -> {"name": "action1", "id": 12 ...}"""
    for node in diagram_metadata["nodes"]:
        if (node["id"] == node_id):
            if data_attribute == "": return node
            elif data_attribute in node: 
                return extract_data_attribute_from_node_metadata(node,data_attribute)

def parseIntoDict(diagram, Spec) -> dict: 
    """Returns a dictionary of json sorted by type.
    Extracts from a diagram based on the provided spec. example: styling, pages.application for UI format"""
    wholeDict = {} #build the dict with empty lists for each type
    for common in ["id","name"]: #skips if no name is available
        try:
            wholeDict[common] = diagram[common]
        except KeyError:
            pass

    for part in Spec.__dict__: #example part = styling or content.pages or category
        if part == "sub_attributes":
            continue
        if len(Spec.__dict__[part]) == 0: #add actors
            wholeDict[part] = diagram[part] # .append(part_instance)
            continue
        # if part not in wholeDict: #is there a list of categories already?
        wholeDict[part] = [] # this will be [ {atribute1, attribute2} ] like for each category
        if isinstance([categoryDict for categoryDict in diagram[part]][0], dict): #categories in list
            partList = []
            for part_instance in diagram[part]: #all categories
                partList.append(part_instance)            
            wholeDict[part] = partList
            continue
        elif isinstance([styleDictkeys for styleDictkeys in diagram[part]][0], str): #keys of dict styling
            wholeDict[part]= diagram[part] # styling
            continue
        for part_type in Spec.__dict__[part]: #with these attributes
            partDict = {}
            if part_type in Spec.sub_attributes: #add to subkeys
                # partDict = {} #example: one category: {atribute1, attribute2}    
                if part_type not in partDict:
                    partDict[part_type] = [] #pages
                for part_instance in diagram[part]: #all pages
                    for small_part in diagram[part][part_instance]: #single page
                        partDict[part_type].append(small_part) 
            else: #add as whole
                for styleDict in diagram[part]:
                    if isinstance(styleDict, list) : #list of lists ??
                        partDict[part_type] = styleDict
                    elif isinstance(styleDict, dict): #categories in list
                        raise Exception("categories should have been handled before")
                    elif isinstance(styleDict, str): #keys of dict styling
                        raise Exception("styling should have been handled before")
        wholeDict[part].append(partDict)
    return wholeDict

#these two under here are older but do the same but for edges and nodes based on json for class activity and usecase diagram 
def parseEdgesIntoDict(diagram, Spec) -> dict: 
    """Returns a dictionary of Edges sorted by type.
    Extract edges from a diagram based on the provided spec. example: interaction, includes for Use case diagram"""
    edgesDict = {} #build the nodes dict with empty lists for each type except action
    for edge_type in Spec.edge_types: #initialize dict
        if edge_type not in edgesDict:
            edgesDict[edge_type] = [] # list of {atributes}

    for edge in diagram["edges"]:
        edge_type = edge["type"]
        attributeDict = {}
        for direction in ["from","to"]:
             attributeDict[direction] = edge["data"][direction]
        if edge_type in Spec.sub_attributes:
            for edge_attribute in Spec.sub_attributes[edge_type]: #add specific info for nodes
                try:
                    attributeDict[edge_attribute] = edge["data"][edge_attribute] #for example name = edge["data"]["name"]
                except KeyError:
                    try:
                        attributeDict[edge_attribute] = edge[edge_attribute] #for example multiplicity= edge["1", "*"]
                    except KeyError:
                        attributeDict[edge_attribute] = ""

        edgesDict[edge_type].append(attributeDict) #add the edge with its values to dict
    return edgesDict

def parseNodesIntoDict(diagram, Spec) -> dict: 
    """Returns a dictionary of nodes sorted by type.
    Extract nodes from a diagram based on the provided spec like usecases, actors, interactions for Ue case diagram"""
    nodesDict = {} #build the nodes dict with empty lists for each type except action
    for node_type in Spec.node_types: #initialize dict
        if node_type not in nodesDict:
            nodesDict[node_type] = [] # list of {atributes}

    for node in diagram["nodes"]:
        node_type = node["type"]
        attributeDict = {}
        if node_type in Spec.sub_attributes:
            for node_attribute in Spec.sub_attributes[node_type]: #add specific info for nodes
                try:
                    attributeDict[node_attribute] = node["data"][node_attribute] #for example action name = node["name"]
                except KeyError:
                    attributeDict[node_attribute] = ""
                
            if "name" not in Spec.sub_attributes[node_type]: # we take name for granted
                try:
                    attributeDict["name"] = node["data"]["name"]
                except KeyError:
                    attributeDict["name"] = ""

        nodesDict[node_type].append(attributeDict) #add the node with its values to dict
    return nodesDict

from .class_utils import ClassSpec, build_adjacency_dicts_from_class_dicts
from .UI_utils import AUTHSpec, Category, UISpec
from .activity_utils import ActivitySpec
from .usecase_utils import UseCaseSpec

def get_dict_from_metadata(diagram_type, metadata_all_diagrams= get_metadata_all_diagrams(), nodes = True, edges = True) -> dict:
    """matches the type of diagram and returns data as a dictionary based on the spec in utils for that diagram
    for everything that was found in metadata of the diagram. nodes or edges can be dismissed, example: nodes = False """
    match diagram_type:
        case "class":
            spec = ClassSpec()
        case "activity":
            spec = ActivitySpec()
        case "usecase":
            spec = UseCaseSpec()
        case "UI": #todo bandaid for application component.
            UIlist = []
            app_components_metadata = metadata_all_diagrams
            for app in app_components_metadata["application_components"]:
                spec = UISpec()
                if "type" in app and app["type"] == "authentication":
                    #there are some different variables in auth app
                    spec = AUTHSpec()
                app_comp = parseIntoDict(app, spec)
                UIlist.append(app_comp)
            return UIlist #old:    parseIntoDict(get_metadata_all_diagrams(), spec)
        case _:
            raise Exception("unknown metadata format requested: "+ str(diagram_type))

    diagram_dicts = {}

    if nodes:
        diagram_dicts["nodes"] = parseNodesIntoDict(extract_data(metadata_all_diagrams, diagram_type), spec)
    if edges:
        diagram_dicts["edges"]= parseEdgesIntoDict(extract_data(metadata_all_diagrams, diagram_type), spec)
    return diagram_dicts

def get_data_from_dict(wholeDict, spec, requestedData ="application") -> any:
    """searches dict of diagram for data with header == requestedData and returns a list or instance of those types"""
    for part in spec.__dict__:
        if part == requestedData:
            return wholeDict[part]
        
        for part_instance in wholeDict[part]: #all pages
            for part_type in spec.__dict__[part]:#(content).pages
                if part_type == requestedData:
                    return part_instance[part_type]
                if part_type in spec.sub_attributes:
                        for part_attribute in spec.sub_attributes[part_type]: #page.application
                            if part_attribute == requestedData:
                                for data in part_instance[part_type]:
                                    return data[part_attribute]
                                

def get_sections_on_page_from_metadata(page_data, app_dict) -> list:
    """returns a list of all sections_metadata on page"""
    sections_metadata_on_page = []
    for section_id in page_data["sections"]:
        for section_component_metadata in app_dict["section_components"]:
            if section_component_metadata["id"] == section_id:
                sections_metadata_on_page.append(section_component_metadata)
    return sections_metadata_on_page

def get_models_without_creates(metadata_all_diagrams = get_metadata_all_diagrams()) -> list:
    """returns a list of all models without createtable compound sections on application components.
    Only returns models for now"""
    dicts = get_dict_from_metadata("UI", metadata_all_diagrams)
    spec = UISpec()
    models = get_models(metadata_all_diagrams)
    models_without_creates = models
    # for app_dict in dicts:
    #     if app_dict["name"] == "authentication" or app_dict["name"] == "Authentication":
    #         continue
    #     pages_data = app_dict["content"]["pages"] 
    #     for page_data in pages_data:
    #         section_data = get_sections_on_page_from_metadata(page_data, app_dict)
    #         for section_data in section_data:
    #             for model in models:
    #                 functionalities_data = get_functionalities_of_model_in_section(model_name=model,
    #                                                                                 section_data=section_data,
    #                                                                                 app_dict=app_dict)
    #                 if model in models_without_creates and contains_create_functionality(functionalities_data):
    #                     models_without_creates.remove(model)
    return models_without_creates

def get_categories_from_metadata(app_name, metadata_all_diagrams = get_metadata_all_diagrams()) -> list:
    """returns a list of all categories found in app component with name = appname. Should also use UI_data"""
    categories = []
    spec = UISpec()
    if app_name == "authentication" or app_name == "Authentication":
        spec = AUTHSpec()
        #currently, auth apps have no categories
        return categories 
    app_dict = get_app_dict(app_name, metadata_all_diagrams)
    categories_data = get_data_from_dict(app_dict, spec, "categories") #we used to find apps via pages

    for category in categories_data:
        category_object = Category(category["id"], category["name"])
        categories.append(category_object)
    return categories


def main():
    #for debugging
    print("this is all metadata: " + str(get_metadata_all_diagrams()))

if __name__ == "__main__":
    main()