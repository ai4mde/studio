import re
from uuid import uuid4

def general_name_sanitization(proposed_name: str) -> str:
    '''Sanitizes names to alphanumeric + underscores only.'''
    if not proposed_name:
        proposed_name = str(uuid4())
    proposed_name = proposed_name.replace(' ', '_')
    proposed_name = proposed_name.replace('-', '_')
    return re.sub(r'[^a-zA-Z0-9_]', '', proposed_name)


def project_name_sanitization(proposed_name: str) -> str:
    return general_name_sanitization(proposed_name)


def app_name_sanitization(proposed_name: str) -> str:
    return general_name_sanitization(proposed_name)


def model_name_sanitization(proposed_name: str) -> str:
    return general_name_sanitization(proposed_name)


def attribute_name_sanitization(proposed_name: str) -> str:
    return general_name_sanitization(proposed_name)


def page_name_sanitization(proposed_name: str) -> str:
    return general_name_sanitization(proposed_name)


def section_name_sanitization(proposed_name: str) -> str:
    return general_name_sanitization(proposed_name)


def category_name_sanitization(proposed_name: str) -> str:
    return general_name_sanitization(proposed_name)
