import sys

import django
from generator import GenerateTarget
from utils.data_validation_utils import sanitize_data_models
from utils.loading_json_utils import get_metadata_all_diagrams, get_run_cls, get_user_types_from_metadata

# creates a models.py file in str(sys.argv[1]) = projectsname/ str(sys.argv[2]) = appname/ folder by filling 
# jinja2template templates/model.py.jinja2
# takes get_run_cls as input data which are the extracted classes from ../../tests/cs3_metadata.json
# Template is searched for in the templates/ dir
def main():
    targetfile = "models.py"
    
    if (len(sys.argv) != 3 or str(sys.argv[1]) == '' or str(sys.argv[2]) == ''  ):
        raise Exception("wrong arguments, call with: project_name app_name")
    
    project_name = str(sys.argv[1]) 
    app_name = str(sys.argv[2])

    metadata_all_diagrams = get_metadata_all_diagrams()

    data = {
        "models": get_run_cls(pre_path_to_run="../", metadata_all_diagrams=metadata_all_diagrams),
        "user_types": get_user_types_from_metadata(metadata_all_diagrams=metadata_all_diagrams)
    }

    data = sanitize_data_models(data)
    
    try:
        GenerateTarget(project_name,app_name,targetfile,data)
        outputPath= "../generated_projects/"+ project_name + "/" + app_name  + "/" + targetfile
        exec(open(outputPath).read())
    except Exception as err:
        if type(err) == SyntaxError:
            print("tried to generate with custom methods but got syntax error: ")
        elif type(err) == django.core.exceptions.ImproperlyConfigured:
            return #succes
        
        print("  " + str(err))
        print("generate with custom methods as comments in "+ str(targetfile))
        GenerateTarget(project_name,app_name,targetfile,data, commented_methods=True)

if __name__ == "__main__":
    main()