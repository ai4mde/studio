#This file is used to generate the generation_table and mostly for models.py, including all data necessary for each script to correctly generate its specific part
#of the prototype and correctly fit neatly into the rest of the generated code
#Here we define functions handling all data coming from the class diagram, with its nodes, edges, rootModel, more to be added..

class ClassSpec:
    '''
    This class specifies the activityDiagram.
    '''
    def __init__(self):
        self.node_types = ["class", "enum"] #class and enum data.name is taken for granted
        self.edge_types = ["association", "composition", "generalization"]
        self.sub_attributes ={
            "association": ["multiplicity", "isDirected"] ,
            "class": ["attributes", "id", "methods"] ,
            "enum": ["literals", "name"] ,

                            #  "composition": "isDirected"} #is always directed right?
        }

from .data_validation_utils import check_models_on_table, class_name_sanitizer

def build_adjacency_dicts_from_class_dicts(class_dicts) -> dict:
    """Builds an adjacency dict for classes and their outgoing edges (associations and compositions) on the class diagram.
    Returns a dictionary with keys: class ids. values: dicts 
    The "value: dictionary" has key: relation type value: dict
    That dict has key: relation_id. value: metadata.
    Example: Product (id:23) -> {"24": {"553" : {"type": "association", "from": "24", "to": "553" },  "34":{ "type": "asso.. etc}}}"""
    class_adjacency_dicts = {}

    for class_data in class_dicts["nodes"]["class"]:
        class_adjacency_dicts[class_data["id"]] = {} # create dicts for each node
        #write down nodes of all outgoing edges
        for association in class_dicts["edges"]["association"]:
            if association["from"] == class_data["id"]:
                class_adjacency_dicts[class_data["id"]][association["to"]] = association
        for composition in class_dicts["edges"]["composition"]:
            if composition["from"] == class_data["id"]:
                class_adjacency_dicts[class_data["id"]][composition["to"]] = composition
    return class_adjacency_dicts

def sanitize_models(table):
    """TODO, only calls check model for now"""
    check_models_on_table(table)