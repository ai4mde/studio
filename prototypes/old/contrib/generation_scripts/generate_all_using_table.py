# This file is used to generate all parts of the prototype app that make use of the table
# The table, which is generated first from diagrams in tests is read to create views, urls and templates of one app

import sys
from generate_section_table import get_apps, maketable
import generate_html_templates, generate_urls, generate_views

def generate_url_view_temp_for_app(table,projectName, appName, is_auth_app, has_auth_app):
    is_auth_app_bool = (is_auth_app == "true")
    has_auth_app_bool = (has_auth_app == "true")
    '''This function calls the scripts for generating urls.py, views.py and html templates for this app'''
    generate_urls.generate(table, projectName, appName, is_auth_app_bool)
    generate_views.generate(table, projectName, appName, is_auth_app_bool)
    generate_html_templates.generate(table, projectName, appName, is_auth_app_bool, has_auth_app_bool) # this one only needs urls of UI data
    #generate_models(table.classdata) #this one only needs class diagram

def main():

    #call this file with app name:
    if (len(sys.argv) >= 5 and str(sys.argv[1]) != "" and str(sys.argv[2]) != ""):
        apps = str(get_apps())
        if (str(sys.argv[2]) in get_apps()): #must be an app in table 
            generate_url_view_temp_for_app(maketable(),str(sys.argv[1]),str(sys.argv[2]),str(sys.argv[3]),str(sys.argv[4]))
            return
        else:
            raise ValueError("app name not on table")
    raise ValueError("no project and app name were given")

if __name__ == "__main__":
    main()