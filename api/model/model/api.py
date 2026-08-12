from typing import Any, Literal, Optional

from diagram.api import diagram_router
from django.http import HttpResponse, JsonResponse
from generator.api import generator_router
from metadata.api import metadata_router
from ninja import NinjaAPI, Schema
from prose.api import prose_router

from model.auth import auth, create_token

api = NinjaAPI(
    title="AI4MDE Studio",
    version="0.0.1",  # TODO: Use package-wide versioning
    description="AI4MDE Studio API",
    auth=auth,
    csrf=False,  # TODO: Ensure this works with Axios frontend / XSRF Header
)
api.add_router("/metadata/", metadata_router)
api.add_router("/diagram/", diagram_router)
api.add_router("/prose/", prose_router)
api.add_router("/generator/", generator_router)


class GenerateModelRequest(Schema):
    process_text: str
    mode: Literal["baseline", "refinement"] = "baseline"
    project_id: Optional[str] = None
    pipeline_profile: Literal["stable", "sketch_review_only", "graph_repair_only", "both_agents", "semantic_deterministic"] = "semantic_deterministic"
    response_mode: Literal["full", "summary"] = "full"
    current_topology_artifact: Optional[dict[str, Any]] = None
    current_semantic_sketch_plan: Optional[dict[str, Any]] = None
    instruction: Optional[str] = None
    use_experimental_compiler: bool = False
    enable_sketch_review_agent: Optional[bool] = None
    enable_prompted_sketch_repair_agent: Optional[bool] = None
    enable_graph_repair_agent: Optional[bool] = None


class RefineModelRequest(Schema):
    process_text: Optional[str] = None
    selected_system_id: Optional[str] = None
    refinement_instruction: Optional[str] = None
    system_id: Optional[str] = None
    instruction: Optional[str] = None
    pipeline_profile: Literal["stable", "sketch_review_only", "graph_repair_only", "both_agents", "semantic_deterministic"] = "semantic_deterministic"
    enable_sketch_review_agent: Optional[bool] = None
    enable_prompted_sketch_repair_agent: Optional[bool] = None
    enable_graph_repair_agent: Optional[bool] = None


class RestoreRevisionRequest(Schema):
    system_id: str
    revision_id: str


class SynchronizeHumanEditRequest(Schema):
    system_id: str


class CandidateNodePosition(Schema):
    x: int
    y: int


class SelectCandidateRequest(Schema):
    candidate_id: str
    node_positions: Optional[dict[str, CandidateNodePosition]] = None


class GetTokenSchema(Schema):
    username: str
    password: str


@api.post("/auth/token", auth=None, tags=["authentication"])
def get_token(request, body: GetTokenSchema, response: HttpResponse):
    user, token = create_token(body.username, body.password)
    if user and token:
        token_str = token if isinstance(token, str) else token.decode("utf-8")
        response.set_cookie(
            "key",
            token_str,
            httponly=True,
        )
        return {
            "token": token_str,
            "id": user.pk,
            "email": user.email or "",
            "username": user.username,
        }
    return JsonResponse({"message": "User not found."}, status=403)


@api.post("/generate-model", auth=None, tags=["experiments"])
def generate_model(request, body: GenerateModelRequest):
    """
    Research prototype: create one experiment-session project, generate activity
    model(s), convert them to AI4MDE export JSON, and import them into that project.
    """
    from model.experiment_pipeline import run_pipeline

    try:
        payload = run_pipeline(
            body.process_text,
            body.mode,
            project_id=body.project_id,
            pipeline_profile=body.pipeline_profile,
            current_topology_artifact=body.current_topology_artifact,
            current_semantic_sketch_plan=body.current_semantic_sketch_plan,
            refinement_instruction=body.instruction,
            use_experimental_compiler=body.use_experimental_compiler,
            enable_sketch_review_agent=body.enable_sketch_review_agent,
            enable_prompted_sketch_repair_agent=body.enable_prompted_sketch_repair_agent,
            enable_graph_repair_agent=body.enable_graph_repair_agent,
        )
        if body.response_mode == "summary":
            payload = {
                "session_id": payload["session_id"],
                "project_id": payload["project_id"],
                "mode": payload["mode"],
                "pipeline_profile": payload["pipeline_profile"],
            }
        return JsonResponse(
            payload
        )
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception as exc:  # noqa: BLE001
        return JsonResponse(
            {"error": "generation_or_import_failed", "detail": str(exc)},
            status=502,
        )


@api.post("/refine-model", auth=None, tags=["experiments"])
def refine_model(request, body: RefineModelRequest):
    """
    Research prototype: refine one previously imported candidate activity model
    using the original process text plus a natural-language refinement instruction.
    """
    from model.experiment_pipeline import refine_selected_model

    try:
        return JsonResponse(
            refine_selected_model(
                body.process_text,
                selected_system_id=body.selected_system_id or body.system_id,
                refinement_instruction=body.refinement_instruction or body.instruction,
                pipeline_profile=body.pipeline_profile,
                enable_sketch_review_agent=body.enable_sketch_review_agent,
                enable_prompted_sketch_repair_agent=body.enable_prompted_sketch_repair_agent,
                enable_graph_repair_agent=body.enable_graph_repair_agent,
            )
        )
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception as exc:  # noqa: BLE001
        return JsonResponse(
            {"error": "refinement_or_import_failed", "detail": str(exc)},
            status=502,
        )


@api.post("/select-candidate", tags=["experiments"])
def select_candidate(request, body: SelectCandidateRequest):
    from model.experiment_pipeline import select_provisional_candidate

    try:
        return JsonResponse(
            select_provisional_candidate(
                candidate_id=body.candidate_id,
                node_positions=(
                    {
                        node_id: position.model_dump()
                        for node_id, position in body.node_positions.items()
                    }
                    if body.node_positions is not None
                    else None
                ),
            )
        )
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception as exc:  # noqa: BLE001
        return JsonResponse(
            {"error": "candidate_selection_failed", "detail": str(exc)},
            status=502,
        )


@api.get("/system-revisions/{system_id}", auth=None, tags=["experiments"])
def system_revisions(request, system_id: str):
    from model.experiment_pipeline import get_system_revisions

    try:
        return JsonResponse(get_system_revisions(system_id))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception as exc:  # noqa: BLE001
        return JsonResponse(
            {"error": "revision_history_failed", "detail": str(exc)},
            status=502,
        )


@api.post("/restore-revision", auth=None, tags=["experiments"])
def restore_revision(request, body: RestoreRevisionRequest):
    from model.experiment_pipeline import restore_revision as restore_revision_pipeline

    try:
        return JsonResponse(
            restore_revision_pipeline(
                system_id=body.system_id,
                revision_id=body.revision_id,
            )
        )
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception as exc:  # noqa: BLE001
        return JsonResponse(
            {"error": "restore_revision_failed", "detail": str(exc)},
            status=502,
        )


@api.post("/synchronize-human-edit", auth=None, tags=["experiments"])
def synchronize_human_edit(request, body: SynchronizeHumanEditRequest):
    from llm.human_edit_synchronizer import HumanEditSynchronizationError
    from model.experiment_pipeline import synchronize_human_edit as synchronize_human_edit_pipeline

    try:
        return JsonResponse(
            synchronize_human_edit_pipeline(system_id=body.system_id)
        )
    except HumanEditSynchronizationError as exc:
        payload = {"error": str(exc)}
        payload.update(exc.diagnostics)
        return JsonResponse(payload, status=422)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception as exc:  # noqa: BLE001
        return JsonResponse(
            {"error": "synchronize_human_edit_failed", "detail": str(exc)},
            status=502,
        )


@api.post("/auth/logout", auth=None, tags=["authentication"])
def logout(request):
    resp = JsonResponse({"message": "Logged out."})
    resp.delete_cookie("key")
    return resp


@api.get("/auth/status", tags=["authentication"])
def get_auth(request):
    user = request.auth
    if user:
        return JsonResponse(
            {
                "id": user.pk,
                "email": user.email or "",
                "username": user.username,
            }
        )
    return JsonResponse({"id": None}, status=403)
