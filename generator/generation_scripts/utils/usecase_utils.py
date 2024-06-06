#This file is used to generate the generation_table and mostly views.py, including all data necessary for each script to correctly generate it specific part
#and correctly fit into the rest of the generated code
#Here we define usecases which handles all data coming from the Design-Time "application", with its model, sections, category, pages, actor, more to be added..


class UseCaseSpec:
    '''
    This class specifies the UseCase Diagram.
    '''
    def __init__(self):
        self.node_types = ["usecase", "actor"]
        self.edge_types = ["interaction", "inclusion", "extension"]
        self.sub_attributes ={
            "usecase": ["name", "id"] ,
            "actor": ["name", "id"]
            #"interaction": ["isDirected"]
        }

def get_data_of_use_case_with_id_from_dict(use_case_diagram_dict, use_case_id, value = "name"): 
    """returns the specified value of use_case attribute with use_case_id in use_case_diagram,
    EXAMPLE: value in ["id","name"]"""

    for node in use_case_diagram_dict["nodes"]["usecase"]:
        if node["id"] == use_case_id:
            return node[value]

def main():
    raise Exception("unimplemented")

if __name__ == "__main__":
    main()