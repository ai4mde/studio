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

from metadata.api.schemas import ExportSingleSystem
from metadata.models import Project, System

from llm.baseline_generator import generate_activity_model
from llm.converter import convert_to_ai4mde, unwrap_ai4mde_systems_export, validate_ai4mde_json
from llm.pipeline_profiles import PipelineProfile, resolve_pipeline_config
from llm.refinement_generator import (
    generate_and_convert_candidates,
    model_activity_with_experimental_compiler,
    refine_activity_model,
)

Mode = Literal["baseline", "refinement"]


def generate_session_id() -> str:
    """Unique label for one user request (session)."""
    return f"Session_{uuid.uuid4().hex[:12]}"


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
    pipeline_profile: PipelineProfile = "stable",
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
    - create one project once
    - generate three initial clean candidates
    - convert/import all three systems into that same project
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
            }
        ]
    elif mode == "refinement":
        if use_experimental_compiler:
            raise ValueError("experimental compiler is currently supported only for baseline mode")
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
        if mode == "baseline" and not use_experimental_compiler and debug_bundle is not None:
            entry["executed_stages"] = debug_bundle.get("executed_stages") or []
        try:
            import_to_ai4mde(project, systems_export)
        except Exception as exc:  # noqa: BLE001 — surface any import failure to client
            entry["import_error"] = str(exc)
        results.append(entry)

        # Keep the exported ids visible to the caller for debugging/UI linkage.
        entry["export_system_id"] = system_json["id"]
        entry["export_name"] = system_json["name"]
        if entry.get("diagram_id"):
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
        "systems": results,
    }


def refine_selected_model(
    process_text: str,
    *,
    selected_system_id: str,
    refinement_instruction: str,
    pipeline_profile: PipelineProfile = "stable",
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
    if not process_text or not str(process_text).strip():
        raise ValueError("process_text must be non-empty")
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
    refined_export = refine_activity_model(
        process_text=process_text,
        current_model=exported_current_model,
        refinement_instruction=refinement_instruction,
        pipeline_profile=pipeline_config["pipeline_profile"],
        enable_sketch_review_agent=pipeline_config["enable_sketch_review_agent"],
        enable_prompted_sketch_repair_agent=pipeline_config["enable_prompted_sketch_repair_agent"],
        enable_graph_repair_agent=pipeline_config["enable_graph_repair_agent"],
    )

    import_to_ai4mde(system.project, refined_export)

    refined_system_json = unwrap_ai4mde_systems_export(refined_export)
    return {
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
