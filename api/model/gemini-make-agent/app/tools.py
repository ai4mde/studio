import os
import requests
import json
from google.adk.tools import FunctionTool

METADATA_API_BASE = os.getenv("METADATA_API_BASE", "http://studio-api:8000/api/v1/metadata")
_METADATA_API_KEY = os.getenv("METADATA_API_KEY")
_AUTH_HEADERS = {"Authorization": f"Bearer {_METADATA_API_KEY}"} if _METADATA_API_KEY else {}
TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../prototypes/backend/generation/templates"))

def get_system_context(system_id: str) -> str:
    """Fetch full system metadata including diagrams, classifiers, and relations."""
    try:
        response = requests.get(f"{METADATA_API_BASE}/systems/{system_id}/", headers=_AUTH_HEADERS)
        response.raise_for_status()
        system_data = response.json()

        classifiers_resp = requests.get(f"{METADATA_API_BASE}/systems/{system_id}/classifiers/", headers=_AUTH_HEADERS)
        relations_resp = requests.get(f"{METADATA_API_BASE}/systems/{system_id}/relations/", headers=_AUTH_HEADERS)

        system_data["classifiers"] = classifiers_resp.json() if classifiers_resp.ok else []
        system_data["relations"] = relations_resp.json() if relations_resp.ok else []

        return json.dumps(system_data, indent=2)
    except Exception as e:
        return f"Error fetching system context: {e}"

def get_interface_config(interface_id: str) -> str:
    """Fetch specific interface configuration and data."""
    try:
        response = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS)
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

def update_interface_data(interface_id: str, data: dict) -> str:
    """Update the 'data' JSON field of a specific interface."""
    try:
        resp = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS)
        resp.raise_for_status()
        current = resp.json()

        payload = {
            "id": interface_id,
            "name": current["name"],
            "description": current["description"],
            "system_id": current["system"],
            "actor_id": current["actor"],
            "data": data,
        }

        response = requests.put(f"{METADATA_API_BASE}/interfaces/{interface_id}/", json=payload, headers=_AUTH_HEADERS)
        response.raise_for_status()
        return f"Successfully updated interface {interface_id} data."
    except Exception as e:
        return f"Error updating interface data: {e}"

def verify_template_logic(content: str, system_id: str) -> str:
    """Verify that template variables and logic match the system metadata."""
    try:
        system_context_json = get_system_context(system_id)
        if system_context_json.startswith("Error"):
            return system_context_json

        system_data = json.loads(system_context_json)
        valid_attributes = set()
        for classifier in system_data.get("classifiers", []):
            attr_data = classifier.get("data", {}).get("attributes", [])
            for attr in attr_data:
                valid_attributes.add(attr.get("name"))

        import re
        matches = re.findall(r"\{\{\s*[^.\} ]+\.([^.\} ]+)\s*\}\}", content)

        findings = []
        for attr in matches:
            if attr not in valid_attributes:
                findings.append(f"Attribute '{attr}' used in template but not found in UML metadata.")

        if not findings:
            return "LOGIC VERIFIED: No attribute mismatches found."
        else:
            return "LOGIC CONFLICTS FOUND:\n" + "\n".join(findings)
    except Exception as e:
        return f"Error verifying template logic: {e}"

def apply_interface_patch(interface_id: str, patch: dict) -> str:
    """Apply a layout/style patch to an interface, preserving all structural fields (class, attributes, operations, name)."""
    try:
        resp = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS)
        resp.raise_for_status()
        current = resp.json()
        data = dict(current.get("data") or {})

        if "sections" in patch:
            section_map = {str(s["id"]): s for s in data.get("sections", [])}
            for ps in patch["sections"]:
                sid = str(ps.get("id", ""))
                if sid not in section_map:
                    continue
                for field in ("layout", "col_span", "position"):
                    if field in ps:
                        section_map[sid][field] = ps[field]
                if "style" in ps:
                    section_map[sid]["style"] = {
                        **(section_map[sid].get("style") or {}),
                        **ps["style"],
                    }
            data["sections"] = list(section_map.values())

        if "pages" in patch:
            page_map = {str(p["id"]): p for p in data.get("pages", [])}
            for pp in patch["pages"]:
                pid = str(pp.get("id", ""))
                if pid not in page_map:
                    continue
                for field in ("layout", "gap"):
                    if field in pp:
                        page_map[pid][field] = pp[field]
            data["pages"] = list(page_map.values())

        if "styling" in patch:
            data["styling"] = {**(data.get("styling") or {}), **patch["styling"]}
        if "tokens" in patch:
            data["tokens"] = {**(data.get("tokens") or {}), **patch["tokens"]}

        payload = {
            "id": interface_id,
            "name": current["name"],
            "description": current["description"],
            "system_id": current["system"],
            "actor_id": current["actor"],
            "data": data,
        }
        put_resp = requests.put(f"{METADATA_API_BASE}/interfaces/{interface_id}/", json=payload, headers=_AUTH_HEADERS)
        put_resp.raise_for_status()
        return f"Patched interface {interface_id} successfully."
    except Exception as e:
        return f"Error patching interface: {e}"


# Register tools for ADK
system_context_tool = FunctionTool(func=get_system_context)
interface_config_tool = FunctionTool(func=get_interface_config)
update_interface_tool = FunctionTool(func=update_interface_data)
update_interface_patch_tool = FunctionTool(func=apply_interface_patch)
list_templates_tool = FunctionTool(func=list_existing_templates)
read_template_tool = FunctionTool(func=read_template_file)
write_template_tool = FunctionTool(func=write_prototype_template)
verify_logic_tool = FunctionTool(func=verify_template_logic)
