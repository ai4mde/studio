import re

from .navigation_planner import build_navigation_plan
from ..token_normalizer import _as_list, _page_name, _section_id, _workflow_page_name


def _build_activity_diagrams(system_data: dict) -> list:
    """Build activity diagrams."""
    diagrams = system_data.get("diagrams") or []
    classifiers = {str(c.get("id")): c for c in _as_list(system_data.get("classifiers"), "classifiers")}
    relations = {str(r.get("id")): r for r in _as_list(system_data.get("relations"), "relations")}
    global_node_cls = {
        str(node.get("id")): str(node.get("cls") or node.get("cls_id") or node.get("cls_ptr") or "")
        for node in (system_data.get("nodes") or [])
        if node.get("id")
    }

    def actor_name_for_ref(ref: object) -> str:
        """Provide a local helper for _build_activity_diagrams."""
        ref = str(ref or "")
        data = (classifiers.get(ref) or {}).get("data", {})
        if data.get("type") == "actor":
            return str(data.get("name") or "").strip()
        node_cls = global_node_cls.get(ref)
        data = (classifiers.get(node_cls) or {}).get("data", {}) if node_cls else {}
        if data.get("type") == "actor":
            return str(data.get("name") or "").strip()
        return ""

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
            cls_data = dict(classifier.get("data", {}) or {})
            if cls_data.get("type") == "action" and cls_data.get("actorNode") and not cls_data.get("actorNodeName"):
                actor_name = actor_name_for_ref(cls_data.get("actorNode"))
                if actor_name:
                    cls_data["actorNodeName"] = actor_name
            nodes.append({"id": str(node.get("id")), "cls_ptr": cls_id, "cls": cls_data, "data": node.get("data", {})})
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
            edges.append({"id": str(edge.get("id")), "source_ptr": source_ptr, "target_ptr": target_ptr, "rel_ptr": rel_id, "rel": relation.get("data", {}), "data": edge.get("data", {})})
        out.append({"id": str(diagram.get("id")), "name": diagram.get("name", ""), "type": "activity", "nodes": nodes, "edges": edges})
    return out


def _actor_refs(system_data: dict, actor_id: str | None, actor_name: str | None = None) -> set[str]:
    """Collect actor ids referenced by a use case classifier."""
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
    """Extract raw reference ids from UML reference fields."""
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
    """Normalize UML reference values into a deduplicated list of ids."""
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
    """Split a model, use-case, or action name into searchable tokens."""
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(value or ""))
    tokens = {
        token
        for token in re.split(r"[^A-Za-z0-9]+", spaced.lower())
        if len(token) > 1
    }
    singulars = {token[:-1] for token in tokens if len(token) > 3 and token.endswith("s")}
    return tokens | singulars


def _rank_models_for_text(text: str, models: list[str], prefer_collections: bool = False) -> list[str]:
    """Score candidate models against action or use-case text."""
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
    """Infer usecase model."""
    for ref in explicit_classes:
        cls = classifiers.get(ref, {})
        cname = cls.get("name") or ref
        if cname in model_names:
            return cname
    ranked = _rank_models_for_text(name, sorted(model_names, key=len, reverse=True))
    return ranked[0] if ranked else ""


def _humanize_action_label(name: str, fallback: str = "Start") -> str:
    """Convert an action name into a concise user-facing label."""
    raw = re.sub(r"[_-]+", " ", str(name or "")).strip()
    if not raw:
        return fallback
    cleaned = re.sub(r"^(manage|view|track|write|browse|search|review)\s+", "", raw, flags=re.I).strip()
    if re.search(r"\b(apply|application|request|submit|onboard|register|book|schedule|reserve|approval|claim|ticket|case|workflow|process)\b", raw, re.I):
        return "Start"
    return cleaned[:1].upper() + cleaned[1:] if cleaned else fallback


def _is_child_collection_model(model_name: str, page_terms: str = "") -> bool:
    """Detect line-item or child models that should be nested under a parent."""
    name_l = str(model_name or "").lower()
    if not name_l:
        return False
    if any(term in _name_tokens(name_l) for term in ("item", "line", "entry", "row", "detail", "selection", "membership", "mapping", "association")):
        return True
    return False


def _plural_page_id(model: str) -> str:
    """Pluralize page id."""
    base = _section_id(model or "items")
    if base.endswith("y"):
        return f"{base[:-1]}ies"
    if base.endswith("s"):
        return base
    return f"{base}s"


def _nav_mapping_for_usecase(usecase: dict, workflow_entry: bool = False) -> dict:
    """Map a use case to navigation role, page role, and operation intent."""
    name = str(usecase.get("name") or "")
    name_l = name.lower()
    primary = usecase.get("primary_model") or ""
    class_names = [m for m in usecase.get("class_names") or [] if m]
    ranked_models = _rank_models_for_text(name, class_names)

    def best_model(default: str = "") -> str:
        """Provide a local helper for _nav_mapping_for_usecase."""
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

    selection_terms = ("select", "choose", "pick")
    if any(term in name_l for term in selection_terms):
        page_model = best_model()
        page_id = _plural_page_id(page_model) if page_model else _section_id(name)
        return {"role": "collection_workspace", "page_id": page_id, "page_name": _page_name(page_id), "page_model": page_model, "operation_kind": "select_existing"}

    inline_terms = ("add", "remove", "delete", "update", "write", "review", "rate")
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
        operation_kind = "select_existing" if "search" in name_l else "view_collection"
        return {"role": "collection_workspace", "page_id": page_id, "page_name": _page_name(page_id), "page_model": page_model, "operation_kind": operation_kind}

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
    """Build activity action indexes."""
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
    """Decide whether a use case should start or participate in a workflow."""
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
    """Infer usecase permissions."""
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
    """Build usecase navigation."""
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
    """Build workflow plan."""
    refs = _actor_refs(system_data, actor_id, actor_name)
    classifiers = {
        str(c.get("id")): (c.get("data") or {})
        for c in _as_list(system_data.get("classifiers"), "classifiers")
    }

    def _class_name(ref) -> str:
        """Provide a local helper for _workflow_plan."""
        if isinstance(ref, dict):
            ref = ref.get("id") or ref.get("value") or ref.get("name")
        ref = str(ref or "")
        return classifiers.get(ref, {}).get("name") or ref

    def _class_refs(raw_classes) -> list:
        """Provide a local helper for _workflow_plan."""
        if isinstance(raw_classes, dict):
            refs = []
            for values in raw_classes.values():
                refs.extend(values or [])
            return refs
        return list(raw_classes or [])

    def _node_classifier(node: dict) -> tuple[str, dict]:
        """Provide a local helper for _workflow_plan."""
        raw = node.get("cls") or {}
        if isinstance(raw, dict):
            cls_id = str(raw.get("id") or node.get("cls_ptr") or node.get("cls_id") or "")
            return cls_id, raw
        cls_id = str(node.get("cls_ptr") or node.get("cls_id") or raw or "")
        return cls_id, classifiers.get(cls_id, {})

    def _resolve_actor_node(raw_actor_node: object, nodes: dict[str, dict]) -> tuple[str, str]:
        """Resolve actor node."""
        raw_actor = str(raw_actor_node or "")
        actor_data = classifiers.get(raw_actor, {})
        if actor_data.get("type") == "actor":
            return raw_actor, str(actor_data.get("name") or "").strip()

        lane_node = nodes.get(raw_actor) or {}
        lane_cls_id, lane_cls = _node_classifier(lane_node)
        if lane_cls.get("type") == "actor":
            return lane_cls_id, str(lane_cls.get("name") or "").strip()

        return raw_actor, ""

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
            actor_node, actor_node_name = _resolve_actor_node(cls.get("actorNode"), nodes)
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
                "actor_node_name": actor_node_name,
                "classes": [_class_name(ref) for ref in _class_refs(cls.get("classes")) if _class_name(ref)],
                "diagram_id": diagram.get("id"),
                "diagram_name": diagram.get("name"),
                "page_id": page_id,
                "page_name": page_name,
                "next_activity_node_ids": next_action_ids,
            })
    return steps


def _activity_models_for_step(step: dict, workflow_entries: list, known_models: set[str]) -> list[str]:
    """Build activity models for step."""
    name_l = str(step.get("activity_node_name") or step.get("page_name") or "").lower()
    explicit_step_models = [m for m in step.get("classes") or [] if m in known_models]
    if explicit_step_models:
        # Activity classifier classes are structured UML input/output bindings.
        # Keep their order here; extract_activity_diagrams already resolves cases
        # where the action title explicitly names a different target model.
        return list(dict.fromkeys(explicit_step_models))[:2]
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

    prefer_collections = any(term in _name_tokens(name_l) for term in ("add", "select", "choose", "pick", "search", "browse", "list", "review", "manage"))
    ranked = _rank_models_for_text(name_l, related, prefer_collections=prefer_collections)
    return ranked[:2] or related[:1]


def _activity_layout_for_step(step_name: str, model: str) -> str:
    """Build activity layout for step."""
    name_tokens = _name_tokens(step_name)
    # "select/choose" = pick from options ? card with select operation, not a form
    if any(term in name_tokens for term in ("select", "choose", "pick", "search", "browse")):
        return "card"
    if any(term in name_tokens for term in (
        "enter", "fill", "input", "provide", "submit",
        "create", "add", "update", "edit", "write", "upload", "register",
        "pay", "record",
    )):
        return "form"
    if _is_child_collection_model(model, step_name) or any(term in name_tokens for term in ("list", "browse", "review", "manage", "track", "history")):
        return "list"
    if any(term in name_tokens for term in ("confirmation", "confirm", "detail", "summary")):
        return "detail"
    return "detail"


