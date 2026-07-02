from utils.sanitization import category_name_sanitization
from typing import List

class Category():
    '''Definition of a Category object.'''
    def __init__(
            self,
            id: str,
            name: str,
    ):
        self.name = category_name_sanitization(name)
        self.display_name = name
        self.id = id

    def __str__(self):
        return self.name