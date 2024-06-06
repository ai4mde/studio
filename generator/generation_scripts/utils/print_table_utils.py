# This file includes all functions and tools build for printing the table
# This is most usefull for debugging.

from utils.section_component import SectionComponent 
from .getters_table import get_sections_components_page_dict_with_app_name_from_table, get_section_component_from_table
from .table_utils import strorlenlist, get_name_or_entire_object

def print_name_or_entire_object(print_this,blocksize = 10, fillchar = " ", row_name = ""):
    """Only print name if possible, else print entire object. Params used for formatting"""
    print_this = str(print_this)
    print_this = row_name + print_this
    print(str(print_this[:blocksize].ljust(blocksize,fillchar)) + " | ",  end="")

def print_type_and_name_or_entire_object(print_this,blocksize = 10, fillchar = " ", row_name = ""):
    """Only type and print name if possible, else print entire object. Params used for formatting"""
    print_type = ""
    if print_this and  print_this != "" and (isinstance(print_this, dict) or (
        isinstance(print_this, object) and not (
            isinstance(print_this, int) or isinstance(print_this, str) or isinstance(print_this, list) ))):
        print_type = str(type(print_this))[8:-2] + " "
        print_type = print_type + "name: "

    print_this = get_name_or_entire_object(print_this)
    if not isinstance(print_this, int) and "{} is unnamed object" in print_this or print_this == "[]" :
        print_this = ""
        print_type = ""

    print_this = row_name + print_type + print_this
    print(str(print_this[:blocksize].ljust(blocksize,fillchar)) + " | ",  end="")


def print_table_info(table, blocksize = 20, fillchar = " ", only_show = []):
    print_table_with_info(table, blocksize, fillchar, only_show)

def print_table_with_info(table, blocksize = 20, fillchar = " ", only_show = []):
    """print the table with heading info and call all other prints of table including apps, pages, actors, classes (and relations of classes and attributes) """
    print("table for project: " + table.projectname )

    print_actors_on_table(table)
    print()

    print_classes_on_table(table)
    print()
    
    print_apps_on_table(table) 
    print()

    print_home_pages_on_table(table)
    print()
    
    print_home_renders_on_table(table)
    print()

    print_section_components_on_table(table, int(3*blocksize/4), only_show=only_show)
    print()

    print_render_table(table, blocksize=blocksize)
    
def print_table_data(functionality_table,table_data_name, blocksize = 20, fillchar = " ", only_show = []):
    "abstract print function for data on table like actors or apps. params blocksize and fillchar determine format"
    #first validate if data is on table
    if table_data_name not in functionality_table.__dict__:
        raise Exception("requested data with name "+ table_data_name+ " is not in table")
    print(table_data_name+": ")
    table_data = getattr(functionality_table,table_data_name)
    if isinstance(table_data, list):
        #data is a list and should be printed for each instance of that list
        for table_data_instance in table_data:
            print_name_or_entire_object(table_data_instance, blocksize, fillchar)

    elif isinstance(table_data, dict):
        #data is a dict and should be printed with each key: value pair example: homepage for app
        helper = ""
        for table_data_dict_key in table_data:
            if only_show and table_data_dict_key not in only_show:
                continue
            print_name_or_entire_object(table_data_dict_key, blocksize, fillchar)
            helper = table_data_dict_key

        #This only really works on dicts which have the same length of keys
        if helper != "" and isinstance(table_data[helper], dict): 
        #if data is like a list, EXAMPLE: section_components_per_id dict on table
            for key in table_data[table_data_dict_key]:
                print()
                row_name = str(key) + ": "
                first = True
                for table_data_dict_key in table_data:
                    print_type_and_name_or_entire_object(table_data[table_data_dict_key][key], blocksize, fillchar, row_name)
                    if first: 
                        row_name = ""
                        first = False
        else:
            print()
            for table_data_dict_key in table_data:
                print_name_or_entire_object(table_data[table_data_dict_key], blocksize, fillchar)
    print()

def print_classes_on_table(functionality_table):
    print_table_data(functionality_table,"class_data_per_name")

def print_actors_on_table(functionality_table):
    print_table_data(functionality_table,"actors")
    
def print_apps_on_table(functionality_table): 
    print_table_data(functionality_table,"app_names")

def print_home_pages_on_table(functionality_table): 
    print_table_data(functionality_table,"home_pages")
    
def print_home_renders_on_table(table): 
    print_table_data(table,"home_renders")


def print_section_component_data_on_table(table, blocksize = 9, fillchar =" ", only_show = []): 
    print_table_data(table,"section_component_data_per_id",blocksize=blocksize,fillchar =" ", only_show=only_show)

def print_section_components_on_table(table, blocksize = 9, fillchar =" ", only_show = []): 
    """todo"""
    print("compound section objects on table: ")
    buffer = []
    for app_name in table.app_names: 
        sections_per_page = table.section_components_per_app_and_page[app_name]
        if sections_per_page != {}:
            for page_name in sections_per_page:
                sections = sections_per_page[page_name]
                for section_data in sections:
                    buffer.append(section_data)
    helper_seccomp = SectionComponent()
    for header in helper_seccomp.__dict__:
        if only_show:
            if header not in only_show:
                continue
        print_name_or_entire_object(header, blocksize, "_")
    
    print()
    for compound_section_object in buffer:
        for header in compound_section_object.__dict__:
            if only_show:
                if header not in only_show:
                    continue
            section_data_attribute = getattr(compound_section_object,header)
            print_name_or_entire_object(section_data_attribute, blocksize, fillchar)
        print()


def print_table(section_table, blocksize = 10, fillchar = " ", only_show = [], whitespace_between_rows = False):
    """print the table. blocksize determines in how many characters an attribute is shown
    fillchar how empty space is filled. onlyshow which attributes will be printed and all if empty, example:
        onlyshow = ["pages"] """
    
    print()
    print("Section_table: ")
    print () 
    for header in section_table.headers:
        if only_show:
            if header not in only_show:
                continue
        print(header[:blocksize].ljust(blocksize,fillchar) + " | ",  end="")
    print()
    print()

    for section in section_table.table:
        for header in section_table.headers:
            if section and header in section.__dict__:
                value = strorlenlist(getattr(section, header))
            else:
                value = " "
                
            if only_show:
                if header not in only_show:
                    continue

            print_name_or_entire_object(value, blocksize, fillchar)
        print()
        if whitespace_between_rows:
            print()
    print()

def print_render_table(table,blocksize =20, fillchar = " ", only_show = [], whitespace_between_rows = False):

    print()
    print("renderTable: ")
    
    for app in table.application_components:
        print(app["name"][:blocksize].ljust(blocksize,fillchar) + " | ",  end="")
    print()

    #first we build buffers example: pages for each app
    buffers = {}
    for application_component in table.application_components:
        app_name = get_name_or_entire_object(application_component)
        buffers[app_name] = []
        
        if app_name == "authentication" or app_name == "Authentication": 
            continue
        for page_key in table.page_data_per_app[app_name]:
            page_data = table.page_data_per_app[app_name][page_key]
            page_name = get_name_or_entire_object(page_data)
            
            buffers[app_name+page_name] = []

            #first we build section buffers for each page example: pages for each app
            for section_id in page_data["sections"]:
                section_data = get_section_component_from_table(table, section_id)
                buffers[app_name+page_name].append(section_data)
            buffers[app_name].append(page_name)

    page_name_for_sections = {}
    totalpages = 0
    for application_component in table.application_components:
        totalpages =max(totalpages, len(buffers[application_component["name"]])+len(page_name_for_sections))
        page_name_for_sections[application_component["name"]] = []
    while totalpages >= 1:
        totalpages = 0
        for application_component in table.application_components:
            app_name = get_name_or_entire_object(application_component)
            if len(page_name_for_sections[app_name]) <1:

                print_page = " "
                if len(buffers[app_name]) >= 1: #print a page of this app
                    #example: for each app, we print out the pages untill there are no more for that app
                    # if len(buffers[page_name]) >= 1: #sections
                    page_name = buffers[app_name].pop()
                    print_page = page_name
                    render_for_page = table.render_per_app_and_page[app_name][print_page]
                    print_page = render_for_page + " -> " + print_page
                    page_name_for_sections[app_name].append(page_name)

                print(print_page[:blocksize].ljust(blocksize,fillchar) + " | ",  end="")
            else:
                print_section = " "
                page_name = page_name_for_sections[app_name].pop() #print section
                if len(buffers[app_name+page_name]) >= 1: #sections this page has sections
                    section_data = buffers[app_name+page_name].pop()
                    print_section = get_name_or_entire_object(section_data)
                    if len(buffers[app_name+page_name]) >= 1: #sections this page has even more sections
                        page_name_for_sections[app_name].append(page_name) #print section
                print(print_section[:blocksize].ljust(blocksize,fillchar) + " | ",  end="")
            totalpages =max(totalpages, len(buffers[app_name])+len(page_name_for_sections[app_name]))
        print()