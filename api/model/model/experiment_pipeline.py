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
    synchronize_persisted_human_edit,
)
from llm.refinement_planner import generate_refinement_plan
from llm.sketch_repair import repair_activity_sketch
from llm.topology_to_sketch_compiler import compile_topology_and_semantics_to_activity_sketch
from llm.converter import convert_to_ai4mde, unwrap_ai4mde_systems_export, validate_ai4mde_json
from llm.pipeline_profiles import PipelineProfile, resolve_pipeline_config
from llm.refinement_generator import (
    _get_clean_model,
    generate_and_convert_candidates,
    model_activity_with_experimental_compiler,
    refine_activity_model,
)

Mode = Literal["baseline", "refinement"]


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
    repaired_sketch, _ = repair_activity_sketch(deterministic_sketch)
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


def import_to_ai4mde(project: Project, systems_export: List[Dict[str, Any]]) -> None:
    """
    Validate and import a wrapped single-system AI4MDE export into ``project``.
    """
    validate_ai4mde_json(systems_export)
    project.import_systems_from_json(systems_export)


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
        candidate_exports = [
            {
                "clean": clean_model,
                "ai4mde": convert_to_ai4mde(
                    clean_model=clean_model,
                    system_id=str(uuid.uuid4()),
                    diagram_id=str(uuid.uuid4()),
                    name=f"{session_id}_Model_1",
                    description=f"Experiment session {session_id}",
                    project_id=resolved_project_id,
                ),
                "debug_bundle": debug_bundle,
            }
        ]
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
            candidate_exports = [
                {
                    "clean": refinement_result["clean_graph"],
                    "ai4mde": convert_to_ai4mde(
                        clean_model=refinement_result["clean_graph"],
                        system_id=str(uuid.uuid4()),
                        diagram_id=str(uuid.uuid4()),
                        name=f"{session_id}_Refined_Model_1",
                        description=f"Refinement session {session_id}",
                        project_id=resolved_project_id,
                    ),
                    "updated_topology_artifact": updated_artifacts["updated_topology_artifact"],
                    "updated_semantic_sketch_plan": updated_artifacts["updated_semantic_sketch_plan"],
                    "artifact_diff": refinement_result["artifact_diff"],
                    "refinement_trace": updated_artifacts.get("refinement_trace"),
                }
            ]
        else:
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
    else:
        raise ValueError("mode must be 'baseline' or 'refinement'")

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
        }
        candidate_debug_bundle = candidate.get("debug_bundle")
        if candidate_debug_bundle is not None:
            entry["executed_stages"] = candidate_debug_bundle.get("executed_stages") or []
            stage_artifacts = candidate_debug_bundle.get("stage_artifacts") or {}
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
                provisional_candidate = ProvisionalCandidate.objects.create(
                    project=project,
                    session_id=session_id,
                    candidate_index=candidate_index,
                    candidate_count=len(candidate_exports),
                    process_text=process_text,
                    pipeline_profile=pipeline_config["pipeline_profile"],
                    activity_graph=candidate["clean"],
                    ai4mde_export=systems_export,
                    topology_artifact=topology_artifact,
                    semantic_sketch_plan=semantic_sketch_plan,
                )
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
        except Exception as exc:  # noqa: BLE001 — surface any import failure to client
            entry["import_error"] = str(exc)
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
def select_provisional_candidate(*, candidate_id: str) -> Dict[str, Any]:
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

    system_json = unwrap_ai4mde_systems_export(candidate.ai4mde_export)
    import_to_ai4mde(candidate.project, candidate.ai4mde_export)
    revision_meta = _create_revision_snapshot(
        system_id=system_json["id"],
        process_text=candidate.process_text,
        pipeline_profile=candidate.pipeline_profile,
        topology_artifact=candidate.topology_artifact,
        semantic_sketch_plan=candidate.semantic_sketch_plan,
        activity_graph=candidate.activity_graph,
        ai4mde_export=candidate.ai4mde_export,
        candidate_index=candidate.candidate_index,
        candidate_count=candidate.candidate_count,
        revision_origin=SystemRevision.REVISION_ORIGIN_BASELINE,
        parent_revision_id=None,
    )
    candidate.selected_system_id = system_json["id"]
    candidate.selected_at = timezone.now()
    candidate.save(update_fields=["selected_system", "selected_at"])
    revision = SystemRevision.objects.get(pk=revision_meta["revision_id"])
    return _selected_candidate_response(candidate, revision)


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

    with transaction.atomic():
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
    return {
        "system_id": system_id,
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
    sync_result = synchronize_persisted_human_edit(
        exported_current_model,
        current_revision=current_revision,
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
