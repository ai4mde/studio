import sys
import os
from jinja2 import Environment, FileSystemLoader
from utils.section_component import SectionComponent
from utils.section_table import SectionTable
from utils.getters_table import get_user_types_from_table
from utils.loading_json_utils import get_categories_from_metadata, get_styling_from_metadata
from utils.section_component_utils import AttributeType, CustomMethod, Link, SectionText, SectionTextTag, SectionComponentType
from utils.getters_table import get_sections_components_page_dict_with_app_name_from_table


def generate_css(project_name : str, app_name: str) -> None:
    # print("Generating style.css for application " + app_name)

    # Set template parameters
    styling = get_styling_from_metadata(appname = app_name)

    # Retrieve template
    env = Environment(loader=FileSystemLoader("./templates"))
    try:
        template = env.get_template("style-" + styling['type'] + ".css.jinja2")
    except:
        raise Exception("Failed to resolve styling Jinja2 template")

    # Fill in template
    output = template.render(logo=styling['logo'], text_color=styling['text-color'], background_color=styling['background-color'], accent_color=styling['accent-color'], radius=styling['radius'], text_alignment=styling['text-alignment'])
    
    # Write output
    os.makedirs(os.path.dirname("../generated_projects/" + project_name + "/" + app_name  + "/static/" + app_name + "/"), exist_ok=True)
    with open("../generated_projects/" + project_name + "/" + app_name  + "/static/" + app_name + "/" + app_name + "-style-" + styling['type'] + ".css", "w+") as fh:
        fh.write(output) 


def generate_basehtml(project_name : str, app_name : str, table : SectionTable, has_auth_app : bool) -> None:
    # print("Generating base.html for application " + app_name)

    # Set template parameters
    category_list = get_categories_from_metadata(app_name = app_name)
    category_names = [category.name for category in category_list]
    styling = get_styling_from_metadata(appname = app_name)
    pages_from_app = table.page_data_per_app[app_name]

    # Retrieve template
    env = Environment(loader=FileSystemLoader("./templates"))
    try:
        template = env.get_template("base.html.jinja2")
    except:
        raise Exception("Failed to resolve base.html Jinja2 template")
    
    # Fill in template
    output = template.render(appname = app_name, categories = category_names, type = styling['type'], pages_from_app = pages_from_app, logo=styling['logo'], has_auth_app=has_auth_app)

    # Write output
    with open("../generated_projects/" + project_name + "/" + app_name  + "/templates/" + app_name + "_base.html", "w+") as fh:
        fh.write(output)


def generate_auth_page(project_name : str, app_name: str, table : SectionTable) -> None:
    # print("Generating customized authentication page")

    # Set template parameters
    user_types = get_user_types_from_table(table)

    # Retrieve template
    env = Environment(loader=FileSystemLoader("./templates"))
    try:
        template = env.get_template("auth_html_template.html.jinja2")
    except:
        raise Exception("Failed to resolve authentication HTML Jinja2 template")
    
    # Fill in template
    output = template.render(project=project_name, user_types=user_types)

    # Write output
    with open("../generated_projects/" + project_name + "/" + app_name  + "/templates/authentication/login.html", "w+") as fh:
        fh.write(output)


def generate_page(project_name : str, app_name: str, page_name : str, table : SectionTable) -> None:
    # print("Generating HTML page: " + page_name + " for application " + app_name)

    # Retrieve template
    env = Environment(loader=FileSystemLoader("./templates"))
    try:
        template = env.get_template("html_template.html.jinja2")
    except:
        raise Exception("Failed to resolve HTML Jinja2 template")
    
    # Set template globals
    template.globals['SectionType'] = SectionComponentType
    template.globals['SectionTextTag'] = SectionTextTag
    template.globals['SectionText'] = SectionText
    template.globals['AttributeType'] = AttributeType
    template.globals['SectionComponent'] = SectionComponent
    template.globals['Link'] = Link
    template.globals['CustomMethod'] = CustomMethod
    
    # Set template parameters
    page_data = table.page_data_per_app[app_name][page_name]
    nr_rows = int(page_data["rows"])
    nr_columns = int(page_data["columns"])

    # Fill in template
    section_components = get_sections_components_page_dict_with_app_name_from_table(table, app_name)
    output = template.render(section_components_on_page=section_components[page_name],
                            nr_rows=nr_rows, nr_columns=nr_columns, app_name=app_name)
    
    # Write output
    with open("../generated_projects/" + project_name + "/" + app_name  + "/templates/" + str(page_data["name"]) + ".html", "w+") as fh:
        fh.write(output)


def generate_home_page(project_name : str, app_name : str) -> None:
    # print("Generating HTML home page for application " + app_name)

    # Retrieve template
    env = Environment(loader=FileSystemLoader("./templates"))
    try:
        template = env.get_template("app_homepage.html.jinja2")
    except:
        raise Exception("Failed to resolve home page HTML Jinja2 template")
    
    output = template.render(app_name=app_name)
    with open("../generated_projects/" + project_name + "/" + app_name  + "/templates/" + app_name + "_home.html", "w+") as fh:
        fh.write(output)


def generate_pages(project_name : str, app_name : str, table : SectionTable) -> None:
    # print("Generating HTML pages for application" + app_name)
    for page_name in table.page_data_per_app[app_name]:
        generate_page(project_name=project_name, app_name=app_name, page_name=page_name, table=table)
    generate_home_page(project_name=project_name, app_name=app_name)
    

# creates a urls.py file in str(sys.argv[1]) = generated_projectsname/ str(sys.argv[2]) = appname/ folder by filling jinja2template with data
# takes run_cls as data which is first created by extracting classes from ../../tests/runtime.json
# Template is searched for in the templates/ dir
def generate(table, project_name : str, app_name : str, is_auth_app : bool, has_auth_app : bool) -> None:
    generate_css(project_name=project_name, app_name=app_name)
    generate_basehtml(project_name=project_name, app_name=app_name, table=table, has_auth_app=has_auth_app)
    if is_auth_app:
        generate_auth_page(project_name=project_name, app_name=app_name, table=table)
    else:
        generate_pages(project_name=project_name, app_name=app_name, table=table)


def main() -> None:
    if (len(sys.argv) != 4 or str(sys.argv[1]) == '' or str(sys.argv[2]) == ''  or str(sys.argv[3]) == ''  ):
        raise Exception("wrong arguments, call with: table project_name app_name")
    
    table = str(sys.argv[1]) 
    project_name = str(sys.argv[2]) 
    app_name = str(sys.argv[3]) 
    
    generate(table=table, project_name=project_name, app_name=app_name, is_auth_app=False)

if __name__ == "__main__":
    main()
