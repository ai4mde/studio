#This file is used to generate the html templates in the correct styling and format as indicated by the UI json
from typing import Dict

from utils.data_validation_utils import section_component_name_sanitizer
from .section_component_utils import SectionText, CustomMethod, translate_and_set_section_component_object_attribute
from utils.section_component_utils import AttributeType
from .query import Comparison

class SectionComponent():
    def __init__(self,
                 id : str = "",
                 name : str = "",
                 app : str = "", 
                 page : str = "",
                 row : int = 0, 
                 col : int = 0, 
                 text : list["SectionText"] = [], 
                 links = [], 
                 actions = [], #derived attribute from functionalities
                 use_cases = [], #derived attribute from functionalities
                 classes = [], #no primary model anymore so derive from this
                 model : str = None,                                # primary model that is acted upon  #objects read in table (subset of classes)?
                 parent_models : list[str] = None,                  # list of parent models (e.g. for creation of child model, on delete=CASCADE)
                 attributes : list[str] = None,                     # list of attributes that section acts upon
                 derived_attributes : list[str] = None,             # subset of attributes that section are marked as derived
                 attribute_types : Dict[str, "AttributeType"] = None, # corresponding attribute types
                 updateable_attributes: Dict[str, bool] = None,
                 hasCreate : bool = False,
                 hasDelete : bool = False,
                 hasUpdate : bool = False, #derived attribute from functionalities
                 isQuery : bool = False,
                 query_condition : Comparison = None, # Future work query_condition : Query
                 custom_methods : list[CustomMethod] = []
                 ):
        self.id = id #validate todo
        self.name = section_component_name_sanitizer(name)
        self.app = app
        self.page = page
        self.row = row
        self.col = col
        self.text = text
        self.links = links
        #these should all be derived from functionalities
        self.actions = actions
        self.use_cases = use_cases
        self.classes = classes
        self.model = model # - model (Product)
        self.attributes = attributes #attributes (& attribute types)
        self.attribute_types = attribute_types
        self.derived_attributes = derived_attributes
        self.updateable_attributes = updateable_attributes # (lijst van alle attributes met true/false)
        self.hasCreate = hasCreate # - HAS_CREATE (true/false)
        self.hasDelete = hasDelete# - HAS_DELETE (true/false)
        self.hasUpdate = hasUpdate# - HAS_UPDATE (true/false)
        self.parent_models = parent_models #not used by section but useful for debugging
        self.isQuery = isQuery
        self.query_condition = query_condition
        self.custom_methods = custom_methods

    def extend_with_data(self, data, source = "any") -> None:
        """Example: data from UI.
        query condition gets set as a string
        type gets set as the above mentioned Enum based on strings.
        Should also work for app and page metadata, by passing their names or entire objects"""
        if isinstance(data, str) and source != "any":
            return translate_and_set_section_component_object_attribute(self, source, data)
        elif isinstance(data, dict):
            for data_type_key in data:
                data_value = data[data_type_key]
                translate_and_set_section_component_object_attribute(self, data_type_key, data_value)
            return
        raise Exception("unkown source ("+source+") for data: "+ str(data))

    def extend_with_all_data(self, section_component_data = {}, app_data = {}, page_data = {}):
        """Extends the section component object used for generation.
        Sets the data type of section component based on the provided data.
        Source varies from UI metadata to previous section_component object.
        section_component_data, including row and col, as well as page_data and app_data are optional params"""
        self.extend_with_data(section_component_data, "section_component")
        self.extend_with_data(app_data, "app")
        self.extend_with_data(page_data, "page")
        self.name = section_component_name_sanitizer(self.name +"for"+self.app)
    
    def contains_custom_on_render_for_model(self, render_this_page, model_name) -> str:
        """returns name of a custom method that should be loaded for @param model_name when it is rendered on @param render_this_page.
        Returns "" if no custom method should be loaded.
        NOTE: only one custom method on page render is supported"""
        #TODO multiple models might need to be updated 
        if self.custom_methods == []:
            return ""
        load_this_method = ""
        for attribute in self.derived_attributes:
            for custom_method in self.custom_methods:
                if "get_"+ attribute in custom_method.method_name:
                    load_this_method = custom_method.method_name
        return load_this_method 

    def contains_query_on_render_for_model(self, render_this_page, model_name) -> str:
        """returns query condition in sqlite format that should be executed for @param model_name when it is rendered on @param render_this_page.
        Returns "" if no query should be applied.
        """
        if not self.isQuery:
            return ""
        return self.query_condition