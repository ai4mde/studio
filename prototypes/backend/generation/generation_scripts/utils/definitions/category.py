from utils.sanitization import category_name_sanitization

class Category():
    '''Definition of a Category object.'''
    def __init__(
            self,
            id: str,
            name: str,
    ):
        self.name = category_name_sanitization(name)
        self.id = id
