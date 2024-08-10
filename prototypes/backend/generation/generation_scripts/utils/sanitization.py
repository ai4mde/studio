import re


def app_name_sanitization(proposed_name: str) -> str:
    '''Sanitizes application component names to alphanumeric + underscores only.'''
    return re.sub(r'[^a-zA-Z0-9_]', '', proposed_name)


def model_name_sanitization(proposed_name: str) -> str:
    '''Sanitizes model names to alphanumeric + underscores only.'''
    return re.sub(r'[^a-zA-Z0-9_]', '', proposed_name)


def attribute_name_sanitization(proposed_name: str) -> str:
    '''Sanitizes attribute names to alphanumeric + underscores only.'''
    return re.sub(r'[^a-zA-Z0-9_]', '', proposed_name)