"""
Agent nodes for the JSON-to-Django UI pipeline.

Each node receives the full PipelineState and returns a dict with the
keys it wants to update.  LangGraph merges the returned dict into state.
"""
import json
import logging
from typing import List

from generator.agents.state import PipelineState, ScreenInfo
from llm.handler import call_openai

logger = logging.getLogger(__name__)


def _parse_json_response(raw: str) -> dict:
    """Parse an LLM response as JSON, stripping markdown code fences if present."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        # Remove opening fence line (e.g. ```json) and any trailing ``` lines
        start = 1
        end = len(lines)
        while end > start and lines[end - 1].strip() in ("", "```"):
            end -= 1
        raw = "\n".join(lines[start:end])
    return json.loads(raw)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Parser Node
#    Reads the raw metadata JSON and extracts per-page summary info.
# ─────────────────────────────────────────────────────────────────────────────

def _extract_diagrams(metadata: dict) -> dict:
    """Extract structured summaries from all UML diagrams in the metadata.

    Returns a dict with three keys:
      usecase  — list of { name, actors, usecases, relations }
                 - usecases: [{name, precondition, postcondition, trigger, scenarios}]
                 - relations: [{type: include|extend|interaction, source, target}]
      activity — list of { name, actors, steps: [{name, actor, automatic, body, precondition, postcondition}] }
      classes  — list of { name, classes: [{name, attributes: [{name, type}]}] }

    Only fields that are non-empty are included to keep the payload lean.
    """
    usecase_diagrams: list[dict] = []
    activity_diagrams: list[dict] = []
    class_diagrams: list[dict] = []

    for diagram in metadata.get("diagrams", []):
        dtype = diagram.get("type", "")
        dname = diagram.get("name", "")
        nodes = diagram.get("nodes", [])
        edges = diagram.get("edges", [])

        if dtype == "usecase":
            # Build a node-id → name map so we can resolve relation endpoints
            node_name_map: dict[str, str] = {}
            usecases = []
            actors = []
            for node in nodes:
                node_id = str(node.get("id", "") or node.get("cls_ptr", ""))
                cls_data = node.get("cls", {})
                ntype = cls_data.get("type", "")
                node_name = cls_data.get("name", "")
                if node_id:
                    node_name_map[node_id] = node_name
                if ntype == "actor":
                    actors.append(node_name)
                elif ntype == "usecase":
                    uc: dict = {"name": node_name}
                    if cls_data.get("precondition"):
                        uc["precondition"] = cls_data["precondition"]
                    if cls_data.get("postcondition"):
                        uc["postcondition"] = cls_data["postcondition"]
                    if cls_data.get("trigger"):
                        uc["trigger"] = cls_data["trigger"]
                    if cls_data.get("scenarios"):
                        uc["scenarios"] = cls_data["scenarios"]
                    usecases.append(uc)

            # Extract Include / Extend / Interaction relations
            relations: list[dict] = []
            for edge in edges:
                rel_data = edge.get("rel", {})
                rtype = rel_data.get("type", "interaction")
                src_id = str(edge.get("source_ptr", "") or edge.get("source", ""))
                tgt_id = str(edge.get("target_ptr", "") or edge.get("target", ""))
                src_name = node_name_map.get(src_id, src_id)
                tgt_name = node_name_map.get(tgt_id, tgt_id)
                if src_name and tgt_name:
                    relations.append({"type": rtype, "source": src_name, "target": tgt_name})

            if usecases or actors:
                entry: dict = {
                    "name": dname,
                    "actors": actors,
                    "usecases": usecases,
                }
                if relations:
                    entry["relations"] = relations
                usecase_diagrams.append(entry)

        elif dtype == "activity":
            steps = []
            actors_in_diagram: list[str] = []
            for node in nodes:
                cls_data = node.get("cls", {})
                ntype = cls_data.get("type", "")
                if ntype == "action":
                    step: dict = {"name": cls_data.get("name", "")}
                    if cls_data.get("actorNodeName"):
                        step["actor"] = cls_data["actorNodeName"]
                        if cls_data["actorNodeName"] not in actors_in_diagram:
                            actors_in_diagram.append(cls_data["actorNodeName"])
                    if cls_data.get("isAutomatic"):
                        step["automatic"] = True
                    if cls_data.get("body"):
                        step["body"] = cls_data["body"]
                    if cls_data.get("localPrecondition"):
                        step["precondition"] = cls_data["localPrecondition"]
                    if cls_data.get("localPostcondition"):
                        step["postcondition"] = cls_data["localPostcondition"]
                    steps.append(step)
                elif ntype == "swimlane":
                    actor_name = cls_data.get("actorNodeName", "")
                    if actor_name and actor_name not in actors_in_diagram:
                        actors_in_diagram.append(actor_name)
            if steps:
                activity_diagrams.append({
                    "name": dname,
                    "actors": actors_in_diagram,
                    "steps": steps,
                })

        elif dtype == "classes":
            classes = []
            for node in nodes:
                cls_data = node.get("cls", {})
                if cls_data.get("type") == "class":
                    entry: dict = {"name": cls_data.get("name", "")}
                    attrs = [
                        {"name": a.get("name", ""), "type": a.get("type", "")}
                        for a in cls_data.get("attributes", [])
                        if a.get("name")
                    ]
                    if attrs:
                        entry["attributes"] = attrs
                    classes.append(entry)
            if classes:
                class_diagrams.append({"name": dname, "classes": classes})

    return {
        "usecase": usecase_diagrams,
        "activity": activity_diagrams,
        "classes": class_diagrams,
    }


# ─────────────────────────────────────────────────────────────────────────────
# New-format (classifiers + relations) parser helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_diagram_summary(classifiers: list, relations: list) -> dict:
    """Build diagram_summary from flat classifiers + relations metadata format.

    Produces the same DiagramSummary structure as _extract_diagrams, but from
    the newer flat representation where every UML node is a classifier and every
    edge is a relation.
    """
    clf_by_id: dict[str, dict] = {c["id"]: c for c in classifiers}

    def _name(clf_id: str) -> str:
        return clf_by_id.get(clf_id, {}).get("data", {}).get("name", clf_id)

    # ── Use Case diagram ──────────────────────────────────────────────────────
    actors: list[str] = [
        c["data"]["name"] for c in classifiers if c["data"].get("type") == "actor"
    ]
    usecases: list[dict] = []
    for c in classifiers:
        d = c["data"]
        if d.get("type") != "usecase":
            continue
        uc: dict = {"name": d["name"]}
        if d.get("precondition"):
            uc["precondition"] = d["precondition"]
        if d.get("postcondition"):
            uc["postcondition"] = d["postcondition"]
        if d.get("trigger"):
            uc["trigger"] = d["trigger"]
        if d.get("scenarios"):
            uc["scenarios"] = d["scenarios"]
        usecases.append(uc)

    uc_relations: list[dict] = [
        {"type": r["data"]["type"], "source": _name(r["source"]), "target": _name(r["target"])}
        for r in relations
        if r["data"]["type"] in ("interaction", "inclusion", "extension")
    ]

    # ── Activity diagram ──────────────────────────────────────────────────────
    activity_actors: list[str] = []
    for c in classifiers:
        if c["data"].get("type") == "swimlanegroup":
            for lane in c["data"].get("swimlanes", []):
                actor_name = lane.get("actorNodeName", "")
                if actor_name and actor_name not in activity_actors:
                    activity_actors.append(actor_name)

    steps: list[dict] = []
    for c in classifiers:
        d = c["data"]
        if d.get("type") != "action":
            continue
        step: dict = {"name": d["name"]}
        if d.get("actorNodeName"):
            step["actor"] = d["actorNodeName"]
        if d.get("isAutomatic"):
            step["automatic"] = True
        if d.get("localPrecondition"):
            step["precondition"] = d["localPrecondition"]
        if d.get("localPostcondition"):
            step["postcondition"] = d["localPostcondition"]
        steps.append(step)

    # ── Class diagram ─────────────────────────────────────────────────────────
    classes: list[dict] = []
    for c in classifiers:
        d = c["data"]
        if d.get("type") != "class":
            continue
        entry: dict = {"name": d["name"]}
        attrs = [
            {"name": a["name"], "type": a["type"]}
            for a in d.get("attributes", [])
            if a.get("name")
        ]
        if attrs:
            entry["attributes"] = attrs
        classes.append(entry)

    return {
        "usecase": [{"name": "Use Case Diagram", "actors": actors, "usecases": usecases, "relations": uc_relations}] if (actors or usecases) else [],
        "activity": [{"name": "Activity Diagram", "actors": activity_actors, "steps": steps}] if steps else [],
        "classes": [{"name": "Class Diagram", "classes": classes}] if classes else [],
    }


_CREATE_KEYWORDS = frozenset({"fill", "submit", "create", "add", "register", "new", "open", "upload", "enter", "apply"})
_UPDATE_KEYWORDS = frozenset({"edit", "update", "modify", "assess", "analyze", "analyse", "review", "decide", "final", "provide", "check", "approve", "perform"})
_DELETE_KEYWORDS = frozenset({"delete", "remove", "cancel", "reject", "deny"})


def _norm_state(label: str) -> str:
    """Normalise state labels into stable snake_case IDs."""
    if not label:
        return ""
    return "_".join(label.strip().lower().replace("-", " ").split())


def _build_parser_dsl(classifiers: list, relations: list) -> dict:
    """Build the canonical Parser DSL from classifiers + relations.

    Output:
      domain      — {name}
      actors      — [{id, name}]
      entities    — [{id, name, fields}]  (domain classes)
      actions     — [{id, name, actor, input?: [entity_ids], auto?: true}]
      workflow    — {nodes: [action_id, ...], edges: [[from, to] or [from, to, condition]]}
    """
    clf_by_id: dict[str, dict] = {c["id"]: c for c in classifiers}
    class_by_id: dict[str, dict] = {c["id"]: c for c in classifiers if c["data"].get("type") == "class"}

    _CONTROL_TYPES = frozenset({"decision", "merge", "fork", "join", "initial", "final", "object", "signal", "event"})

    # Build adjacency list for controlflow edges (used by BFS)
    edges_by_source: dict[str, list] = {}
    for r in relations:
        if r.get("data", {}).get("type") == "controlflow":
            edges_by_source.setdefault(r["source"], []).append(r)

    # Build bidirectional adjacency for entity-field lookup
    adjacent_nodes: dict[str, list] = {}
    for r in relations:
        if r.get("data", {}).get("type") in ("controlflow", "objectflow"):
            adjacent_nodes.setdefault(r["source"], []).append(r["target"])
            adjacent_nodes.setdefault(r["target"], []).append(r["source"])

    def _input_entities_for(action_id: str) -> list[str]:
        """Return entity (class) IDs from object nodes adjacent to an action."""
        entity_ids: list[str] = []
        seen: set[str] = set()
        for neighbor_id in adjacent_nodes.get(action_id, []):
            neighbor_data = clf_by_id.get(neighbor_id, {}).get("data", {})
            if neighbor_data.get("type") == "object":
                cls_id = neighbor_data.get("cls", "")
                if cls_id and cls_id not in seen:
                    seen.add(cls_id)
                    entity_ids.append(cls_id)
        return entity_ids

    def _find_action_successors(node_id: str, visited: frozenset) -> list[dict]:
        """BFS through non-action control nodes to find the next action(s)."""
        results = []
        source_type = clf_by_id.get(node_id, {}).get("data", {}).get("type", "")
        for edge_idx, edge in enumerate(edges_by_source.get(node_id, [])):
            target_id = edge["target"]
            if target_id in visited:
                continue
            visited = visited | {target_id}
            target_data = clf_by_id.get(target_id, {}).get("data", {})
            t_type = target_data.get("type", "")
            if t_type == "action":
                trans: dict = {"to": target_id}
                cond = edge.get("data", {}).get("condition") or {}
                guard = edge.get("data", {}).get("guard") or ""
                if cond and not cond.get("isElse") and cond.get("target_attribute"):
                    trans["condition"] = f"{cond['target_attribute']} == {cond['threshold']}"
                elif cond and cond.get("isElse"):
                    trans["condition"] = "else"
                elif guard:
                    trans["condition"] = guard
                elif source_type == "decision":
                    trans["condition"] = f"branch_{edge_idx + 1}"
                results.append(trans)
            elif t_type in _CONTROL_TYPES:
                sub = _find_action_successors(target_id, visited)
                if source_type == "decision":
                    for s in sub:
                        if "condition" not in s:
                            s["condition"] = f"branch_{edge_idx + 1}"
                results.extend(sub)
        return results

    # domain name (from system_name on classifiers)
    domain_name = next((c.get("system_name", "") for c in classifiers if c.get("system_name")), "")

    # actors
    actors = [
        {"id": c["id"], "name": c["data"]["name"]}
        for c in classifiers if c["data"].get("type") == "actor"
    ]

    # Also index by swimlane actorNode IDs (actions use these, not classifier IDs)
    _swimlane_id_to_name: dict[str, str] = {}
    for c in classifiers:
        d = c.get("data", {})
        if d.get("type") == "swimlanegroup":
            for lane in d.get("swimlanes", []):
                node_id = lane.get("actorNode")
                name = lane.get("actorNodeName")
                if node_id and name:
                    _swimlane_id_to_name[node_id] = name
    # Add swimlane actor nodes deduplicated by id
    existing_ids = {a["id"] for a in actors}
    for node_id, name in _swimlane_id_to_name.items():
        if node_id not in existing_ids:
            actors.append({"id": node_id, "name": name})
            existing_ids.add(node_id)

    # entities (domain classes)
    entities = [
        {
            "id": c["id"],
            "name": c["data"]["name"],
            "fields": [a["name"] for a in c["data"].get("attributes", []) if a.get("name")],
        }
        for c in classifiers if c["data"].get("type") == "class"
    ]

    # actions (all action nodes)
    actions = []
    for c in classifiers:
        d = c["data"]
        if d.get("type") != "action":
            continue
        is_auto = bool(d.get("isAutomatic"))
        action: dict = {
            "id": c["id"],
            "name": d["name"],
        }
        if d.get("actorNode"):
            action["actor"] = d["actorNode"]
        if is_auto:
            action["auto"] = True
        input_entities = _input_entities_for(c["id"])
        if input_entities:
            action["input"] = input_entities
        actions.append(action)

    # workflow — nodes list + edges [[from, to] or [from, to, condition]]
    wf_nodes = [c["id"] for c in classifiers if c["data"].get("type") == "action"]
    wf_edges: list[list] = []
    for c in classifiers:
        if c["data"].get("type") != "action":
            continue
        for succ in _find_action_successors(c["id"], frozenset({c["id"]})):
            edge: list = [c["id"], succ["to"]]
            if "condition" in succ:
                edge.append(succ["condition"])
            wf_edges.append(edge)

    return {
        "domain": {"name": domain_name},
        "actors": actors,
        "entities": entities,
        "actions": actions,
        "workflow": {
            "nodes": wf_nodes,
            "edges": wf_edges,
        },
    }


def _build_flow_graph(classifiers: list, relations: list, parser_dsl: dict) -> dict:
    """Build a normalised flow graph used by state-driven page mapping.

    This is the intermediate layer between parser and UI synthesis:
      - states: canonical workflow states
      - transitions: actor-bound actions moving entity state from -> to
    """
    actors = {a["id"]: a for a in parser_dsl.get("actors", []) or []}
    actions = {a["id"]: a for a in parser_dsl.get("actions", []) or []}
    workflow_edges = parser_dsl.get("workflow", {}).get("edges", []) or []

    clf_by_id = {c["id"]: c for c in classifiers}
    object_nodes = {
        c["id"]: c for c in classifiers
        if c.get("data", {}).get("type") == "object"
    }

    incoming_object_states: dict[str, set[str]] = {}
    outgoing_object_states: dict[str, set[str]] = {}
    for rel in relations:
        if rel.get("data", {}).get("type") != "controlflow":
            continue
        src = rel.get("source")
        tgt = rel.get("target")
        if src in object_nodes and tgt in actions:
            s = _norm_state(object_nodes[src].get("data", {}).get("state", ""))
            if s:
                incoming_object_states.setdefault(tgt, set()).add(s)
        if src in actions and tgt in object_nodes:
            s = _norm_state(object_nodes[tgt].get("data", {}).get("state", ""))
            if s:
                outgoing_object_states.setdefault(src, set()).add(s)

    predecessors: dict[str, set[str]] = {}
    for edge in workflow_edges:
        if len(edge) < 2:
            continue
        src, tgt = edge[0], edge[1]
        if src in actions and tgt in actions:
            predecessors.setdefault(tgt, set()).add(src)

    action_from_state: dict[str, str] = {}
    action_to_state: dict[str, str] = {}

    for aid, action in actions.items():
        in_states = sorted(incoming_object_states.get(aid, set()))
        out_states = sorted(outgoing_object_states.get(aid, set()))
        action_from_state[aid] = in_states[0] if in_states else ""

        if out_states:
            action_to_state[aid] = out_states[0]
        else:
            action_to_state[aid] = _norm_state(f"{action.get('name', aid)} done")

    for aid, action in actions.items():
        if action_from_state.get(aid):
            continue
        pred_states = {
            action_to_state[p]
            for p in predecessors.get(aid, set())
            if action_to_state.get(p)
        }
        if len(pred_states) == 1:
            action_from_state[aid] = next(iter(pred_states))
        elif len(pred_states) > 1:
            action_from_state[aid] = "or_" + "_".join(sorted(pred_states))
        else:
            action_from_state[aid] = "start"

    states = {"start"}
    transitions = []
    for aid, action in actions.items():
        actor_id = action.get("actor")
        from_state = action_from_state.get(aid, "start") or "start"
        to_state = action_to_state.get(aid, "done") or "done"
        states.add(from_state)
        states.add(to_state)
        transitions.append({
            "id": f"tr_{aid}_{from_state}_{to_state}",
            "action_id": aid,
            "from": from_state,
            "to": to_state,
            "actor": actor_id,
            "action": action.get("name", aid),
            "auto": bool(action.get("auto", False)),
        })

    entity_names = [e.get("name", "") for e in parser_dsl.get("entities", []) or [] if e.get("name")]
    actor_names = [a.get("name", "") for a in parser_dsl.get("actors", []) or [] if a.get("name")]
    return {
        "entities": entity_names,
        "states": sorted(states),
        "actors": actor_names,
        "transitions": transitions,
    }


def _build_screens(classifiers: list, relations: list) -> List[ScreenInfo]:
    """Build a ScreenInfo for every non-automatic action in the classifier list.

    Models are inferred from object classifiers reachable via controlflow edges.
    CRUD flags are inferred from action name words matched against keyword sets.
    """
    obj_by_id: dict[str, dict] = {
        c["id"]: c for c in classifiers if c["data"].get("type") == "object"
    }

    def _connected_models(action_id: str) -> list[str]:
        models: list[str] = []
        for r in relations:
            if r["data"].get("type") != "controlflow":
                continue
            other_id: str = ""
            if r["source"] == action_id:
                other_id = r["target"]
            elif r["target"] == action_id:
                other_id = r["source"]
            if other_id and other_id in obj_by_id:
                clsname = obj_by_id[other_id]["data"].get("clsName", "")
                if clsname and clsname not in models:
                    models.append(clsname)
        return models

    screens: List[ScreenInfo] = []
    for c in classifiers:
        d = c["data"]
        if d.get("type") != "action" or d.get("isAutomatic"):
            continue
        name: str = d.get("name", "")
        words = set(name.lower().split())
        screens.append(ScreenInfo(
            page_id=c["id"],
            page_name=name,
            screen_type="",
            has_create=bool(words & _CREATE_KEYWORDS),
            has_update=bool(words & _UPDATE_KEYWORDS),
            has_delete=bool(words & _DELETE_KEYWORDS),
            models=_connected_models(c["id"]),
            sections_count=1,
        ))
    return screens


def parser_node(state: PipelineState) -> dict:
    """Parse metadata JSON (classifiers + relations format) → ScreenInfo list + diagram summary + DSL."""
    try:
        metadata = json.loads(state["metadata"])
        classifiers: list = metadata.get("classifiers", [])
        relations: list = metadata.get("relations", [])
        screens = _build_screens(classifiers, relations)
        diagram_summary = _build_diagram_summary(classifiers, relations)
        parser_dsl = _build_parser_dsl(classifiers, relations)
        flow_graph = _build_flow_graph(classifiers, relations, parser_dsl)
        parser_dsl["flow_graph"] = flow_graph
        return {
            "screens": screens,
            "diagram_summary": diagram_summary,
            "parser_dsl": parser_dsl,
            "flow_graph": flow_graph,
            "error": None,
        }
    except Exception as exc:
        logger.exception("parser_node failed")
        return {
            "screens": [],
            "diagram_summary": {"usecase": [], "activity": [], "classes": []},
            "parser_dsl": {"actors": [], "objects": [], "activities": [], "workflow": {"transitions": []}},
            "flow_graph": {"entities": [], "states": [], "actors": [], "transitions": []},
            "error": str(exc),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Page Synthesis — deterministic UI segmentation compiler pass
#    Input:  parser_dsl (actors / entities / actions / workflow)
#    Output: list of PageSpec dicts, one per navigational unit
#
#    Algorithm (three phases):
#      1. Filter   — skip auto=True actions (no human UI)
#      2. Cluster  — group manual actions by actor; within each actor
#                    group, merge pairs whose affinity score > THRESHOLD
#      3. Cut      — if a cluster > MAX_ACTIONS_PER_PAGE, split it
# ─────────────────────────────────────────────────────────────────────────────

_PAGE_AFFINITY_THRESHOLD = 0.5   # minimum score to share a page
_MAX_ACTIONS_PER_PAGE    = 5     # hard split ceiling per page


def _synthesise_pages(parser_dsl: dict) -> dict:
    """Pure, deterministic page synthesis.

    Returns a ui_ir-format dict:
        {
          "apps": [
            {
              "actor_id": str,                # actor id
              "pages": [
                {
                  "name":       str,          # PascalCase page name
                  "components": [ComponentSpec],
                }
              ],
            }
          ],
          "routing": {
            "auth_role_map": {actor_id: "/<actor_id>"},
          },
        }

    ComponentSpec:
        {
          "type":        str,           # form | detail | delete_confirm | list
          "bind_action": str,           # action id that triggers this component
          "entity_id":   str | None,    # entity this component operates on
          "fields":      [str],         # entity field names (empty if no entity)
        }

    Guarantees:
    - Auto actions produce no pages.
    - Actions for different actors are never on the same page.
    - Same input always produces the same output (deterministic).
    - An empty or missing DSL returns {"apps": [], "routing": {"auth_role_map": {}}}.
    """
    _EMPTY: dict = {"apps": [], "routing": {"auth_role_map": {}}}

    flow_graph = parser_dsl.get("flow_graph") or {}
    transitions = flow_graph.get("transitions", []) if isinstance(flow_graph, dict) else []
    if transitions:
        actors = {a["id"]: a for a in parser_dsl.get("actors", []) or []}
        actor_groups: dict[tuple[str, str], list[dict]] = {}
        for t in transitions:
            if t.get("auto"):
                continue
            actor_id = t.get("actor")
            if not actor_id or actor_id not in actors:
                continue
            from_state = _norm_state(t.get("from", "start")) or "start"
            actor_groups.setdefault((actor_id, from_state), []).append(t)

        if not actor_groups:
            return _EMPTY

        actions_by_id = {a["id"]: a for a in parser_dsl.get("actions", []) or []}
        entities_by_id = {e["id"]: e for e in parser_dsl.get("entities", []) or []}

        apps_by_actor: dict[str, list] = {}
        for actor_id, state in sorted(actor_groups.keys()):
            group = actor_groups[(actor_id, state)]
            actor_name = actors.get(actor_id, {}).get("name", actor_id)
            state_token = "".join(w.capitalize() for w in state.split("_")) or "State"
            page_name = f"{''.join(w.capitalize() for w in actor_name.replace('-', ' ').split())}{state_token}Page"
            page_id = "_".join(actor_name.lower().replace("-", "_").split()) + f"_{state}_page"
            action_ids = [t["action_id"] for t in group]
            transition_ids = [t["id"] for t in group]
            intent_hints = []
            for t in group:
                act = actions_by_id.get(t["action_id"], {})
                entity_ids = act.get("input", []) or []
                entity_names = [
                    entities_by_id.get(eid, {}).get("name", eid)
                    for eid in entity_ids
                ]
                attribute_contracts = []
                binding_groups = []
                operation_hint = {
                    "endpoint": f"/action/{t['action_id']}/",
                    "allowed": ["create", "update", "delete", "readonly"],
                    "kind": "llm_decide",
                }
                for eid in entity_ids:
                    entity = entities_by_id.get(eid, {})
                    entity_name = entity.get("name", eid)
                    fields = entity.get("fields", []) or []
                    binds = []
                    for field in fields:
                        bind_expr = f"{entity_name}.{field}"
                        binds.append(bind_expr)
                        attribute_contracts.append({
                            "entity_id": eid,
                            "entity_name": entity_name,
                            "attribute": field,
                            "bind": bind_expr,
                            "ui_policy": {
                                "validation": [],
                                "operations": operation_hint,
                            },
                        })
                    if len(binds) >= 2:
                        binding_groups.append({
                            "entity_id": eid,
                            "entity_name": entity_name,
                            "bind": binds,
                            "kind": "attribute_set_projection",
                        })
                intent_hints.append({
                    "action_id": t["action_id"],
                    "action_name": act.get("name", t["action_id"]),
                    "transition_id": t["id"],
                    "entity_ids": entity_ids,
                    "entity_names": entity_names,
                    "attribute_contracts": attribute_contracts,
                    "binding_groups": binding_groups,
                })
            apps_by_actor.setdefault(actor_id, []).append({
                "page_id": page_id,
                "name": page_name,
                "state": state,
                "action_ids": action_ids,
                "transition_ids": transition_ids,
                "intent_hints": intent_hints,
            })

        apps = [
            {
                "actor_id": actor_id,
                "actor_name": actors.get(actor_id, {}).get("name", actor_id),
                "pages": pages,
            }
            for actor_id, pages in apps_by_actor.items()
        ]
        routing = {"auth_role_map": {a: f"/{a}" for a in apps_by_actor}}
        return {"apps": apps, "routing": routing}

    actors  = {a["id"]: a for a in parser_dsl.get("actors",  []) or []}
    actions = {a["id"]: a for a in parser_dsl.get("actions", []) or []}
    edges   = parser_dsl.get("workflow", {}).get("edges", []) or []

    # ── Phase 1: filter manual actions only ──────────────────────────────────
    manual = {
        aid: act
        for aid, act in actions.items()
        if not act.get("auto", False)
        and act.get("actor") in actors
    }
    if not manual:
        return _EMPTY

    # ── Build adjacency set from workflow edges ──────────────────────────────
    adjacent: set[tuple] = set()
    for edge in edges:
        if len(edge) >= 2:
            adjacent.add((edge[0], edge[1]))
            adjacent.add((edge[1], edge[0]))   # treat as undirected for affinity

    # ── Phase 2: greedy cluster per actor ────────────────────────────────────
    def _affinity(a_id: str, b_id: str) -> float:
        a, b = manual[a_id], manual[b_id]
        score = 0.0
        if a.get("actor") == b.get("actor"):
            score += 0.4
        if (a_id, b_id) in adjacent:
            score += 0.3
        # shared input entity
        a_inputs = set(a.get("input", []) or [])
        b_inputs = set(b.get("input", []) or [])
        if a_inputs & b_inputs:
            score += 0.3
        return score

    # Initialise: each action is its own cluster
    clusters: list[list[str]] = [[aid] for aid in manual]

    changed = True
    while changed:
        changed = False
        merged: list[list[str]] = []
        used = [False] * len(clusters)
        for i in range(len(clusters)):
            if used[i]:
                continue
            current = clusters[i]
            for j in range(i + 1, len(clusters)):
                if used[j]:
                    continue
                other = clusters[j]
                # Hard constraint: never mix actors
                actor_i = manual[current[0]].get("actor")
                actor_j = manual[other[0]].get("actor")
                if actor_i != actor_j:
                    continue
                # Would merge violate size limit?
                if len(current) + len(other) > _MAX_ACTIONS_PER_PAGE:
                    continue
                # Check average affinity between all pairs across the two clusters
                pairs = [(a, b) for a in current for b in other]
                avg_score = sum(_affinity(a, b) for a, b in pairs) / len(pairs)
                if avg_score >= _PAGE_AFFINITY_THRESHOLD:
                    current = current + other
                    used[j] = True
                    changed = True
            merged.append(current)
            used[i] = True
        clusters = merged

    # ── Phase 3: cut oversized clusters ─────────────────────────────────────
    final_clusters: list[list[str]] = []
    for cluster in clusters:
        if len(cluster) <= _MAX_ACTIONS_PER_PAGE:
            final_clusters.append(cluster)
        else:
            for k in range(0, len(cluster), _MAX_ACTIONS_PER_PAGE):
                final_clusters.append(cluster[k: k + _MAX_ACTIONS_PER_PAGE])

    # ── Emit ui_ir ──────────────────────────────────────────────────────────
    entity_list = parser_dsl.get("entities", []) or []
    entity_by_id = {e["id"]: e for e in entity_list}

    def _page_name(actor_name: str, page_num: int) -> str:
        safe = actor_name.lower().replace("-", "_").replace(" ", "_")
        raw = f"{safe}_page" if page_num == 0 else f"{safe}_page_{page_num + 1}"
        return "".join(w.capitalize() for w in raw.split("_"))

    # Group clusters by actor, preserving ordering
    apps_by_actor: dict[str, list] = {}
    actor_page_counter: dict[str, int] = {}
    for cluster in final_clusters:
        actor_id = manual[cluster[0]].get("actor", "")
        actor_name = actors.get(actor_id, {}).get("name", actor_id)
        page_num = actor_page_counter.get(actor_id, 0)
        actor_page_counter[actor_id] = page_num + 1
        apps_by_actor.setdefault(actor_id, []).append({
            "name":       _page_name(actor_name, page_num),
            "action_ids": cluster,
        })

    apps = [
        {"actor_id": actor_id, "actor_name": actors.get(actor_id, {}).get("name", actor_id), "pages": pages}
        for actor_id, pages in apps_by_actor.items()
    ]
    routing = {"auth_role_map": {a: f"/{a}" for a in apps_by_actor}}
    return {"apps": apps, "routing": routing}


# ─────────────────────────────────────────────────────────────────────────────
# UI Designer Agent
#    Takes the final UX design and generates a modern Tailwind-based
#    Django base.html + style.css. The Jinja2-generated page content
#    blocks automatically inherit the new look.
# ─────────────────────────────────────────────────────────────────────────────

def ui_designer_node(state: PipelineState) -> dict:
    """UI Designer: runs page synthesis then calls LLM for ui_ir component mapping."""
    from llm.prompts.agents import AGENT_UI_DESIGNER

    parser_dsl = state.get("parser_dsl") or {}

    # ── Deterministic page synthesis (pre-LLM) ───────────────────────────────
    page_ir = _synthesise_pages(parser_dsl)

    prompt = AGENT_UI_DESIGNER.format(
        project_name=state["project_name"],
        application_name=state["application_name"],
        page_ir_json=json.dumps(page_ir, indent=2),
        parser_dsl_json=json.dumps(parser_dsl, indent=2),
    )

    try:
        raw = call_openai("gpt-4o", prompt)
        ui_design = _parse_json_response(raw)
        # Default ui_ir to the deterministic page_ir when LLM omits it
        ui_design.setdefault("ui_ir", page_ir)
        # Merge actor_name from page_ir into the LLM ui_ir (LLM may not emit it)
        page_ir_actor_names = {app["actor_id"]: app.get("actor_name") for app in page_ir.get("apps", [])}
        for app in ui_design["ui_ir"].get("apps", []):
            if not app.get("actor_name"):
                app["actor_name"] = page_ir_actor_names.get(app["actor_id"])
        logger.info("ui_designer_node: %d ui_ir apps",
                    len(ui_design.get("ui_ir", {}).get("apps", [])))
        return {"page_ir": page_ir, "ui_design": ui_design, "error": None}
    except Exception as exc:
        logger.warning("ui_designer_node failed (%s); skipping UI enhancement", exc)
        return {"page_ir": page_ir, "ui_design": None, "error": None}  # non-fatal: Jinja2 fallback still works


# ── Theme Node ────────────────────────────────────────────────────────────────

def _collect_variants(obj: object, seen: set | None = None) -> list:
    """Recursively walk ui_design and collect unique {tag, variant} pairs from AST nodes."""
    if seen is None:
        seen = set()
    results = []
    if isinstance(obj, dict):
        variant = obj.get("variant")
        if variant:
            tag = obj.get("tag", "div")
            key = (tag, variant)
            if key not in seen:
                seen.add(key)
                results.append({"tag": tag, "variant": variant})
        for v in obj.values():
            results.extend(_collect_variants(v, seen))
    elif isinstance(obj, list):
        for item in obj:
            results.extend(_collect_variants(item, seen))
    return results


def theme_node(state: PipelineState) -> dict:
    """Theme Agent: inspects actual AST variant labels and generates matching design tokens.

    The LLM decides the token key namespace (region.*, component.*, element.*) based on
    the tag + variant context. No keys are hardcoded — tokens are driven entirely by what
    variants the UI Designer placed in the AST.
    """
    from llm.prompts.agents import AGENT_THEME_DESIGNER

    ui_design = state.get("ui_design") or {}
    variants = _collect_variants(ui_design)

    if not variants:
        logger.info("theme_node: no variants found in ui_design; skipping LLM call")
        return {"theme": {"name": "default", "tokens": {}}}

    design_goal = (state.get("theme") or {}).get("design_goal") or \
                  f"Clean professional UI for {state['project_name']}"

    prompt = AGENT_THEME_DESIGNER.format(
        project_name=state["project_name"],
        application_name=state["application_name"],
        design_goal=design_goal,
        variants_json=json.dumps(variants, indent=2),
    )

    refine_prompt = state.get("refine_prompt")
    if refine_prompt:
        prompt += (
            f"\n\nREFINEMENT REQUEST FROM USER:\n{refine_prompt}\n"
            "Adjust the design tokens to satisfy this request. "
            "Keep all required variant keys — update only the Tailwind class values."
        )

    try:
        raw = call_openai("gpt-4o", prompt)
        theme = _parse_json_response(raw)
        logger.info(
            "theme_node: generated theme '%s' with %d tokens",
            theme.get("name"), len(theme.get("tokens", {})),
        )
        return {"theme": theme}
    except Exception as exc:
        logger.warning("theme_node failed (%s); using empty theme", exc)
        return {"theme": {"name": "default", "tokens": {}}}

