import requests
import json
from google.adk.tools import FunctionTool
from .interface_schemas import _DATA_SCHEMA, _LAYOUT_SCHEMA
from .service_clients import METADATA_API_BASE, PROTOTYPE_API_BASE, _AUTH_HEADERS, render_candidate_preview_func

def run_seed_script(python_code: str) -> str:
    try:
        resp = requests.post(f"{PROTOTYPE_API_BASE}/seed_script", json={"script": python_code}, timeout=120)
        if resp.ok: return resp.text or "Seeded OK"
        return f"Seed failed ({resp.status_code}): {resp.text}"
    except Exception as e: return f"Error calling seed_script endpoint: {e}"

def get_available_paths(system_id: str, class_id: str, depth=2) -> str:
    try:
        system_json = get_system_context(system_id)
        if system_json.startswith("Error"): return system_json
        system_data = json.loads(system_json); classifiers = {c["id"]: c for c in system_data.get("classifiers", [])}; relations = system_data.get("relations", [])
        def traverse(cid, current_path, current_depth):
            if current_depth > depth: return []
            paths = []; cls = classifiers.get(cid)
            if not cls: return []
            for attr in cls.get("data", {}).get("attributes", []): attr_name = attr.get("name"); paths.append(f"{current_path}{attr_name}".lstrip("."))
            for rel in relations:
                source_id = rel.get("source"); target_id = rel.get("target"); rel_name = rel.get("name", "").lower()
                if source_id == cid: new_path = f"{current_path}{rel_name}."; paths.extend(traverse(target_id, new_path, current_depth + 1))
            return paths
        return json.dumps(list(set(traverse(class_id, "", 0))))
    except Exception as e: return f"Error computing paths: {e}"



from .metadata_context import get_interface_config, get_interface_full_context, get_system_context
from .candidate_generation import generate_candidate_set, regenerate_candidate_set, validate_and_save_candidate
from .interface_patch import apply_interface_patch
render_candidate_preview = render_candidate_preview_func

system_context_tool = FunctionTool(func=get_system_context)
interface_config_tool = FunctionTool(func=get_interface_config)
update_interface_patch_tool = FunctionTool(func=apply_interface_patch)
run_seed_script_tool = FunctionTool(func=run_seed_script)
get_available_paths_tool = FunctionTool(func=get_available_paths)
get_interface_full_context_tool = FunctionTool(func=get_interface_full_context)
generate_candidate_set_tool = FunctionTool(func=generate_candidate_set)
regenerate_candidate_set_tool = FunctionTool(func=regenerate_candidate_set)

