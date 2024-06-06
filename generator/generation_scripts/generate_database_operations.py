import sys
from generator import GenerateTarget
from utils.data_validation_utils import sanitize_data_models
from utils.loading_json_utils import get_metadata_all_diagrams, get_models_without_creates, get_models_without_parents, get_run_cls, get_user_types_from_metadata

# creates a generate_database_operations.py file in str(sys.argv[1]) = projectsname/ folder by filling 
# jinja2template templates/generate_database_operations.py.jinja2 with models.py data and list_of_models_without_creates.
# First generate objects from list without parents like now, only skip user types
# Then, also, object with parents should be created, after their parents have been created 
# extracted classes from ../../tests/cs3_metadata.json
# Template is searched for in the templates/ dir
def main():
    targetfile = "database_operations.py"
    
    if (len(sys.argv) <= 1 or str(sys.argv[1]) == ''):
        raise Exception("wrong arguments, call with: project_name ")
    
    generate_these_models = {}
    project_name = str(sys.argv[1])
    metadata_all_diagrams = get_metadata_all_diagrams("../")
    list_of_models_without_creates = get_models_without_creates(metadata_all_diagrams)
    user_types = get_user_types_from_metadata(metadata_all_diagrams)
    list_of_models_without_parents = get_models_without_parents(metadata_all_diagrams)
    count = 1
    #TODO add graph traversal for class diagram. increasing count for each level deeper
    generate_these_models[count] = []

    for model_without_create in list_of_models_without_creates:
        if model_without_create in user_types or model_without_create == "User" or model_without_create == "user":
            #create default users another way todo
            continue
        if model_without_create in list_of_models_without_parents:
            generate_these_models[count].append(model_without_create)
            print("create new "+ model_without_create)
    
    # data_of_models = sanitize_data_models(get_run_cls(pre_path_to_run="../"))

    data = {
        "models": get_run_cls(pre_path_to_run="../"), # <-old, the new version uses ^ : data_of_models,
        "list_of_models_without_creates": generate_these_models[1],
        
    }

    data = sanitize_data_models(data)
    
    GenerateTarget(project_name,"../"+project_name,targetfile,data)

if __name__ == "__main__":
    main()