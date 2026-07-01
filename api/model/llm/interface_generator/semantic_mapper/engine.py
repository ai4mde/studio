"""
Transformation Engine — Stage 1: UML Diagrams -> Interface Metadata JSON

Reads and executes rules from interface_mapper_rules.yaml (TKB).
Adding a new UML->interface mapping requires editing only the YAML file.

Output format is compatible with loading_json_utils.retrieve_pages /
retrieve_section_components.

UseCase extraction is equivalent to _build_usecase_navigation:
  - primary_model inferred from UC name + explicit class refs
  - actor_permissions aggregated from UC names (view/create/update/delete)
  - page roles (collection_workspace / detail_workspace / workflow_entry)
  - section->page assignment uses primary_model for precision
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

import yaml

from .sanitization import (
    app_name_sanitization,
    page_name_sanitization,
    section_name_sanitization,
)

log = logging.getLogger(__name__)

TKB_PATH = Path(__file__).parent / "interface_mapper_rules.yaml"


# =============================================================================
# UseCase extraction helpers (ported from usecase_workflow.py)
# =============================================================================

def _uc_name_tokens(text: str) -> set[str]:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(text or ""))
    tokens = {t for t in re.split(r"[^A-Za-z0-9]+", spaced.lower()) if len(t) > 1}
    singulars = {t[:-1] for t in tokens if len(t) > 3 and t.endswith("s")}
    return tokens | singulars


def _rank_models(text: str, model_names: list[str]) -> list[str]:
    text_tokens = _uc_name_tokens(text)
    ranked = []
    for i, model in enumerate(model_names):
        mt = _uc_name_tokens(model)
        overlap = len(text_tokens & mt)
        compact_m = re.sub(r"[^a-z0-9]+", "", model.lower())
        compact_t = re.sub(r"[^a-z0-9]+", "", text.lower())
        sub = 2 if compact_m and compact_m in compact_t else 0
        ranked.append((overlap + sub, -i, model))
    ranked.sort(reverse=True)
    return [m for score, _, m in ranked if score > 0]


def _uc_infer_model(cls: dict, all_class_names: list[str]) -> str:
    """Infer primary model from UseCase name + explicit class refs."""
    explicit = cls.get("classes") or []
    if isinstance(explicit, dict):
        flat: list = []
        for v in explicit.values():
            flat.extend(v or [])
        explicit = flat
    for ref in explicit:
        ref_name = ref if isinstance(ref, str) else str(ref.get("name") or ref.get("id") or "")
        if ref_name in all_class_names:
            return ref_name
    ranked = _rank_models(cls.get("name", ""), all_class_names)
    return ranked[0] if ranked else ""


def _uc_infer_permissions(uc_name: str, perm_keywords: dict, manage_cfg: dict) -> list[str]:
    name_l = str(uc_name or "").lower()
    perms: set[str] = {"view"}
    for perm, keywords in perm_keywords.items():
        if any(k in name_l for k in (keywords or [])):
            perms.add(perm)
    if manage_cfg and "manage" in name_l:
        excludes = manage_cfg.get("excludes") or []
        requires = manage_cfg.get("requires") or []
        if not any(e in name_l for e in excludes) and any(r in name_l for r in requires):
            perms.update({"create", "delete"})
    return [p for p in ("view", "create", "update", "delete") if p in perms]


def _uc_infer_role(uc_name: str, role_keywords: dict, default: str = "object_workspace") -> str:
    name_l = str(uc_name or "").lower()
    for role, keywords in role_keywords.items():
        if any(k in name_l for k in (keywords or [])):
            return role
    return default


def _uc_infer_operation(uc_name: str, op_keywords: dict, default: str = "manage_object") -> str:
    name_l = str(uc_name or "").lower()
    for op, keywords in op_keywords.items():
        if any(k in name_l for k in (keywords or [])):
            return op
    return default


# =============================================================================
# Semantic Interpretation — Stage 1
# =============================================================================

def _interpret_entity_intents(
    cls: dict,
    rules: list[dict],
    has_composition_children: bool = False,
) -> list[str]:
    """
    Derive a flat Interaction Intent list for a class classifier.

    Two rule types (read from YAML intent_rules):
      primary: [...]   first-match-wins; default CRUD
      add: [...]       all matching secondary rules fire (additive)

    Result: [primary, *secondary]  — domain-independent interaction vocabulary.
    """
    op_count   = len(cls.get("operations") or [])
    attr_count = len(cls.get("attributes") or [])
    attr_names = [
        (a["name"] if isinstance(a, dict) else str(a)).lower()
        for a in (cls.get("attributes") or [])
    ]
    name = str(cls.get("name") or "")

    # Pass 1 — primary intent (first match wins)
    primary = "CRUD"
    for rule in rules:
        if "primary" not in rule:
            continue
        when = rule.get("when") or {}
        if "max_operations" in when and op_count > when["max_operations"]:
            continue
        if "max_attributes" in when and attr_count > when["max_attributes"]:
            continue
        if "name_matches" in when and not re.search(when["name_matches"], name, re.I):
            continue
        raw = rule["primary"]
        primary = raw[0] if isinstance(raw, list) else str(raw)
        break

    # Pass 2 — secondary intents (additive)
    secondary: list[str] = []
    for rule in rules:
        if "add" not in rule:
            continue
        when = rule.get("when") or {}

        if when.get("computed") == "from_composition":
            if has_composition_children:
                secondary.extend(rule["add"])
            continue

        if "primary_is" in when and primary != when["primary_is"]:
            continue
        if "min_attributes" in when and attr_count < when["min_attributes"]:
            continue
        if "attribute_name_matches" in when:
            if not any(re.search(when["attribute_name_matches"], n, re.I) for n in attr_names):
                continue

        secondary.extend(rule["add"])

    # Merge: primary first, then secondary (preserve order, no duplicates)
    seen: set[str] = {primary}
    intents: list[str] = [primary]
    for i in secondary:
        if i not in seen:
            intents.append(i)
            seen.add(i)
    return intents


def _ops_from_profile(profile: dict) -> dict:
    """Map an Interaction Intent profile to Interface Metadata section.operations flags."""
    intents = set(profile.get("intents") or [])
    if "CRUD" in intents:
        return {"create": True, "update": True, "delete": True, "select": True}
    if "Configuration" in intents:
        return {"create": False, "update": True, "delete": False, "select": True}
    # Lookup or unknown: read-only
    return {"create": False, "update": False, "delete": False, "select": True}


def _layout_from_intent_profile(profile: dict) -> str:
    """Infer the most appropriate default section layout from a semantic intent profile.

    Intent → layout mapping rationale:
      Configuration  → form   (admin-only, single-record update)
      Lookup         → list   (small reference table, read-only)
      StateTransition or Hierarchy → table (tracked lifecycle / nested records)
      CRUD + Search  → card   (many-attribute entity, browseable as cards)
      CRUD only      → card   (default; candidate phase will vary this)
    """
    intents = set(profile.get("intents") or [])
    if "Configuration" in intents:
        return "form"
    if "Lookup" in intents:
        return "list"
    if "StateTransition" in intents or "Hierarchy" in intents:
        return "table"
    if "CRUD" in intents and "Search" in intents:
        return "card"
    return "card"


def _recognize_workflow(diagram: dict, patterns: list[dict], ctx: "_Context") -> list[str]:
    """
    Recognize the workflow kind of an activity diagram from its node topology.

    Scans all Action and Decision nodes; tests each pattern's AND-conditions.
    First matching pattern wins. Default: [Workflow, Sequential].
    """
    action_text = ""
    has_decision = False
    for node in diagram.get("nodes", []):
        nt  = ctx.node_type(node)
        cls = ctx.cls_data(node)
        name = str(cls.get("name") or "").lower()
        if nt == "action":
            action_text += " " + name
        elif nt == "decision":
            has_decision = True

    for pattern in patterns:
        intents = pattern.get("intents") or ["Workflow", "Sequential"]
        match   = pattern.get("match") or {}

        if match.get("requires_decision") and not has_decision:
            continue

        if not all(
            re.search(p, action_text, re.I)
            for p in (match.get("action_name_matches") or [])
        ):
            continue

        return list(intents)

    return ["Workflow", "Sequential"]


# =============================================================================
# Expression evaluator
# =============================================================================

# Simple single-value transforms (no context needed)
_TRANSFORMS: dict[str, Callable] = {
    "app_name":    app_name_sanitization,
    "page_name":   page_name_sanitization,
    "section_name": section_name_sanitization,
    "lower":       str.lower,
}

# Context-aware transforms: (value, ctx) -> result
# Semantic inference reads keyword tables from ctx._si (loaded from YAML)
_CTX_TRANSFORMS: dict[str, Callable] = {
    "infer_model": lambda cls, ctx: _uc_infer_model(
        cls if isinstance(cls, dict) else {},
        ctx.all_class_names(),
    ),
    "infer_role": lambda name, ctx: _uc_infer_role(
        name,
        ctx._si.get("role_keywords") or {},
        ctx._si.get("role_default", "object_workspace"),
    ),
    "infer_operation": lambda name, ctx: _uc_infer_operation(
        name,
        ctx._si.get("operation_keywords") or {},
        ctx._si.get("operation_default", "manage_object"),
    ),
    "infer_permissions": lambda name, ctx: _uc_infer_permissions(
        name,
        ctx._si.get("permission_keywords") or {},
        ctx._si.get("manage_implies_create_delete") or {},
    ),
    # Stage 2 — Pattern Derivation: read Interaction Intent profiles from Stage 1
    "entity_intents":          lambda ptr,    ctx: ctx.semantic_profiles.get(str(ptr or ""), {}).get("intents", ["CRUD"]),
    "entity_ops":              lambda ptr,    ctx: _ops_from_profile(ctx.semantic_profiles.get(str(ptr or ""), {})),
    "entity_layout":           lambda ptr,    ctx: _layout_from_intent_profile(ctx.semantic_profiles.get(str(ptr or ""), {})),
    "diagram_workflow_intents": lambda diag_id, ctx: ctx.workflow_profiles.get(str(diag_id or ""), {}).get("intents", ["Workflow", "Sequential"]),
}


_SELF_REF = "@self"


def _eval_path_expr(expr: str, source: dict, ctx: "_Context") -> Any:
    """Evaluate a $-path expression with an optional transform."""
    raw = expr[1:]
    path_part, transform_name = (raw.split(" | ", 1) if " | " in raw else (raw, None))
    value = _resolve_path(path_part.strip(), source)
    if transform_name:
        tn = transform_name.strip()
        if tn in _CTX_TRANSFORMS:
            value = _CTX_TRANSFORMS[tn](value, ctx)
        else:
            fn = _TRANSFORMS.get(tn)
            if fn and value is not None:
                value = fn(value)
    return value


def _eval(expr: Any, source: dict, ctx: "_Context") -> Any:
    """
    Evaluate one TKB mapping expression.

    Syntax:
      $path.to.field         dot-path into source
      $path | transform      dot-path then named transform
      @uuid                  new UUID4
      @list / @dict / @null  empty collection / None
      @self                  source dict itself
      non-string             returned as-is
    """
    if not isinstance(expr, str):
        return expr
    if expr == "@uuid":   return str(uuid4())
    if expr == "@list":   return []
    if expr == "@dict":   return {}
    if expr == "@null":   return None
    if expr == _SELF_REF:   return source

    if expr.startswith("$"):
        return _eval_path_expr(expr, source, ctx)

    return expr  # plain string constant


def _resolve_path(path: str, source: dict) -> Any:
    current: Any = source
    for key in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _set_nested(target: dict, dotted_key: str, value: Any) -> None:
    keys = dotted_key.split(".")
    for key in keys[:-1]:
        target = target.setdefault(key, {})
    target[keys[-1]] = value


def _apply_mapping(mapping: dict, source: dict, ctx: "_Context") -> dict:
    result: dict = {}
    for dotted_key, expr in mapping.items():
        _set_nested(result, dotted_key, _eval(expr, source, ctx))
    return result


def _edge_mult_matches(edge: dict, req_types: set, allowed_src_mult: set, allowed_tgt_mult: set, rel_data: dict) -> bool:
    """Return True if an edge satisfies type and multiplicity constraints."""
    if req_types and rel_data.get("type") not in req_types:
        return False
    mult = rel_data.get("multiplicity", {})
    if allowed_src_mult and mult.get("source") not in allowed_src_mult:
        return False
    if allowed_tgt_mult and mult.get("target") not in allowed_tgt_mult:
        return False
    return True


def _match_pattern(diagram: dict, pattern: list, ctx: "_Context") -> list[dict]:
    """
    Find all subgraph matches for a pattern spec.

    Each item in pattern is either a node binding:
        {bind: $varname, node_type: actor}
    or an edge constraint:
        {edge_type: association, from: $actor, to: $uc, source_multiplicity: [...], ...}

    Returns a list of match dicts: {varname: node, ..., "_edge": edge}
    """
    node_specs: dict[str, dict] = {}
    edge_specs: list[dict] = []
    for item in pattern:
        if "bind" in item:
            node_specs[item["bind"].lstrip("$")] = item
        elif "edge_type" in item:
            edge_specs.append(item)

    if not edge_specs:
        return []

    matches: list[dict] = []
    for espec in edge_specs:
        from_var = espec["from"].lstrip("$")
        to_var   = espec["to"].lstrip("$")
        req_type = espec.get("edge_type")
        req_types = set(req_type if isinstance(req_type, list) else [req_type]) if req_type else set()
        allowed_src_mult = set(espec.get("source_multiplicity") or [])
        allowed_tgt_mult = set(espec.get("target_multiplicity") or [])
        matches.extend(
            _match_edges_for_spec(
                diagram, ctx, from_var, to_var,
                req_types, allowed_src_mult, allowed_tgt_mult, node_specs,
            )
        )

    return matches


def _match_edges_for_spec(
    diagram: dict,
    ctx: "_Context",
    from_var: str,
    to_var: str,
    req_types: set,
    allowed_src_mult: set,
    allowed_tgt_mult: set,
    node_specs: dict,
) -> list[dict]:
    """Yield all edge matches for a single edge-spec within a diagram."""
    results: list[dict] = []
    for edge in diagram.get("edges", []):
        rel = edge.get("rel") or {}
        rel_data = rel.get("data", rel)
        if not _edge_mult_matches(edge, req_types, allowed_src_mult, allowed_tgt_mult, rel_data):
            continue
        src_id = ctx.edge_source_id(edge)
        tgt_id = ctx.edge_target_id(edge)
        src_node = ctx.find_node(diagram, src_id) or ctx.find_node_by_ptr(diagram, src_id)
        tgt_node = ctx.find_node(diagram, tgt_id) or ctx.find_node_by_ptr(diagram, tgt_id)
        if not src_node or not tgt_node:
            continue
        from_type = node_specs.get(from_var, {}).get("node_type")
        to_type   = node_specs.get(to_var,   {}).get("node_type")
        if from_type and ctx.node_type(src_node) != from_type:
            continue
        if to_type and ctx.node_type(tgt_node) != to_type:
            continue
        results.append({from_var: src_node, to_var: tgt_node, "_edge": edge})
    return results


def _build_attributes(raw: list) -> list:
    out = []
    for attr in raw:
        if isinstance(attr, str):
            out.append({"name": attr, "type": "str"})
            continue
        if not isinstance(attr, dict) or not attr.get("name"):
            continue
        entry: dict = {"name": attr["name"], "type": attr.get("type", "str")}
        if attr.get("type") == "enum" and attr.get("enum"):
            entry["enum"] = attr["enum"]
        if attr.get("derived"):
            entry["derived"] = True
        out.append(entry)
    return out


# =============================================================================
# Context
# =============================================================================

class _Context:
    def __init__(self, metadata: dict, si: dict | None = None):
        self.metadata = metadata
        self._si: dict = si or {}
        # Semantic profiles built during Stage 1 (semantic_interpretation_pass).
        # Keyed by classifier UUID (cls_ptr). Available to all Stage 2 transforms.
        self.semantic_profiles: dict[str, dict] = {}
        # Workflow profiles: keyed by activity diagram id → {intents: [...]}
        self.workflow_profiles: dict[str, dict] = {}
        self.actor_registry: dict[str, str] = {}
        self.class_section_registry: dict[str, dict] = {}
        self.activity_actor_classes: dict[str, set] = {}
        self.interfaces: dict[str, dict] = {}
        self._section_placement: dict[str, list[str]] = {}
        self._pending_action_sections: dict[str, dict] = {}
        # UseCase extraction registries
        self._actor_permissions: dict[str, dict[str, list[str]]] = {}  # actor -> model -> perms
        self._page_model: dict[str, str] = {}  # page_id -> primary_model_name

    # ── Diagram helpers ──────────────────────────────────────────────────────

    def diagrams_of_type(self, dtype: str) -> list[dict]:
        return [d for d in self.metadata.get("diagrams", []) if d.get("type") == dtype]

    def node_type(self, node: dict) -> str | None:
        cls = node.get("cls") or {}
        data = cls.get("data", cls)
        return data.get("type") if isinstance(data, dict) else None

    def cls_data(self, node: dict) -> dict:
        cls = node.get("cls") or {}
        return cls.get("data", cls) if isinstance(cls.get("data"), dict) else cls

    def edge_source_id(self, edge: dict) -> str | None:
        src = edge.get("source_ptr") or edge.get("source")
        return src.get("id") if isinstance(src, dict) else src

    def edge_target_id(self, edge: dict) -> str | None:
        tgt = edge.get("target_ptr") or edge.get("target")
        return tgt.get("id") if isinstance(tgt, dict) else tgt

    def find_node(self, diagram: dict, node_id: str | None) -> dict | None:
        if not node_id:
            return None
        return next((n for n in diagram.get("nodes", []) if n.get("id") == node_id), None)

    def find_node_by_ptr(self, diagram: dict, ptr: str) -> dict | None:
        for n in diagram.get("nodes", []):
            if str(n.get("cls_ptr") or n.get("id")) == ptr:
                return n
        return None

    def all_class_names(self) -> list[str]:
        """All class names in the system, for model inference."""
        names = []
        for cls in self.metadata.get("classifiers", []):
            cdata = cls.get("data", {}) or {}
            if cdata.get("type") in {"class", "entity", "model"} and cdata.get("name"):
                names.append(cdata["name"])
        return names

    # ── Interface helpers ────────────────────────────────────────────────────

    def _make_interface(self, actor_name: str) -> None:
        if actor_name not in self.interfaces:
            self.interfaces[actor_name] = {
                "label": actor_name,
                "value": {
                    "name": actor_name,
                    "data": {
                        "pages": [],
                        "sections": [],
                        "categories": [],
                        "styling": {},
                        "settings": {},
                        "actor_permissions": {},
                    },
                },
            }

    def add_page(self, actor_name: str, page: dict) -> None:
        self._make_interface(actor_name)
        self.interfaces[actor_name]["value"]["data"]["pages"].append(page)

    def add_section(self, actor_name: str, section: dict) -> None:
        self._make_interface(actor_name)
        existing = {s["id"] for s in self.interfaces[actor_name]["value"]["data"]["sections"]}
        if section["id"] not in existing:
            self.interfaces[actor_name]["value"]["data"]["sections"].append(section)
            self._section_placement.setdefault(section["id"], []).append(actor_name)

    # ── Permission helpers ────────────────────────────────────────────────────

    def record_permissions(self, actor_name: str, model: str, perms: list[str]) -> None:
        actor_map = self._actor_permissions.setdefault(actor_name, {})
        existing = set(actor_map.get(model, []))
        existing.update(perms)
        actor_map[model] = [p for p in ("view", "create", "update", "delete") if p in existing]

    def flush_permissions(self) -> None:
        """Copy collected permissions into each interface's data."""
        for actor_name, model_map in self._actor_permissions.items():
            if actor_name in self.interfaces:
                self.interfaces[actor_name]["value"]["data"]["actor_permissions"] = model_map

    # ── Resolution helpers ────────────────────────────────────────────────────

    def resolve_actor(self, cls: dict) -> str | None:
        ref = cls.get("actorNode")
        if ref and ref in self.actor_registry:
            return self.actor_registry[ref]
        name = cls.get("actorNodeName")
        return app_name_sanitization(name) if name else None

    def infer_actors_for_class(self, class_name: str) -> list[str]:
        low = class_name.lower()
        return [a for a, classes in self.activity_actor_classes.items() if low in classes]

    def actors_for_section(self, section_id: str | None) -> list[str]:
        if not section_id:
            return list(self.interfaces)
        return self._section_placement.get(section_id, list(self.interfaces))

    def build_output(self) -> dict:
        # Build name-keyed profiles for consumers outside the engine.
        # Keyed by class name (string) so nav-plan / section-composition code
        # can look up intents without needing the classifier UUID.
        profiles_by_name: dict[str, dict] = {}
        for _ptr, profile in self.semantic_profiles.items():
            name = profile.get("name", "")
            if name:
                profiles_by_name[name] = {"intents": list(profile.get("intents") or [])}
        return {
            "interfaces": list(self.interfaces.values()),
            "semantic_profiles": profiles_by_name,
        }


# =============================================================================
# Engine
# =============================================================================

class TransformationEngine:
    def __init__(self, rules_path: Path = TKB_PATH):
        with open(rules_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self._rules: list[dict] = data["rules"]
        self._si: dict  = data.get("semantic_inference") or {}
        self._sm: dict  = data.get("semantic_model") or {}
        # Section composition patterns (YAML-driven OOUI pattern table).
        # Exposed via transform() output under "section_composition".
        self._sc: dict  = data.get("section_composition") or {}

    def transform(self, metadata: dict) -> dict:
        ctx = _Context(metadata, si=self._si)
        self._semantic_interpretation_pass(ctx)
        post_assign_rules = []
        for rule in self._rules:
            if rule.get("strategy") == "post_assign_sections":
                post_assign_rules.append(rule)
                continue
            try:
                self._execute(rule, ctx)
            except Exception as exc:
                log.warning("Rule '%s' failed: %s", rule.get("id"), exc)
        _add_classifier_sections(ctx)
        for rule in post_assign_rules:
            self._execute(rule, ctx)
        ctx.flush_permissions()
        output = ctx.build_output()
        # Attach the section_composition patterns so downstream consumers
        # (navigation_planner) can drive section composition from YAML rules
        # instead of hardcoded Python logic.
        output["section_composition"] = self._sc
        return output

    # ── Stage 1: Semantic Interpretation ─────────────────────────────────────

    def _semantic_interpretation_pass(self, ctx: _Context) -> None:
        """
        Pre-pass: build a Semantic Profile for every Class classifier.

        Answers "What kind of entity is this?" before any mapping rules run.
        Results stored in ctx.semantic_profiles (keyed by cls_ptr UUID) and
        consumed in Stage 2 via entity_intents / entity_ops transforms.
        """
        if not self._sm:
            return
        intent_rules = self._sm.get("intent_rules") or []

        # Identify classes that own 1:N composition children (→ Hierarchy intent)
        composition_parents: set[str] = set()
        for diagram in ctx.diagrams_of_type("classes"):
            for edge in diagram.get("edges", []):
                rel_data = (edge.get("rel") or {}).get("data") or {}
                if rel_data.get("type") not in {"composition", "aggregation"}:
                    continue
                mult = rel_data.get("multiplicity") or {}
                if mult.get("target") in {"*", "0..*", "1..*"}:
                    src_ptr = str(edge.get("source_ptr") or "")
                    if src_ptr:
                        composition_parents.add(src_ptr)

        for classifier in ctx.metadata.get("classifiers", []):
            cls_data = classifier.get("data") or {}
            if cls_data.get("type") not in {"class", "entity", "model"}:
                continue
            ptr = str(classifier.get("id") or "")
            if not ptr:
                continue
            has_children = ptr in composition_parents
            intents      = _interpret_entity_intents(cls_data, intent_rules, has_children)
            ctx.semantic_profiles[ptr] = {
                "intents": intents,
                "name":    cls_data.get("name", ""),
            }
            log.debug(
                "Intent profile: %s → %s",
                cls_data.get("name", ptr), intents,
            )

        # Workflow Recognition: classify each activity diagram by topology
        workflow_patterns = self._sm.get("workflow_patterns") or []
        for diagram in ctx.diagrams_of_type("activity"):
            diag_id = str(diagram.get("id") or "")
            if not diag_id:
                continue
            wf_intents = _recognize_workflow(diagram, workflow_patterns, ctx)
            ctx.workflow_profiles[diag_id] = {"intents": wf_intents}
            log.debug("Workflow profile: diagram %s → %s", diag_id, wf_intents)

    # ── Top-level dispatcher ──────────────────────────────────────────────────

    def _execute(self, rule: dict, ctx: _Context) -> None:
        strategy = rule.get("strategy", "default")
        if strategy == "post_assign_sections":
            self._post_assign_sections(ctx)
            return

        from_spec = rule.get("from", {})
        diagram_type = from_spec.get("diagram_type", "")
        for diagram in ctx.diagrams_of_type(diagram_type):
            if from_spec.get("pattern"):
                self._run_on_pattern(rule, diagram, ctx)
            elif from_spec.get("edge_type"):
                self._run_on_edges(rule, diagram, ctx)
            elif from_spec.get("node_type"):
                self._run_on_nodes(rule, diagram, from_spec["node_type"], ctx)

    # ── Node dispatcher ───────────────────────────────────────────────────────

    def _run_on_nodes(self, rule: dict, diagram: dict, node_type: str, ctx: _Context) -> None:
        for node in diagram.get("nodes", []):
            if ctx.node_type(node) != node_type:
                continue
            cls = ctx.cls_data(node)
            source = {"node": node, "cls": cls, "diagram": diagram}
            if rule.get("strategy") == "after_action_section":
                self._strategy_after_action_section(rule, source, ctx)
            else:
                self._apply_rule(rule, source, ctx)

    # ── Edge dispatcher ───────────────────────────────────────────────────────

    def _run_on_edges(self, rule: dict, diagram: dict, ctx: _Context) -> None:
        from_spec = rule.get("from", {})
        allowed_src = set(from_spec.get("source_multiplicity") or [])
        allowed_tgt = set(from_spec.get("target_multiplicity") or [])

        for edge in diagram.get("edges", []):
            rel = edge.get("rel") or {}
            rel_data = rel.get("data", rel)
            if rel_data.get("type") != "association":
                continue
            mult = rel_data.get("multiplicity", {})
            if allowed_src and mult.get("source") not in allowed_src:
                continue
            if allowed_tgt and mult.get("target") not in allowed_tgt:
                continue

            src_ptr = str(edge.get("source_ptr", ""))
            tgt_ptr = str(edge.get("target_ptr", ""))
            tgt_node = ctx.find_node_by_ptr(diagram, tgt_ptr)
            if not tgt_node or src_ptr not in ctx.class_section_registry:
                continue

            related_key = f"{tgt_ptr}:related:{src_ptr}"
            if related_key in ctx.class_section_registry:
                continue

            tgt_cls = ctx.cls_data(tgt_node)
            source = {
                "node": tgt_node, "cls": tgt_cls, "target_cls": tgt_cls,
                "edge": edge,
                "source_section": ctx.class_section_registry[src_ptr],
                "diagram": diagram,
            }
            self._apply_rule(rule, source, ctx, registry_key=related_key)

    # ── Strategies ────────────────────────────────────────────────────────────

    def _run_on_pattern(self, rule: dict, diagram: dict, ctx: _Context) -> None:
        """
        Execute a rule whose `from:` spec declares a graph pattern.

        For each subgraph match the engine:
          1. Builds a source dict with named bindings ($actor, $uc, $src, $tgt, ...)
             accessible via dot-paths in mapping expressions.
          2. Resolves the target interface from `to.interface` as an expression.
          3. Enriches source with `source_section` for class association patterns.
        """
        from_spec = rule.get("from", {})
        to_spec   = rule.get("to", {})
        interface_expr = to_spec.get("interface", "")

        for binding in _match_pattern(diagram, from_spec["pattern"], ctx):
            edge = binding.pop("_edge", None)

            # Build source: each bound variable accessible as $varname.field
            source: dict = {"diagram": diagram}
            for varname, node in binding.items():
                source[varname] = {"node": node, "cls": ctx.cls_data(node)}
            if edge:
                source["edge"] = edge

            # Class association pattern: enrich with source_section + dedup
            registry_key: str | None = None
            if "src" in binding and "tgt" in binding:
                src_ptr = str(binding["src"].get("cls_ptr") or binding["src"].get("id", ""))
                tgt_ptr = str(binding["tgt"].get("cls_ptr") or binding["tgt"].get("id", ""))
                if src_ptr not in ctx.class_section_registry:
                    continue  # source class has no section yet
                registry_key = f"{tgt_ptr}:related:{src_ptr}"
                if registry_key in ctx.class_section_registry:
                    continue  # already processed
                source["source_section"] = ctx.class_section_registry[src_ptr]

            # Resolve interface name from binding expression
            interface_name: str | None = None
            if interface_expr.startswith("$"):
                interface_name = str(_eval(interface_expr, source, ctx) or "")

            self._apply_rule(rule, source, ctx,
                             registry_key=registry_key,
                             interface_name=interface_name)

    def _strategy_after_action_section(
        self, rule: dict, source: dict, ctx: _Context
    ) -> None:
        """
        Action node -> activity page linked to its pending action section.
        """
        node = source["node"]
        cls = source["cls"]
        actor_name = ctx.resolve_actor(cls)
        if not actor_name:
            log.warning("Action node '%s' has no actor — page skipped", cls.get("name", node["id"]))
            return

        page = _apply_mapping(rule.get("mapping", {}), source, ctx)
        pending = ctx._pending_action_sections.get(node["id"])
        page["sections"] = [{"value": pending["id"]}] if pending else []

        ctx.add_page(actor_name, page)
        ctx.activity_actor_classes.setdefault(actor_name, set()).add(
            cls.get("name", "").lower()
        )

    # ── Core rule application ─────────────────────────────────────────────────

    def _apply_rule(
        self, rule: dict, source: dict, ctx: _Context,
        registry_key: str | None = None,
        interface_name: str | None = None,
    ) -> None:
        to_spec = rule.get("to", {})
        output_type = to_spec.get("output")
        interface_mode = to_spec.get("interface", "")

        result = _apply_mapping(rule.get("mapping", {}), source, ctx)
        attrs_expr = rule.get("attributes_from")
        if attrs_expr:
            result["attributes"] = _build_attributes(_eval(attrs_expr, source, ctx) or [])

        for reg in rule.get("registers", []):
            self._write_register(reg, source, ctx, generated=result, registry_key=registry_key)

        if output_type == "interface":
            actor_name = result.get("label")
            if actor_name:
                ctx._make_interface(actor_name)
                ctx.interfaces[actor_name].update(result)

        elif output_type == "section" and interface_mode == "actorNode_ref":
            cls = source.get("cls", {})
            actor_name = ctx.resolve_actor(cls)
            if actor_name:
                ctx.add_section(actor_name, result)
                ctx._pending_action_sections[source["node"]["id"]] = result

        elif output_type == "section":
            key = registry_key or result.get("class") or result.get("id", str(uuid4()))
            ctx.class_section_registry[key] = result

        elif output_type == "page":
            if interface_name:
                # Pattern-matched rule: interface resolved from binding expression.
                # Extract permissions before storing (they're a side effect, not page data).
                perms = result.pop("permissions", None) or []
                primary_model = result.get("primary_model") or ""
                ctx.add_page(interface_name, result)
                if primary_model:
                    ctx._page_model[result["id"]] = primary_model
                    ctx.record_permissions(interface_name, primary_model, perms)
            elif interface_mode == "actorNode_ref":
                cls = source.get("cls", {})
                actor_name = ctx.resolve_actor(cls)
                if actor_name:
                    ctx.add_page(actor_name, result)
                else:
                    log.warning("No actor for page '%s' — skipped", result.get("name"))

    # ── Post-processing ───────────────────────────────────────────────────────

    def _post_assign_sections(self, ctx: _Context) -> None:
        """
        assign_sections_to_interfaces (Rule 7):

        1. Distribute class data sections to interfaces (by activity actor inference).
        2. For UseCase pages with primary_model: link only the matching section.
        3. For UseCase pages without primary_model: link all data sections.
        4. Related sections follow their parent section's interface.
        """
        primary_keys = [k for k in ctx.class_section_registry if ":related:" not in k]
        related_keys = [k for k in ctx.class_section_registry if ":related:" in k]

        for key in primary_keys:
            section = ctx.class_section_registry[key]
            actors = ctx.infer_actors_for_class(section.get("label", ""))
            for actor_name in (actors or list(ctx.interfaces)):
                ctx.add_section(actor_name, section)

        for key in related_keys:
            section = ctx.class_section_registry[key]
            for actor_name in ctx.actors_for_section(section.get("related_to")):
                ctx.add_section(actor_name, section)

        # Link sections to UseCase (normal) pages
        for iface in ctx.interfaces.values():
            data = iface["value"]["data"]
            # Key by label (class name string), not class (classifier UUID)
            section_by_class: dict[str, dict] = {}
            for s in data["sections"]:
                cls_name = s.get("label") or s.get("name") or ""
                if cls_name and s.get("type") == "data" and cls_name not in section_by_class:
                    section_by_class[cls_name] = s

            all_section_ids = {s["id"] for s in data["sections"]}

            for page in data["pages"]:
                page_type = page.get("type", {})
                is_normal = (
                    (isinstance(page_type, dict) and page_type.get("value") == "normal")
                    or page_type == "normal"
                )
                if not is_normal:
                    continue

                already = {r["value"] for r in page.get("sections", []) if "value" in r}
                primary_model = ctx._page_model.get(page["id"]) or page.get("primary_model") or ""

                if primary_model and primary_model in section_by_class:
                    # Precise: only the matching section
                    target_sec = section_by_class[primary_model]
                    if target_sec["id"] not in already and target_sec["id"] in all_section_ids:
                        page.setdefault("sections", []).append({"value": target_sec["id"]})
                else:
                    # Fallback: all data sections (human removes unwanted ones)
                    for s in data["sections"]:
                        if s.get("type") != "data":
                            continue
                        if s["id"] in already or s["id"] not in all_section_ids:
                            continue
                        page.setdefault("sections", []).append({"value": s["id"]})

    # ── Register writer ───────────────────────────────────────────────────────

    def _write_register(
        self,
        reg: dict,
        source: dict,
        ctx: _Context,
        generated: dict | None = None,
        registry_key: str | None = None,
    ) -> None:
        guard = reg.get("if")
        if guard and not _eval(guard, source, ctx):
            return

        registry = reg.get("registry")
        key = _eval(reg.get("key", ""), source, ctx)
        val_expr = reg.get("value", "@null")
        value = generated if val_expr == _SELF_REF else _eval(val_expr, source, ctx)

        if key is None:
            return

        if registry == "actor":
            ctx.actor_registry[str(key)] = value
        elif registry == "class_section":
            ctx.class_section_registry[registry_key or str(key)] = (
                generated if val_expr == _SELF_REF else value
            )


# =============================================================================
# Classifier fallback (flat class list, no diagram)
# =============================================================================

def _add_classifier_sections(ctx: _Context) -> None:
    for classifier in ctx.metadata.get("classifiers", []):
        cls_data = classifier.get("data", {})
        if cls_data.get("type") not in {"class", "entity", "model"} or not cls_data.get("name"):
            continue
        ptr = str(classifier["id"])
        if ptr in ctx.class_section_registry:
            continue
        profile = ctx.semantic_profiles.get(ptr, {})
        ops = _ops_from_profile(profile)
        layout = _layout_from_intent_profile(profile)
        ctx.class_section_registry[ptr] = {
            "id": str(uuid4()),
            "name": section_name_sanitization(cls_data["name"]),
            "label": cls_data["name"],
            "type": "data",
            "class": ptr,
            "attributes": _build_attributes(cls_data.get("attributes", [])),
            "operations": ops,
            "layout": layout,
            "position": "main",
            "col_span": 12,
            "style": {},
            "query": {},
            "behavior": {},
            "workflow": {},
        }


# =============================================================================
# Public entry point
# =============================================================================

def generate_interface_metadata(metadata_json: str) -> str:
    """
    Transform UML metadata JSON into interface metadata JSON.

    Compatible with loading_json_utils.retrieve_pages and
    retrieve_section_components.
    """
    metadata = json.loads(metadata_json)
    return json.dumps(
        TransformationEngine().transform(metadata),
        indent=2,
        ensure_ascii=False,
    )
