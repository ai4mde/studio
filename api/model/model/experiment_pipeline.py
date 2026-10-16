"""
Research experiment pipeline: LLM activity models -> AI4MDE export -> DB import.

Session model
-------------
- Each run creates exactly one ``Project``.
- Baseline mode creates one model inside that project.
- Refinement mode creates three initial candidate models inside that same project.
- Later refinement iterations must continue updating the selected model in the
  same project; this module only handles the initial candidate generation step.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import logging
import uuid
from typing import Any, Dict, List, Literal, Optional

from django.db import transaction
from django.utils import timezone
from metadata.api.schemas import ExportSingleSystem
from metadata.models import (
    ProvisionalCandidate,
    Project,
    System,
    SystemRevision,
    create_system_revision,
    get_current_revision,
    get_generation_process_text,
    get_semantic_sketch_plan,
    get_topology_artifact,
    list_system_revisions,
    persist_semantic_generation_artifacts,
    set_current_revision,
)

from llm.baseline_generator import generate_activity_model
from llm.experimental_compiler import compile_activity_sketch
from llm.human_edit_synchronizer import (
    _canonicalize_graph,
    synchronize_persisted_human_edit,
)
from llm.refinement_planner import generate_refinement_plan
from llm.sketch_repair import repair_activity_sketch
from llm.topology_to_sketch_compiler import compile_topology_and_semantics_to_activity_sketch
from llm.technical_validity import (
    TechnicalValidityError,
    merge_technical_validity_reports,
    normalize_and_validate_activity_graph,
)
from llm.converter import convert_to_ai4mde, unwrap_ai4mde_systems_export, validate_ai4mde_json
from llm.pipeline_profiles import PipelineProfile, resolve_pipeline_config
from llm.refinement_generator import (
    _get_clean_model,
    _raise_for_unresolved_explicit_loop_targets,
    generate_and_convert_candidates,
    model_activity_with_experimental_compiler,
    refine_activity_model,
)

Mode = Literal["baseline", "refinement"]
logger = logging.getLogger(__name__)


class RefinementConflictError(Exception):
    """The saved process or its synchronized revision changed before import."""


class UnsupportedRefinementFieldError(RefinementConflictError):
    """The current Studio fields cannot safely round-trip through ActivityGraph."""


_SYNC_BEFORE_REFINEMENT = (
    "The saved diagram has unsynchronized process changes. "
    "Use Sync with AI before refining again."
)

_UNSUPPORTED_FIELDS_REFINEMENT = (
    "AI refinement cannot safely preserve these saved process fields: {fields}. "
    "Your saved model is unchanged. Review or remove those fields before refining."
)

# These values affect only how the diagram is drawn. All other native data is
# compared against both the synchronized revision and a converter round trip.
_LAYOUT_NODE_FIELDS = {"position"}
_LAYOUT_EDGE_FIELDS = {"style", "position_handlers", "source_offset", "target_offset"}
_LAYOUT_RELATION_FIELDS = {"position_handlers"}
_LAYOUT_CLASSIFIER_FIELDS = {"fork": {"height", "width"}, "join": {"height", "width"}}


def _process_data(data: Any, ignored: set[str]) -> Dict[str, Any]:
    return {key: value for key, value in (data or {}).items() if key not in ignored}


def _same_native_value(actual: Any, expected: Any) -> bool:
    # Native optional text fields may export as null, blank, or absent. All
    # three mean no user-entered content; nonempty values still require proof.
    return actual == expected or (actual in (None, "") and expected in (None, ""))


def _native_process_snapshot(exported: Dict[str, Any] | List[Dict[str, Any]]) -> Dict[str, Any]:
    """Capture all editable native content, excluding only explicit layout fields."""
    system = unwrap_ai4mde_systems_export(exported)
    return {
        "name": system.get("name"),
        "description": system.get("description"),
        "interfaces": system.get("interfaces") or [],
        "imported_classifiers": system.get("imported_classifiers") or [],
        "classifiers": {
            str(item["id"]): _process_data(
                item.get("data"),
                _LAYOUT_CLASSIFIER_FIELDS.get((item.get("data") or {}).get("type"), set()),
            )
            for item in system.get("classifiers") or []
        },
        "relations": {
            str(item["id"]): {
                "source": item.get("source"),
                "target": item.get("target"),
                "data": _process_data(item.get("data"), _LAYOUT_RELATION_FIELDS),
            }
            for item in system.get("relations") or []
        },
        "diagrams": {
            str(diagram["id"]): {
                "name": diagram.get("name"),
                "description": diagram.get("description"),
                "type": diagram.get("type"),
                "nodes": {
                    str(node["id"]): {
                        "cls": node.get("cls"),
                        "data": _process_data(node.get("data"), _LAYOUT_NODE_FIELDS),
                    }
                    for node in diagram.get("nodes") or []
                },
                "edges": {
                    str(edge["id"]): {
                        "rel": edge.get("rel"),
                        "data": _process_data(edge.get("data"), _LAYOUT_EDGE_FIELDS),
                    }
                    for edge in diagram.get("edges") or []
                },
            }
            for diagram in system.get("diagrams") or []
        },
    }


def _unrepresentable_refinement_fields(exported: Dict[str, Any] | List[Dict[str, Any]]) -> List[str]:
    """Find every native field that the current ActivityGraph converter would lose.

    The converter is the authority for defaults and supported fields; this also
    catches future editable fields without maintaining a second schema here.
    """
    system = unwrap_ai4mde_systems_export(exported)
    issues: set[str] = set()
    diagrams = system.get("diagrams") or []
    if not diagrams and not (system.get("classifiers") or system.get("relations") or system.get("interfaces") or system.get("imported_classifiers")):
        # Legacy refinement also accepts an empty system as an initial canvas.
        # It has no existing model fields for a conversion to discard.
        return []
    if len(diagrams) != 1 or diagrams[0].get("type") != "activity":
        return ["activity diagram structure"]
    if system.get("interfaces") or system.get("imported_classifiers"):
        issues.add("system interfaces or imported classifiers")
    diagram = diagrams[0]
    try:
        clean_graph = _get_clean_model(exported)
        roundtrip = unwrap_ai4mde_systems_export(convert_to_ai4mde(
            clean_model=clean_graph,
            system_id=str(system["id"]),
            diagram_id=str(diagram["id"]),
            name=str(system.get("name") or ""),
            description=str(system.get("description") or ""),
            project_id=str(system["project"]),
        ))
    except (KeyError, TypeError, ValueError):
        return sorted(issues | {"ActivityGraph conversion"})

    expected_diagram = roundtrip["diagrams"][0]
    for field in ("name", "description", "type"):
        if diagram.get(field) != expected_diagram.get(field):
            issues.add(f"diagram.{field}")
    nodes = diagram.get("nodes") or []
    edges = diagram.get("edges") or []
    classifiers = {str(item["id"]): item for item in system.get("classifiers") or []}
    relations = {str(item["id"]): item for item in system.get("relations") or []}
    if (
        len(nodes) != len(expected_diagram["nodes"])
        or len(edges) != len(expected_diagram["edges"])
        or len(classifiers) != len(nodes)
        or len(relations) != len(edges)
        or len({str(node.get("cls")) for node in nodes}) != len(nodes)
        or len({str(edge.get("rel")) for edge in edges}) != len(edges)
    ):
        return sorted(issues | {"diagram classifier or flow references"})

    expected_classifiers = {item["id"]: item for item in roundtrip["classifiers"]}
    for node, expected_node in zip(nodes, expected_diagram["nodes"]):
        current = classifiers.get(str(node.get("cls")))
        expected = expected_classifiers[expected_node["cls"]]
        if current is None:
            issues.add("diagram classifier references")
            continue
        actual_data = _process_data(
            current.get("data"),
            _LAYOUT_CLASSIFIER_FIELDS.get((current.get("data") or {}).get("type"), set()),
        )
        expected_data = _process_data(
            expected["data"],
            _LAYOUT_CLASSIFIER_FIELDS.get(expected["data"].get("type"), set()),
        )
        issues.update(
            f"{actual_data.get('type', 'classifier')}.{key}"
            for key in actual_data.keys() | expected_data.keys()
            if not _same_native_value(actual_data.get(key), expected_data.get(key))
        )
        actual_node = _process_data(node.get("data"), _LAYOUT_NODE_FIELDS)
        expected_node_data = _process_data(expected_node.get("data"), _LAYOUT_NODE_FIELDS)
        issues.update(
            f"diagram node.{key}"
            for key in actual_node.keys() | expected_node_data.keys()
            if not _same_native_value(actual_node.get(key), expected_node_data.get(key))
        )

    expected_relations = {item["id"]: item for item in roundtrip["relations"]}
    for edge, expected_edge in zip(edges, expected_diagram["edges"]):
        current = relations.get(str(edge.get("rel")))
        expected = expected_relations[expected_edge["rel"]]
        if current is None:
            issues.add("diagram flow references")
            continue
        actual_data = _process_data(current.get("data"), _LAYOUT_RELATION_FIELDS)
        expected_data = _process_data(expected["data"], _LAYOUT_RELATION_FIELDS)
        # ObjectFlow.cls refers to a newly allocated classifier after import.
        for data, relation in ((actual_data, current), (expected_data, expected)):
            cls = str(data.get("cls") or "")
            if cls:
                if cls == str(relation.get("source")):
                    data["cls"] = "source"
                elif cls == str(relation.get("target")):
                    data["cls"] = "target"
        issues.update(
            f"{actual_data.get('type', 'flow')}.{key}"
            for key in actual_data.keys() | expected_data.keys()
            if not _same_native_value(actual_data.get(key), expected_data.get(key))
        )
        actual_edge = _process_data(edge.get("data"), _LAYOUT_EDGE_FIELDS)
        expected_edge_data = _process_data(expected_edge.get("data"), _LAYOUT_EDGE_FIELDS)
        issues.update(
            f"diagram edge.{key}"
            for key in actual_edge.keys() | expected_edge_data.keys()
            if not _same_native_value(actual_edge.get(key), expected_edge_data.get(key))
        )
    return sorted(issues)


def _unrepresentable_activity_graph_fields(graph: Dict[str, Any]) -> List[str]:
    """Partition is process meaning, but the Studio converter has no lane mapping.

    Origin ids are planner provenance regenerated from topology/semantic artifacts,
    rather than editable content of the saved Studio model.
    """
    return [
        "ActivityGraph node.partition"
        for node in graph.get("nodes") or []
        if isinstance(node, dict) and str(node.get("partition") or "").strip()
    ][:1]


def _saved_process_graph(exported: Dict[str, Any]) -> Dict[str, Any]:
    """Compare process content using the same layout-free graph as human Sync."""
    try:
        return _canonicalize_graph(_get_clean_model(exported))
    except Exception as exc:  # noqa: BLE001
        raise RefinementConflictError(_SYNC_BEFORE_REFINEMENT) from exc


def _guarded_flow_signatures(exported: Dict[str, Any] | List[Dict[str, Any]]) -> Counter:
    """Identify guarded flows by their process endpoints, independent of new import IDs."""
    system = unwrap_ai4mde_systems_export(exported)
    classifiers = {
        str(item["id"]): item.get("data") or {}
        for item in system.get("classifiers") or []
    }

    def endpoint(classifier_id: Any) -> tuple[str, str]:
        data = classifiers.get(str(classifier_id), {})
        return (str(data.get("type") or ""), str(data.get("name") or data.get("label") or ""))

    return Counter(
        (
            endpoint(relation.get("source")),
            endpoint(relation.get("target")),
            str((relation.get("data") or {}).get("guard")),
        )
        for relation in system.get("relations") or []
        if (relation.get("data") or {}).get("guard")
    )


def _diff_topology_artifact(
    before: Optional[Dict[str, Any]],
    after: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    before_structures = {
        str(structure["id"]): structure
        for structure in (before or {}).get("structures", [])
        if isinstance(structure, dict) and structure.get("id") is not None
    }
    after_structures = {
        str(structure["id"]): structure
        for structure in (after or {}).get("structures", [])
        if isinstance(structure, dict) and structure.get("id") is not None
    }
    all_ids = sorted(set(before_structures) | set(after_structures))
    return {
        "before": before,
        "after": after,
        "changed": before != after,
        "structures": {
            "added": [after_structures[structure_id] for structure_id in all_ids if structure_id not in before_structures],
            "removed": [before_structures[structure_id] for structure_id in all_ids if structure_id not in after_structures],
            "modified": [
                {
                    "id": structure_id,
                    "before": before_structures[structure_id],
                    "after": after_structures[structure_id],
                }
                for structure_id in all_ids
                if structure_id in before_structures
                and structure_id in after_structures
                and before_structures[structure_id] != after_structures[structure_id]
            ],
        },
    }


def _diff_semantic_sketch_plan(
    before: Optional[Dict[str, Any]],
    after: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    before_root_actions = {
        str(entry["slot_id"]): entry
        for entry in (before or {}).get("root_actions", [])
        if isinstance(entry, dict) and entry.get("slot_id") is not None
    }
    after_root_actions = {
        str(entry["slot_id"]): entry
        for entry in (after or {}).get("root_actions", [])
        if isinstance(entry, dict) and entry.get("slot_id") is not None
    }
    before_branch_plans = {
        (str(entry["structure_id"]), str(entry["branch"])): entry
        for entry in (before or {}).get("branch_plans", [])
        if isinstance(entry, dict)
        and entry.get("structure_id") is not None
        and entry.get("branch") is not None
    }
    after_branch_plans = {
        (str(entry["structure_id"]), str(entry["branch"])): entry
        for entry in (after or {}).get("branch_plans", [])
        if isinstance(entry, dict)
        and entry.get("structure_id") is not None
        and entry.get("branch") is not None
    }
    root_slot_ids = sorted(set(before_root_actions) | set(after_root_actions))
    branch_keys = sorted(set(before_branch_plans) | set(after_branch_plans))
    return {
        "before": before,
        "after": after,
        "changed": before != after,
        "root_actions": {
            "added": [after_root_actions[slot_id] for slot_id in root_slot_ids if slot_id not in before_root_actions],
            "removed": [before_root_actions[slot_id] for slot_id in root_slot_ids if slot_id not in after_root_actions],
            "modified": [
                {
                    "slot_id": slot_id,
                    "before": before_root_actions[slot_id],
                    "after": after_root_actions[slot_id],
                }
                for slot_id in root_slot_ids
                if slot_id in before_root_actions
                and slot_id in after_root_actions
                and before_root_actions[slot_id] != after_root_actions[slot_id]
            ],
        },
        "branch_plans": {
            "added": [after_branch_plans[key] for key in branch_keys if key not in before_branch_plans],
            "removed": [before_branch_plans[key] for key in branch_keys if key not in after_branch_plans],
            "modified": [
                {
                    "structure_id": key[0],
                    "branch": key[1],
                    "before": before_branch_plans[key],
                    "after": after_branch_plans[key],
                }
                for key in branch_keys
                if key in before_branch_plans
                and key in after_branch_plans
                and before_branch_plans[key] != after_branch_plans[key]
            ],
        },
    }


def _build_artifact_diff(
    *,
    before_topology_artifact: Optional[Dict[str, Any]],
    after_topology_artifact: Optional[Dict[str, Any]],
    before_semantic_sketch_plan: Optional[Dict[str, Any]],
    after_semantic_sketch_plan: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "topology_artifact_diff": _diff_topology_artifact(
            before_topology_artifact,
            after_topology_artifact,
        ),
        "semantic_sketch_plan_diff": _diff_semantic_sketch_plan(
            before_semantic_sketch_plan,
            after_semantic_sketch_plan,
        ),
    }


def _persist_semantic_artifacts_if_present(
    *,
    system_id: str,
    process_text: str,
    pipeline_profile: PipelineProfile,
    debug_bundle: Optional[Dict[str, Any]] = None,
) -> None:
    if pipeline_profile != "semantic_deterministic" or not debug_bundle:
        return

    stage_artifacts = debug_bundle.get("stage_artifacts") or {}
    topology_artifact = stage_artifacts.get("topology_artifact")
    semantic_plan = stage_artifacts.get("semantic_plan")
    if topology_artifact is None or semantic_plan is None:
        return

    persist_semantic_generation_artifacts(
        system_id=system_id,
        process_text=process_text,
        pipeline_profile=pipeline_profile,
        topology_artifact=topology_artifact,
        semantic_sketch_plan=semantic_plan,
    )


@transaction.atomic
def _create_revision_snapshot(
    *,
    system_id: str,
    process_text: str,
    pipeline_profile: PipelineProfile,
    activity_graph: Dict[str, Any],
    ai4mde_export: List[Dict[str, Any]] | Dict[str, Any],
    topology_artifact: Optional[Dict[str, Any]] = None,
    semantic_sketch_plan: Optional[Dict[str, Any]] = None,
    refinement_trace: Optional[Dict[str, Any]] = None,
    refinement_instruction: Optional[str] = None,
    candidate_index: Optional[int] = None,
    candidate_count: Optional[int] = None,
    revision_origin: str = SystemRevision.REVISION_ORIGIN_BASELINE,
    parent_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    revision = create_system_revision(
        system_id=system_id,
        process_text=process_text,
        pipeline_profile=pipeline_profile,
        topology_artifact=topology_artifact,
        semantic_sketch_plan=semantic_sketch_plan,
        activity_graph=activity_graph,
        ai4mde_export=ai4mde_export,
        refinement_trace=refinement_trace,
        refinement_instruction=refinement_instruction,
        candidate_index=candidate_index,
        candidate_count=candidate_count,
        revision_origin=revision_origin,
        parent_revision_id=parent_revision_id,
        set_as_current=True,
    )
    if topology_artifact is not None and semantic_sketch_plan is not None:
        persist_semantic_generation_artifacts(
            system_id=system_id,
            process_text=process_text,
            pipeline_profile=pipeline_profile,
            topology_artifact=topology_artifact,
            semantic_sketch_plan=semantic_sketch_plan,
        )
    return {
        "revision_id": str(revision.id),
        "revision_index": revision.revision_index,
        "parent_revision_id": str(revision.parent_revision_id) if revision.parent_revision_id else None,
        "revision_origin": revision.revision_origin,
        "candidate_index": revision.candidate_index,
        "candidate_count": revision.candidate_count,
    }


def _run_semantic_refinement_from_artifacts(
    process_text: str,
    *,
    current_topology_artifact: Dict[str, Any],
    current_semantic_sketch_plan: Dict[str, Any],
    refinement_instruction: str,
) -> Dict[str, Any]:
    planner_result = generate_refinement_plan(
        process_text,
        current_topology_artifact=current_topology_artifact,
        current_semantic_sketch_plan=current_semantic_sketch_plan,
        instruction=refinement_instruction,
    )
    updated_artifacts = planner_result["artifact"]
    deterministic_sketch = compile_topology_and_semantics_to_activity_sketch(
        updated_artifacts["updated_topology_artifact"],
        updated_artifacts["updated_semantic_sketch_plan"],
    )
    repaired_sketch, repair_report = repair_activity_sketch(deterministic_sketch)
    _raise_for_unresolved_explicit_loop_targets(repair_report)
    clean_graph = compile_activity_sketch(repaired_sketch)
    return {
        "planner_result": planner_result,
        "artifact_diff": _build_artifact_diff(
            before_topology_artifact=current_topology_artifact,
            after_topology_artifact=updated_artifacts["updated_topology_artifact"],
            before_semantic_sketch_plan=current_semantic_sketch_plan,
            after_semantic_sketch_plan=updated_artifacts["updated_semantic_sketch_plan"],
        ),
        "updated_artifacts": updated_artifacts,
        "clean_graph": clean_graph,
    }


def generate_session_id() -> str:
    """Unique label for one user request (session)."""
    return f"Session_{uuid.uuid4().hex[:12]}"


def _diagram_id_from_exported_system(exported_current_model: Dict[str, Any]) -> str:
    diagrams = exported_current_model.get("diagrams") or []
    if not diagrams:
        return "diagram1"
    return str(diagrams[0].get("id") or "diagram1")


def create_experiment_project(*, mode: Mode, session_id: str) -> Project:
    """Create one fresh project for the current experiment session."""
    return Project.objects.create(
        name=f"Generated Modelling Session {session_id}",
        description=(
            "Auto-created for baseline or refinement experiment "
            f"({mode}, {session_id})"
        ),
    )


def resolve_experiment_project(
    *,
    mode: Mode,
    session_id: str,
    project_id: Optional[str] = None,
) -> Project:
    """
    Return the project to use for this generation run.

    - If ``project_id`` is provided, reuse that existing project.
    - Otherwise create a fresh project for this session.
    """
    if project_id:
        try:
            return Project.objects.get(pk=project_id)
        except Project.DoesNotExist as exc:
            raise ValueError(f"Project {project_id!r} does not exist.") from exc
    return create_experiment_project(mode=mode, session_id=session_id)


def _delete_failed_empty_project(project_id: str) -> bool:
    from diagram.models import Diagram

    with transaction.atomic():
        project = Project.objects.select_for_update().filter(pk=project_id).first()
        if project is None:
            return False

        candidates = ProvisionalCandidate.objects.filter(project=project)
        has_protected_state = (
            System.objects.filter(project=project).exists()
            or Diagram.objects.filter(system__project=project).exists()
            or SystemRevision.objects.filter(system__project=project).exists()
            or candidates.filter(selected_system__isnull=False).exists()
            or candidates.exists()
        )
        if has_protected_state:
            logger.warning(
                "Skipped cleanup for failed generation project %s because it contains persistent model state.",
                project_id,
            )
            return False

        project.delete()
        return True


def import_to_ai4mde(project: Project, systems_export: List[Dict[str, Any]]) -> None:
    """
    Validate and import a wrapped single-system AI4MDE export into ``project``.
    """
    validate_ai4mde_json(systems_export)
    project.import_systems_from_json(systems_export)


def _convert_candidate_graph(
    clean_graph: Dict[str, Any],
    *,
    system_id: str,
    diagram_id: str,
    name: str,
    description: str,
    project_id: str,
    prior_report: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    clean_graph, final_report = normalize_and_validate_activity_graph(clean_graph)
    report = merge_technical_validity_reports(prior_report, final_report)
    try:
        ai4mde = convert_to_ai4mde(
            clean_model=clean_graph,
            system_id=system_id,
            diagram_id=diagram_id,
            name=name,
            description=description,
            project_id=project_id,
        )
    except Exception as exc:
        report["technical_accepted"] = False
        report["conversion_result"] = "failed"
        report["failure_reason"] = str(exc)
        raise TechnicalValidityError(
            f"ActivityGraph failed AI4MDE conversion: {exc}", report=report
        ) from exc
    report["conversion_result"] = "accepted"
    return {"clean": clean_graph, "ai4mde": ai4mde, "technical_validity": report}


def run_pipeline(
    process_text: str,
    mode: Mode,
    *,
    project_id: Optional[str] = None,
    pipeline_profile: PipelineProfile = "semantic_deterministic",
    current_topology_artifact: Optional[Dict[str, Any]] = None,
    current_semantic_sketch_plan: Optional[Dict[str, Any]] = None,
    refinement_instruction: Optional[str] = None,
    use_experimental_compiler: bool = False,
    enable_sketch_review_agent: Optional[bool] = None,
    enable_prompted_sketch_repair_agent: Optional[bool] = None,
    enable_graph_repair_agent: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Generate experiment models, convert them to native AI4MDE export JSON, and import them.

    Baseline:
    - create one project
    - generate one clean model
    - convert/import one system

    Refinement:
    - either generate three initial clean candidates
    - or refine one provided topology/semantic artifact pair
    - convert/import the resulting system(s) into the target project
    """
    if not process_text or not str(process_text).strip():
        raise ValueError("process_text must be non-empty")

    session_id = generate_session_id()
    project = resolve_experiment_project(mode=mode, session_id=session_id, project_id=project_id)
    resolved_project_id = str(project.id)
    pipeline_config = resolve_pipeline_config(
        pipeline_profile=pipeline_profile,
        enable_sketch_review_agent=enable_sketch_review_agent,
        enable_prompted_sketch_repair_agent=enable_prompted_sketch_repair_agent,
        enable_graph_repair_agent=enable_graph_repair_agent,
    )
    results: List[Dict[str, Any]] = []
    direct_refinement_requested = any(
        value is not None
        for value in (
            current_topology_artifact,
            current_semantic_sketch_plan,
            refinement_instruction,
        )
    )
    provisional_candidate_generation = mode == "refinement" and not direct_refinement_requested

    if mode == "baseline":
        if use_experimental_compiler:
            clean_model = model_activity_with_experimental_compiler(
                process_text,
                use_sketch_review_agent=pipeline_config["enable_sketch_review_agent"],
                use_prompted_sketch_repair_agent=pipeline_config["enable_prompted_sketch_repair_agent"],
            )
            debug_bundle = None
        else:
            debug_bundle = generate_activity_model(
                process_text,
                debug=True,
                pipeline_profile=pipeline_config["pipeline_profile"],
                enable_sketch_review_agent=pipeline_config["enable_sketch_review_agent"],
                enable_prompted_sketch_repair_agent=pipeline_config["enable_prompted_sketch_repair_agent"],
                enable_graph_repair_agent=pipeline_config["enable_graph_repair_agent"],
            )
            clean_model = debug_bundle["parsed"]
        candidate_export = _convert_candidate_graph(
            clean_model,
            system_id=str(uuid.uuid4()),
            diagram_id=str(uuid.uuid4()),
            name=f"{session_id}_Model_1",
            description=f"Experiment session {session_id}",
            project_id=resolved_project_id,
            prior_report=(
                ((debug_bundle.get("stage_artifacts") or {}).get("validation") or {}).get(
                    "technical_validity"
                )
                if debug_bundle is not None
                else None
            ),
        )
        candidate_export["debug_bundle"] = debug_bundle
        candidate_exports = [candidate_export]
    elif mode == "refinement":
        if use_experimental_compiler:
            raise ValueError("experimental compiler is currently supported only for baseline mode")
        if direct_refinement_requested:
            if (
                current_topology_artifact is None
                or current_semantic_sketch_plan is None
                or not refinement_instruction
            ):
                raise ValueError(
                    "direct refinement requires current_topology_artifact, "
                    "current_semantic_sketch_plan, and instruction"
                )
            if pipeline_config["pipeline_profile"] != "semantic_deterministic":
                raise ValueError(
                    "direct refinement via /generate-model currently requires "
                    "pipeline_profile='semantic_deterministic'"
                )
            refinement_result = _run_semantic_refinement_from_artifacts(
                process_text,
                current_topology_artifact=current_topology_artifact,
                current_semantic_sketch_plan=current_semantic_sketch_plan,
                refinement_instruction=refinement_instruction,
            )
            updated_artifacts = refinement_result["updated_artifacts"]
            candidate_export = _convert_candidate_graph(
                refinement_result["clean_graph"],
                system_id=str(uuid.uuid4()),
                diagram_id=str(uuid.uuid4()),
                name=f"{session_id}_Refined_Model_1",
                description=f"Refinement session {session_id}",
                project_id=resolved_project_id,
            )
            candidate_export.update(
                {
                    "updated_topology_artifact": updated_artifacts["updated_topology_artifact"],
                    "updated_semantic_sketch_plan": updated_artifacts["updated_semantic_sketch_plan"],
                    "artifact_diff": refinement_result["artifact_diff"],
                    "refinement_trace": updated_artifacts.get("refinement_trace"),
                }
            )
            candidate_exports = [candidate_export]
        else:
            try:
                candidate_exports = generate_and_convert_candidates(
                    process_text,
                    n=3,
                    project_id=resolved_project_id,
                    pipeline_profile=pipeline_config["pipeline_profile"],
                    enable_sketch_review_agent=pipeline_config["enable_sketch_review_agent"],
                    enable_prompted_sketch_repair_agent=pipeline_config["enable_prompted_sketch_repair_agent"],
                    enable_graph_repair_agent=pipeline_config["enable_graph_repair_agent"],
                    name_prefix=f"{session_id}_Model",
                    description_template=f"Experiment session {session_id}",
                )
            except Exception:
                if not project_id:
                    try:
                        _delete_failed_empty_project(resolved_project_id)
                    except Exception:
                        logger.exception(
                            "Failed to clean up empty project %s after candidate generation failed.",
                            resolved_project_id,
                        )
                raise
    else:
        raise ValueError("mode must be 'baseline' or 'refinement'")

    provisional_candidates: List[ProvisionalCandidate] = []
    if provisional_candidate_generation:
        for candidate_index, candidate in enumerate(candidate_exports, start=1):
            candidate_stage_artifacts = (
                (candidate.get("debug_bundle") or {}).get("stage_artifacts") or {}
            )
            provisional_candidates.append(
                ProvisionalCandidate(
                    project=project,
                    session_id=session_id,
                    candidate_index=candidate_index,
                    candidate_count=len(candidate_exports),
                    process_text=process_text,
                    pipeline_profile=pipeline_config["pipeline_profile"],
                    activity_graph=candidate["clean"],
                    ai4mde_export=candidate["ai4mde"],
                    topology_artifact=candidate_stage_artifacts.get("topology_artifact"),
                    semantic_sketch_plan=candidate_stage_artifacts.get("semantic_plan"),
                )
            )
        # Persist the complete selectable set atomically so a failed write cannot
        # leave an incomplete multi-candidate request behind.
        with transaction.atomic():
            ProvisionalCandidate.objects.bulk_create(provisional_candidates)

    for candidate in candidate_exports:
        systems_export = candidate["ai4mde"]
        system_json = unwrap_ai4mde_systems_export(systems_export)

        entry: Dict[str, Any] = {
            "name": system_json["name"],
            "system_id": system_json["id"],
            "diagram_id": (
                str((system_json.get("diagrams") or [{}])[0].get("id"))
                if system_json.get("diagrams")
                else None
            ),
            "project_id": resolved_project_id,
            "import_error": None,
            "activity_graph": candidate["clean"],
            "ai4mde": systems_export,
            "technical_validity": candidate.get("technical_validity"),
        }
        candidate_debug_bundle = candidate.get("debug_bundle")
        if candidate_debug_bundle is not None:
            entry["executed_stages"] = candidate_debug_bundle.get("executed_stages") or []
            stage_artifacts = candidate_debug_bundle.get("stage_artifacts") or {}
            if stage_artifacts.get("control_evidence") is not None:
                entry["control_evidence"] = stage_artifacts["control_evidence"]
            if stage_artifacts.get("topology_artifact") is not None:
                entry["topology_artifact"] = stage_artifacts["topology_artifact"]
            if stage_artifacts.get("semantic_plan") is not None:
                entry["semantic_sketch_plan"] = stage_artifacts["semantic_plan"]
        if candidate.get("updated_topology_artifact") is not None:
            entry["topology_artifact"] = candidate["updated_topology_artifact"]
        if candidate.get("updated_semantic_sketch_plan") is not None:
            entry["semantic_sketch_plan"] = candidate["updated_semantic_sketch_plan"]
        if candidate.get("artifact_diff") is not None:
            entry["artifact_diff"] = candidate["artifact_diff"]
        if candidate.get("refinement_trace") is not None:
            entry["refinement_trace"] = candidate["refinement_trace"]
        try:
            topology_artifact = entry.get("topology_artifact")
            semantic_sketch_plan = entry.get("semantic_sketch_plan")
            if provisional_candidate_generation:
                candidate_index = len(results) + 1
                provisional_candidate = provisional_candidates[candidate_index - 1]
                entry.update(
                    {
                        "candidate_id": str(provisional_candidate.id),
                        "candidate_index": candidate_index,
                        "candidate_count": len(candidate_exports),
                        "provisional": True,
                    }
                )
            else:
                with transaction.atomic():
                    import_to_ai4mde(project, systems_export)
                    if candidate.get("technical_validity") is not None:
                        candidate["technical_validity"]["import_result"] = "accepted"
                    revision_meta = _create_revision_snapshot(
                        system_id=system_json["id"],
                        process_text=process_text,
                        pipeline_profile=pipeline_config["pipeline_profile"],
                        topology_artifact=topology_artifact,
                        semantic_sketch_plan=semantic_sketch_plan,
                        activity_graph=candidate["clean"],
                        ai4mde_export=systems_export,
                        refinement_trace=entry.get("refinement_trace"),
                        refinement_instruction=refinement_instruction if direct_refinement_requested else None,
                        revision_origin=(
                            SystemRevision.REVISION_ORIGIN_AI_REFINEMENT
                            if direct_refinement_requested
                            else SystemRevision.REVISION_ORIGIN_BASELINE
                        ),
                        parent_revision_id=None,
                    )
                entry.update(revision_meta)
                entry["current_revision_id"] = revision_meta["revision_id"]
                entry["provisional"] = False
        except TechnicalValidityError:
            raise
        except Exception as exc:
            report = candidate.get("technical_validity") or {}
            report["technical_accepted"] = False
            report["import_result"] = "failed"
            report["failure_reason"] = str(exc)
            raise TechnicalValidityError(
                f"ActivityGraph failed AI4MDE import: {exc}", report=report
            ) from exc
        results.append(entry)

        # Keep the exported ids visible to the caller for debugging/UI linkage.
        entry["export_system_id"] = system_json["id"]
        entry["export_name"] = system_json["name"]
        if entry.get("diagram_id") and not entry.get("provisional"):
            entry["ui_path"] = f"/diagram/{entry['diagram_id']}"

    return {
        "session_id": session_id,
        "project_id": resolved_project_id,
        "mode": mode,
        "pipeline_profile": pipeline_config["pipeline_profile"],
        "use_experimental_compiler": use_experimental_compiler,
        "enable_sketch_review_agent": pipeline_config["enable_sketch_review_agent"],
        "enable_prompted_sketch_repair_agent": pipeline_config["enable_prompted_sketch_repair_agent"],
        "enable_graph_repair_agent": pipeline_config["enable_graph_repair_agent"],
        "candidates": results if provisional_candidate_generation else [],
        "systems": results,
    }


@transaction.atomic
def select_provisional_candidate(
    *,
    candidate_id: str,
    node_positions: Optional[Dict[str, Dict[str, int]]] = None,
) -> Dict[str, Any]:
    if not candidate_id or not str(candidate_id).strip():
        raise ValueError("candidate_id must be non-empty")

    try:
        candidate_project_id = ProvisionalCandidate.objects.values_list(
            "project_id", flat=True
        ).get(pk=candidate_id)
    except ProvisionalCandidate.DoesNotExist as exc:
        raise ValueError(f"Provisional candidate {candidate_id!r} does not exist.") from exc

    # All selections within a project serialize on the same stable row.
    Project.objects.select_for_update().get(pk=candidate_project_id)
    candidate = ProvisionalCandidate.objects.select_for_update().select_related("project").get(
        pk=candidate_id
    )
    session_candidates = ProvisionalCandidate.objects.filter(
        project=candidate.project,
        session_id=candidate.session_id,
    )
    selected_candidate = session_candidates.filter(selected_system__isnull=False).first()
    if selected_candidate is not None:
        if selected_candidate.id != candidate.id:
            raise ValueError("a different candidate has already been selected for this session")
        revision = SystemRevision.objects.filter(
            system_id=selected_candidate.selected_system_id,
            revision_index=0,
            revision_origin=SystemRevision.REVISION_ORIGIN_BASELINE,
        ).first()
        if revision is None:
            raise ValueError("selected candidate is missing its official Revision 0")
        return _selected_candidate_response(selected_candidate, revision)

    selected_export = _apply_candidate_node_positions(
        candidate.ai4mde_export,
        node_positions,
    )
    system_json = unwrap_ai4mde_systems_export(selected_export)
    import_to_ai4mde(candidate.project, selected_export)
    revision_meta = _create_revision_snapshot(
        system_id=system_json["id"],
        process_text=candidate.process_text,
        pipeline_profile=candidate.pipeline_profile,
        topology_artifact=candidate.topology_artifact,
        semantic_sketch_plan=candidate.semantic_sketch_plan,
        activity_graph=candidate.activity_graph,
        ai4mde_export=selected_export,
        candidate_index=candidate.candidate_index,
        candidate_count=candidate.candidate_count,
        revision_origin=SystemRevision.REVISION_ORIGIN_BASELINE,
        parent_revision_id=None,
    )
    candidate.ai4mde_export = selected_export
    candidate.selected_system_id = system_json["id"]
    candidate.selected_at = timezone.now()
    candidate.save(update_fields=["ai4mde_export", "selected_system", "selected_at"])
    revision = SystemRevision.objects.get(pk=revision_meta["revision_id"])
    return _selected_candidate_response(candidate, revision)


def _apply_candidate_node_positions(
    ai4mde_export: List[Dict[str, Any]] | Dict[str, Any],
    node_positions: Optional[Dict[str, Dict[str, int]]],
) -> List[Dict[str, Any]] | Dict[str, Any]:
    if not node_positions:
        return ai4mde_export

    arranged_export = deepcopy(ai4mde_export)
    system_json = unwrap_ai4mde_systems_export(arranged_export)
    exported_nodes = {
        str(node["id"]): node
        for diagram in system_json.get("diagrams") or []
        for node in diagram.get("nodes") or []
    }
    unknown_node_ids = sorted(set(node_positions) - set(exported_nodes))
    if unknown_node_ids:
        raise ValueError(
            "candidate layout references unknown node ids: "
            + ", ".join(unknown_node_ids)
        )

    for node_id, position in node_positions.items():
        exported_nodes[node_id].setdefault("data", {})["position"] = {
            "x": int(position["x"]),
            "y": int(position["y"]),
        }
    return arranged_export


def _selected_candidate_response(
    candidate: ProvisionalCandidate,
    revision: SystemRevision,
) -> Dict[str, Any]:
    system_json = unwrap_ai4mde_systems_export(candidate.ai4mde_export)
    diagrams = system_json.get("diagrams") or []
    diagram_id = str(diagrams[0].get("id")) if diagrams else None
    response = {
        "candidate_id": str(candidate.id),
        "candidate_index": candidate.candidate_index,
        "candidate_count": candidate.candidate_count,
        "session_id": candidate.session_id,
        "project_id": str(candidate.project_id),
        "system_id": str(candidate.selected_system_id),
        "diagram_id": diagram_id,
        "name": system_json["name"],
        "process_text": candidate.process_text,
        "pipeline_profile": candidate.pipeline_profile,
        "activity_graph": candidate.activity_graph,
        "topology_artifact": candidate.topology_artifact,
        "semantic_sketch_plan": candidate.semantic_sketch_plan,
        "ai4mde": candidate.ai4mde_export,
        "provisional": False,
        "current_revision_id": str(revision.id),
        "revision_id": str(revision.id),
        "revision_index": revision.revision_index,
        "revision_origin": revision.revision_origin,
        "parent_revision_id": None,
    }
    if diagram_id:
        response["ui_path"] = f"/diagram/{diagram_id}"
    return response


def refine_selected_model(
    process_text: Optional[str],
    *,
    selected_system_id: str,
    refinement_instruction: str,
    pipeline_profile: PipelineProfile = "semantic_deterministic",
    enable_sketch_review_agent: Optional[bool] = None,
    enable_prompted_sketch_repair_agent: Optional[bool] = None,
    enable_graph_repair_agent: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Refine one existing imported candidate system in place.

    The workflow is:
    - load the selected system from the database
    - export it into the AI4MDE shape expected by ``refine_activity_model``
    - run refinement with the original process text and user instruction
    - import the refined export back into the same project
    - return the updated export payload and identifiers
    """
    if not selected_system_id or not str(selected_system_id).strip():
        raise ValueError("selected_system_id must be non-empty")
    if not refinement_instruction or not str(refinement_instruction).strip():
        raise ValueError("refinement_instruction must be non-empty")

    try:
        system = System.objects.select_related("project").prefetch_related("diagrams").get(
            pk=selected_system_id
        )
    except System.DoesNotExist as exc:
        raise ValueError(f"System {selected_system_id!r} does not exist.") from exc

    exported_current_model = ExportSingleSystem.model_validate(system).model_dump(mode="json")
    pipeline_config = resolve_pipeline_config(
        pipeline_profile=pipeline_profile,
        enable_sketch_review_agent=enable_sketch_review_agent,
        enable_prompted_sketch_repair_agent=enable_prompted_sketch_repair_agent,
        enable_graph_repair_agent=enable_graph_repair_agent,
    )
    source_revision = get_current_revision(
        str(system.id),
        fallback_process_text=process_text,
        fallback_pipeline_profile=pipeline_config["pipeline_profile"],
    )
    if source_revision is None or not source_revision.activity_graph:
        raise RefinementConflictError(_SYNC_BEFORE_REFINEMENT)
    try:
        saved_process_graph = _saved_process_graph(exported_current_model)
    except RefinementConflictError:
        unrepresentable_fields = _unrepresentable_refinement_fields(exported_current_model)
        if unrepresentable_fields:
            raise UnsupportedRefinementFieldError(
                _UNSUPPORTED_FIELDS_REFINEMENT.format(fields=", ".join(unrepresentable_fields))
            ) from None
        raise
    try:
        synchronized_process_graph = _saved_process_graph(source_revision.ai4mde_export)
    except Exception as exc:  # noqa: BLE001
        raise RefinementConflictError(_SYNC_BEFORE_REFINEMENT) from exc
    if saved_process_graph != synchronized_process_graph:
        raise RefinementConflictError(_SYNC_BEFORE_REFINEMENT)
    try:
        saved_fields = _native_process_snapshot(exported_current_model)
        synchronized_fields = _native_process_snapshot(source_revision.ai4mde_export)
    except (TypeError, ValueError, KeyError) as exc:
        raise RefinementConflictError(_SYNC_BEFORE_REFINEMENT) from exc
    if saved_fields != synchronized_fields:
        raise RefinementConflictError(_SYNC_BEFORE_REFINEMENT)
    unrepresentable_fields = (
        _unrepresentable_refinement_fields(exported_current_model)
        + _unrepresentable_activity_graph_fields(source_revision.activity_graph)
    )
    if unrepresentable_fields:
        raise UnsupportedRefinementFieldError(
            _UNSUPPORTED_FIELDS_REFINEMENT.format(fields=", ".join(unrepresentable_fields))
        )
    has_human_sync_history = SystemRevision.objects.filter(
        system=system,
        revision_origin=SystemRevision.REVISION_ORIGIN_HUMAN_SYNC,
    ).exists()
    if has_human_sync_history and pipeline_config["pipeline_profile"] != "semantic_deterministic":
        raise ValueError(
            "systems with synchronized human edits require pipeline_profile='semantic_deterministic'"
        )
    resolved_process_text = str(process_text).strip() if process_text and str(process_text).strip() else None
    if pipeline_config["pipeline_profile"] == "semantic_deterministic":
        if resolved_process_text is None:
            resolved_process_text = (
                source_revision.process_text if source_revision is not None else get_generation_process_text(str(system.id))
            )
        if resolved_process_text is None:
            raise ValueError(
                "semantic_deterministic refinement requires a persisted process_text for the selected system"
            )
        current_topology_artifact = (
            source_revision.topology_artifact if source_revision is not None else get_topology_artifact(str(system.id))
        )
        current_semantic_sketch_plan = (
            source_revision.semantic_sketch_plan
            if source_revision is not None
            else get_semantic_sketch_plan(str(system.id))
        )
        if current_topology_artifact is None or current_semantic_sketch_plan is None:
            raise ValueError(
                "semantic_deterministic refinement requires persisted topology and semantic artifacts for the selected system"
            )
        refinement_result = _run_semantic_refinement_from_artifacts(
            resolved_process_text,
            current_topology_artifact=current_topology_artifact,
            current_semantic_sketch_plan=current_semantic_sketch_plan,
            refinement_instruction=refinement_instruction,
        )
        artifact_diff = refinement_result["artifact_diff"]
        updated_artifacts = refinement_result["updated_artifacts"]
        clean_graph = refinement_result["clean_graph"]
        refined_export = convert_to_ai4mde(
            clean_model=clean_graph,
            system_id=str(system.id),
            diagram_id=_diagram_id_from_exported_system(exported_current_model),
            name=str(exported_current_model.get("name") or system.name),
            description=str(exported_current_model.get("description") or system.description),
            project_id=str(system.project_id),
        )
    else:
        if resolved_process_text is None:
            resolved_process_text = (
                source_revision.process_text if source_revision is not None else None
            )
        if resolved_process_text is None:
            raise ValueError("process_text must be non-empty")
        refined_export = refine_activity_model(
            process_text=resolved_process_text,
            current_model=exported_current_model,
            refinement_instruction=refinement_instruction,
            pipeline_profile=pipeline_config["pipeline_profile"],
            enable_sketch_review_agent=pipeline_config["enable_sketch_review_agent"],
            enable_prompted_sketch_repair_agent=pipeline_config["enable_prompted_sketch_repair_agent"],
            enable_graph_repair_agent=pipeline_config["enable_graph_repair_agent"],
        )
        clean_graph = _get_clean_model(refined_export)
        updated_artifacts = {
            "updated_topology_artifact": None,
            "updated_semantic_sketch_plan": None,
            "refinement_trace": {"user_instruction": refinement_instruction},
        }
        artifact_diff = None

    if _guarded_flow_signatures(exported_current_model) - _guarded_flow_signatures(refined_export):
        raise UnsupportedRefinementFieldError(
            _UNSUPPORTED_FIELDS_REFINEMENT.format(fields="Flow guard")
        )

    with transaction.atomic():
        current_system = System.objects.select_for_update().get(pk=system.id)
        current_export = ExportSingleSystem.model_validate(current_system).model_dump(mode="json")
        if (
            current_system.current_revision_id != source_revision.id
            or _saved_process_graph(current_export) != saved_process_graph
            or _native_process_snapshot(current_export) != saved_fields
        ):
            raise RefinementConflictError(_SYNC_BEFORE_REFINEMENT)
        unrepresentable_fields = (
            _unrepresentable_refinement_fields(current_export)
            + _unrepresentable_activity_graph_fields(source_revision.activity_graph)
        )
        if unrepresentable_fields:
            raise UnsupportedRefinementFieldError(
                _UNSUPPORTED_FIELDS_REFINEMENT.format(fields=", ".join(unrepresentable_fields))
            )
        import_to_ai4mde(system.project, refined_export)
        revision_meta = _create_revision_snapshot(
            system_id=str(system.id),
            process_text=resolved_process_text,
            pipeline_profile=pipeline_config["pipeline_profile"],
            topology_artifact=updated_artifacts["updated_topology_artifact"],
            semantic_sketch_plan=updated_artifacts["updated_semantic_sketch_plan"],
            activity_graph=clean_graph,
            ai4mde_export=refined_export,
            refinement_trace=updated_artifacts.get("refinement_trace"),
            refinement_instruction=refinement_instruction,
            revision_origin=SystemRevision.REVISION_ORIGIN_AI_REFINEMENT,
            parent_revision_id=str(source_revision.id) if source_revision is not None else None,
        )

    refined_system_json = unwrap_ai4mde_systems_export(refined_export)
    response = {
        "project_id": str(system.project_id),
        "system_id": refined_system_json["id"],
        "name": refined_system_json["name"],
        "refinement_instruction": refinement_instruction,
        "pipeline_profile": pipeline_config["pipeline_profile"],
        "enable_sketch_review_agent": pipeline_config["enable_sketch_review_agent"],
        "enable_prompted_sketch_repair_agent": pipeline_config["enable_prompted_sketch_repair_agent"],
        "enable_graph_repair_agent": pipeline_config["enable_graph_repair_agent"],
        "ai4mde": refined_export,
    }
    response.update(revision_meta)
    response["current_revision_id"] = revision_meta["revision_id"]
    response["revision_origin"] = revision_meta["revision_origin"]
    if pipeline_config["pipeline_profile"] == "semantic_deterministic":
        response["process_text"] = resolved_process_text
        response["activity_graph"] = clean_graph
        response["topology_artifact"] = updated_artifacts["updated_topology_artifact"]
        response["semantic_sketch_plan"] = updated_artifacts["updated_semantic_sketch_plan"]
        response["artifact_diff"] = artifact_diff
        response["refinement_trace"] = updated_artifacts.get("refinement_trace")
    else:
        response["process_text"] = resolved_process_text
        response["activity_graph"] = clean_graph
        response["topology_artifact"] = None
        response["semantic_sketch_plan"] = None
        response["artifact_diff"] = None
        response["refinement_trace"] = updated_artifacts.get("refinement_trace")
    return response


@transaction.atomic
def restore_revision(*, system_id: str, revision_id: str) -> Dict[str, Any]:
    if not system_id or not str(system_id).strip():
        raise ValueError("system_id must be non-empty")
    if not revision_id or not str(revision_id).strip():
        raise ValueError("revision_id must be non-empty")

    try:
        system = System.objects.select_for_update().select_related("project").get(pk=system_id)
    except System.DoesNotExist as exc:
        raise ValueError(f"System {system_id!r} does not exist.") from exc

    revisions = {
        str(revision.id): revision
        for revision in list_system_revisions(system_id)
    }
    revision = revisions.get(str(revision_id))
    if revision is None:
        raise ValueError(f"Revision {revision_id!r} does not exist for system {system_id!r}.")
    import_to_ai4mde(system.project, revision.ai4mde_export)
    set_current_revision(system_id, revision_id)
    if revision.topology_artifact is not None and revision.semantic_sketch_plan is not None:
        persist_semantic_generation_artifacts(
            system_id=system_id,
            process_text=revision.process_text,
            pipeline_profile=revision.pipeline_profile,
            topology_artifact=revision.topology_artifact,
            semantic_sketch_plan=revision.semantic_sketch_plan,
        )

    return {
        "project_id": str(system.project_id),
        "system_id": str(system.id),
        "current_revision_id": str(revision.id),
        "revision_id": str(revision.id),
        "revision_index": revision.revision_index,
        "revision_origin": revision.revision_origin,
        "parent_revision_id": (
            str(revision.parent_revision_id) if revision.parent_revision_id else None
        ),
        "process_text": revision.process_text,
        "pipeline_profile": revision.pipeline_profile,
        "activity_graph": revision.activity_graph,
        "topology_artifact": revision.topology_artifact,
        "semantic_sketch_plan": revision.semantic_sketch_plan,
        "refinement_trace": revision.refinement_trace,
        "refinement_instruction": revision.refinement_instruction,
        "ai4mde": revision.ai4mde_export,
    }


def get_system_revisions(system_id: str) -> Dict[str, Any]:
    if not system_id or not str(system_id).strip():
        raise ValueError("system_id must be non-empty")
    revisions = list_system_revisions(system_id)
    current_revision = get_current_revision(system_id)
    original_revision = revisions[0] if revisions else None
    return {
        "system_id": system_id,
        "process_text": original_revision.process_text if original_revision is not None else None,
        "current_revision_id": str(current_revision.id) if current_revision is not None else None,
        "revisions": [
            {
                "revision_id": str(revision.id),
                "revision_index": revision.revision_index,
                "parent_revision_id": (
                    str(revision.parent_revision_id) if revision.parent_revision_id else None
                ),
                "pipeline_profile": revision.pipeline_profile,
                "revision_origin": revision.revision_origin,
                "candidate_index": revision.candidate_index,
                "candidate_count": revision.candidate_count,
                "refinement_instruction": revision.refinement_instruction,
                "created_at": revision.created_at.isoformat(),
                "is_current": bool(current_revision and current_revision.id == revision.id),
            }
            for revision in revisions
        ],
    }


def synchronize_human_edit(*, system_id: str) -> Dict[str, Any]:
    if not system_id or not str(system_id).strip():
        raise ValueError("system_id must be non-empty")

    try:
        system = System.objects.select_related("project").prefetch_related("diagrams").get(pk=system_id)
    except System.DoesNotExist as exc:
        raise ValueError(f"System {system_id!r} does not exist.") from exc

    current_revision = get_current_revision(str(system.id))
    if current_revision is None:
        raise ValueError("human edit synchronization requires an existing canonical revision")
    if current_revision.pipeline_profile != "semantic_deterministic":
        raise ValueError("human edit synchronization currently supports only semantic_deterministic revisions")

    exported_current_model = ExportSingleSystem.model_validate(system).model_dump(mode="json")
    try:
        unchanged_native_process = (
            _native_process_snapshot(exported_current_model)
            == _native_process_snapshot(current_revision.ai4mde_export)
        )
    except (TypeError, ValueError, KeyError):
        unchanged_native_process = False
    sync_result = synchronize_persisted_human_edit(
        exported_current_model,
        current_revision=current_revision,
        unchanged_native_process=unchanged_native_process,
    )

    revision_meta = _create_revision_snapshot(
        system_id=str(system.id),
        process_text=current_revision.process_text,
        pipeline_profile=current_revision.pipeline_profile,
        topology_artifact=sync_result["topology_artifact"],
        semantic_sketch_plan=sync_result["semantic_sketch_plan"],
        activity_graph=sync_result["activity_graph"],
        ai4mde_export=[exported_current_model],
        refinement_trace={
            "event": "human_sync",
            "source_revision_id": str(current_revision.id),
        },
        refinement_instruction=None,
        revision_origin=SystemRevision.REVISION_ORIGIN_HUMAN_SYNC,
        parent_revision_id=str(current_revision.id),
    )
    artifact_diff = _build_artifact_diff(
        before_topology_artifact=current_revision.topology_artifact,
        after_topology_artifact=sync_result["topology_artifact"],
        before_semantic_sketch_plan=current_revision.semantic_sketch_plan,
        after_semantic_sketch_plan=sync_result["semantic_sketch_plan"],
    )

    return {
        "project_id": str(system.project_id),
        "system_id": str(system.id),
        "name": str(system.name),
        "process_text": current_revision.process_text,
        "pipeline_profile": current_revision.pipeline_profile,
        "activity_graph": sync_result["activity_graph"],
        "topology_artifact": sync_result["topology_artifact"],
        "semantic_sketch_plan": sync_result["semantic_sketch_plan"],
        "ai4mde": [exported_current_model],
        "artifact_diff": artifact_diff,
        "synchronization_diagnostics": sync_result["diagnostics"],
        "current_revision_id": revision_meta["revision_id"],
        **revision_meta,
    }
