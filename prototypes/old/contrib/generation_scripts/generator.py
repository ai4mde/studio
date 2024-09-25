#this python file will be used to set up generation of table.py, models.py, views.py and urls.py
#In the generation process, the correct json is set up and the main script starts calling smaller genenaration scripts
#then the django project is created in generated_projects folder using generation templates
#from the generation_scripts/templates folder. Metadata from the diagrams is parsed into a table in generate_section_table.py which before individual apps
# Afterwards the data on the section_table is accessed by the smaller python scripts using the jinja2 templates for models.py,
# urls.py views.py and html templates for each app in the project

import sys, jinja2, pathlib
from jinja2 import Environment, FileSystemLoader
from utils.section_component_utils import AttributeType, SectionComponentType
from utils.loading_json_utils import get_run_cls

#checks if path to target file exists and opens and writes to the target file 
def SaveOutput(renderoutput, outputPath="output.py"):
    pathlib.Path(outputPath).parent.mkdir(parents=True, exist_ok=True) 
    with open(outputPath, "w+") as fh:
        fh.write(renderoutput)

#takes a jinja2 template file and data to generate target file in generated_projects/project_name/app_name dir
def GenerateTarget( project_name = "test_forms_project", 
                    app_name = "test_forms_app", 
                    target_name = "views.py", 
                    data = {
                        "models": get_run_cls(),
                        "app_name": "test_forms_app",
                    },
                    is_auth_app = False,
                    commented_methods = False):
    template_dir = "./templates"
    outputPath= "../generated_projects/"+ project_name + "/" + app_name  + "/" + target_name
    if (commented_methods and target_name == "models.py" ):
        template_name = "models_no_method.py.jinja2"
    elif (not is_auth_app):
        template_name = target_name + '.jinja2'    
    else:
        template_name ="auth_" + target_name + ".jinja2"
    
    try:
        #load jinja2 template of file
        env = Environment(loader=FileSystemLoader(template_dir))
        try:
            template = env.get_template(template_name)

        except jinja2.exceptions.TemplateNotFound: #for the html templates, no single file is created and this template is used
            template = env.get_template("template_base.html.jinja2")

    except jinja2.exceptions.TemplateNotFound: #Might use this from parent dir
         #load jinja2 template of file
        env = Environment(loader=FileSystemLoader("./generation_scripts"+template_dir[1:]))
        try:
            template = env.get_template(template_name)
        except jinja2.exceptions.TemplateNotFound: #for the html templates, no single file is created and this template is used
            template = env.get_template("template_base.html.jinja2")

    template.globals['SectionComponentType'] = SectionComponentType #bandaid? this might need to be defined somewehere else
    template.globals['AttributeType'] = AttributeType
    #Render the target with data and save the generated file to outputPath if possible
    SaveOutput(template.render(data), outputPath)

# creates str(sys.argv[3]) = target python file in str(sys.argv[1]) = generated_projectsname/ str(sys.argv[2]) = appname/ folder by filling jinja2template with data
# by default takes the run_cls list as models or data for input as the fourth argument
# run_cls is first created by extracting classes from ../../tests/runtime.json
# Template is searched for in the templates/ dir
def main():
    if len(sys.argv) >= 6 :
        if ( str(sys.argv[1]) != "" and str(sys.argv[2]) != "" and str(sys.argv[3]) != "" and list(sys.argv[4]) != []
            and (sys.argv[5]) != ""):
            GenerateTarget(str(sys.argv[1]),str(sys.argv[2]),str(sys.argv[3]),data=list(sys.argv[4]),is_auth_app=bool((sys.argv[5])))
            return
    
    elif len(sys.argv) >= 5 :
        if ( str(sys.argv[1]) != "" and str(sys.argv[2]) != "" and str(sys.argv[3]) != "" and list(sys.argv[4]) != []):
            GenerateTarget(str(sys.argv[1]),str(sys.argv[2]),str(sys.argv[3]),data=list(sys.argv[4]))
            return
        
    #maybe you want to call this function with default data, then this is sufficient:
    elif (len(sys.argv) >= 4 and str(sys.argv[1]) != "" and str(sys.argv[2]) != "" and str(sys.argv[3]) != "" ):
        GenerateTarget(str(sys.argv[1]),str(sys.argv[2]),str(sys.argv[3]))
        return
    
    
    #if no arguments were given, generate test_forms with default arguments or do
    #raise Exception("wrong arguments, call with: project_name app_name target_python_file_name [input_list] ")
    GenerateTarget()
    return

#in other scripts we usually import generate_target() to specify which files we wish to create, but it can be used like this for debugging
if __name__ == "__main__":
    main()