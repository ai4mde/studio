import os
import requests
import json
from google.adk.tools import FunctionTool

METADATA_API_BASE = "http://localhost:8000/v1/metadata"
TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../prototypes/backend/generation/templates"))

def get_system_context(system_id: str) -> str:
    """Fetch full system metadata including diagrams, classifiers, and relations."""
    try:
        # We use the export endpoint or manually collect if export isn't suitable
        # For now, let's assume we can get it via the systems/{id} or a specialized export
        response = requests.get(f"{METADATA_API_BASE}/systems/{system_id}/")
        response.raise_for_status()
        system_data = response.json()
        
        # Also fetch classifiers and relations explicitly if not in the main response
        # (Based on our research, read_system has diagrams_by_type but maybe not all classifiers)
        # Let's use the manual construction similar to what we did in interfaces.py
        
        classifiers_resp = requests.get(f"{METADATA_API_BASE}/systems/{system_id}/classifiers/")
        relations_resp = requests.get(f"{METADATA_API_BASE}/systems/{system_id}/relations/")
        
        system_data["classifiers"] = classifiers_resp.json() if classifiers_resp.ok else []
        system_data["relations"] = relations_resp.json() if relations_resp.ok else []
        
        return json.dumps(system_data, indent=2)
    except Exception as e:
        return f"Error fetching system context: {e}"

def get_interface_config(interface_id: str) -> str:
    """Fetch specific interface configuration and data."""
    try:
        response = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return f"Error fetching interface config: {e}"

def list_existing_templates() -> list:
    """List all available Jinja2 and HTML templates in the prototype engine."""
    try:
        if not os.path.exists(TEMPLATES_DIR):
            return [f"Templates directory not found at {TEMPLATES_DIR}"]
        return os.listdir(TEMPLATES_DIR)
    except Exception as e:
        return [f"Error listing templates: {e}"]

def read_template_file(filename: str) -> str:
    """Read the content of an existing template file."""
    try:
        path = os.path.join(TEMPLATES_DIR, filename)
        if not os.path.exists(path):
            return f"File {filename} not found."
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading template: {e}"

def write_prototype_template(filename: str, content: str) -> str:
    """Write generated template content to the prototype templates directory."""
    try:
        if not filename.endswith((".html", ".jinja2")):
            return "Error: File must be .html or .jinja2"
        
        os.makedirs(TEMPLATES_DIR, exist_ok=True)
        path = os.path.join(TEMPLATES_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {filename} to {TEMPLATES_DIR}"
    except Exception as e:
        return f"Error writing template: {e}"

# Register tools for ADK
system_context_tool = FunctionTool(func=get_system_context)
interface_config_tool = FunctionTool(func=get_interface_config)
list_templates_tool = FunctionTool(func=list_existing_templates)
read_template_tool = FunctionTool(func=read_template_file)
write_template_tool = FunctionTool(func=write_prototype_template)
