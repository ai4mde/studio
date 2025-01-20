import re
import keyword
from uuid import uuid4

def general_name_sanitization(proposed_name: str) -> str:
    '''Sanitizes names to alphanumeric + underscores only.'''
    if not proposed_name:
        proposed_name = str(uuid4())
    proposed_name = proposed_name.replace(' ', '_')
    proposed_name = proposed_name.replace('-', '_')
    while '__' in proposed_name:
        proposed_name = proposed_name.replace('__', '_')
    if keyword.iskeyword(proposed_name):
        proposed_name = "nm_" + proposed_name
    return re.sub(r'[^a-zA-Z0-9_]', '', proposed_name)


def project_name_sanitization(proposed_name: str) -> str:
    return general_name_sanitization(proposed_name)


def app_name_sanitization(proposed_name: str) -> str:
    return general_name_sanitization(proposed_name)


def model_name_sanitization(proposed_name: str) -> str:
    if proposed_name.lower() == "user":
        proposed_name = "cls_user"
    name = general_name_sanitization(proposed_name)
    if name[0].isdigit(): # model names may not start with a digit
        name = "cls_" + name
    return name


def attribute_name_sanitization(proposed_name: str) -> str:
    name = general_name_sanitization(proposed_name)
    if name[0].isdigit(): # attribute names may not start with a digit
        name = "att_" + name
    return name


def page_name_sanitization(proposed_name: str) -> str:
    if proposed_name.lower() == "base":
        proposed_name = uuid4()
    return general_name_sanitization(proposed_name)


def section_name_sanitization(proposed_name: str) -> str:
    return general_name_sanitization(proposed_name)


def category_name_sanitization(proposed_name: str) -> str:
    if proposed_name in ["", None]:
        return proposed_name
    return general_name_sanitization(proposed_name)


def custom_method_name_sanitization(proposed_name: str) -> str:
    return general_name_sanitization(proposed_name)