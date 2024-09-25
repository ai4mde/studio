from typing import List
from utils.sanitization import app_name_sanitization
import json

def get_apps(metadata: str) -> List[str]:
    """Returns a list of all application component names"""
    apps = []
    
    try:
        if metadata:
            for interface in json.loads(metadata)["interfaces"]:
                apps.append(app_name_sanitization(interface["value"]["name"]))
    except:
        raise Exception("Failed to retrieve names of interfaces")
    return " ".join(apps)