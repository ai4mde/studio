import os
import requests
import json
import re
from google.adk.tools import FunctionTool

METADATA_API_BASE = os.getenv("METADATA_API_BASE", "http://studio-api:8000/api/v1/metadata")
PROTOTYPE_API_BASE = os.getenv("PROTOTYPE_API_BASE", "http://studio-prototypes:8010")
_METADATA_API_KEY = os.getenv("METADATA_API_KEY")
_AUTH_HEADERS = {"Authorization": f"Bearer {_METADATA_API_KEY}"} if _METADATA_API_KEY else {}
TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../prototypes/backend/generation/templates"))

def _as_list(payload, key: str) -> list:
    if isinstance(payload, dict):
        return payload.get(key, []) or []
    return payload or []

def _name_id(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_\\s-]", "", str(value or ""))
    value = re.sub(r"[\\s-]+", "_", value.strip())
    return value or "workflow_step"

def _page_name(value: str) -> str:
    return "_".join(part[:1].upper() + part[1:] for part in _name_id(value).split("_") if part)

def _section_id(value: str) -> str:
    return _name_id(value).lower()

def _build_activity_diagrams(system_data: dict) -> list:
    """Return activity diagrams in the shape expected by the prototype workflow parser."""
    diagrams = system_data.get("diagrams") or []
    classifiers = {str(c.get("id")): c for c in _as_list(system_data.get("classifiers"), "classifiers")}
    relations = {str(r.get("id")): r for r in _as_list(system_data.get("relations"), "relations")}
    out = []
    for diagram in diagrams:
        if diagram.get("type") != "activity":
            continue
        raw_nodes = diagram.get("nodes") or []
        raw_edges = diagram.get("edges") or []
        nodes = []
        node_by_cls = {}
        for node in raw_nodes:
            cls_id = str(node.get("cls") or node.get("cls_id") or node.get("cls_ptr") or "")
            classifier = classifiers.get(cls_id, {})
            nodes.append({
                "id": str(node.get("id")),
                "cls_ptr": cls_id,
                "cls": classifier.get("data", {}),
                "data": node.get("data", {}),
            })
            if cls_id:
                node_by_cls[cls_id] = str(node.get("id"))

        edges = []
        for edge in raw_edges:
            rel_id = str(edge.get("rel") or edge.get("rel_id") or edge.get("rel_ptr") or "")
            relation = relations.get(rel_id, {})
            source_cls = str(relation.get("source") or relation.get("source_id") or "")
            target_cls = str(relation.get("target") or relation.get("target_id") or "")
            source_ptr = node_by_cls.get(source_cls)
            target_ptr = node_by_cls.get(target_cls)
            if not source_ptr or not target_ptr:
                continue
            edges.append({
                "id": str(edge.get("id")),
                "source_ptr": source_ptr,
                "target_ptr": target_ptr,
                "rel_ptr": rel_id,
                "rel": relation.get("data", {}),
                "data": edge.get("data", {}),
            })
        out.append({
            "id": str(diagram.get("id")),
            "name": diagram.get("name", ""),
            "type": "activity",
            "nodes": nodes,
            "edges": edges,
        })
    return out

def _actor_refs(system_data: dict, actor_id: str | None, actor_name: str | None = None) -> set[str]:
    refs = {str(actor_id)} if actor_id else set()
    actor_name_norm = str(actor_name or "").lower()
    classifiers = {str(c.get("id")): c.get("data", {}) for c in _as_list(system_data.get("classifiers"), "classifiers")}
    for diagram in system_data.get("diagrams", []):
        if diagram.get("type") != "usecase":
            continue
        for node in diagram.get("nodes", []):
            cls_id = str(node.get("cls") or node.get("cls_id") or node.get("cls_ptr") or "")
            cls = classifiers.get(cls_id, {})
            if cls.get("type") == "actor" and (cls_id == str(actor_id) or str(cls.get("name", "")).lower() == actor_name_norm):
                refs.add(str(node.get("id")))
                refs.add(cls_id)
    return {ref for ref in refs if ref and ref != "None"}

def _workflow_plan(system_data: dict, actor_id: str | None, actor_name: str | None = None) -> list:
    refs = _actor_refs(system_data, actor_id, actor_name)
    steps = []
    for diagram in system_data.get("activity_diagrams", []):
        nodes = {str(n.get("id")): n for n in diagram.get("nodes", [])}
        outgoing = {}
        for edge in diagram.get("edges", []):
            outgoing.setdefault(str(edge.get("source_ptr")), []).append(str(edge.get("target_ptr")))
        for node in diagram.get("nodes", []):
            cls = node.get("cls", {})
            if cls.get("type") != "action":
                continue
            actor_node = str(cls.get("actorNode") or "")
            if refs and actor_node not in refs:
                continue
            name = cls.get("name") or "Workflow Step"
            page_name = _page_name(name)
            page_id = _section_id(page_name)
            next_action_ids = [
                target for target in outgoing.get(str(node.get("id")), [])
                if (nodes.get(target, {}).get("cls") or {}).get("type") == "action"
            ]
            steps.append({
                "activity_node_id": str(node.get("id")),
                "activity_node_name": name,
                "actor_node": actor_node,
                "diagram_id": diagram.get("id"),
                "diagram_name": diagram.get("name"),
                "page_id": page_id,
                "page_name": page_name,
                "next_activity_node_ids": next_action_ids,
            })
    return steps

def _ensure_workflow_pages(pages: list, sections: list, workflow_steps: list) -> tuple[list, list]:
    if not workflow_steps:
        return pages, sections

    pages = [dict(p) for p in pages]
    sections = [dict(s) for s in sections]
    section_ids = {str(s.get("id")) for s in sections}

    def page_action_id(page: dict) -> str:
        action = page.get("action") or {}
        if isinstance(action, dict):
            return str(action.get("value") or action.get("id") or "")
        return ""

    page_by_action = {page_action_id(p): p for p in pages if page_action_id(p)}

    for step in workflow_steps:
        node_id = step["activity_node_id"]
        page = page_by_action.get(node_id)
        if not page:
            page = {
                "id": step["page_id"],
                "name": step["page_name"],
                "primary_model": "",
                "type": {"value": "activity", "label": "Activity"},
                "action": {"value": node_id, "label": step["activity_node_name"]},
                "sections": [],
                "category": None,
            }
            pages.append(page)
            page_by_action[node_id] = page
        else:
            page["type"] = {"value": "activity", "label": "Activity"}
            page["action"] = {"value": node_id, "label": step["activity_node_name"]}
            page.setdefault("category", None)
            page.setdefault("sections", [])

        button_id = f"{_section_id(page.get('id') or page.get('name'))}_workflow_action"
        if button_id not in section_ids:
            sections.append({
                "id": button_id,
                "name": f"{page.get('name', step['page_name']).replace('_', ' ')} Continue",
                "label": "Continue",
                "type": "activity_action",
                "layout": "activity_action",
                "primary_model": "",
                "class": "",
                "operations": {"create": False, "update": False, "delete": False},
                "attributes": [],
                "methods": [],
                "col_span": 12,
                "position": "main",
                "style": {"variant": "wizard_next", "align": "right", "size": "lg"},
                "workflow": {"action": "complete"},
            })
            section_ids.add(button_id)

        refs = page.get("sections") or []
        ref_ids = {
            str(ref.get("value") if isinstance(ref, dict) else ref)
            for ref in refs
        }
        if button_id not in ref_ids:
            refs.append({"value": button_id})
            page["sections"] = refs

    return pages, sections

def _normalize_activity_action_sections(pages: list, sections: list) -> list:
    activity_page_section_ids = set()
    for page in pages:
        page_type = page.get("type", {})
        page_type_value = page_type.get("value") if isinstance(page_type, dict) else page_type
        if page_type_value != "activity":
            continue
        for ref in page.get("sections") or []:
            activity_page_section_ids.add(str(ref.get("value") if isinstance(ref, dict) else ref))

    for section in sections:
        sid = str(section.get("id", ""))
        is_activity_action = section.get("type") == "activity_action" or section.get("layout") == "activity_action"
        if not is_activity_action:
            continue

        operations = section.get("operations") or {}
        has_data_shape = bool(section.get("primary_model")) or bool(section.get("attributes")) or any(operations.values())

        if has_data_shape and sid not in activity_page_section_ids:
            section["layout"] = "list"
            if section.get("type") == "activity_action":
                section.pop("type", None)
            section.pop("workflow", None)
            section.pop("workflow_action", None)
            section.pop("target_page", None)
            section.pop("targetPage", None)
            style = section.get("style") or {}
            if style.get("variant") in {"button", "link", "fab", "wizard_next", "auto"}:
                style.pop("variant", None)
            section["style"] = style
            continue

        section["type"] = "activity_action"
        section["layout"] = "activity_action"
        section["primary_model"] = ""
        section["class"] = ""
        section["attributes"] = []
        section["operations"] = {"create": False, "update": False, "delete": False}
        section.setdefault("label", section.get("name") or "Continue")
        workflow = section.get("workflow") or {}
        workflow.setdefault("action", section.get("workflow_action") or "complete")
        section["workflow"] = workflow

    return sections

def _actor_name_from_context(system_context: dict, actor_id: str | None) -> str | None:
    for classifier in _as_list(system_context.get("classifiers"), "classifiers"):
        if str(classifier.get("id")) == str(actor_id):
            return (classifier.get("data") or {}).get("name")
    return None

def _apply_builtin_workflow_logic(interface_data: dict, system_id: str | None, actor_id: str | None) -> dict:
    """Deterministically add activity pages/buttons from the system activity diagrams."""
    data = dict(interface_data or {})
    pages = list(data.get("pages") or [])
    sections = list(data.get("sections") or [])
    if system_id:
        system_context = _fetch_system_context_data(system_id)
        actor_name = _actor_name_from_context(system_context, actor_id)
        workflow_steps = _workflow_plan(system_context, str(actor_id or ""), actor_name)
        pages, sections = _ensure_workflow_pages(pages, sections, workflow_steps)
    sections = _normalize_activity_action_sections(pages, sections)
    data["pages"] = pages
    data["sections"] = sections
    return data

def _fetch_system_context_data(system_id: str) -> dict:
    response = requests.get(f"{METADATA_API_BASE}/systems/{system_id}/", headers=_AUTH_HEADERS)
    response.raise_for_status()
    system_data = response.json()

    classifiers_resp = requests.get(f"{METADATA_API_BASE}/systems/{system_id}/classifiers/", headers=_AUTH_HEADERS)
    relations_resp = requests.get(f"{METADATA_API_BASE}/systems/{system_id}/relations/", headers=_AUTH_HEADERS)
    system_data["classifiers"] = classifiers_resp.json() if classifiers_resp.ok else []
    system_data["relations"] = relations_resp.json() if relations_resp.ok else []

    export_resp = requests.get(
        f"{METADATA_API_BASE}/systems/export/",
        params=[("system_ids", system_id)],
        headers=_AUTH_HEADERS,
    )
    if export_resp.ok:
        exported = export_resp.json()
        if exported:
            system_data["diagrams"] = exported[0].get("diagrams", [])
    system_data["activity_diagrams"] = _build_activity_diagrams(system_data)
    return system_data

def get_system_context(system_id: str) -> str:
    """Fetch full system metadata including diagrams, classifiers, and relations."""
    try:
        system_data = _fetch_system_context_data(system_id)
        system_data["workflow_plan"] = _workflow_plan(system_data, None)
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
                for field in ("layout", "col_span", "position", "attributes", "query", "workflow", "label", "target_page", "workflow_action"):
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

        try:
            data = _apply_builtin_workflow_logic(data, current.get("system"), current.get("actor"))
        except Exception:
            data["sections"] = _normalize_activity_action_sections(data.get("pages") or [], data.get("sections") or [])

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


def run_seed_script(python_code: str) -> str:
    """Execute a Python seed script in the currently running prototype's Django context.

    The script must be self-contained: it should import Django models from
    shared_models.models and use them to create objects. Delta-checking
    (skipping non-empty models) should be done inside the script.
    Returns stdout on success or an error message.
    """
    try:
        resp = requests.post(
            f"{PROTOTYPE_API_BASE}/seed_script",
            json={"script": python_code},
            timeout=120,
        )
        if resp.ok:
            return resp.text or "Seeded OK"
        return f"Seed failed ({resp.status_code}): {resp.text}"
    except Exception as e:
        return f"Error calling seed_script endpoint: {e}"


def get_available_paths(system_id: str, class_id: str, depth=2) -> str:
    """Recursively traverse relationships to return all valid attribute paths for a class."""
    try:
        system_json = get_system_context(system_id)
        if system_json.startswith("Error"):
            return system_json
        
        system_data = json.loads(system_json)
        classifiers = {c["id"]: c for c in system_data.get("classifiers", [])}
        relations = system_data.get("relations", [])
        
        def traverse(cid, current_path, current_depth):
            if current_depth > depth:
                return []
            
            paths = []
            cls = classifiers.get(cid)
            if not cls:
                return []
            
            # Add attributes of current class
            for attr in cls.get("data", {}).get("attributes", []):
                attr_name = attr.get("name")
                paths.append(f"{current_path}{attr_name}".lstrip("."))
            
            # Recurse through relations
            for rel in relations:
                source_id = rel.get("source")
                target_id = rel.get("target")
                rel_name = rel.get("name", "").lower()
                
                if source_id == cid:
                    new_path = f"{current_path}{rel_name}."
                    paths.extend(traverse(target_id, new_path, current_depth + 1))
            
            return paths

        return json.dumps(list(set(traverse(class_id, "", 0))))
    except Exception as e:
        return f"Error computing paths: {e}"

_VALID_LAYOUTS = {
    "card", "list", "table", "detail", "gallery", "filter", "form", "activity_action",
    "promo-bar", "logo", "search-bar", "icon-actions", "nav-links", "main-header",
    "minimal-header", "site-nav", "site-footer", "service-bar", "link-grid", "brand-strip",
}
_VALID_STYLE = {
    "color":        {"blue", "green", "purple", "orange", "rose", "slate"},
    "density":      {"compact", "normal", "spacious"},
    "shadow":       {"none", "sm", "md", "lg", "xl"},
    "border":       {"none", "light", "colored", "strong"},
    "bg":           {"white", "light", "gray", "dark"},
    "header_style": {"default", "large", "small", "colored", "hidden"},
    "display_mode": {"grid", "carousel", "banner"},
    "card_style":   {"default", "product", "category", "compact"},
    "list_style":   {"default", "product", "cart-item"},
    "form_style":   {"default", "auth", "step", "summary"},
    "image_position": {"left", "top", "right"},
    "image_size":   {"sm", "md", "lg"},
}


def get_interface_full_context(interface_id: str) -> str:
    """Fetch interface config plus full system context (classifiers, relations, diagrams) in one call.
    Strips current pages/sections/candidates from interface data — the agent generates these from scratch."""
    try:
        iface_resp = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS)
        iface_resp.raise_for_status()
        iface = iface_resp.json()
        system_id = iface.get("system")
        system_ctx = _fetch_system_context_data(system_id) if system_id else {}
        actor_id = iface.get("actor")
        actor_name = None
        for classifier in _as_list(system_ctx.get("classifiers"), "classifiers"):
            if str(classifier.get("id")) == str(actor_id):
                actor_name = (classifier.get("data") or {}).get("name")
                break
        system_ctx["workflow_plan"] = _workflow_plan(system_ctx, str(actor_id or ""), actor_name)

        # Strip existing layout data so the agent generates fresh candidates,
        # not influenced by whatever is currently rendered on the interface.
        iface_clean = {k: v for k, v in iface.items() if k != "data"}
        iface_clean["actor_name"] = iface.get("actor_name") or iface.get("actor")

        return json.dumps({"interface": iface_clean, "system": system_ctx}, indent=2)
    except Exception as e:
        return f"Error fetching full context: {e}"


def validate_and_save_candidate(
    interface_id: str,
    candidate_index: int,
    name: str,
    description: str,
    pages: list,
    sections: list,
    tokens: dict = None,
    styling: dict = None,
) -> str:
    """Validate a DSL candidate (model names, attributes, layout values, navigation targets) and
    save it to interface.data['candidates'][candidate_index]. Returns validation errors or 'OK'."""
    try:
        if styling:
            styling = dict(styling)
            alias_map = {
                "accent_color": "accentColor",
                "background_color": "backgroundColor",
                "text_color": "textColor",
                "selected_style": "selectedStyle",
            }
            for old_key, new_key in alias_map.items():
                if old_key in styling and new_key not in styling:
                    styling[new_key] = styling.pop(old_key)
            if isinstance(styling.get("radius"), str):
                radius_map = {"none": 0, "sm": 4, "md": 8, "lg": 12, "xl": 16, "2xl": 24}
                styling["radius"] = radius_map.get(styling["radius"], 8)

        # Fetch classifiers for validation
        iface_resp = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS)
        iface_resp.raise_for_status()
        iface = iface_resp.json()
        system_id = iface.get("system")

        cls_resp = requests.get(f"{METADATA_API_BASE}/systems/{system_id}/classifiers/", headers=_AUTH_HEADERS)
        classifiers_data = cls_resp.json() if cls_resp.ok else {}
        raw_classifiers = classifiers_data.get("classifiers", []) if isinstance(classifiers_data, dict) else classifiers_data

        # Build lookup: model_name → set of attribute names
        model_attrs: dict[str, set] = {}
        actor_name = None
        for c in raw_classifiers:
            cdata = c.get("data", {})
            cname = cdata.get("name", "")
            if str(c.get("id")) == str(iface.get("actor")):
                actor_name = cname
            attrs = {a.get("name", "") for a in cdata.get("attributes", []) if a.get("name")}
            if cname:
                model_attrs[cname] = attrs
        known_models = set(model_attrs.keys())
        try:
            completed_data = _apply_builtin_workflow_logic(
                {"pages": pages, "sections": sections},
                system_id,
                iface.get("actor"),
            )
            pages = completed_data.get("pages") or []
            sections = completed_data.get("sections") or []
        except Exception as e:
            # Candidate validation should still work if workflow metadata is incomplete.
            sections = _normalize_activity_action_sections(pages, sections)
        page_names = {p.get("name", "") for p in pages}
        page_ref_to_name = {}
        for p in pages:
            pname = p.get("name", "")
            pid = p.get("id", "")
            if pname:
                page_ref_to_name[pname] = pname
                page_ref_to_name[pname.lower()] = pname
            if pid:
                page_ref_to_name[pid] = pname
                page_ref_to_name[pid.lower()] = pname

        errors = []

        for s in sections:
            sname = s.get("name", "?")
            layout = s.get("layout", "")
            if layout and layout not in _VALID_LAYOUTS:
                errors.append(f"section '{sname}': invalid layout '{layout}'")

            pm = s.get("primary_model", "")
            if pm and pm not in known_models:
                errors.append(f"section '{sname}': unknown primary_model '{pm}'")

            for attr in s.get("attributes", []):
                attr_name = attr.get("name", attr) if isinstance(attr, dict) else attr
                if "." in attr_name:
                    # dot-notation: validate first segment is a known model
                    first = attr_name.split(".")[0]
                    if first not in known_models:
                        errors.append(f"section '{sname}': dot-notation prefix '{first}' not a known model")
                elif pm and pm in model_attrs and attr_name and attr_name not in model_attrs[pm]:
                    errors.append(f"section '{sname}': attribute '{attr_name}' not found on {pm}")

            vdp = s.get("view_detail_page", "")
            if vdp and vdp not in page_names:
                errors.append(f"section '{sname}': view_detail_page '{vdp}' not in pages")

            sp = (s.get("style") or {}).get("success_page", "")
            if sp and sp not in page_names:
                errors.append(f"section '{sname}': success_page '{sp}' not in pages")

            workflow = s.get("workflow") or {}
            workflow_action = workflow.get("action") or s.get("workflow_action", "")
            if workflow_action and workflow_action not in {"complete", "complete_then_page", "complete_then_target", "navigate", "none"}:
                errors.append(f"section '{sname}': invalid workflow.action '{workflow_action}'")
            workflow_target = (
                workflow.get("target_page")
                or workflow.get("targetPage")
                or s.get("target_page")
                or s.get("targetPage")
                or ""
            )
            if workflow_target and workflow_target in page_ref_to_name:
                workflow["target_page"] = page_ref_to_name[workflow_target]
                s["workflow"] = workflow
            if workflow_target and workflow_target not in page_names:
                normalized_workflow_target = page_ref_to_name.get(str(workflow_target).lower())
                if normalized_workflow_target:
                    workflow["target_page"] = normalized_workflow_target
                    s["workflow"] = workflow
                else:
                    errors.append(f"section '{sname}': workflow target_page '{workflow_target}' not in pages")

            for field, valid_vals in _VALID_STYLE.items():
                val = (s.get("style") or {}).get(field, "")
                if val and val not in valid_vals:
                    errors.append(f"section '{sname}': invalid style.{field} '{val}'")

            # Filter field validation: direct field, one-hop FK (dot-notation), multi-hop warning
            for f_cond in (s.get("query") or {}).get("filters") or []:
                f_field = (f_cond.get("field") or "").strip()
                if not f_field:
                    continue
                dot_parts = f_field.replace("__", ".").split(".")
                if len(dot_parts) == 1:
                    if pm and pm in model_attrs and f_field not in model_attrs[pm] and f_field != "id" and not f_field.endswith("_id"):
                        errors.append(f"section '{sname}': filter field '{f_field}' not found on model '{pm}'")
                elif len(dot_parts) == 2:
                    fk_model = dot_parts[0][0].upper() + dot_parts[0][1:] if dot_parts[0] else ""
                    sub_field = dot_parts[1]
                    if fk_model and fk_model not in known_models:
                        errors.append(f"section '{sname}': filter FK model '{fk_model}' not a known model")
                    elif sub_field and fk_model in model_attrs and sub_field not in model_attrs[fk_model] and sub_field != "id":
                        errors.append(f"section '{sname}': filter '{f_field}' - attribute '{sub_field}' not found on '{fk_model}'")
                else:
                    errors.append(f"section '{sname}': filter '{f_field}' traverses {len(dot_parts)-1} hops (max 1 supported; use related_to for deeper traversal)")

        # Auto-fix: strip unknown attributes rather than blocking save
        fixed_sections = []
        for s in sections:
            pm = s.get("primary_model", "")
            if pm and pm in model_attrs:
                new_attrs = []
                for attr in s.get("attributes", []):
                    attr_name = attr.get("name", attr) if isinstance(attr, dict) else attr
                    if "." in attr_name or not pm or attr_name in model_attrs.get(pm, set()):
                        new_attrs.append(attr)
                s = {**s, "attributes": new_attrs}
            fixed_sections.append(s)

        # Auto-assign ids to pages/sections that are missing them.
        # Also ensure every page has a `category` field (null = no category filter),
        # required by the prototype generator's loading_json_utils.py.
        fixed_pages = []
        for i, p in enumerate(pages):
            if not p.get("id"):
                p = {**p, "id": f"page_{candidate_index}_{i}"}
            if "category" not in p:
                p = {**p, "category": None}
            fixed_pages.append(p)

        for i, s in enumerate(fixed_sections):
            if not s.get("id"):
                layout = s.get("layout", "section")
                model = (s.get("primary_model") or "chrome").lower().replace(" ", "_")
                fixed_sections[i] = {**s, "id": f"{model}_{layout}_{candidate_index}_{i}"}
            if not fixed_sections[i].get("name"):
                fixed_sections[i] = {**fixed_sections[i], "name": fixed_sections[i]["id"]}

        # Auto-build page.sections references if pages don't have them.
        # The renderer reads pages[i].sections = [{"value": section_id}, ...] to know
        # which sections belong to each page. Chrome sections (header/footer/sidebar)
        # are auto-injected by the renderer, so only assign main-content sections here.
        chrome_positions = {"header", "hero", "footer", "sidebar"}
        content_sections = [s for s in fixed_sections if s.get("position", "main") not in chrome_positions]

        # Normalize page.sections to [{"value": "section_id"}, ...] format.
        # The prototype generator's retrieve_section_components expects this dict format.
        # The agent may output plain string arrays like ["s0_0", "s0_1"] — normalize those too.
        def _norm_section_refs(refs: list) -> list:
            result = []
            for r in refs:
                if isinstance(r, dict):
                    result.append(r)
                elif isinstance(r, str):
                    result.append({"value": r})
            return result

        for i, p in enumerate(fixed_pages):
            if p.get("sections") is not None:
                fixed_pages[i] = {**p, "sections": _norm_section_refs(p["sections"])}

        pages_need_sections = any(not p.get("sections") for p in fixed_pages)
        if pages_need_sections and content_sections:
            # Build a mapping: primary_model → list of sections (in order)
            from collections import defaultdict
            model_to_sections: dict = defaultdict(list)
            for s in content_sections:
                model_to_sections[s.get("primary_model", "")].append(s["id"])

            rebuilt_pages = []
            model_assigned: dict = defaultdict(int)

            for p in fixed_pages:
                if p.get("sections"):
                    rebuilt_pages.append(p)
                    continue
                pm = p.get("primary_model", "")
                candidates_for_page = model_to_sections.get(pm, [])

                start = model_assigned[pm]
                assigned = []
                if start < len(candidates_for_page):
                    assigned = [{"value": candidates_for_page[start]}]
                    model_assigned[pm] += 1

                if not assigned and model_to_sections.get("", []):
                    fallback = model_to_sections[""]
                    fb_start = model_assigned[""]
                    if fb_start < len(fallback):
                        assigned = [{"value": fallback[fb_start]}]
                        model_assigned[""] += 1

                rebuilt_pages.append({**p, "sections": assigned})
            fixed_pages = rebuilt_pages

        # Check for orphaned page section references (pages reference IDs not in sections[])
        section_ids = {s["id"] for s in fixed_sections}
        orphans = []
        for p in fixed_pages:
            for ref in p.get("sections", []):
                sid = ref.get("value") if isinstance(ref, dict) else str(ref)
                if sid and sid not in section_ids:
                    orphans.append(f"page '{p.get('name')}' references section '{sid}' which is not in sections[]")
        if orphans:
            missing = "; ".join(orphans[:5])
            return (
                f"INCOMPLETE: pages reference section IDs that are missing from sections[]. "
                f"You MUST include ALL referenced sections in the sections[] argument. "
                f"Missing: {missing}. "
                f"Please call validate_and_save_candidate again with the complete sections[] list."
            )

        # Fetch current interface data and update candidates list
        data = dict(iface.get("data") or {})
        candidates = list(data.get("candidates") or [])
        candidate = {
            "id": f"c{candidate_index}",
            "name": name,
            "description": description,
            "pages": fixed_pages,
            "sections": fixed_sections,
            **({"tokens": tokens} if tokens else {}),
            **({"styling": styling} if styling else {}),
        }
        while len(candidates) <= candidate_index:
            candidates.append(None)
        candidates[candidate_index] = candidate
        data["candidates"] = candidates

        payload = {
            "id": interface_id,
            "name": iface["name"],
            "description": iface.get("description", ""),
            "system_id": system_id,
            "actor_id": iface.get("actor"),
            "data": data,
        }
        put_resp = requests.put(f"{METADATA_API_BASE}/interfaces/{interface_id}/", json=payload, headers=_AUTH_HEADERS)
        if not put_resp.ok:
            return f"Error saving candidate: PUT returned {put_resp.status_code} — {put_resp.text[:200]}"
        put_resp.raise_for_status()

        if errors:
            return f"Saved with {len(errors)} auto-fixed issue(s): " + "; ".join(errors[:5])
        return f"OK: candidate {candidate_index} '{name}' saved successfully."
    except Exception as e:
        return f"Error saving candidate: {e}"


def render_candidate_preview(interface_id: str, candidate_index: int) -> str:
    """Trigger server-side rendering of a saved candidate's preview HTML."""
    try:
        resp = requests.post(
            f"{METADATA_API_BASE}/interfaces/{interface_id}/candidates/{candidate_index}/render/",
            headers=_AUTH_HEADERS,
            timeout=60,
        )
        if resp.ok:
            return f"OK: preview rendered for candidate {candidate_index}."
        return f"Render failed ({resp.status_code}): {resp.text}"
    except Exception as e:
        return f"Error rendering preview: {e}"


# Register tools
system_context_tool = FunctionTool(func=get_system_context)
interface_config_tool = FunctionTool(func=get_interface_config)
update_interface_patch_tool = FunctionTool(func=apply_interface_patch)
run_seed_script_tool = FunctionTool(func=run_seed_script)
get_available_paths_tool = FunctionTool(func=get_available_paths)
get_interface_full_context_tool = FunctionTool(func=get_interface_full_context)
validate_save_candidate_tool = FunctionTool(func=validate_and_save_candidate)
render_candidate_preview_tool = FunctionTool(func=render_candidate_preview)
