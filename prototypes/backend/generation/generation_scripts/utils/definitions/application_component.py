from utils.sanitization import app_name_sanitization
from typing import List
from utils.definitions.page import Page
from utils.definitions.styling import Styling

class ApplicationComponent():
    '''Definition of an Application Component. One application component
    maps to an input interface, and to an output Django app.'''
    def __init__(
        self,
        id: str,
        project: str,
        name: str,
        pages: List[Page],
        styling: Styling
    ):
        self.id = id
        self.project = project
        self.name = app_name_sanitization(name)
        self.pages = pages
        self.styling = styling

    def __str__(self):
        return self.name