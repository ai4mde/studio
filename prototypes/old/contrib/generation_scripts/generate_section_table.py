#This file is used to generate compound sections without functionalities using a table of data,
#including everything that is necessary for views, urls and html templates scripts to correctly generate code 

import sys
from utils.section_table import SectionTable
from utils.print_table_utils import print_table_with_info
from utils.setters_table import set_class_data_on_table, set_UI_data_on_table, set_home_pages_and_renders, set_metadata_of_diagrams_on_table
from utils.loading_json_utils import get_app_components, get_apps, get_child_models_of_model, get_dict_from_metadata, get_metadata_all_diagrams, get_models, get_models_without_creates, get_models_without_parents, get_parent_models_of_model, get_user_types_from_metadata

def maketable(print_table = False):
    """Creates a table based on the metadata of all diagrams found in standard dir"""
    
    table = SectionTable()
    metadata_all_diagrams = get_metadata_all_diagrams()
    set_metadata_of_diagrams_on_table(table, metadata_all_diagrams)
    set_class_data_on_table(table, get_dict_from_metadata("class", metadata_all_diagrams))
    set_UI_data_on_table(table, get_app_components(metadata_all_diagrams))
    set_home_pages_and_renders(table)
    
    if print_table:
        print_table_with_info(table,blocksize=29)
    return table

def main():
    
    if (len(sys.argv) >= 2 and str(sys.argv[1]) == "get_apps"): #for generator.sh
        print(get_apps())  
    elif (len(sys.argv) >= 2 and str(sys.argv[1]) == "get_user_types_from_metadata"): #for generator.sh
        print(get_user_types_from_metadata())  
    elif (len(sys.argv) >= 2 and str(sys.argv[1]) == "get_models"): #for generator.sh
        print(get_models())  
    elif (len(sys.argv) >= 2 and str(sys.argv[1]) == "get_models_without_creates"): #for generator.sh
        print(get_models_without_creates())  
    elif (len(sys.argv) >= 2 and str(sys.argv[1]) == "get_models_without_parents"): #for generator.sh
        print(get_models_without_parents())  
    elif (len(sys.argv) >= 3 and str(sys.argv[1]) == "get_child_models_of_model"): #for generator.sh
        print(get_child_models_of_model(str(sys.argv[2])))
    elif (len(sys.argv) >= 3 and str(sys.argv[1]) == "get_parent_models_of_model"): #for generator.sh
        print(get_parent_models_of_model(str(sys.argv[2])))
    elif (len(sys.argv) >= 2 and str(sys.argv[1]) == "print"): #for generator.sh
        table = maketable(True)
    else:
        table = maketable(False)
        return table
if __name__ == "__main__":
    main()