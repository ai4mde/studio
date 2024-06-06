#This file is used to generate the generation_table which includes all data necessary for each script to correctly generate its specific part
#and correctly fit into the rest of the generated code
#Here we define ActivitySpec which handles all data coming from the activity diagram, with the flow, actions and their attributes, ....


class ActivitySpec:
    '''
    This class specifies the activityDiagram.
    '''
    def __init__(self):
        self.node_types = ["initial", "final", "fork", "merge", "join", "decision", "action"]
        self.edge_types = ["activity"]
        self.sub_attributes ={
            "activity": ["guard", "isDirected"] ,
            "action": [
                "id",
                "role", 
            ]
        }

def get_data_of_action_with_id_from_dict(activity_diagram_dict, action_id, value = "type"): 
    """returns the specified value of action attribute with action_id in activitydiagram,
    EXAMPLE: value in ["id","data","type"]"""

    for node in activity_diagram_dict["nodes"]["action"]:
        if node["id"] == action_id:
            return node[value]
