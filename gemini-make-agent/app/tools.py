import os
import requests
import json
import re
from google.adk.tools import FunctionTool
from .navigation_planner import DATA_SECTION_ROLES, build_navigation_plan
from .interface_schemas import _DATA_SCHEMA, _LAYOUT_SCHEMA
from .service_clients import METADATA_API_BASE, PROTOTYPE_API_BASE, _AUTH_HEADERS, render_candidate_preview_func

from .styling_engine import *


def _build_activity_diagrams(system_data: dict) -> list:
    diagrams = system_data.get("diagrams") or []
    classifiers = {str(c.get("id")): c for c in _as_list(system_data.get("classifiers"), "classifiers")}
    relations = {str(r.get("id")): r for r in _as_list(system_data.get("relations"), "relations")}
    out = []
    for diagram in diagrams:
        if diagram.get("type") != "activity": continue
        raw_nodes = diagram.get("nodes") or []; raw_edges = diagram.get("edges") or []; nodes = []; node_by_cls = {}
        for node in raw_nodes:
            cls_id = str(node.get("cls") or node.get("cls_id") or node.get("cls_ptr") or ""); classifier = classifiers.get(cls_id, {}); nodes.append({"id": str(node.get("id")), "cls_ptr": cls_id, "cls": classifier.get("data", {}), "data": node.get("data", {})})
            if cls_id: node_by_cls[cls_id] = str(node.get("id"))
        edges = []
        for edge in raw_edges:
            rel_id = str(edge.get("rel") or edge.get("rel_id") or edge.get("rel_ptr") or ""); relation = relations.get(rel_id, {}); source_cls = str(relation.get("source") or relation.get("source_id") or ""); target_cls = str(relation.get("target") or relation.get("target_id") or ""); source_ptr = node_by_cls.get(source_cls); target_ptr = node_by_cls.get(target_cls)
            if not source_ptr or not target_ptr: continue
            edges.append({"id": str(edge.get("id")), "source_ptr": source_ptr, "target_ptr": target_ptr, "rel_ptr": rel_id, "rel": relation.get("data", {}), "data": edge.get("data", {})})
        out.append({"id": str(diagram.get("id")), "name": diagram.get("name", ""), "type": "activity", "nodes": nodes, "edges": edges})
    return out

def _actor_refs(system_data: dict, actor_id: str | None, actor_name: str | None = None) -> set[str]:
    refs = {str(actor_id)} if actor_id else set()
    actor_name_norm = str(actor_name or "").lower()
    classifiers = {
        str(c.get("id")): c.get("data", {})
        for c in _as_list(system_data.get("classifiers"), "classifiers")
    }
    for diagram in system_data.get("diagrams", []):
        if diagram.get("type") != "usecase":
            continue
        for node in diagram.get("nodes", []):
            cls_id = str(node.get("cls") or node.get("cls_id") or node.get("cls_ptr") or "")
            cls = classifiers.get(cls_id, {})
            if cls.get("type") == "actor" and (
                cls_id == str(actor_id)
                or str(cls.get("name", "")).lower() == actor_name_norm
            ):
                refs.add(str(node.get("id")))
                refs.add(cls_id)
    return {ref for ref in refs if ref and ref != "None"}

def _ref_values(values) -> set[str]:
    out = set()
    for value in values or []:
        if isinstance(value, dict):
            ref = value.get("id") or value.get("value") or value.get("classifier") or value.get("node")
        else:
            ref = value
        if ref:
            out.add(str(ref))
    return out

def _ref_list(values) -> list[str]:
    out = []
    seen = set()
    for value in values or []:
        if isinstance(value, dict):
            ref = value.get("id") or value.get("value") or value.get("classifier") or value.get("node")
        else:
            ref = value
        if ref and str(ref) not in seen:
            out.append(str(ref))
            seen.add(str(ref))
    return out

def _name_tokens(value: str) -> set[str]:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(value or ""))
    tokens = {
        token
        for token in re.split(r"[^A-Za-z0-9]+", spaced.lower())
        if len(token) > 1
    }
    singulars = {token[:-1] for token in tokens if len(token) > 3 and token.endswith("s")}
    return tokens | singulars

def _rank_models_for_text(text: str, models: list[str], prefer_collections: bool = False) -> list[str]:
    text_tokens = _name_tokens(text)
    ranked = []
    for index, model in enumerate(models or []):
        model_tokens = _name_tokens(model)
        if not model_tokens:
            continue
        overlap = len(text_tokens & model_tokens)
        compact_model = re.sub(r"[^a-z0-9]+", "", str(model).lower())
        compact_text = re.sub(r"[^a-z0-9]+", "", str(text).lower())
        substring = 2 if compact_model and compact_model in compact_text else 0
        collection_bonus = 1 if prefer_collections and _is_child_collection_model(model, text) else 0
        ranked.append((overlap + substring + collection_bonus, -index, model))
    ranked.sort(reverse=True)
    return [model for score, _index, model in ranked if score > 0]

def _infer_usecase_model(name: str, explicit_classes: list[str], classifiers: dict[str, dict], model_names: set[str]) -> str:
    for ref in explicit_classes:
        cls = classifiers.get(ref, {})
        cname = cls.get("name") or ref
        if cname in model_names:
            return cname
    ranked = _rank_models_for_text(name, sorted(model_names, key=len, reverse=True))
    return ranked[0] if ranked else ""

def _humanize_action_label(name: str, fallback: str = "Start") -> str:
    raw = re.sub(r"[_-]+", " ", str(name or "")).strip()
    if not raw:
        return fallback
    cleaned = re.sub(r"^(manage|view|track|write|browse|search|review)\s+", "", raw, flags=re.I).strip()
    if re.search(r"\b(apply|application|request|submit|onboard|register|book|schedule|reserve|approval|claim|ticket|case|workflow|process)\b", raw, re.I):
        return "Start"
    return cleaned[:1].upper() + cleaned[1:] if cleaned else fallback

def _is_child_collection_model(model_name: str, page_terms: str = "") -> bool:
    name_l = str(model_name or "").lower()
    if not name_l:
        return False
    if any(term in _name_tokens(name_l) for term in ("item", "line", "entry", "row", "detail", "selection", "membership", "mapping", "association")):
        return True
    return False

def _plural_page_id(model: str) -> str:
    base = _section_id(model or "items")
    if base.endswith("y"):
        return f"{base[:-1]}ies"
    if base.endswith("s"):
        return base
    return f"{base}s"

def _nav_mapping_for_usecase(usecase: dict, workflow_entry: bool = False) -> dict:
    name = str(usecase.get("name") or "")
    name_l = name.lower()
    primary = usecase.get("primary_model") or ""
    class_names = [m for m in usecase.get("class_names") or [] if m]
    ranked_models = _rank_models_for_text(name, class_names)

    def best_model(default: str = "") -> str:
        return primary or (ranked_models[0] if ranked_models else (class_names[0] if class_names else default))

    if any(term in name_l for term in ("system process", "background", "automated", "notification")):
        return {"role": "background", "page_id": "", "page_name": "", "page_model": primary, "operation_kind": "background"}

    if workflow_entry:
        page_model = best_model()
        page_id = _section_id(page_model or name)
        return {
            "role": "workflow_entry",
            "page_id": page_id,
            "page_name": _page_name(page_id),
            "page_model": page_model,
            "operation_kind": "start_workflow",
        }

    inline_terms = ("add", "remove", "delete", "update", "select", "write", "review", "rate")
    if any(term in name_l for term in inline_terms) and "manage" not in name_l:
        page_model = best_model()
        target_model = next((m for m in ranked_models + class_names if m and m != page_model), page_model)
        operation_kind = "delete" if any(term in name_l for term in ("remove", "delete")) else (
            "create_related" if target_model and target_model != page_model and any(term in name_l for term in ("add", "write", "create", "select")) else "object_operation"
        )
        return {
            "role": "inline_operation",
            "page_id": _section_id(page_model or name),
            "page_name": _page_name(page_model or name),
            "page_model": page_model,
            "operation_kind": operation_kind,
            "target_model": target_model,
        }

    if any(term in name_l for term in ("browse", "search", "catalog", "list", "overview", "directory")):
        page_model = best_model()
        page_id = _plural_page_id(page_model) if page_model else _section_id(name)
        return {"role": "collection_workspace", "page_id": page_id, "page_name": _page_name(page_id), "page_model": page_model, "operation_kind": "view_collection"}

    if "detail" in name_l or name_l.startswith("view "):
        page_model = best_model()
        page_id = f"{_section_id(page_model)}_detail" if page_model else _section_id(name)
        return {"role": "detail_workspace", "page_id": page_id, "page_name": _page_name(page_id), "page_model": page_model, "operation_kind": "view_detail"}

    if "track" in name_l or "history" in name_l:
        page_model = best_model()
        page_id = _plural_page_id(page_model) if page_model else _section_id(name)
        return {"role": "collection_workspace", "page_id": page_id, "page_name": _page_name(page_id), "page_model": page_model, "operation_kind": "view_collection"}

    if any(term in name_l for term in ("account", "profile", "settings")):
        page_model = best_model()
        page_id = _section_id(page_model or name)
        return {"role": "object_workspace", "page_id": page_id, "page_name": _page_name(page_id), "page_model": page_model, "operation_kind": "manage_object"}

    page_id = _section_id(primary or name)
    return {"role": "object_workspace", "page_id": page_id, "page_name": _page_name(page_id), "page_model": primary, "operation_kind": "manage_object"}

def _activity_action_indexes(system_data: dict) -> tuple[dict[str, dict], set[str], set[str]]:
    by_id = {}
    first_ids = set()
    all_ids = set()
    for diagram in system_data.get("activity_diagrams") or []:
        incoming = {}
        outgoing = {}
        action_ids = set()
        for node in diagram.get("nodes") or []:
            cls = node.get("cls") or {}
            if cls.get("type") == "action":
                nid = str(node.get("id"))
                cid = str(node.get("cls_ptr") or "")
                action_ids.add(nid)
                all_ids.update({nid, cid})
                by_id[nid] = {"node_id": nid, "classifier_id": cid, "name": cls.get("name", ""), "diagram_id": diagram.get("id"), "diagram_name": diagram.get("name", "")}
                if cid:
                    by_id[cid] = by_id[nid]
        for edge in diagram.get("edges") or []:
            source = str(edge.get("source_ptr") or "")
            target = str(edge.get("target_ptr") or "")
            if source and target:
                incoming.setdefault(target, []).append(source)
                outgoing.setdefault(source, []).append(target)
        for aid in action_ids:
            source_nodes = incoming.get(aid, [])
            if not source_nodes or any(((next((n for n in diagram.get("nodes") or [] if str(n.get("id")) == src), {}).get("cls") or {}).get("type") == "initial") for src in source_nodes):
                first_ids.add(aid)
                cls_id = by_id.get(aid, {}).get("classifier_id")
                if cls_id:
                    first_ids.add(cls_id)
    return by_id, first_ids, all_ids

def _usecase_has_workflow_entry(usecase: dict, has_activity_workflow: bool, activity_first_ids: set[str], activity_all_ids: set[str]) -> bool:
    if not has_activity_workflow:
        return False
    refs = set(usecase.get("activities") or []) | set(usecase.get("actions") or [])
    if refs:
        return bool(refs & (activity_first_ids or activity_all_ids))
    name_l = usecase.get("name", "").lower()
    passive_terms = {"browse", "search", "view", "track", "receive", "manage account", "settings", "profile", "history", "status"}
    if any(term in name_l for term in passive_terms):
        return False
    intent_terms = {
        "apply", "application", "request", "submit", "book", "schedule",
        "reserve", "register", "onboard", "approve", "approval", "claim", "ticket", "case",
        "process", "workflow"
    }
    if any(term in name_l for term in intent_terms):
        return True
    return False

def _infer_usecase_permissions(name: str) -> list[str]:
    name_l = str(name or "").lower()
    perms = {"view"}
    if any(term in name_l for term in ("add", "create", "write", "submit")):
        perms.add("create")
    if any(term in name_l for term in ("manage", "update", "edit", "select", "enter", "process", "confirm", "track")):
        perms.add("update")
    if "manage" in name_l and not any(term in name_l for term in ("account", "profile", "settings", "password")):
        if any(term in name_l for term in ("item", "items", "record", "records", "entry", "entries", "line", "lines")):
            perms.update({"create", "delete"})
    if any(term in name_l for term in ("delete", "remove", "cancel")):
        perms.add("delete")
    return [p for p in ("view", "create", "update", "delete") if p in perms]

def _build_usecase_navigation(system_data: dict, actor_id: str | None, actor_name: str | None = None) -> dict:
    refs = _actor_refs(system_data, actor_id, actor_name)
    classifiers = {
        str(c.get("id")): (c.get("data") or {})
        for c in _as_list(system_data.get("classifiers"), "classifiers")
    }
    model_names = {
        cdata.get("name")
        for cdata in classifiers.values()
        if cdata.get("name") and cdata.get("type") in {"class", "entity", "model"}
    }
    model_attrs = {
        cdata.get("name"): {a.get("name") for a in cdata.get("attributes", []) if a.get("name")}
        for cdata in classifiers.values()
        if cdata.get("name") and cdata.get("type") in {"class", "entity", "model"}
    }
    relations = {str(r.get("id")): r for r in _as_list(system_data.get("relations"), "relations")}
    usecases = {}
    includes = {}
    for diagram in system_data.get("diagrams", []):
        if diagram.get("type") != "usecase":
            continue
        node_by_cls = {}
        for node in diagram.get("nodes", []):
            cls_id = str(node.get("cls") or node.get("cls_id") or node.get("cls_ptr") or "")
            if cls_id:
                node_by_cls[cls_id] = str(node.get("id"))
        for edge in diagram.get("edges", []):
            rel_id = str(edge.get("rel") or edge.get("rel_id") or edge.get("rel_ptr") or "")
            rel = relations.get(rel_id, {})
            rdata = rel.get("data") or {}
            source = str(rel.get("source") or rel.get("source_id") or "")
            target = str(rel.get("target") or rel.get("target_id") or "")
            if rdata.get("type") == "interaction":
                source_cls = classifiers.get(source, {})
                target_cls = classifiers.get(target, {})
                uc_id = ""
                if source in refs and target_cls.get("type") == "usecase":
                    uc_id = target
                elif target in refs and source_cls.get("type") == "usecase":
                    uc_id = source
                if uc_id and uc_id not in usecases:
                    uc = classifiers.get(uc_id, {})
                    explicit_classes = _ref_list(uc.get("classes"))
                    model = _infer_usecase_model(uc.get("name", ""), explicit_classes, classifiers, model_names)
                    page_id = _section_id(uc.get("name") or "usecase")
                    class_names = [
                        classifiers.get(cid, {}).get("name")
                        for cid in explicit_classes
                        if classifiers.get(cid, {}).get("name") in model_names
                    ]
                    page_terms = f"{uc.get('name', '')} {uc.get('trigger', '')} {uc.get('precondition', '')}"
                    usecases[uc_id] = {
                        "id": uc_id,
                        "node_id": node_by_cls.get(uc_id, ""),
                        "name": uc.get("name", ""),
                        "page_id": page_id,
                        "page_name": _page_name(uc.get("name") or page_id),
                        "primary_model": model,
                        "permissions": _infer_usecase_permissions(uc.get("name", "")),
                        "classes": explicit_classes,
                        "class_names": class_names,
                        "pre_workflow_collections": [m for m in class_names if m != model and _is_child_collection_model(m, page_terms)],
                        "activities": sorted(_ref_values(uc.get("activities"))),
                        "actions": sorted(_ref_values(uc.get("actions"))),
                        "trigger": uc.get("trigger", ""),
                        "precondition": uc.get("precondition", ""),
                        "postcondition": uc.get("postcondition", ""),
                    }
            elif rdata.get("type") in {"inclusion", "extension"}:
                includes.setdefault(source, []).append({"type": rdata.get("type"), "usecase_id": target, "name": classifiers.get(target, {}).get("name", "")})
    activity_by_id, activity_first_ids, activity_all_ids = _activity_action_indexes(system_data)
    has_activity_workflow = bool(system_data.get("activity_diagrams"))
    actor_permissions = {}
    for uc_id, uc in usecases.items():
        uc["related_usecases"] = includes.get(uc_id, [])
        has_workflow_entry = _usecase_has_workflow_entry(uc, has_activity_workflow, activity_first_ids, activity_all_ids)
        ui_mapping = _nav_mapping_for_usecase(uc, has_workflow_entry)
        uc["ui_mapping"] = ui_mapping
        if ui_mapping.get("page_id"):
            uc["page_id"] = ui_mapping["page_id"]
            uc["page_name"] = ui_mapping.get("page_name") or _page_name(ui_mapping["page_id"])
        if ui_mapping.get("page_model"):
            uc["page_model"] = ui_mapping["page_model"]
        model = uc.get("primary_model")
        if model:
            current = set(actor_permissions.get(model, []))
            current.update(uc.get("permissions") or [])
            actor_permissions[model] = [p for p in ("view", "create", "update", "delete") if p in current]
        for related_model in uc.get("class_names") or []:
            if not related_model:
                continue
            current = set(actor_permissions.get(related_model, []))
            current.add("view")
            if _is_child_collection_model(related_model, f"{uc.get('name', '')} {uc.get('trigger', '')}"):
                current.update({"update", "delete"})
            actor_permissions[related_model] = [p for p in ("view", "create", "update", "delete") if p in current]
    page_entries = {}
    for uc in usecases.values():
        mapping = uc.get("ui_mapping") or {}
        page_id = mapping.get("page_id") or uc.get("page_id")
        if not page_id or mapping.get("role") == "background":
            continue
        current = page_entries.setdefault(page_id, {
            "page_id": page_id,
            "page_name": mapping.get("page_name") or uc.get("page_name") or _page_name(page_id),
            "primary_model": mapping.get("page_model") or uc.get("page_model") or uc.get("primary_model", ""),
            "roles": [],
            "usecases": [],
        })
        if mapping.get("role") and mapping["role"] not in current["roles"]:
            current["roles"].append(mapping["role"])
        current["usecases"].append(uc.get("name"))
    nav_pages = [
        entry["page_id"]
        for entry in page_entries.values()
        if any(role in entry["roles"] for role in ("collection_workspace", "object_workspace", "workflow_entry"))
    ]
    icon_actions = [pid for pid in nav_pages if any(term in pid for term in ("account", "profile", "settings", "search"))]
    workflow_entry_points = []
    for uc in usecases.values():
        if _usecase_has_workflow_entry(uc, has_activity_workflow, activity_first_ids, activity_all_ids):
            refs = set(uc.get("activities") or []) | set(uc.get("actions") or [])
            linked_actions = [activity_by_id[ref] for ref in refs if ref in activity_by_id]
            first_linked = next((a for a in linked_actions if a.get("node_id") in activity_first_ids or a.get("classifier_id") in activity_first_ids), None)
            first_action = first_linked or (linked_actions[0] if linked_actions else None)
            label = _humanize_action_label(uc.get("name", ""), "Start")
            workflow_entry_points.append({
                "page_id": uc.get("page_id"),
                "page_name": uc.get("page_name"),
                "usecase_name": uc.get("name"),
                "section_layout": "activity_start",
                "label": label,
                "button_label": label,
                "primary_model": uc.get("primary_model", ""),
                "related_models": uc.get("class_names") or [],
                "pre_workflow_collections": uc.get("pre_workflow_collections") or [],
                "starts_activity_node_id": first_action.get("node_id") if first_action else "",
                "starts_activity_name": first_action.get("name") if first_action else "",
                "reason": "Starts the executable workflow for this use case; downstream activity pages stay gated by active_process_node_id.",
            })
    nav = {
        "actor_refs": sorted(refs),
        "usecases": list(usecases.values()),
        "pages": list(page_entries.values()),
        "nav_bar_pages": nav_pages,
        "icon_actions": icon_actions,
        "actor_permissions": actor_permissions,
        "workflow_entry_points": workflow_entry_points,
        "_note": "Use usecases for high-level pages, navigation entries, icon buttons, and actor permissions; use activity_diagrams/workflow_plan only for executable workflow tasks.",
    }
    workflow_steps = _workflow_plan(system_data, actor_id, actor_name)
    nav["workflow_steps"] = workflow_steps
    nav["nav_plan"] = build_navigation_plan(nav, model_attrs, workflow_steps)
    return nav

def _workflow_plan(system_data: dict, actor_id: str | None, actor_name: str | None = None) -> list:
    refs = _actor_refs(system_data, actor_id, actor_name)
    classifiers = {
        str(c.get("id")): (c.get("data") or {})
        for c in _as_list(system_data.get("classifiers"), "classifiers")
    }

    def _class_name(ref) -> str:
        if isinstance(ref, dict):
            ref = ref.get("id") or ref.get("value") or ref.get("name")
        ref = str(ref or "")
        return classifiers.get(ref, {}).get("name") or ref

    def _class_refs(raw_classes) -> list:
        if isinstance(raw_classes, dict):
            refs = []
            for values in raw_classes.values():
                refs.extend(values or [])
            return refs
        return list(raw_classes or [])

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
            page_name = _workflow_page_name(name)
            page_id = _section_id(page_name)
            next_action_ids = [
                target
                for target in outgoing.get(str(node.get("id")), [])
                if (nodes.get(target, {}).get("cls") or {}).get("type") == "action"
            ]
            steps.append({
                "activity_node_id": str(node.get("id")),
                "activity_node_name": name,
                "actor_node": actor_node,
                "classes": [_class_name(ref) for ref in _class_refs(cls.get("classes")) if _class_name(ref)],
                "diagram_id": diagram.get("id"),
                "diagram_name": diagram.get("name"),
                "page_id": page_id,
                "page_name": page_name,
                "next_activity_node_ids": next_action_ids,
            })
    return steps

def _activity_models_for_step(step: dict, workflow_entries: list, known_models: set[str]) -> list[str]:
    name_l = str(step.get("activity_node_name") or step.get("page_name") or "").lower()
    explicit_step_models = [m for m in step.get("classes") or [] if m in known_models]
    if explicit_step_models:
        ranked = _rank_models_for_text(name_l, explicit_step_models, prefer_collections=True)
        return (ranked + [m for m in explicit_step_models if m not in ranked])[:2]
    entries = [e for e in workflow_entries if not e.get("diagram_id") or e.get("diagram_id") == step.get("diagram_id")]
    related = []
    for entry in entries or workflow_entries:
        related.extend(entry.get("pre_workflow_collections") or [])
        related.extend(entry.get("related_models") or [])
        if entry.get("primary_model"):
            related.append(entry.get("primary_model"))
    related = [m for m in dict.fromkeys(related) if m in known_models]
    if not related:
        return []

    prefer_collections = any(term in _name_tokens(name_l) for term in ("add", "select", "choose", "list", "review", "manage"))
    ranked = _rank_models_for_text(name_l, related, prefer_collections=prefer_collections)
    return ranked[:2] or related[:1]

def _activity_layout_for_step(step_name: str, model: str) -> str:
    name_tokens = _name_tokens(step_name)
    # "select/choose" = pick from options ? card with select operation, not a form
    if any(term in name_tokens for term in ("select", "choose", "pick")):
        return "card"
    if any(term in name_tokens for term in (
        "enter", "fill", "input", "provide", "submit",
        "create", "add", "update", "edit", "write", "upload", "register",
        "book", "pay", "record",
    )):
        return "form"
    if _is_child_collection_model(model, step_name) or any(term in name_tokens for term in ("list", "browse", "review", "manage", "track", "history")):
        return "list"
    if any(term in name_tokens for term in ("confirmation", "confirm", "detail", "summary")):
        return "detail"
    return "detail"

def _normalize_section_operations(operations) -> dict:
    defaults = {"create": False, "update": False, "delete": False, "select": False}
    select_terms = {"select", "choose", "pick", "bulk_select", "multi_select", "batch_select"}
    false_terms = {"", "0", "false", "no", "none", "null", "off"}

    def enabled(value) -> bool:
        if isinstance(value, str):
            return value.strip().lower() not in false_terms
        return bool(value)

    if isinstance(operations, dict):
        normalized = dict(defaults)
        normalized.update({
            "create": any(enabled(operations.get(term, False)) for term in ("create", "add")),
            "update": any(enabled(operations.get(term, False)) for term in ("update", "edit")),
            "delete": any(enabled(operations.get(term, False)) for term in ("delete", "remove")),
            "select": any(enabled(operations.get(term, False)) for term in select_terms),
        })
        return normalized
    if isinstance(operations, str):
        operations = re.split(r"[\s,;|]+", operations)
    if isinstance(operations, list):
        values = {str(value).strip().lower() for value in operations}
        return {
            "create": bool({"create", "add"} & values),
            "update": bool({"update", "edit"} & values),
            "delete": bool({"delete", "remove"} & values),
            "select": bool(select_terms & values),
        }
    return defaults.copy()

_LAYOUT_ALIASES = {
    "nav": "nav-links",
    "navigation": "nav-links",
    "navbar": "nav-links",
    "side-nav": "nav-links",
    "top-nav": "nav-links",
    "footer-links": "link-grid",
    "footer-brand": "brand-strip",
    "service-strip": "service-bar",
}

_HEADER_TEMPLATE_LAYOUTS = {
    "promo-bar", "logo", "search-bar", "icon-actions", "nav-links", "main-header", "minimal-header",
    "commerce-header", "dashboard-header", "split-header", "app-header", "compact-header", "mega-header",
    "hero-header", "tabbed-header", "glass-header", "command-header", "site-nav",
}
_HEADER_SHELL_LAYOUTS = {
    "main-header", "minimal-header", "commerce-header", "dashboard-header",
    "split-header", "app-header", "compact-header", "mega-header", "hero-header", "tabbed-header",
    "glass-header", "command-header",
}
_HEADER_NAV_LAYOUTS = {
    "nav-links", "site-nav", "nav-bar", "main-header", "commerce-header", "dashboard-header",
    "split-header", "app-header", "compact-header", "mega-header", "hero-header", "tabbed-header",
    "glass-header", "command-header",
}
_PAGE_NAV_LAYOUTS = {"nav-links", "site-nav", "nav-bar", "tabbed-header", "mega-header"}
_FOOTER_TEMPLATE_LAYOUTS = {
    "service-bar", "link-grid", "brand-strip", "compact-footer", "legal-footer",
    "newsletter-footer", "social-footer", "mega-footer", "site-footer", "split-footer", "app-footer",
    "cta-footer", "minimal-footer",
}
_CHROME_TEMPLATE_LAYOUTS = _HEADER_TEMPLATE_LAYOUTS | _FOOTER_TEMPLATE_LAYOUTS
_VALID_SECTION_LAYOUTS = {"card", "list", "table", "detail", "gallery", "filter", "form", "activity_action", "activity_start", "activity_tasks"} | _CHROME_TEMPLATE_LAYOUTS
_DATA_SECTION_LAYOUTS = {"card", "list", "table", "detail", "gallery", "form"}
_VALID_SECTION_STYLE = {
    "color": {
        "blue", "sky", "cyan", "aqua", "teal", "turquoise", "green", "emerald", "lime",
        "yellow", "amber", "gold", "orange", "red", "rose", "pink", "purple", "violet",
        "indigo", "navy", "brown", "beige", "tan", "cream", "slate", "zinc", "neutral",
        "black", "white", "accent", "accent-secondary",
    },
    "density": {"compact", "normal", "spacious"},
    "nav_height": {"compact", "normal", "tall", "xl"},
    "shadow": {"none", "sm", "md", "lg", "xl"},
    "border": {"none", "light", "colored", "strong"},
    "bg": {"white", "light", "gray", "dark"},
    "header_style": {"default", "large", "small", "colored", "hidden"},
    "display_mode": {"grid", "carousel", "banner"},
    "card_style": {"default", "product", "category", "compact"},
    "list_style": {"default", "product", "cart-item", "related"},
    "form_style": {"default", "auth", "step", "summary"},
    "image_position": {"left", "top", "right"},
    "image_size": {"sm", "md", "lg"},
    "banner_height": {"sm", "md", "lg", "xl"},
    "image_ratio": {"wide", "16:9", "4:3", "1:1", "portrait"},
    "logo_size": {"sm", "md", "lg", "xl"},
    "logo_shape": {"rounded", "circle", "square"},
}

def _normalize_layout_alias(layout) -> str:
    if isinstance(layout, list):
        raw_values = layout
    else:
        raw_values = re.split(r"[,|/]+", str(layout or ""))
    values = [str(value or "").strip() for value in raw_values if str(value or "").strip()]
    for value in values:
        normalized = _LAYOUT_ALIASES.get(value, value)
        if normalized in _CHROME_TEMPLATE_LAYOUTS or normalized in {"card", "list", "table", "detail", "gallery", "filter", "form", "activity_action", "activity_start", "activity_tasks"}:
            return normalized
    value = values[0] if values else ""
    return _LAYOUT_ALIASES.get(value, value)

def _workflow_task_section(step: dict, model: str, model_attrs: dict) -> dict:
    page_id = _section_id(step.get("page_id") or step.get("page_name") or "workflow")
    model_id = _section_id(model)
    layout = _activity_layout_for_step(step.get("activity_node_name", ""), model)
    name_l = f"{step.get('activity_node_name', '')} {model}".lower()
    style = {
        "color": "accent",
        "density": "compact" if layout in {"list", "table"} else "normal",
        "shadow": "sm",
        "border": "light",
        "bg": "white",
    }
    if layout == "list":
        style["list_style"] = "default"
    if layout == "form":
        style["form_style"] = "step"
        style["cta_label"] = "Save"
    return {
        "id": f"{page_id}_{model_id}_task_content",
        "name": f"{step.get('activity_node_name') or 'Task'} {model}",
        "layout": layout,
        "primary_model": model,
        "class": model,
        "attributes": _model_field_names(model_attrs, model, 8),
        "operations": {
            "create": layout == "form",
            "update": layout in {"form", "list", "table", "detail"},
            "delete": layout in {"list", "table"},
        },
        "query": {},
        "col_span": 12,
        "position": "main",
        "style": style,
    }

def _ensure_workflow_pages(pages: list, sections: list, workflow_steps: list, model_attrs: dict | None = None, usecase_navigation: dict | None = None) -> tuple[list, list]:
    if not workflow_steps:
        return pages, sections
    model_attrs = model_attrs or {}
    known_models = set(model_attrs.keys())
    workflow_entries = (usecase_navigation or {}).get("workflow_entry_points") or []
    pages = [dict(p) for p in pages]
    sections = [dict(s) for s in sections]
    section_ids = {str(s.get("id")) for s in sections}
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}

    def page_action_id(p: dict) -> str:
        action = p.get("action") or {}
        if isinstance(action, dict):
            return str(action.get("value") or action.get("id") or "")
        return ""

    page_by_action = {page_action_id(p): p for p in pages if page_action_id(p)}
    # Fallback index: Step-5 pages from interface_planner have no action.value (no node UUID),
    # but their name matches the activity action name ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â use this to avoid creating duplicates.
    page_by_name = {
        _section_id(p.get("name") or ""): p
        for p in pages
        if _page_type_value(p) == "activity" and not page_action_id(p)
    }
    for step in workflow_steps:
        node_id = step["activity_node_id"]
        name_key = _section_id(step.get("activity_node_name") or "")
        page = page_by_action.get(node_id) or page_by_name.get(name_key)
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
        refs = page.get("sections") or []
        ref_ids = {str(ref.get("value") if isinstance(ref, dict) else ref) for ref in refs}
        has_existing_content = any(
            (section_map.get(sid) or {}).get("layout") not in {"filter", "activity_action", "activity_start", "activity_tasks"}
            and (section_map.get(sid) or {}).get("position", "main") == "main"
            for sid in ref_ids
        )
        for sid in list(ref_ids):
            existing = section_map.get(sid) or {}
            model = existing.get("primary_model") or existing.get("class")
            if (
                model
                and existing.get("position", "main") == "main"
                and existing.get("layout") not in {"filter", "activity_action", "activity_start", "activity_tasks"}
            ):
                desired_layout = _activity_layout_for_step(step.get("activity_node_name", ""), model)
                existing["layout"] = desired_layout
                if desired_layout == "form":
                    existing["role"] = "object_form"
                    existing["component"] = existing.get("component") or "ObjectForm"
                    style = existing.get("style") if isinstance(existing.get("style"), dict) else {}
                    style["form_style"] = style.get("form_style") or "step"
                    style["cta_label"] = style.get("cta_label") or "Save"
                    existing["style"] = style
                elif desired_layout == "list":
                    existing["role"] = existing.get("role") or "object_collection"
                else:
                    existing["role"] = existing.get("role") or "object_detail"
                existing["operations"] = {
                    "create": desired_layout == "form",
                    "update": desired_layout in {"form", "list", "table", "detail"},
                    "delete": desired_layout in {"list", "table"},
                }
        for model in ([] if has_existing_content else _activity_models_for_step(step, workflow_entries, known_models)[:1]):
            content = _workflow_task_section(step, model, model_attrs)
            if any((section_map.get(sid) or {}).get("primary_model") == model and (section_map.get(sid) or {}).get("layout") != "filter" for sid in ref_ids):
                continue
            sid = content["id"]
            suffix = 2
            base_sid = sid
            while sid in section_ids:
                sid = f"{base_sid}_{suffix}"
                suffix += 1
            content["id"] = sid
            sections.append(content)
            section_ids.add(sid)
            section_map[sid] = content
            refs.append({"value": sid})
            ref_ids.add(sid)
        existing_action_ids = [
            sid for sid in ref_ids
            if (section_map.get(sid) or {}).get("type") == "activity_action"
            or (section_map.get(sid) or {}).get("layout") == "activity_action"
        ]
        button_id = existing_action_ids[0] if existing_action_ids else f"{_section_id(page.get('id') or page.get('name'))}_workflow_action"
        if not existing_action_ids:
            if button_id not in section_ids:
                button = {
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
                }
                sections.append(button)
                section_map[button_id] = button
                section_ids.add(button_id)
            if button_id not in ref_ids:
                refs.append({"value": button_id})
            page["sections"] = refs
    return pages, sections

def _normalize_activity_action_sections(pages: list, sections: list) -> list:
    activity_page_section_ids = set()
    for page in pages:
        page_type = page.get("type", {}); page_type_value = page_type.get("value") if isinstance(page_type, dict) else page_type
        if page_type_value != "activity": continue
        for ref in page.get("sections") or []: activity_page_section_ids.add(str(ref.get("value") if isinstance(ref, dict) else ref))
    for section in sections:
        sid = str(section.get("id", "")); is_activity_action = section.get("type") == "activity_action" or section.get("layout") == "activity_action"
        if not is_activity_action: continue
        operations = _normalize_section_operations(section.get("operations"))
        section["operations"] = operations
        has_data_shape = bool(section.get("primary_model")) or bool(section.get("attributes")) or any(operations.values())
        if has_data_shape and sid not in activity_page_section_ids:
            section["layout"] = "list"; section.pop("type", None); section.pop("workflow", None); section.pop("workflow_action", None); section.pop("target_page", None); section.pop("targetPage", None); style = section.get("style") or {}
            if style.get("variant") in {"button", "link", "fab", "wizard_next", "auto"}: style.pop("variant", None)
            section["style"] = style; continue
        section["type"] = "activity_action"; section["layout"] = "activity_action"; section["primary_model"] = ""; section["class"] = ""; section["attributes"] = []; section["operations"] = {"create": False, "update": False, "delete": False}; section.setdefault("label", section.get("name") or "Continue"); workflow = section.get("workflow") or {}; workflow.setdefault("action", section.get("workflow_action") or "complete"); section["workflow"] = workflow
    # Deduplicate: per activity page, keep only one activity_action (prefer complete/complete_then_page)
    section_map = {str(s.get("id", "")): s for s in sections}
    to_remove: set = set()
    for page in pages:
        page_type = page.get("type", {}); page_type_value = page_type.get("value") if isinstance(page_type, dict) else page_type
        if page_type_value != "activity": continue
        ref_ids = [str(r.get("value") if isinstance(r, dict) else r) for r in (page.get("sections") or [])]
        action_ids = [sid for sid in ref_ids if (section_map.get(sid) or {}).get("layout") == "activity_action"]
        if len(action_ids) <= 1: continue
        action_ids.sort(key=lambda sid: 0 if (section_map.get(sid) or {}).get("workflow", {}).get("action") in {"complete", "complete_then_page"} else 1)
        extras = set(action_ids[1:])
        to_remove |= extras
        page["sections"] = [r for r in (page.get("sections") or []) if str(r.get("value") if isinstance(r, dict) else r) not in extras]
    if to_remove:
        sections = [s for s in sections if str(s.get("id", "")) not in to_remove]
    return sections

def _normalize_chrome_sections(sections: list) -> list:
    """Keep header/footer/navigation chrome out of workflow/action rendering paths."""
    normalized = []
    for section in sections or []:
        section = dict(section)
        layout = _normalize_layout_alias(section.get("layout"))
        role = str(section.get("role") or "").lower()
        position = section.get("position")
        is_chrome = (
            layout in _CHROME_TEMPLATE_LAYOUTS
            or position in {"header", "footer"}
            or role in {"header", "footer", "navigation", "nav", "brand"}
        )
        if is_chrome:
            # If the agent assigned a data/action layout to a chrome position, replace with
            # the positional default so _infer_section_component returns the right component.
            if layout not in _CHROME_TEMPLATE_LAYOUTS:
                layout = "site-footer" if position == "footer" else "main-header"
            section["layout"] = layout
            section["primary_model"] = ""
            section["class"] = ""
            section["attributes"] = []
            section["operations"] = {"create": False, "update": False, "delete": False, "select": False}
            section.pop("type", None)
            for key in ("workflow", "workflow_action", "target_page", "targetPage"):
                section.pop(key, None)
            # Clear any stale component so _infer_section_component runs fresh from layout.
            section.pop("component", None)
            section["component"] = _infer_section_component(section)
        normalized.append(section)
    return normalized

def _actor_name_from_context(system_context: dict, actor_id: str | None) -> str | None:
    for classifier in _as_list(system_context.get("classifiers"), "classifiers"):
        if str(classifier.get("id")) == str(actor_id): return (classifier.get("data") or {}).get("name")
    return None

def _apply_builtin_workflow_logic(interface_data: dict, system_id: str | None, actor_id: str | None) -> dict:
    data = dict(interface_data or {}); pages = list(data.get("pages") or []); sections = list(data.get("sections") or [])
    if system_id:
        system_context = _fetch_system_context_data(system_id)
        actor_name = _actor_name_from_context(system_context, actor_id)
        model_attrs = {}
        for c in _as_list(system_context.get("classifiers"), "classifiers"):
            cdata = c.get("data") or {}
            cname = cdata.get("name")
            if cname:
                model_attrs[cname] = {a.get("name") for a in cdata.get("attributes", []) if a.get("name")}
        usecase_navigation = _build_usecase_navigation(system_context, str(actor_id or ""), actor_name)
        workflow_steps = _workflow_plan(system_context, str(actor_id or ""), actor_name)
        pages, sections = _ensure_workflow_pages(pages, sections, workflow_steps, model_attrs, usecase_navigation)
    sections = _normalize_chrome_sections(_normalize_activity_action_sections(pages, sections)); data["pages"] = pages; data["sections"] = sections
    return data

def _page_type_value(page: dict) -> str:
    page_type = page.get("type")
    if isinstance(page_type, dict):
        return str(page_type.get("value") or "").strip().lower()
    return str(page_type or "").strip().lower()

def _infer_page_type_value(page: dict) -> str:
    explicit = _page_type_value(page)
    if explicit in {"normal", "activity"}:
        return explicit
    action = page.get("action")
    page_key = f"{page.get('id', '')} {page.get('name', '')} {page.get('display_name', '')}".lower()
    if action or "workflow" in page_key:
        return "activity"
    return "normal"

def _canonical_page_type(value: str) -> dict:
    if value == "activity":
        return {"value": "activity", "label": "Activity"}
    return {"value": "normal", "label": "Normal"}

def _ref_id(ref) -> str:
    return str(ref.get("value") if isinstance(ref, dict) else ref or "")

def _navigation_methods(names: list[str]) -> list[dict]:
    return [
        {"name": str(name), "label": str(name).replace("_", " "), "action": "navigate"}
        for name in names
        if name
    ]

def _workflow_icon_links(usecase_navigation: dict, page_by_id: dict | None = None) -> list[dict]:
    links = []
    seen = set()
    page_by_id = page_by_id or {}
    for entry in (usecase_navigation or {}).get("workflow_entry_points") or []:
        page_id = _section_id(entry.get("page_id") or entry.get("page_name"))
        if not page_id or page_id in seen:
            continue
        page = page_by_id.get(page_id) or {}
        page_name = page.get("name") or entry.get("page_name") or _page_name(page_id)
        label = entry.get("button_label") or entry.get("label") or entry.get("usecase_name") or "Start"
        links.append({"page": page_name, "label": label, "icon": "task"})
        seen.add(page_id)
    return links

def _infer_section_component(section: dict) -> str:
    """
    Generically infers a suitable high-fidelity component name based on 
    layout and model characteristics, avoiding app-specific hardcoding.
    """
    component = section.get("component")
    if component:
        return str(component)
    
    layout = _normalize_layout_alias(section.get("layout"))
    role = str(section.get("role") or "")
    model_name = str(section.get("primary_model") or section.get("class") or "").lower()
    attrs = {str(a.get("name") if isinstance(a, dict) else a).lower() for a in section.get("attributes", [])}
    
    # Generic rules based on data traits
    has_image = any(term in attrs for term in ("image", "img", "url", "avatar", "photo", "media"))
    is_person = any(term in model_name for term in ("user", "customer", "employee", "doctor", "member", "actor"))
    
    if layout == "logo": return "Logo"
    if layout == "search-bar": return "SearchBar"
    if layout == "icon-actions": return "IconActions"
    if layout in _FOOTER_TEMPLATE_LAYOUTS: return "FooterTemplate"
    if layout in _HEADER_TEMPLATE_LAYOUTS and layout not in {"logo", "search-bar", "icon-actions", "site-nav", "nav-links"}:
        return "HeaderTemplate"
    if layout in {"site-nav", "nav-links", "nav-bar"}: return "NavBar"
    
    if layout == "form":
        if any(term in model_name for term in ("address", "location")): return "AddressForm"
        if any(term in model_name for term in ("payment", "card", "billing")): return "PaymentForm"
        return "ObjectForm"
        
    if layout == "gallery" or layout == "card":
        if has_image: return "ImageCardGrid" if layout == "gallery" else "ImageCard"
        if is_person: return "PersonCardGrid"
        return "ObjectCardGrid"
        
    if layout == "detail":
        return "ObjectDetailPanel" if not has_image else "MediaDetailPanel"
        
    if layout == "table": return "DataTable"
    if layout == "list": return "ObjectList"
    if layout == "filter": return "FilterPanel"
    
    return "SectionPanel"

def _field_layout_field_refs(field_layout) -> set[str]:
    refs = set()
    if not isinstance(field_layout, dict):
        return refs
    slot_keys = {"image", "video", "media", "avatar", "hero", "title", "subtitle", "primary", "price", "description", "count"}
    list_keys = {"secondary", "badges", "meta", "facts", "fields", "hidden"}
    for key, value in field_layout.items():
        if key in slot_keys and isinstance(value, str) and value:
            refs.add(value)
        elif key in list_keys and isinstance(value, list):
            refs.update(str(v) for v in value if isinstance(v, str) and v)
        elif key == "columns" and isinstance(value, list):
            for column in value:
                if isinstance(column, dict) and column.get("field"):
                    refs.add(str(column["field"]))
        elif key == "groups" and isinstance(value, list):
            for group in value:
                if isinstance(group, dict) and isinstance(group.get("fields"), list):
                    refs.update(str(v) for v in group["fields"] if isinstance(v, str) and v)
        elif key == "field_styles" and isinstance(value, dict):
            refs.update(str(field) for field in value.keys() if field)
    return refs

_FIELD_SLOT_MAP = {
    "card": {"image", "video", "media", "title", "subtitle", "primary", "secondary", "hidden"},
    "gallery": {"image", "video", "media", "title", "subtitle", "primary", "secondary", "hidden"},
    "list": {"columns", "hidden"},
    "table": {"columns", "hidden"},
    "detail": {"image", "video", "media", "title", "hero", "fields", "hidden"},
    "form": {"fields", "hidden"},
    "filter": {"fields", "hidden"},
}
_COMPONENT_FIELD_SLOT_MAP = {
    "ProductCardGrid": _FIELD_SLOT_MAP["card"],
    "CategoryTileGrid": {"image", "title", "subtitle", "secondary", "hidden"},
    "PersonCardGrid": {"image", "title", "subtitle", "secondary", "hidden"},
    "CardGrid": _FIELD_SLOT_MAP["card"],
    "DataTable": _FIELD_SLOT_MAP["table"],
    "ObjectList": _FIELD_SLOT_MAP["list"],
    "LineItemList": _FIELD_SLOT_MAP["list"],
    "RelatedObjectList": _FIELD_SLOT_MAP["list"],
    "ProductDetailPanel": _FIELD_SLOT_MAP["detail"],
    "DetailPanel": _FIELD_SLOT_MAP["detail"],
    "SummaryPanel": {"title", "fields", "hidden"},
    "ObjectForm": _FIELD_SLOT_MAP["form"],
    "AddressForm": _FIELD_SLOT_MAP["form"],
    "PaymentMethodForm": _FIELD_SLOT_MAP["form"],
    "ReviewForm": _FIELD_SLOT_MAP["form"],
    "FilterPanel": _FIELD_SLOT_MAP["filter"],
    "SearchBar": _FIELD_SLOT_MAP["filter"],
    "Logo": set(),
    "BrandLockup": set(),
    "ImageLogo": set(),
    "IconActions": set(),
    "SiteFooter": set(),
    "FooterLinkGrid": set(),
}

def _attr_name(attr) -> str:
    return str(attr.get("name") if isinstance(attr, dict) else attr or "")

def _attr_type(attr) -> str:
    return str(attr.get("type") if isinstance(attr, dict) else "").lower()

def _field_kind(name: str, type_name: str = "") -> str:
    low = name.lower()
    if type_name in {"image", "video"} or any(term in low for term in ("image", "img", "photo", "avatar", "thumbnail", "media", "video", "poster")):
        return "media"
    if low in {"id", "uuid"} or low.endswith("_id") or any(term in low for term in ("internal", "password", "token", "secret")):
        return "hidden"
    if any(term in low for term in ("name", "title", "code", "number", "label", "subject")):
        return "title"
    if any(term in low for term in ("price", "amount", "total", "status", "state", "date", "created", "updated", "count", "quantity")):
        return "primary"
    if any(term in low for term in ("description", "summary", "body", "content", "note", "comment", "message")):
        return "body"
    return "secondary"

def _supported_field_slots(section: dict) -> set[str]:
    component = str(section.get("component") or "")
    layout = str(section.get("layout") or "")
    return set(_COMPONENT_FIELD_SLOT_MAP.get(component) or _FIELD_SLOT_MAP.get(layout) or set())

def _field_list(value) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        if isinstance(item, dict) and item.get("field"):
            result.append(str(item["field"]))
        elif isinstance(item, str) and item:
            result.append(item)
    return result

def _component_for_layout(section: dict, layout: str) -> str:
    if layout == "table":
        return "DataTable"
    if layout == "list":
        return "ObjectList"
    if layout == "form":
        return "ObjectForm"
    if layout == "filter":
        return "FilterPanel"
    section = {**section, "layout": layout}
    return _infer_section_component(section)

def _normalize_field_layout(section: dict) -> dict:
    attrs = section.get("attributes") or []
    attr_names = [_attr_name(attr) for attr in attrs if _attr_name(attr)]
    if not attr_names or not section.get("primary_model"):
        return {}
    attr_set = set(attr_names)
    supported = _supported_field_slots(section)
    if not supported:
        return {}

    raw = section.get("field_layout") if isinstance(section.get("field_layout"), dict) else {}
    existing_styles = raw.get("field_styles") if isinstance(raw.get("field_styles"), dict) else {}
    cleaned_styles = {}
    for fname, cfg in existing_styles.items():
        if fname not in attr_set or not isinstance(cfg, dict):
            continue
        clean = {}
        if isinstance(cfg.get("order"), int) or str(cfg.get("order", "")).isdigit():
            clean["order"] = int(cfg.get("order"))
        if str(cfg.get("col_span", "")) in {"3", "4", "6", "8", "12"}:
            clean["col_span"] = int(cfg.get("col_span"))
        if cfg.get("height") in {"sm", "md", "lg", "xl"}:
            clean["height"] = cfg.get("height")
        if cfg.get("text_size") in {"xs", "sm", "md", "lg", "xl"}:
            clean["text_size"] = cfg.get("text_size")
        if cfg.get("align") in {"left", "center", "right"}:
            clean["align"] = cfg.get("align")
        if cfg.get("label") in {"show", "hidden"}:
            clean["label"] = cfg.get("label")
        if cfg.get("visible") in {"show", "hidden"}:
            clean["visible"] = cfg.get("visible")
        if clean:
            cleaned_styles[fname] = clean

    hidden = [f for f in _field_list(raw.get("hidden")) if f in attr_set]
    for attr in attrs:
        name = _attr_name(attr)
        if name and _field_kind(name, _attr_type(attr)) == "hidden" and name not in hidden:
            hidden.append(name)
    for name, cfg in cleaned_styles.items():
        if cfg.get("visible") == "hidden" and name not in hidden:
            hidden.append(name)
    visible_names = [name for name in attr_names if name not in set(hidden)]

    def first_existing(keys: list[str]) -> str:
        for key in keys:
            value = raw.get(key)
            if isinstance(value, str) and value in visible_names:
                return value
        return ""

    media = first_existing(["media", "image", "video", "avatar"])
    title = first_existing(["title"])
    subtitle = first_existing(["subtitle"])
    primary = first_existing(["primary", "price", "count"])
    secondary = [f for f in (_field_list(raw.get("secondary")) + _field_list(raw.get("meta")) + _field_list(raw.get("facts"))) if f in visible_names]
    fields = [f for f in (_field_list(raw.get("fields")) + _field_list(raw.get("columns"))) if f in visible_names]
    hero = [f for f in _field_list(raw.get("hero")) if f in visible_names]

    by_kind = {name: _field_kind(name, _attr_type(attr)) for name, attr in zip(attr_names, attrs)}
    if not media:
        media = next((n for n in visible_names if by_kind.get(n) == "media"), "")
    if not title:
        title = next((n for n in visible_names if by_kind.get(n) == "title"), "")
    if not primary:
        primary = next((n for n in visible_names if by_kind.get(n) == "primary" and n != title), "")
    if not secondary:
        secondary = [n for n in visible_names if n not in {media, title, primary} and by_kind.get(n) in {"secondary", "body", "primary"}][:4]
    if not fields:
        fields = visible_names
    if not hero:
        hero = [n for n in visible_names if n in {title, primary} or by_kind.get(n) == "body"][:4]

    out = {}
    if "image" in supported and media:
        media_attr = next((a for a in attrs if _attr_name(a) == media), None)
        if _attr_type(media_attr) == "video":
            if "video" in supported:
                out["video"] = media
            elif "media" in supported:
                out["media"] = media
        else:
            out["image"] = media
    elif "media" in supported and media:
        out["media"] = media
    if "title" in supported and title:
        out["title"] = title
    if "subtitle" in supported and subtitle:
        out["subtitle"] = subtitle
    if "primary" in supported and primary:
        out["primary"] = primary
    if "secondary" in supported:
        out["secondary"] = [f for f in secondary if f not in {media, title, primary}]
    if "columns" in supported:
        out["columns"] = fields
    if "fields" in supported:
        out["fields"] = fields
    if "hero" in supported:
        out["hero"] = hero
    if "hidden" in supported and hidden:
        out["hidden"] = hidden
    if cleaned_styles:
        out["field_styles"] = cleaned_styles
    return out

def _model_field_names(model_attrs: dict, model: str, limit: int = 6) -> list[str]:
    preferred = ["image_url", "photo_url", "avatar_url", "thumbnail_url", "poster_url", "cover_url", "logo_url", "name", "title", "status", "price", "total", "quantity", "description", "created_at"]
    attrs = list(model_attrs.get(model) or [])
    media = [name for name in attrs if name and _field_kind(name) == "media"]
    selected = [name for name in preferred if name in attrs]
    for name in media:
        if name not in selected:
            selected.insert(0, name)
    selected.extend([name for name in attrs if name and name not in selected and name.lower() != "id"])
    return selected[:limit] or attrs[:limit]

def _finalize_data_section_bindings(sections: list, model_attrs: dict, limit: int = 8) -> list:
    data_layouts = {"card", "list", "table", "detail", "gallery", "filter", "form"}
    model_names = set(model_attrs.keys())
    model_names_fuzzy = {re.sub(r"[\s_-]", "", str(name or "")).lower(): name for name in model_names}

    def canonical_model(name: str) -> str:
        if name in model_attrs:
            return name
        return model_names_fuzzy.get(re.sub(r"[\s_-]", "", str(name or "")).lower(), "")

    fixed = []
    for section in sections:
        section = dict(section)
        section["layout"] = _normalize_layout_alias(section.get("layout"))
        layout = section.get("layout", "")
        component = str(section.get("component") or "")
        if component == "NavBar" and layout in {"", "nav", "navigation", "navbar"}:
            section["layout"] = "nav-links"
            layout = "nav-links"

        pm = canonical_model(str(section.get("primary_model") or section.get("class") or ""))
        if pm:
            section["primary_model"] = pm
            section["class"] = pm

        if pm and layout in data_layouts:
            valid_attrs = set(model_attrs.get(pm) or [])
            normalized_attrs = []
            for attr in section.get("attributes") or []:
                attr_name = attr.get("name", attr) if isinstance(attr, dict) else attr
                attr_name = str(attr_name or "")
                if not attr_name:
                    continue
                if "." in attr_name:
                    first, rest = attr_name.split(".", 1)
                    related_model = canonical_model(first)
                    if related_model and rest in set(model_attrs.get(related_model) or []):
                        normalized = dict(attr) if isinstance(attr, dict) else {"name": attr_name}
                        normalized["name"] = f"{related_model}.{rest}"
                        normalized.setdefault("source", "related")
                        normalized.setdefault("readonly", True)
                        normalized_attrs.append(normalized)
                    continue
                if attr_name in valid_attrs:
                    normalized_attrs.append(attr)
            if not normalized_attrs:
                normalized_attrs = _model_field_names(model_attrs, pm, limit)
            section["attributes"] = normalized_attrs
        section["component"] = _infer_section_component(section)
        section["field_layout"] = _normalize_field_layout(section)
        fixed.append(section)
    return fixed

def _snake_name(value: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(value or ""))
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")

def _guess_relation_field(child_model: str, parent_model: str, model_attrs: dict) -> str:
    attrs = set(model_attrs.get(child_model) or [])
    parent_snake = _snake_name(parent_model)
    candidates = [
        f"{parent_snake}_id",
        f"{parent_snake}id",
        f"{parent_model}_id",
        f"{parent_model}Id",
        f"{parent_model.lower()}_id",
        f"{parent_model.lower()}id",
    ]
    for candidate in candidates:
        if candidate in attrs:
            return candidate
    return ""

def _related_models_from_attrs(section: dict, model_attrs: dict) -> list[str]:
    related: list[str] = []
    known = set(model_attrs.keys())
    known_fuzzy = {re.sub(r"[\s_-]", "", name).lower(): name for name in known}
    for attr in section.get("attributes") or []:
        name = attr.get("name", attr) if isinstance(attr, dict) else attr
        if "." not in str(name):
            continue
        prefix = str(name).split(".", 1)[0]
        model = prefix if prefix in known else known_fuzzy.get(re.sub(r"[\s_-]", "", prefix).lower(), "")
        if model and model not in related and model != section.get("primary_model"):
            related.append(model)
    return related

def _default_join_for_models(source_model: str, related_model: str) -> dict:
    related_snake = _snake_name(related_model)
    source_snake = _snake_name(source_model)
    return {
        "type": "left",
        "model": related_model,
        "on": f"{source_model}.{related_snake}_id = {related_model}.id"
        if related_snake
        else f"{source_model}.{source_snake}_id = {related_model}.id",
    }

def _section_is_data(section: dict) -> bool:
    layout = _normalize_layout_alias(section.get("layout"))
    role = str(section.get("role") or "")
    return bool(
        section.get("primary_model")
        and (
            layout in {"card", "list", "table", "detail", "gallery", "filter", "form", "calendar", "timeline", "map"}
            or role in DATA_SECTION_ROLES
            or section.get("attributes")
        )
    )

def _section_is_collection(section: dict) -> bool:
    layout = _normalize_layout_alias(section.get("layout"))
    role = str(section.get("role") or "")
    return layout in {"card", "list", "table", "gallery", "calendar", "timeline", "map"} or role in {"object_collection", "child_collection", "related_collection"}

def _ensure_section_data_relationships(
    pages: list,
    sections: list,
    model_attrs: dict,
) -> tuple[list, list]:
    """Populate SP data-source, related-object, and item-click metadata from OOUI page structure."""
    pages = [dict(p) for p in pages or []]
    sections = [dict(s) for s in sections or []]
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}

    detail_page_by_model: dict[str, str] = {}
    detail_section_by_page: dict[str, dict] = {}
    for page in pages:
        page_id = str(page.get("id") or "")
        page_model = str(page.get("primary_model") or "")
        refs = [_ref_id(ref) for ref in page.get("sections") or [] if _ref_id(ref)]
        data_sections = [section_map.get(ref) for ref in refs if section_map.get(ref)]
        candidates = [
            s for s in data_sections
            if s
            and str(s.get("primary_model") or "") == page_model
            and (
                str(s.get("role") or "") == "object_detail"
                or _normalize_layout_alias(s.get("layout")) in {"detail", "form"}
            )
        ]
        if not candidates:
            candidates = [
                s for s in data_sections
                if s
                and str(s.get("role") or "") == "object_detail"
                and str(s.get("primary_model") or "")
            ]
        if candidates:
            detail_section_by_page[page_id] = candidates[0]
            model = str(candidates[0].get("primary_model") or "")
            if model and model not in detail_page_by_model:
                detail_page_by_model[model] = page.get("name") or page_id

    for page in pages:
        page_id = str(page.get("id") or "")
        source_section = detail_section_by_page.get(page_id)
        source_id = str((source_section or {}).get("id") or "")
        source_model = str((source_section or {}).get("primary_model") or "")
        for ref in page.get("sections") or []:
            section = section_map.get(_ref_id(ref) or "")
            if not section or not _section_is_data(section):
                continue
            model = str(section.get("primary_model") or "")
            section.setdefault("class", model)

            data_source = dict(section.get("data_source") or {})
            data_source["mode"] = "query"
            data_source.setdefault("from", {"model": model})
            if not isinstance(data_source.get("from"), dict) or not data_source["from"].get("model"):
                data_source["from"] = {"model": model}
            joins = list(data_source.get("joins") or [])
            joined_models = {str(join.get("model") or "") for join in joins if isinstance(join, dict)}
            for related_model in _related_models_from_attrs(section, model_attrs):
                if related_model not in joined_models:
                    joins.append(_default_join_for_models(model, related_model))
                    joined_models.add(related_model)
            data_source["joins"] = joins
            section["data_source"] = data_source

            query = dict(section.get("query") or {})
            role = str(section.get("role") or "")
            if source_id and source_id != str(section.get("id") or "") and _section_is_collection(section):
                if not section.get("related_to"):
                    section["related_to"] = source_id
                relationship = dict(section.get("relationship") or {})
                if source_model and source_model == model:
                    relationship.setdefault("mode", "same_parent")
                    query.setdefault("exclude_source", True)
                else:
                    relationship.setdefault("mode", "direct")
                    relation_field = section.get("relation_field") or _guess_relation_field(model, source_model, model_attrs)
                    if relation_field:
                        section["relation_field"] = relation_field
                relationship.setdefault("source_model", source_model)
                relationship.setdefault("target_model", model)
                section["relationship"] = relationship
                if role in {"child_collection", "related_collection"}:
                    query.setdefault("limit", 4)
            section["query"] = query

            if _section_is_collection(section):
                target_page = detail_page_by_model.get(model)
                if target_page and target_page != page.get("name"):
                    behavior = dict(section.get("behavior") or {})
                    item_click = dict(behavior.get("item_click") or {})
                    if not item_click.get("type") or item_click.get("type") == "none":
                        item_click.update({"type": "navigate", "target_page": target_page})
                    elif item_click.get("type") == "navigate" and not item_click.get("target_page"):
                        item_click["target_page"] = target_page
                    behavior["item_click"] = item_click
                    section["behavior"] = behavior

    return pages, list(section_map.values())

def _infer_section_layout(page: dict, candidate_index: int = 0) -> str:
    tokens = _name_tokens(f"{page.get('name', '')} {page.get('id', '')}")
    if tokens & {"detail", "view", "profile", "summary"}:
        return "detail"
    if tokens & {"form", "enter", "submit", "create", "edit", "update", "provide", "select", "choose"}:
        return "form"
    if tokens & {"list", "manage", "track", "history", "item", "line", "entry", "row"}:
        return "list"
    if tokens & {"browse", "catalog", "gallery", "showcase", "discover"}:
        return "gallery" if candidate_index % 2 == 0 else "card"
    return ("card", "table", "list")[candidate_index % 3]

def _fallback_model_for_page(page: dict, known_models: set[str]) -> str:
    if page.get("primary_model"):
        return str(page.get("primary_model"))
    page_name = f"{page.get('name', '')} {page.get('id', '')}".lower()
    for model in sorted(known_models):
        if model.lower() in page_name:
            return model
    non_process = [m for m in sorted(known_models) if m.lower() not in {"user", "group", "permission"}]
    return non_process[0] if non_process else ""

def _default_category_for_model(model: str, model_id_by_name: dict[str, str] | None = None) -> dict | None:
    model = str(model or "").strip()
    if not model:
        return None
    model_id_by_name = model_id_by_name or {}
    return {
        "label": model,
        "value": {
            "id": str(model_id_by_name.get(model) or model),
            "name": model,
        },
    }

def _model_for_page_category(page: dict, sections_by_id: dict[str, dict], known_models: set[str]) -> str:
    explicit = str(page.get("primary_model") or "").strip()
    if explicit in known_models:
        return explicit
    for ref in page.get("sections") or []:
        section = sections_by_id.get(_ref_id(ref) or "")
        model = str((section or {}).get("primary_model") or "").strip()
        if model in known_models:
            return model
    fallback = _fallback_model_for_page(page, known_models)
    return fallback if fallback in known_models else ""

def _assign_default_page_categories(pages: list, sections: list, model_id_by_name: dict[str, str] | None = None) -> list:
    model_id_by_name = model_id_by_name or {}
    known_models = set(model_id_by_name.keys())
    sections_by_id = {str(s.get("id")): s for s in sections or [] if s.get("id")}
    next_pages = []
    for raw in pages or []:
        page = dict(raw)
        if _page_type_value(page) == "activity":
            page["category"] = None
            next_pages.append(page)
            continue
        if page.get("category"):
            next_pages.append(page)
            continue
        model = _model_for_page_category(page, sections_by_id, known_models)
        page["category"] = _default_category_for_model(model, model_id_by_name)
        next_pages.append(page)
    return next_pages

def _merge_page_categories(categories: list, pages: list) -> list:
    merged = []
    seen = set()
    for category in categories or []:
        if not isinstance(category, dict):
            continue
        cid = str(category.get("id") or ((category.get("value") or {}).get("id") if isinstance(category.get("value"), dict) else "") or "")
        name = str(category.get("name") or ((category.get("value") or {}).get("name") if isinstance(category.get("value"), dict) else "") or category.get("label") or "")
        if not cid and not name:
            continue
        key = cid or name
        seen.add(key)
        merged.append(category)
    for page in pages or []:
        category = page.get("category")
        if not isinstance(category, dict):
            continue
        value = category.get("value") if isinstance(category.get("value"), dict) else {}
        cid = str(value.get("id") or category.get("id") or "")
        name = str(value.get("name") or category.get("name") or category.get("label") or "")
        key = cid or name
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append({"id": cid or name, "name": name or cid})
    return merged

def _default_section_for_page(page: dict, model: str, model_attrs: dict, candidate_index: int) -> dict:
    layout = _infer_section_layout(page, candidate_index)
    page_id = _section_id(page.get("id") or page.get("name") or "page")
    sid = f"{page_id}_{_section_id(model or 'content')}_{layout}"
    attrs = _model_field_names(model_attrs, model, 8 if layout in {"table", "detail"} else 5)
    operations = {"create": layout == "form", "update": layout in {"detail", "form"}, "delete": False}
    style = {
        "color": "accent",
        "density": ("normal", "compact", "spacious")[candidate_index % 3],
        "shadow": "md" if layout in {"card", "gallery", "detail"} else "sm",
        "border": "light",
        "bg": "white",
        "header_style": "large" if layout in {"gallery", "detail"} else "default",
    }
    if layout in {"card", "gallery"}:
        style.update({"display_mode": "grid", "card_style": "default", "columns": "3"})
    elif layout == "list":
        style.update({"list_style": "default"})
    elif layout == "form":
        style.update({"form_style": "step", "cta_label": "Continue"})
    elif layout == "detail":
        style.update({"image_position": "left", "image_size": "md"})
    return {
        "id": sid,
        "name": page.get("name", sid).replace("_", " "),
        "layout": layout,
        "primary_model": model,
        "class": model,
        "attributes": attrs,
        "operations": operations,
        "query": {},
        "col_span": 12,
        "position": "main",
        "style": style,
    }

def _header_sections_for_candidate(normal_pages: list, candidate_index: int = 0, model_attrs: dict | None = None) -> list[dict]:
    """Create a single editable header template section with deterministic variation."""
    nav_methods = _navigation_methods([p.get("name") for p in normal_pages if p.get("name")])
    variant = candidate_index % 3
    ops = {"create": False, "update": False, "delete": False}
    templates = ("main-header", "split-header", "dashboard-header", "commerce-header", "app-header", "compact-header", "mega-header", "minimal-header", "hero-header", "tabbed-header", "glass-header", "command-header")
    layout = templates[candidate_index % len(templates)]
    style = {
        "color": "accent",
        "density": ("normal", "compact", "spacious")[variant],
        "shadow": ("sm", "md", "lg")[variant],
        "border": "light",
        "bg": "white",
        "header_variant": {
            "main-header": "commerce",
            "commerce-header": "commerce",
            "split-header": "split-dark",
            "dashboard-header": "dashboard",
            "app-header": "app",
            "compact-header": "compact",
            "mega-header": "mega",
            "minimal-header": "minimal",
            "hero-header": "hero",
            "tabbed-header": "tabs",
            "glass-header": "glass",
            "command-header": "command",
        }.get(layout, "commerce"),
        "nav_height": ("normal", "compact", "tall")[variant],
    }
    return [{
        "id": "app_header_template",
        "name": "Header",
        "role": "header",
        "layout": layout,
        "component": "HeaderTemplate",
        "primary_model": "",
        "class": "",
        "attributes": [],
        "operations": ops,
        "methods": nav_methods,
        "text": "Search",
        "col_span": 12,
        "position": "header",
        "style": style,
    }]

def _footer_sections_for_candidate(candidate_index: int = 0, normal_pages: list | None = None) -> list[dict]:
    ops = {"create": False, "update": False, "delete": False}
    templates = ("site-footer", "mega-footer", "legal-footer", "newsletter-footer", "compact-footer", "social-footer", "split-footer", "app-footer", "cta-footer", "minimal-footer")
    layout = templates[candidate_index % len(templates)]
    nav_methods = _navigation_methods([p.get("name") for p in (normal_pages or []) if p.get("name")])
    return [{
        "id": "app_footer_template",
        "name": "Footer",
        "role": "footer",
        "layout": layout,
        "component": "FooterTemplate",
        "primary_model": "",
        "class": "",
        "attributes": [],
        "operations": ops,
        "methods": nav_methods or ["Help", "Privacy", "Terms", "Contact"],
        "col_span": 12,
        "position": "footer",
        "style": {
            "color": "accent",
            "density": ("normal", "compact", "spacious")[candidate_index % 3],
            "shadow": "sm",
            "border": "light",
            "bg": "white",
            "footer_variant": layout,
        },
    }]

def _top_nav_section_for_candidate(normal_pages: list, candidate_index: int = 0) -> dict:
    nav_methods = _navigation_methods([p.get("name") for p in normal_pages if p.get("name")])
    return {
        "id": "app_page_nav",
        "name": "Navigation",
        "role": "navigation",
        "layout": "site-nav",
        "component": "NavBar",
        "primary_model": "",
        "class": "",
        "attributes": [],
        "operations": {"create": False, "update": False, "delete": False, "select": False},
        "methods": nav_methods,
        "col_span": 12,
        "position": "header",
        "style": {
            "color": "accent",
            "density": ("normal", "compact", "spacious")[int(candidate_index or 0) % 3],
            "shadow": "sm",
            "border": "light",
            "bg": "white",
            "variant": "page-nav",
            "nav_height": ("compact", "normal", "tall")[int(candidate_index or 0) % 3],
        },
    }

def _sidebar_nav_section_for_candidate(normal_pages: list, candidate_index: int = 0) -> dict:
    nav_methods = _navigation_methods([p.get("name") for p in normal_pages if p.get("name")])
    side = "left" if int(candidate_index or 0) % 2 == 0 else "right"
    return {
        "id": "app_sidebar_nav",
        "name": "Navigation",
        "role": "navigation",
        "layout": "site-nav",
        "component": "NavBar",
        "primary_model": "",
        "class": "",
        "attributes": [],
        "operations": {"create": False, "update": False, "delete": False, "select": False},
        "methods": nav_methods,
        "col_span": 12,
        "position": "sidebar",
        "style": {
            "color": "accent",
            "density": ("normal", "compact", "spacious")[int(candidate_index or 0) % 3],
            "shadow": "sm",
            "border": "light",
            "bg": "white",
            "variant": "rail",
            "sidebar_side": side,
            "sidebar_width": 3,
            "nav_height": "tall",
            "full_height": True,
        },
    }

def _ensure_normal_page_navigation(pages: list, sections: list, normal_pages: list, candidate_index: int = 0) -> tuple[list, list]:
    if not normal_pages:
        return pages, sections
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    nav_methods = _navigation_methods([p.get("name") for p in normal_pages if p.get("name")])
    for section in sections:
        if section.get("position") == "footer" or _normalize_layout_alias(section.get("layout")) in _FOOTER_TEMPLATE_LAYOUTS:
            existing = section.get("methods") or []
            existing_names = {
                str(m.get("name") if isinstance(m, dict) else m).strip().lower()
                for m in existing
            }
            if nav_methods and (not existing_names or existing_names.issubset({"help", "privacy", "terms", "contact"})):
                section["methods"] = nav_methods
    nav_ids = [
        sid for sid, section in section_map.items()
        if (
            _normalize_layout_alias(section.get("layout")) in {"site-nav", "nav-links", "nav-bar"}
            or str(section.get("component") or "") == "NavBar"
            or str(section.get("role") or "").lower() == "navigation"
        )
    ]
    header_nav_ids = [
        sid for sid, section in section_map.items()
        if section.get("position") == "header"
        and _normalize_layout_alias(section.get("layout")) in _PAGE_NAV_LAYOUTS
    ]
    sidebar_nav_ids = [
        sid for sid in nav_ids
        if (section_map.get(sid) or {}).get("position") == "sidebar"
    ]
    keep_nav_id = header_nav_ids[0] if header_nav_ids else (sidebar_nav_ids[0] if sidebar_nav_ids else "")
    duplicate_nav_ids = set(nav_ids)
    if keep_nav_id:
        duplicate_nav_ids.discard(keep_nav_id)
    if duplicate_nav_ids:
        sections = [s for s in sections if str(s.get("id") or "") not in duplicate_nav_ids]
        section_map = {str(s.get("id")): s for s in sections if s.get("id")}
        for page in pages:
            page["sections"] = [
                ref for ref in (page.get("sections") or [])
                if _ref_id(ref) not in duplicate_nav_ids
            ]

    if not keep_nav_id:
        nav_section = (
            _sidebar_nav_section_for_candidate(normal_pages, candidate_index)
            if int(candidate_index or 0) % 3 == 2
            else _top_nav_section_for_candidate(normal_pages, candidate_index)
        )
        sid = nav_section["id"]
        suffix = 2
        while sid in section_map:
            sid = f"{nav_section['id']}_{suffix}"
            suffix += 1
        nav_section["id"] = sid
        sections.append(nav_section)
        section_map[sid] = nav_section
        keep_nav_id = sid
    elif int(candidate_index or 0) % 3 != 2 and keep_nav_id in sidebar_nav_ids and not header_nav_ids:
        nav_section = section_map.get(keep_nav_id) or {}
        nav_section["position"] = "header"
        nav_section["layout"] = "nav-links"
        nav_section["component"] = "NavBar"
        style = dict(nav_section.get("style") or {})
        style.pop("sidebar_side", None)
        style.pop("sidebar_width", None)
        style["variant"] = "page-nav"
        nav_section["style"] = style

    if keep_nav_id:
        for page in normal_pages:
            refs = [{"value": _ref_id(ref)} for ref in page.get("sections") or [] if _ref_id(ref)]
            ref_ids = {_ref_id(ref) for ref in refs}
            if keep_nav_id not in ref_ids:
                keep_nav_section = section_map.get(keep_nav_id) or {}
                if keep_nav_section.get("position") == "sidebar":
                    page["sections"] = [{"value": keep_nav_id}] + refs
                else:
                    page["sections"] = refs
    return pages, sections

def _ensure_mapping_chrome_sections(pages: list, sections: list) -> tuple[list, list]:
    """Add stable app chrome during UML mapping so candidates can focus on visual variants."""
    pages = [dict(p) for p in pages or []]
    sections = [dict(s) for s in sections or []]
    normal_pages = [p for p in pages if _page_type_value(p) != "activity"]
    if not normal_pages:
        return pages, sections

    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    if not any(s.get("position") == "header" for s in sections):
        _inject_chrome_sections(
            _header_sections_for_candidate(normal_pages, 0),
            sections,
            section_map,
            normal_pages,
            prepend=True,
        )

    if not any(s.get("position") == "footer" for s in sections):
        _inject_chrome_sections(
            _footer_sections_for_candidate(0, normal_pages),
            sections,
            section_map,
            normal_pages,
            prepend=False,
        )

    pages, sections = _ensure_normal_page_navigation(pages, sections, normal_pages, 0)
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    global_region_ids = [
        str(s.get("id"))
        for s in sections
        if s.get("id") and s.get("position") in {"header", "sidebar", "footer"}
    ]

    for page in normal_pages:
        refs = [{"value": _ref_id(ref)} for ref in page.get("sections") or [] if _ref_id(ref)]
        ref_ids = {_ref_id(ref) for ref in refs}
        before = [
            {"value": sid}
            for sid in global_region_ids
            if sid not in ref_ids and (section_map.get(sid) or {}).get("position") in {"header", "sidebar"}
        ]
        after = [
            {"value": sid}
            for sid in global_region_ids
            if sid not in ref_ids and (section_map.get(sid) or {}).get("position") == "footer"
        ]
        if before or after:
            page["sections"] = before + refs + after

    return pages, sections

def _ensure_mapping_content_sections(
    pages: list,
    sections: list,
    usecase_navigation: dict,
    model_attrs: dict,
) -> tuple[list, list]:
    """Materialize OOUI/data support sections once during UML mapping, not during candidate generation."""
    pages, sections = _materialize_nav_plan_sections(
        pages,
        sections,
        (usecase_navigation or {}).get("nav_plan") or {},
        model_attrs,
    )
    pages, sections = _ensure_workflow_entry_sections(pages, sections, usecase_navigation or {})
    pages, sections = _ensure_candidate_content_structure(
        pages,
        sections,
        model_attrs,
        0,
        "",
        add_missing_content=True,
    )
    pages, sections = _ensure_pre_workflow_content_sections(
        pages,
        sections,
        usecase_navigation or {},
        model_attrs,
        0,
        add_missing_content=True,
    )
    sections = _apply_nav_methods(pages, sections, usecase_navigation or {})
    pages, sections = _ensure_section_data_relationships(pages, sections, model_attrs)
    return pages, sections

def _drop_unreferenced_non_global_sections(pages: list, sections: list) -> list:
    referenced = {
        _ref_id(ref)
        for page in pages or []
        for ref in (page.get("sections") or [])
        if _ref_id(ref)
    }
    result = []
    for section in sections or []:
        sid = str(section.get("id") or "")
        if not sid or sid in referenced:
            result.append(section)
            continue
        if section.get("position") in {"header", "footer", "sidebar"}:
            result.append(section)
            continue
        layout = _normalize_layout_alias(section.get("layout"))
        if layout in _CHROME_TEMPLATE_LAYOUTS:
            result.append(section)
    return result

def _dedupe_agent_header_shells(pages: list, sections: list) -> tuple[list, list]:
    """Agent output may compose many header elements, but only one header/nav shell."""
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    header_shell_ids = [
        sid for sid, section in section_map.items()
        if section.get("position") == "header"
        and _normalize_layout_alias(section.get("layout")) in _HEADER_SHELL_LAYOUTS
    ]
    if len(header_shell_ids) <= 1:
        return pages, sections
    duplicate_ids = set(header_shell_ids[1:])
    next_sections = [section for section in sections if str(section.get("id")) not in duplicate_ids]
    next_pages = []
    for page in pages:
        page = dict(page)
        page["sections"] = [
            ref for ref in (page.get("sections") or [])
            if _ref_id(ref) and _ref_id(ref) not in duplicate_ids
        ]
        next_pages.append(page)
    return next_pages, next_sections

def _inject_chrome_sections(new_sections: list, sections: list, section_map: dict, pages: list, prepend: bool) -> None:
    for s in new_sections:
        sid = s["id"]; suffix = 2
        while sid in section_map:
            sid = f"{s['id']}_{suffix}"; suffix += 1
        s["id"] = sid
        sections.append(s); section_map[sid] = s
    for page in pages:
        refs = page.get("sections") or []
        ref_ids = {_ref_id(ref) for ref in refs}
        new_refs = [{"value": s["id"]} for s in new_sections if s["id"] not in ref_ids]
        if new_refs:
            page["sections"] = new_refs + refs if prepend else refs + new_refs


def _ensure_candidate_content_structure(
    pages: list,
    sections: list,
    model_attrs: dict,
    candidate_index: int = 0,
    prompt: str = "",
    add_missing_content: bool = True,
) -> tuple[list, list]:
    known_models = set(model_attrs.keys())
    sections = [dict(s) for s in sections]
    for section in sections:
        section["layout"] = _normalize_layout_alias(section.get("layout"))
        if section.get("component") == "NavBar" and not section.get("layout"):
            section["layout"] = "nav-links"
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    activity_section_ids = {sid for sid, s in section_map.items() if s.get("type") == "activity_action" or s.get("layout") == "activity_action"}
    chrome_layouts = _CHROME_TEMPLATE_LAYOUTS | {"activity_start", "activity_tasks"}

    _, sections = _dedupe_agent_header_shells([], sections)
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    keep_header_shell_id = next(
        (
            sid for sid, section in section_map.items()
            if section.get("position") == "header"
            and _normalize_layout_alias(section.get("layout")) in _HEADER_SHELL_LAYOUTS
        ),
        "",
    )

    fixed_pages = []
    normal_pages = []
    activity_pages = []
    normal_pages_by_key = {}
    for page in pages:
        page = dict(page)
        refs = [{"value": _ref_id(ref)} for ref in page.get("sections") or [] if _ref_id(ref)]
        if keep_header_shell_id:
            seen_header_shell = False
            deduped_refs = []
            for ref in refs:
                section = section_map.get(ref["value"]) or {}
                is_header_shell_ref = (
                    section.get("position") == "header"
                    and _normalize_layout_alias(section.get("layout")) in _HEADER_SHELL_LAYOUTS
                )
                if is_header_shell_ref:
                    if seen_header_shell:
                        continue
                    seen_header_shell = True
                deduped_refs.append(ref)
            refs = deduped_refs
        if _page_type_value(page) != "activity":
            refs = [ref for ref in refs if ref["value"] not in activity_section_ids]
            page["sections"] = refs
            page_key = _section_id(page.get("name") or page.get("id") or page.get("display_name"))
            if page_key and page_key in normal_pages_by_key:
                existing = normal_pages_by_key[page_key]
                existing_refs = [{"value": _ref_id(ref)} for ref in existing.get("sections") or [] if _ref_id(ref)]
                existing_ids = {_ref_id(ref) for ref in existing_refs}
                existing["sections"] = existing_refs + [ref for ref in refs if ref["value"] not in existing_ids]
                continue
            normal_pages_by_key[page_key] = page
            normal_pages.append(page)
        else:
            page["sections"] = refs
            activity_pages.append(page)

    normal_page_ids = {_section_id(p.get("id") or p.get("name")) for p in normal_pages}
    has_header_region = any(s.get("id") and s.get("position") == "header" for s in sections)
    if normal_pages and not has_header_region:
        _inject_chrome_sections(_header_sections_for_candidate(normal_pages, candidate_index, model_attrs), sections, section_map, normal_pages, prepend=True)

    has_footer_region = any(s.get("id") and s.get("position") == "footer" for s in sections)
    if normal_pages and not has_footer_region:
        _inject_chrome_sections(_footer_sections_for_candidate(candidate_index, normal_pages), sections, section_map, normal_pages, prepend=False)

    _all_pages_for_nav = normal_pages + activity_pages
    _all_pages_for_nav, sections = _ensure_normal_page_navigation(_all_pages_for_nav, sections, normal_pages, candidate_index)
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}

    def _is_global_region_section(section: dict) -> bool:
        position = section.get("position")
        if position not in {"header", "sidebar", "footer"} or not section.get("id"):
            return False
        layout = section.get("layout")
        style = section.get("style") or {}
        role = str(section.get("role") or "").lower()
        scope = str(section.get("scope") or style.get("scope") or "").lower()
        if scope == "global":
            return True
        if layout in chrome_layouts:
            return True
        if not section.get("primary_model"):
            return True
        return role in {
            "brand", "navigation", "search", "actions", "action", "promo", "utility",
            "status", "summary", "kpi", "stats", "legal", "contact", "help", "footer",
        }

    header_region_ids = [
        str(s.get("id")) for s in sections
        if _is_global_region_section(s) and s.get("position") == "header"
    ]
    sidebar_region_ids = [
        str(s.get("id")) for s in sections
        if _is_global_region_section(s) and s.get("position") == "sidebar"
    ]
    footer_region_ids = [
        str(s.get("id")) for s in sections
        if _is_global_region_section(s) and s.get("position") == "footer"
    ]
    if header_region_ids or sidebar_region_ids or footer_region_ids:
        for page in normal_pages:
            refs = [{"value": _ref_id(ref)} for ref in page.get("sections") or [] if _ref_id(ref)]
            ref_ids = {_ref_id(ref) for ref in refs}
            header_refs = [{"value": sid} for sid in header_region_ids if sid not in ref_ids]
            sidebar_refs = [{"value": sid} for sid in sidebar_region_ids if sid not in ref_ids]
            footer_refs = [{"value": sid} for sid in footer_region_ids if sid not in ref_ids]
            if header_refs or sidebar_refs or footer_refs:
                page["sections"] = header_refs + sidebar_refs + refs + footer_refs

    referenced_region_ids = {
        _ref_id(ref)
        for page in normal_pages
        for ref in (page.get("sections") or [])
        if _ref_id(ref)
    }

    def _best_page_for_region_section(section: dict) -> dict | None:
        if not normal_pages:
            return None
        pm = str(section.get("primary_model") or "")
        if pm:
            pm_key = _section_id(pm)
            for page in normal_pages:
                page_pm = str(page.get("primary_model") or "")
                page_text = f"{page.get('id', '')} {page.get('name', '')}"
                if page_pm == pm or pm_key in _section_id(page_text):
                    return page
        return normal_pages[0]

    for section in sections:
        sid = str(section.get("id") or "")
        position = section.get("position")
        if not sid or sid in referenced_region_ids or position not in {"header", "sidebar", "footer"}:
            continue
        page = _best_page_for_region_section(section)
        if not page:
            continue
        refs = [{"value": _ref_id(ref)} for ref in page.get("sections") or [] if _ref_id(ref)]
        if position == "footer":
            page["sections"] = refs + [{"value": sid}]
        else:
            page["sections"] = [{"value": sid}] + refs
        referenced_region_ids.add(sid)

    for page in normal_pages:
        model = _fallback_model_for_page(page, known_models)
        if model and not page.get("primary_model"):
            page["primary_model"] = model
        ref_ids = {_ref_id(ref) for ref in page.get("sections") or []}
        has_content = False
        for sid in ref_ids:
            section = section_map.get(sid) or {}
            if section.get("position", "main") == "main" and section.get("layout") not in chrome_layouts and section.get("layout") != "activity_action":
                has_content = True
                if model and not section.get("primary_model"):
                    section["primary_model"] = model
                    section["class"] = model
                if section.get("primary_model") in model_attrs and not section.get("attributes"):
                    section["attributes"] = _model_field_names(model_attrs, section["primary_model"])
                section.setdefault("operations", {"create": False, "update": False, "delete": False})
        if add_missing_content and not has_content and model:
            section = _default_section_for_page(page, model, model_attrs, candidate_index)
            dedupe_id = section["id"]
            suffix = 2
            while dedupe_id in section_map:
                dedupe_id = f"{section['id']}_{suffix}"
                suffix += 1
            section["id"] = dedupe_id
            sections.append(section)
            section_map[dedupe_id] = section
            page.setdefault("sections", [])
            page["sections"].append({"value": dedupe_id})
    fixed_pages = normal_pages + activity_pages
    return fixed_pages, sections

def _ensure_usecase_pages(pages: list, usecase_navigation: dict) -> list:
    if not usecase_navigation:
        return pages
    pages = [dict(p) for p in pages]
    existing = {_section_id(p.get("id") or p.get("name")) for p in pages}
    page_entries = usecase_navigation.get("pages") or []
    if not page_entries:
        page_entries = [
            {
                "page_id": usecase.get("page_id"),
                "page_name": usecase.get("page_name"),
                "primary_model": usecase.get("page_model") or usecase.get("primary_model", ""),
                "usecases": [usecase.get("name")],
            }
            for usecase in usecase_navigation.get("usecases") or []
            if (usecase.get("ui_mapping") or {}).get("role") != "background"
        ]
    for page_entry in page_entries:
        page_id = _section_id(page_entry.get("page_id") or page_entry.get("page_name"))
        if not page_id or page_id in existing:
            continue
        pages.append({
            "id": page_id,
            "name": page_entry.get("page_name") or _page_name(page_id),
            "primary_model": page_entry.get("primary_model", ""),
            "type": {"value": "normal", "label": "Normal"},
            "sections": [],
            "category": None,
            "source_usecases": page_entry.get("usecases") or [],
        })
        existing.add(page_id)
    return pages

def _ensure_workflow_entry_sections(pages: list, sections: list, usecase_navigation: dict) -> tuple[list, list]:
    entries = usecase_navigation.get("workflow_entry_points") or []
    if not entries:
        return pages, sections
    pages = [dict(p) for p in pages]
    sections = [dict(s) for s in sections]
    section_ids = {str(s.get("id")) for s in sections if s.get("id")}
    page_by_id = {_section_id(p.get("id") or p.get("name")): p for p in pages}
    for entry in entries:
        page = page_by_id.get(_section_id(entry.get("page_id") or entry.get("page_name")))
        if not page:
            continue
        sid = f"{_section_id(page.get('id') or page.get('name'))}_workflow_start"
        if sid not in section_ids:
            sections.append({
                "id": sid,
                "name": entry.get("label") or "Start Workflow",
                "label": entry.get("label") or "Start Workflow",
                "type": "activity_start",
                "layout": "activity_start",
                "primary_model": "",
                "class": "",
                "operations": {"create": False, "update": False, "delete": False},
                "attributes": [],
                "methods": [],
                "col_span": 12,
                "position": "main",
                "style": {"color": "accent", "density": "normal", "shadow": "sm", "bg": "white", "columns": "1", "cta_label": entry.get("button_label") or "Start"},
            })
            section_ids.add(sid)
        refs = page.get("sections") or []
        if sid not in {_ref_id(ref) for ref in refs}:
            page["sections"] = refs + [{"value": sid}]
    return pages, sections

def _ensure_pre_workflow_content_sections(
    pages: list,
    sections: list,
    usecase_navigation: dict,
    model_attrs: dict,
    candidate_index: int = 0,
    add_missing_content: bool = True,
) -> tuple[list, list]:
    if not add_missing_content:
        return pages, sections
    entries = usecase_navigation.get("workflow_entry_points") or []
    if not entries:
        return pages, sections
    pages = [dict(p) for p in pages]
    sections = [dict(s) for s in sections]
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    page_by_id = {_section_id(p.get("id") or p.get("name")): p for p in pages}
    known_models = set(model_attrs.keys())

    for entry in entries:
        page_id = _section_id(entry.get("page_id") or entry.get("page_name"))
        page = page_by_id.get(page_id)
        if not page:
            continue
        refs = [{"value": _ref_id(ref)} for ref in page.get("sections") or [] if _ref_id(ref)]
        ref_ids = {_ref_id(ref) for ref in refs}
        main_data_sections = [
            section_map.get(sid) or {}
            for sid in ref_ids
            if (section_map.get(sid) or {}).get("position", "main") == "main"
            and (section_map.get(sid) or {}).get("layout") in {"card", "list", "table", "detail", "gallery", "form"}
        ]
        preferred_models = [
            m for m in (entry.get("pre_workflow_collections") or [])
            if m in known_models
        ]
        if not preferred_models:
            preferred_models = [
                m for m in (entry.get("related_models") or [])
                if m in known_models and _is_child_collection_model(m, f"{entry.get('page_name', '')} {entry.get('usecase_name', '')}")
            ]
        if not preferred_models:
            preferred_models = [m for m in [entry.get("primary_model")] if m in known_models]
        model = preferred_models[0] if preferred_models else ""
        if not model:
            continue
        has_model_section = any(s.get("primary_model") == model for s in main_data_sections)
        if has_model_section:
            continue
        sid = f"{page_id}_{_section_id(model)}_pre_workflow"
        suffix = 2
        base_sid = sid
        while sid in section_map:
            sid = f"{base_sid}_{suffix}"
            suffix += 1
        layout = "list" if _is_child_collection_model(model, f"{entry.get('page_name', '')} {entry.get('usecase_name', '')}") else _infer_section_layout({"id": page_id, "name": page.get("name", "")}, candidate_index)
        style = {
            "color": "accent",
            "density": "compact" if layout in {"list", "table"} else "normal",
            "shadow": "sm",
            "border": "light",
            "bg": "white",
        }
        if layout == "list":
            style["list_style"] = "default"
        section = {
            "id": sid,
            "name": f"{model} Items" if _is_child_collection_model(model, page_id) else f"{model} Overview",
            "layout": layout,
            "primary_model": model,
            "class": model,
            "attributes": _model_field_names(model_attrs, model, 8),
            "operations": {
                "create": False,
                "update": layout in {"list", "table", "detail", "form"},
                "delete": layout in {"list", "table", "card", "gallery"},
            },
            "query": {},
            "col_span": 12,
            "position": "main",
            "style": style,
        }
        sections.append(section)
        section_map[sid] = section
        activity_start_refs = [ref for ref in refs if (section_map.get(_ref_id(ref)) or {}).get("layout") == "activity_start"]
        other_refs = [ref for ref in refs if ref not in activity_start_refs]
        page["sections"] = other_refs + [{"value": sid}] + activity_start_refs
    return pages, sections

def _apply_nav_methods(pages: list, sections: list, usecase_navigation: dict) -> list:
    nav_ids = {_section_id(pid) for pid in (usecase_navigation.get("nav_bar_pages") or []) if pid}
    page_by_id = {_section_id(p.get("id") or p.get("name")): p for p in pages}
    nav_names = [
        (page_by_id.get(pid) or {}).get("name") or _page_name(pid)
        for pid in usecase_navigation.get("nav_bar_pages") or []
        if _section_id(pid) in page_by_id
    ]
    workflow_icon_links = _workflow_icon_links(usecase_navigation, page_by_id)
    if not nav_names and not workflow_icon_links:
        return sections
    fixed = []
    for section in sections:
        section = dict(section)
        layout = _normalize_layout_alias(section.get("layout"))
        if nav_ids and (layout in (_HEADER_NAV_LAYOUTS | {"nav-bar"}) or (section.get("position") in {"header", "sidebar"} and layout in {"site-nav", "nav-links", "nav-bar"})):
            section["layout"] = layout
            section["methods"] = _navigation_methods(nav_names)
        if section.get("position") == "header" or layout in _HEADER_TEMPLATE_LAYOUTS or layout == "icon-actions":
            style = dict(section.get("style") or {})
            if workflow_icon_links and not style.get("icon_links"):
                style["icon_links"] = workflow_icon_links[:2]
            section["style"] = style
        fixed.append(section)
    return fixed

def _materialize_nav_plan_sections(pages: list, sections: list, nav_plan: dict, model_attrs: dict) -> tuple[list, list]:
    if not nav_plan:
        return pages, sections
    pages = [dict(p) for p in pages]
    sections = [dict(s) for s in sections]
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    page_by_id = {_section_id(p.get("id") or p.get("name")): p for p in pages}

    for section_plan in nav_plan.get("sections") or []:
        if section_plan.get("role") not in DATA_SECTION_ROLES:
            continue
        sid = section_plan.get("id")
        page_id = _section_id(section_plan.get("page_id"))
        model = section_plan.get("primary_model") or ""
        if not sid or not page_id or not model or sid in section_map:
            continue
        if model not in model_attrs:
            continue
        editable = set(section_plan.get("editable_fields") or [])
        operations = _normalize_section_operations(section_plan.get("operations"))
        operations["update"] = bool(operations.get("update") or editable)
        attrs = list(section_plan.get("visible_fields") or [])
        attrs.extend([
            {"name": name, "source": "related", "readonly": True}
            for name in section_plan.get("related_visible_fields") or []
        ])
        if not attrs:
            attrs = _model_field_names(model_attrs, model, 8)
        section = {
            "id": sid,
            "name": section_plan.get("name") or sid,
            "role": section_plan.get("role"),
            "layout": section_plan.get("layout") or "detail",
            "component": section_plan.get("component") or _infer_section_component(section_plan),
            "primary_model": model,
            "class": model,
            "attributes": attrs,
            "field_layout": section_plan.get("field_layout") or {},
            "behavior": section_plan.get("behavior") or {},
            "related_to": section_plan.get("related_to"),
            "relationship": section_plan.get("relationship") or {},
            "relation_field": section_plan.get("relation_field"),
            "operations": operations,
            "data_source": section_plan.get("data_source") or {},
            "query": section_plan.get("query") or {},
            "col_span": section_plan.get("col_span", 12),
            "position": "main",
            "style": section_plan.get("style") or {"color": "accent", "density": "normal", "shadow": "sm", "bg": "white"},
        }
        sections.append(section)
        section_map[sid] = section
        page = page_by_id.get(page_id)
        if page:
            refs = page.get("sections") or []
            if sid not in {_ref_id(ref) for ref in refs}:
                page["sections"] = refs + [{"value": sid}]
    return pages, sections


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



from .metadata_context import _build_known_attrs, _fetch_system_context_data, get_interface_config, get_interface_full_context, get_system_context
from .candidate_generation import generate_candidate_set, regenerate_candidate_set, validate_and_save_candidate
from .interface_patch import apply_interface_patch
from .prompt_guardrails import compile_prompt_intent, apply_hard_constraints
render_candidate_preview = render_candidate_preview_func

system_context_tool = FunctionTool(func=get_system_context)
interface_config_tool = FunctionTool(func=get_interface_config)
update_interface_patch_tool = FunctionTool(func=apply_interface_patch)
run_seed_script_tool = FunctionTool(func=run_seed_script)
get_available_paths_tool = FunctionTool(func=get_available_paths)
get_interface_full_context_tool = FunctionTool(func=get_interface_full_context)
generate_candidate_set_tool = FunctionTool(func=generate_candidate_set)
regenerate_candidate_set_tool = FunctionTool(func=regenerate_candidate_set)

