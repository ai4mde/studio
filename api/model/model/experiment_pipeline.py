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

from metadata.models import Project

from llm.baseline_generator import generate_activity_model
from llm.converter import convert_to_ai4mde, unwrap_ai4mde_systems_export, validate_ai4mde_json
from llm.refinement_generator import generate_and_convert_candidates

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
    results: List[Dict[str, Any]] = []

    if mode == "baseline":
        clean_model = generate_activity_model(process_text)
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
        candidate_exports = generate_and_convert_candidates(
            process_text,
            n=3,
            project_id=resolved_project_id,
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
            "project_id": resolved_project_id,
            "import_error": None,
        }
        try:
            import_to_ai4mde(project, systems_export)
        except Exception as exc:  # noqa: BLE001 — surface any import failure to client
            entry["import_error"] = str(exc)
        results.append(entry)

        # Keep the exported ids visible to the caller for debugging/UI linkage.
        entry["export_system_id"] = system_json["id"]
        entry["export_name"] = system_json["name"]

    return {
        "session_id": session_id,
        "project_id": resolved_project_id,
        "mode": mode,
        "systems": results,
    }
