#this file is used as the main utils file of generate_section_table.py

from .table_utils import TableSpec

class SectionTable:
    '''
    This class specifies the Section table that includes data for generation of the Django app based on diagram metadata.

    projectname = Name of all prject with all apps combined
    actors = List of all actors from use case diagram like Customer, OrderManager
    app_names = List of all loaded apps from applications like AUTH, Customer, OrderManager
    app_components = List of all loaded metadata belonging to apps containing section components etc..
    table = List of all sections, example: Create Order
    class_names = List of all loaded class names from class diagram
    class_data = List of all loaded class names from class diagram
    render_per_app_and_page = helper for render functions (example: call on landing page)
    home_pages = Dict with key for each app, value: homepage
    home_render = Dict with key for each app, value: home entry used to load above homepage
    spec = TableSpec()
    headers: Lists names of columns of table, as specified in spec. example: App_name, Action, page_out
    '''
    def __init__(self,projectname = "debug"):
        self.projectname = projectname
        self.metadata_all_diagrams = "" #holds all diagram data, which will be loaded from cs3_metadata_hacked.json
        self.actors = []
        self.app_names = []
        self.application_components = [] #contains all data 
        self.table = [] # contains all loaded sections
        self.class_names = []
        self.class_data_per_name = {} #keys: class names values: parsed metadata including all attributes and linked classes
        self.page_data_per_app = {} # helper for render functions (example: call on landing page)
        self.render_per_app_and_page = {} # helper for render functions (example: call on landing page)
        self.section_components_per_app_and_page = {}
        self.section_components = []
        self.section_component_data_per_id = {} # helper for page generarion
        self.home_pages = {} #key: app_name, value: homepage
        self.home_renders = {} # key: app_name, value: render for to above homepage
        spec = TableSpec()
        self.headers = spec.headers