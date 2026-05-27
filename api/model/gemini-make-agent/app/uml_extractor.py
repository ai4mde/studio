"""
UML Intelligence Extractor
Extracts all structured information from 3 UML diagram types:
  1. Class diagrams    → model graph (attributes, relationships, inheritance)
  2. Use case diagrams → actor permissions, page roles, CRUD mapping
  3. Activity diagrams → workflow sequences, step components
"""

import re
from collections import defaultdict


# ─── utilities ───────────────────────────────────────────────────────────────

def _sid(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", str(name or "").strip()).strip("_").lower()
    return s or "section"


def _plural(model: str) -> str:
    base = _sid(model or "items")
    if base.endswith("y") and not base.endswith(("ay", "ey", "oy", "uy")):
        return f"{base[:-1]}ies"
    if base.endswith("s"):
        return base
    return f"{base}s"


def _cardinality(source_mult: str, target_mult: str) -> str:
    def is_many(m: str) -> bool:
        m = str(m or "").strip()
        return "*" in m or "n" in m.lower() or "+" in m
    s = is_many(source_mult)
    t = is_many(target_mult)
    if s and t:
        return "many-many"
    if t:
        return "1-many"
    if s:
        return "many-1"
    return "1-1"


def _ref_list(raw) -> list:
    if isinstance(raw, dict):
        refs = []
        for v in raw.values():
            refs.extend(v or [])
        return refs
    return list(raw or [])


# ─── layout scoring ──────────────────────────────────────────────────────────

_ATTR_SIGNALS: dict[str, frozenset] = {
    "image":     frozenset({"image_url", "photo_url", "avatar_url", "thumbnail_url",
                             "cover_url", "picture_url", "profile_picture"}),
    "video":     frozenset({"video_url", "trailer_url", "media_url", "clip_url"}),
    "price":     frozenset({"price", "amount", "total", "cost", "balance", "fee",
                             "salary", "discount", "tax", "subtotal", "unit_price"}),
    "status":    frozenset({"status", "state", "stage", "phase", "step", "is_active",
                             "is_approved", "is_completed", "is_deleted", "is_archived"}),
    "date":      frozenset({"created_at", "updated_at", "date", "scheduled_at", "started_at",
                             "completed_at", "due_date", "birth_date", "appointment_date",
                             "start_date", "end_date", "expiry_date"}),
    "time":      frozenset({"start_time", "end_time", "duration", "time"}),
    "content":   frozenset({"description", "body", "content", "summary", "notes",
                             "comment", "text", "bio", "about", "details", "remarks"}),
    "identity":  frozenset({"name", "title", "full_name", "first_name", "last_name",
                             "username", "code", "sku", "reference", "slug", "number"}),
    "contact":   frozenset({"email", "phone", "address", "street", "city", "postcode",
                             "zip", "country", "website", "mobile"}),
    "rating":    frozenset({"rating", "score", "stars", "likes", "votes", "views", "downloads"}),
    "quantity":  frozenset({"quantity", "qty", "count", "stock", "inventory", "units"}),
    "geo":       frozenset({"latitude", "longitude", "lat", "lng", "location", "coordinates"}),
}


def score_layout(attr_names: set[str]) -> dict[str, float]:
    """Score how well a model fits each layout based on attribute names."""
    names_l = {n.lower() for n in attr_names}
    hits: dict[str, int] = defaultdict(int)
    for attr in names_l:
        for sig_key, sig_set in _ATTR_SIGNALS.items():
            if attr in sig_set or any(s in attr for s in sig_set if len(s) > 4):
                hits[sig_key] += 1

    has_image = hits["image"] > 0
    has_video = hits["video"] > 0
    has_price = hits["price"] > 0
    has_status = hits["status"] > 0
    has_date = hits["date"] > 0
    has_time = hits["time"] > 0
    has_content = hits["content"] > 0
    has_contact = hits["contact"] > 0
    has_geo = hits["geo"] > 0
    attr_count = len(attr_names)

    return {
        "gallery":   0.9 if has_image else (0.3 if hits["rating"] > 0 else 0.1),
        "table":     0.85 if (has_price and has_status) else (0.7 if (has_status or attr_count > 8) else 0.4),
        "list":      0.75 if (has_status and has_date and not has_image) else 0.35,
        "detail":    0.9 if (has_content or attr_count > 8) else 0.5,
        "form":      0.8 if (has_contact or hits["identity"] > 0) else 0.5,
        "calendar":  0.9 if (has_time or (has_date and hits["time"] > 0)) else 0.0,
        "timeline":  0.8 if (has_date and has_status and not has_image) else 0.0,
        "map":       0.9 if has_geo else 0.0,
        "card":      0.6 if has_image else 0.25,
    }


# ─── Class Diagram Extraction ────────────────────────────────────────────────

CLASS_REL_TYPES = frozenset({
    "association", "directed_association", "composition", "aggregation",
    "generalization", "inheritance", "realization", "dependency",
})

CHILD_PATTERNS = frozenset({"item", "line", "entry", "row", "selection", "option", "membership", "mapping"})


def _is_child_model(name: str) -> bool:
    n = name.lower()
    return any(p in n for p in CHILD_PATTERNS)


def extract_class_diagram(classifiers: dict, relations: dict) -> dict[str, dict]:
    """
    Build the model graph from class diagram data.

    Returns {model_name: model_info} where model_info contains:
      attributes, layout_score, compositions_owned, composition_parent,
      associations, aggregations, specializes, specialized_by
    """
    id_to_name = {cid: cd.get("name") for cid, cd in classifiers.items() if cd.get("name")}
    models: dict[str, dict] = {}

    for cid, cdata in classifiers.items():
        if cdata.get("type") not in {"class", "entity", "model"}:
            continue
        name = cdata.get("name")
        if not name:
            continue
        attrs_raw = cdata.get("attributes") or []
        attrs = [
            {
                "name": a.get("name", ""),
                "type": a.get("type") or a.get("data_type") or "string",
                "required": bool(a.get("required") or a.get("is_required")),
                "enum_values": a.get("enum_values") or a.get("options") or [],
            }
            for a in attrs_raw if a.get("name")
        ]
        attr_names = {a["name"] for a in attrs}
        models[name] = {
            "id": cid,
            "name": name,
            "is_abstract": bool(cdata.get("is_abstract")),
            "stereotype": cdata.get("stereotype") or "",
            "attributes": attrs,
            "attr_names": attr_names,
            "layout_score": score_layout(attr_names),
            # Populated below from relations
            "compositions_owned": [],    # [{model, cardinality}] — children owned by this model
            "composition_parent": None,  # str — parent that owns this model
            "aggregations_owned": [],    # [{model, cardinality}]
            "associations": [],          # [{model, cardinality, name, navigable}]
            "specializes": [],           # parent model names (this extends them)
            "specialized_by": [],        # child model names (they extend this)
        }

    for rel_id, rel in relations.items():
        rdata = rel.get("data") or {}
        rtype = rdata.get("type") or rdata.get("relation_type") or ""
        if rtype not in CLASS_REL_TYPES:
            continue

        source_id = str(rel.get("source") or "")
        target_id = str(rel.get("target") or "")
        src_name = id_to_name.get(source_id, "")
        tgt_name = id_to_name.get(target_id, "")

        if not src_name or not tgt_name:
            continue
        if src_name not in models or tgt_name not in models:
            continue

        src_mult = str(rdata.get("source_multiplicity") or rdata.get("source_cardinality") or "1")
        tgt_mult = str(rdata.get("target_multiplicity") or rdata.get("target_cardinality") or "*")
        card = _cardinality(src_mult, tgt_mult)
        rel_name = rdata.get("name") or rdata.get("label") or ""

        if rtype == "composition":
            # source is the whole; target is the part (owned)
            models[src_name]["compositions_owned"].append({"model": tgt_name, "cardinality": card})
            if models[tgt_name]["composition_parent"] is None:
                models[tgt_name]["composition_parent"] = src_name

        elif rtype == "aggregation":
            models[src_name]["aggregations_owned"].append({"model": tgt_name, "cardinality": card, "name": rel_name})

        elif rtype in {"association", "directed_association"}:
            navigable_both = rtype == "association"
            models[src_name]["associations"].append({"model": tgt_name, "cardinality": card, "name": rel_name, "navigable": True})
            if navigable_both:
                models[tgt_name]["associations"].append({"model": src_name, "cardinality": _cardinality(tgt_mult, src_mult), "name": rel_name, "navigable": True})

        elif rtype in {"generalization", "inheritance"}:
            # Arrow goes from child → parent in UML
            models[src_name]["specializes"].append(tgt_name)
            models[tgt_name]["specialized_by"].append(src_name)

    return models


# ─── Use Case Diagram Extraction ─────────────────────────────────────────────

_VERB_PERMS: dict[str, str] = {
    "create": "create", "add": "create", "register": "create", "submit": "create",
    "place": "create", "book": "create", "upload": "create", "post": "create",
    "write": "create", "issue": "create", "generate": "create", "open": "create",
    "view": "read", "browse": "read", "search": "read", "list": "read",
    "track": "read", "check": "read", "monitor": "read", "download": "read",
    "read": "read", "see": "read",
    "update": "update", "edit": "update", "modify": "update", "manage": "update",
    "change": "update", "configure": "update", "assign": "update", "select": "update",
    "confirm": "update", "approve": "update", "process": "update", "set": "update",
    "review": "update", "rate": "update", "accept": "update", "reject": "update",
    "delete": "delete", "remove": "delete", "cancel": "delete", "deactivate": "delete",
    "archive": "delete", "dismiss": "delete", "close": "delete",
}

_PAGE_ROLE_SIGNALS: dict[str, frozenset] = {
    "collection_workspace": frozenset({"browse", "search", "list", "catalog", "directory",
                                        "overview", "track", "history", "manage", "all"}),
    "detail_workspace":     frozenset({"detail", "profile", "show", "info"}),
    "workflow_entry":       frozenset({"checkout", "submit", "apply", "order", "book", "schedule",
                                        "request", "enroll", "onboard", "start", "apply for",
                                        "place", "initiate", "open"}),
    "object_workspace":     frozenset({"account", "settings", "preferences", "dashboard", "my"}),
}


def _infer_permissions(uc_name: str) -> list[str]:
    n = uc_name.lower()
    perms = {"read"}
    for word, perm in _VERB_PERMS.items():
        if word in n:
            perms.add(perm)
    return [p for p in ("create", "read", "update", "delete") if p in perms]


def _infer_page_role(uc_name: str, has_workflow: bool) -> str:
    if has_workflow:
        return "workflow_entry"
    n = uc_name.lower()
    for role, sigs in _PAGE_ROLE_SIGNALS.items():
        if any(s in n for s in sigs):
            return role
    return "object_workspace"


# Domain synonyms: action keywords → partial model name signals
_DOMAIN_SYNONYMS: list[tuple[str, str]] = [
    ("inventory", "product"),
    ("stock",     "product"),
    ("catalogue", "product"),
    ("catalog",   "product"),
    ("listing",   "product"),
    ("shipment",  "order"),
    ("dispatch",  "order"),
    ("fulfil",    "order"),
    ("fulfill",   "order"),
    ("basket",    "cart"),
    ("checkout",  "cart"),
    ("invoice",   "payment"),
    ("billing",   "payment"),
    ("refund",    "payment"),
    ("profile",   "user"),
    ("account",   "user"),
    ("credential","user"),
    ("appointment","booking"),
    ("schedule",  "booking"),
    ("slot",      "booking"),
]


def _best_model_for_text(text: str, model_names: list[str], model_attr_names: dict[str, set[str]] | None = None) -> str:
    t = text.lower()
    model_names_sorted = sorted(model_names, key=len, reverse=True)

    # Pass 1: model name directly in action text
    for m in model_names_sorted:
        if m.lower() in t:
            return m

    # Pass 2: action words match model attribute names (len >= 5 to avoid generic words)
    if model_attr_names:
        action_words = {w for w in re.findall(r'\b\w{5,}\b', t)}
        for m in model_names_sorted:
            if action_words & (model_attr_names.get(m) or set()):
                return m

    # Pass 3: domain synonym mapping (keyword in action → partial model name)
    for keyword, model_signal in _DOMAIN_SYNONYMS:
        if keyword in t:
            for m in model_names_sorted:
                if model_signal in m.lower():
                    return m

    return ""


def extract_use_case_diagram(
    classifiers: dict,
    relations: dict,
    diagrams: list,
    actor_id: str,
    actor_name: str,
    model_names: set[str],
    uc_ids_with_workflows: set[str],
) -> dict:
    """
    Extract actor intelligence from use case diagrams.

    Returns:
      target_permissions: {model: [create, read, update, delete]}
      target_use_cases: [{name, primary_model, page_role, permissions, has_workflow, explicit_models}]
      all_actors: {actor_name: [use_case_names]}
    """
    actor_refs: set[str] = {str(actor_id)}
    for cid, cdata in classifiers.items():
        if cdata.get("type") == "actor":
            if cdata.get("name") == actor_name or cid == str(actor_id):
                actor_refs.add(cid)

    model_names_list = sorted(model_names, key=len, reverse=True)
    target_permissions: dict[str, set] = defaultdict(set)
    target_use_cases: list[dict] = []
    all_actors: dict[str, list] = defaultdict(list)

    for diagram in diagrams:
        if diagram.get("type") != "usecase":
            continue

        node_by_cls: dict[str, str] = {}
        for node in diagram.get("nodes") or []:
            cls_id = str(node.get("cls") or node.get("cls_ptr") or "")
            if cls_id:
                node_by_cls[cls_id] = str(node.get("id"))

        for edge in diagram.get("edges") or []:
            rel_id = str(edge.get("rel") or edge.get("rel_ptr") or "")
            rel = relations.get(rel_id, {})
            rdata = rel.get("data") or {}

            if rdata.get("type") != "interaction":
                continue

            source_id = str(rel.get("source") or "")
            target_id = str(rel.get("target") or "")
            src_cls = classifiers.get(source_id, {})
            tgt_cls = classifiers.get(target_id, {})

            # Determine which is actor and which is use case
            if src_cls.get("type") == "actor" and tgt_cls.get("type") == "usecase":
                actor_cls_id, uc_cls_id = source_id, target_id
            elif tgt_cls.get("type") == "actor" and src_cls.get("type") == "usecase":
                actor_cls_id, uc_cls_id = target_id, source_id
            else:
                continue

            uc = classifiers.get(uc_cls_id, {})
            actor_cls = classifiers.get(actor_cls_id, {})
            uc_name = uc.get("name") or ""
            actor_cls_name = actor_cls.get("name") or ""

            if not uc_name:
                continue

            # Explicit model references from use case
            explicit_models = [
                classifiers.get(ref, {}).get("name")
                for ref in _ref_list(uc.get("classes"))
                if classifiers.get(ref, {}).get("type") in {"class", "entity", "model"}
                   and classifiers.get(ref, {}).get("name") in model_names
            ]

            primary_model = explicit_models[0] if explicit_models else _best_model_for_text(uc_name, model_names_list)
            has_workflow = uc_cls_id in uc_ids_with_workflows
            page_role = _infer_page_role(uc_name, has_workflow)
            perms = _infer_permissions(uc_name)

            all_actors[actor_cls_name].append(uc_name)

            is_target = actor_cls_id in actor_refs or actor_cls_name == actor_name
            if is_target:
                if primary_model:
                    target_permissions[primary_model].update(perms)
                for m in explicit_models:
                    if m != primary_model:
                        target_permissions[m].add("read")

                target_use_cases.append({
                    "name": uc_name,
                    "primary_model": primary_model,
                    "explicit_models": explicit_models,
                    "page_role": page_role,
                    "permissions": perms,
                    "has_workflow": has_workflow,
                    "uc_id": uc_cls_id,
                })

    normalized_perms = {
        m: [p for p in ("create", "read", "update", "delete") if p in ps]
        for m, ps in target_permissions.items()
    }

    return {
        "target_permissions": normalized_perms,
        "target_use_cases": target_use_cases,
        "all_actors": dict(all_actors),
    }


# ─── Activity Diagram Extraction ─────────────────────────────────────────────

_ACTION_COMPONENT_SIGNALS: dict[str, list[str]] = {
    "PaymentMethodForm": ["payment", "pay", "charge", "billing", "card"],
    "AddressForm":       ["address", "shipping", "delivery", "location"],
    "ReviewForm":        ["review", "rate", "rating", "feedback"],
    "FileUpload":        ["upload", "photo", "image", "attachment", "document"],
    "SelectionList":     ["select", "choose", "pick", "browse"],
    "DetailPanel":       ["view", "display", "show", "confirm", "summary", "review", "check"],
    "ObjectForm":        ["enter", "fill", "input", "provide", "edit", "update", "create"],
}


def _action_component(action_name: str) -> str:
    n = action_name.lower()
    for component, signals in _ACTION_COMPONENT_SIGNALS.items():
        if any(s in n for s in signals):
            return component
    return "ObjectForm"


def extract_activity_diagrams(
    classifiers: dict,
    system_data: dict,
    model_names: set[str],
    model_attr_names: dict[str, set[str]] | None = None,
) -> dict:
    """
    Extract workflow sequences from activity diagrams.

    Returns:
      workflows: [{name, steps: [{action, model, component_hint}], step_count}]
      uc_ids_with_workflows: set of usecase classifier IDs that have linked activity nodes
    """
    model_names_list = sorted(model_names, key=len, reverse=True)
    workflows: list[dict] = []
    uc_ids_with_workflows: set[str] = set()

    for diagram in system_data.get("activity_diagrams") or []:
        diagram_name = diagram.get("name") or "Workflow"
        nodes: dict[str, dict] = {str(n.get("id")): n for n in diagram.get("nodes") or []}

        # Collect classifier IDs referenced by action nodes (for linking to use cases)
        for node in nodes.values():
            cls_id = str(node.get("cls_ptr") or node.get("cls") or "")
            if cls_id:
                uc_ids_with_workflows.add(cls_id)
                # Also check parent via cls data
                cls = classifiers.get(cls_id, {})
                parent_uc = cls.get("usecase") or cls.get("use_case")
                if parent_uc:
                    uc_ids_with_workflows.add(str(parent_uc))

        # Build outgoing adjacency
        outgoing: dict[str, list] = defaultdict(list)
        incoming_count: dict[str, int] = defaultdict(int)
        for edge in diagram.get("edges") or []:
            src = str(edge.get("source_ptr") or edge.get("source") or "")
            tgt = str(edge.get("target_ptr") or edge.get("target") or "")
            guard = edge.get("guard") or edge.get("label") or ""
            if src and tgt:
                outgoing[src].append({"target": tgt, "guard": guard})
                incoming_count[tgt] += 1

        # Find start node (no incoming edges, or initial pseudostate)
        start_candidates = []
        for nid, node in nodes.items():
            cls_id = str(node.get("cls_ptr") or node.get("cls") or "")
            cls = classifiers.get(cls_id, {})
            cls_type = cls.get("type") or node.get("type") or ""
            if cls_type in {"initial", "start", "initial_pseudostate"}:
                start_candidates = [nid]
                break
            if incoming_count[nid] == 0 and cls_type == "action":
                start_candidates.append(nid)

        if not start_candidates:
            start_candidates = [nid for nid in nodes if incoming_count[nid] == 0][:1]

        # BFS traversal — extract action steps in order
        steps: list[dict] = []
        visited: set[str] = set()
        queue: list[str] = list(start_candidates)

        while queue and len(steps) < 25:
            nid = queue.pop(0)
            if nid in visited:
                continue
            visited.add(nid)

            node = nodes.get(nid, {})
            cls_id = str(node.get("cls_ptr") or node.get("cls") or "")
            cls = classifiers.get(cls_id, {})
            cls_type = cls.get("type") or node.get("type") or ""
            action_name = cls.get("name") or node.get("label") or node.get("name") or ""

            if cls_type == "action" and action_name:
                model = _best_model_for_text(action_name, model_names_list, model_attr_names)
                steps.append({
                    "action": action_name,
                    "model": model or None,
                    "component_hint": _action_component(action_name),
                    "is_decision": False,
                    "is_automatic": bool(cls.get("isAutomatic", False)),
                    "actor_node_name": (cls.get("actorNodeName") or "").strip(),
                })
            elif cls_type in {"decision", "merge"}:
                # Mark next steps with branch info
                pass

            for edge in outgoing.get(nid, []):
                tgt = edge["target"]
                if tgt not in visited:
                    queue.append(tgt)

        if steps:
            workflows.append({
                "name": diagram_name,
                "steps": steps,
                "step_count": len(steps),
                "is_multi_step": len(steps) > 2,
            })

    return {
        "workflows": workflows,
        "uc_ids_with_workflows": uc_ids_with_workflows,
    }


# ─── Semantic Decision Detection ─────────────────────────────────────────────

_CALENDAR_MODELS   = frozenset({"appointment", "meeting", "event", "booking", "reservation",
                                 "schedule", "slot", "shift", "session"})
_TIMELINE_MODELS   = frozenset({"history", "log", "audit", "timeline", "activity", "feed",
                                 "transaction", "change", "record", "event"})
_MAP_MODELS        = frozenset({"location", "address", "place", "venue", "store", "branch",
                                 "delivery", "route"})
_DASHBOARD_MODELS  = frozenset({"dashboard", "report", "analytics", "metric", "summary",
                                 "overview", "stat", "kpi"})


def detect_semantic_decisions(model_name: str, model_info: dict, page_role: str) -> dict | None:
    """Return a semantic_decision entry if the model requires LLM judgment for layout/component."""
    m = model_name.lower()
    score = model_info.get("layout_score") or {}
    attr_names = {a["name"].lower() for a in (model_info.get("attributes") or [])}

    has_time_range = (
        ("start_time" in attr_names or "start_date" in attr_names) and
        ("end_time" in attr_names or "end_date" in attr_names)
    )
    is_calendar_like = any(kw in m for kw in _CALENDAR_MODELS) or has_time_range
    if is_calendar_like:
        evidence = [a for a in ("start_time", "end_time", "start_date", "end_date",
                                 "is_recurring", "recurrence") if a in attr_names]
        return {
            "model": model_name,
            "aspect": "collection_component",
            "question": f"How should a list of {model_name} be displayed?",
            "options": [
                {"component": "CalendarView",  "layout": "calendar",
                 "evidence": evidence or ["model name suggests calendar"]},
                {"component": "DataTable",     "layout": "table",
                 "evidence": ["fallback for schedulable entities without visual calendar"]},
                {"component": "ObjectList",    "layout": "list",
                 "evidence": ["simple chronological list"]},
            ],
            "default": "CalendarView" if evidence else "DataTable",
        }

    is_timeline_like = any(kw in m for kw in _TIMELINE_MODELS) and score.get("calendar", 0) < 0.5
    if is_timeline_like:
        return {
            "model": model_name,
            "aspect": "collection_component",
            "question": f"Should {model_name} be shown as a chronological timeline or a searchable table?",
            "options": [
                {"component": "TimelineList", "layout": "timeline",
                 "evidence": ["chronological event data"]},
                {"component": "DataTable",    "layout": "table",
                 "evidence": ["filterable/sortable entries"]},
            ],
            "default": "TimelineList",
        }

    is_map_like = any(kw in m for kw in _MAP_MODELS) and score.get("map", 0) > 0.5
    if is_map_like:
        return {
            "model": model_name,
            "aspect": "collection_component",
            "question": f"Should {model_name} be displayed on a map or as a list?",
            "options": [
                {"component": "MapView",    "layout": "map",   "evidence": ["has geo coordinates"]},
                {"component": "CardGrid",   "layout": "gallery", "evidence": ["visual card display"]},
                {"component": "DataTable",  "layout": "table",  "evidence": ["tabular view"]},
            ],
            "default": "MapView",
        }

    return None


# ─── Main Entry Point ────────────────────────────────────────────────────────

def _sys_as_list(system_data: dict, key: str) -> list:
    """Safely extract a list from system_data[key], handling both list and wrapped-dict formats."""
    raw = system_data.get(key) or []
    if isinstance(raw, dict):
        # Handle {"classifiers": [...]} wrapper format
        inner = raw.get(key)
        if isinstance(inner, list):
            return inner
        # Fallback: first list value
        for v in raw.values():
            if isinstance(v, list):
                return v
        return []
    if isinstance(raw, list):
        return raw
    return []


def _expand_actor_scope(model_graph: dict, initial_permissions: dict) -> dict:
    """
    From use-case-derived permissions, traverse class diagram relationships to find
    all models the actor implicitly needs access to:
      - Composition children: owned by accessible model → add read access
      - Aggregation children: loosely associated → add read access
      - Composition parent: context for a child model → add read access
      - Direct 1:many associations: commonly displayed as sub-lists → add read access
    Stops at depth 2 to avoid over-expansion.
    """
    expanded: dict[str, set] = {m: set(ps) for m, ps in initial_permissions.items()}
    frontier = list(initial_permissions.keys())
    visited = set(frontier)
    depth_map = {m: 0 for m in frontier}

    while frontier:
        model = frontier.pop(0)
        depth = depth_map[model]
        if depth >= 2:
            continue
        info = model_graph.get(model) or {}

        # Composition children (always reachable via parent's detail page)
        for comp in info.get("compositions_owned") or []:
            child = comp["model"]
            if child not in visited:
                expanded.setdefault(child, set()).add("read")
                frontier.append(child)
                visited.add(child)
                depth_map[child] = depth + 1

        # Aggregation children (loosely related)
        for agg in info.get("aggregations_owned") or []:
            child = agg["model"]
            if child not in visited:
                expanded.setdefault(child, set()).add("read")
                # Don't traverse further from aggregations
                visited.add(child)
                depth_map[child] = 2

        # Composition parent (need context when viewing a child directly)
        parent = info.get("composition_parent")
        if parent and parent not in visited:
            expanded.setdefault(parent, set()).add("read")
            visited.add(parent)
            depth_map[parent] = depth + 1

        # 1:many associations (the "many" side is often shown as a sub-list)
        for assoc in info.get("associations") or []:
            if assoc["cardinality"] == "1-many":
                rel = assoc["model"]
                if rel not in visited:
                    expanded.setdefault(rel, set()).add("read")
                    visited.add(rel)
                    depth_map[rel] = depth + 1

    return {m: [p for p in ("create", "read", "update", "delete") if p in ps]
            for m, ps in expanded.items()}


def extract_uml_intelligence(
    system_data: dict,
    actor_id: str,
    actor_name: str,
) -> dict:
    """
    Extract and combine intelligence from all 3 UML diagram types.

    Returns a dict with:
      model_graph:        full model/relationship graph
      actor_intel:        permissions, use cases, page roles for target actor
      workflow_intel:     workflow sequences from activity diagrams
      semantic_decisions: layout/component choices requiring LLM judgment
    """
    # ── Index classifiers (handles both list and wrapped-dict formats) ────────
    raw_cls = _sys_as_list(system_data, "classifiers")
    classifiers: dict[str, dict] = {
        str(c.get("id")): (c.get("data") or {})
        for c in raw_cls if isinstance(c, dict) and c.get("id")
    }

    # ── Index relations ───────────────────────────────────────────────────────
    raw_rels = _sys_as_list(system_data, "relations")
    relations: dict[str, dict] = {
        str(r.get("id")): {
            "source": str(r.get("source") or r.get("source_id") or ""),
            "target": str(r.get("target") or r.get("target_id") or ""),
            "data": r.get("data") or {},
        }
        for r in raw_rels if isinstance(r, dict) and r.get("id")
    }

    diagrams: list = system_data.get("diagrams") or []
    if isinstance(diagrams, dict):
        diagrams = diagrams.get("diagrams") or []

    model_names: set[str] = {
        cd.get("name")
        for cd in classifiers.values()
        if cd.get("type") in {"class", "entity", "model"} and cd.get("name")
    }

    # 1 — Class diagram first so we can pass attribute names to activity extractor
    model_graph = extract_class_diagram(classifiers, relations)
    model_attr_names = {
        m: {a["name"].lower() for a in info.get("attributes", [])}
        for m, info in model_graph.items()
    }

    # 2 — Activity diagrams with attribute-aware model matching
    workflow_intel = extract_activity_diagrams(classifiers, system_data, model_names, model_attr_names)

    # (model_graph already extracted above)

    # 3 — Use case diagram actor intelligence
    actor_intel = extract_use_case_diagram(
        classifiers, relations, diagrams,
        actor_id, actor_name, model_names,
        workflow_intel["uc_ids_with_workflows"],
    )

    # 4 — Expand actor scope via class diagram relationships
    #     (critical when use-case diagram is sparse — only 1-2 use cases linked)
    expanded_permissions = _expand_actor_scope(model_graph, actor_intel["target_permissions"])
    actor_intel["target_permissions"] = expanded_permissions

    # 5 — Semantic decisions for each actor-accessible model
    semantic_decisions: list[dict] = []
    for model, perms in expanded_permissions.items():
        info = model_graph.get(model)
        if info:
            decision = detect_semantic_decisions(model, info, "collection_workspace")
            if decision:
                semantic_decisions.append(decision)

    return {
        "model_graph": model_graph,
        "actor_intel": actor_intel,
        "workflow_intel": workflow_intel,
        "semantic_decisions": semantic_decisions,
        "actor_name": actor_name,
        "_meta": {
            "total_models": len(model_graph),
            "actor_accessible_models": len(actor_intel["target_permissions"]),
            "workflow_count": len(workflow_intel["workflows"]),
            "use_case_count": len(actor_intel["target_use_cases"]),
            "decision_count": len(semantic_decisions),
        },
    }
