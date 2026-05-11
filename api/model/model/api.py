from typing import Literal, Optional

from diagram.api import diagram_router
from django.http import HttpResponse, JsonResponse
from generator.api import generator_router
from metadata.api import metadata_router
from ninja import NinjaAPI, Schema
from prose.api import prose_router

from model.auth import auth, create_token, resolve_request_user

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
    return 403, {"message": "User not found."}


@api.post("/generate-model", auth=None, tags=["experiments"])
def generate_model(request, body: GenerateModelRequest):
    """
    Research prototype: create one experiment-session project, generate activity
    model(s), convert them to AI4MDE export JSON, and import them into that project.
    """
    from model.experiment_pipeline import run_pipeline

    try:
        return JsonResponse(
            run_pipeline(
                body.process_text,
                body.mode,
                project_id=body.project_id,
            )
        )
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception as exc:  # noqa: BLE001
        return JsonResponse(
            {"error": "generation_or_import_failed", "detail": str(exc)},
            status=502,
        )


@api.post("/auth/logout", auth=None, tags=["authentication"])
def logout(request):
    resp = JsonResponse({"message": "Logged out."})
    resp.delete_cookie("key")
    return resp


@api.get("/auth/status", auth=None, tags=["authentication"])
def get_auth(request):
    user = resolve_request_user(request)
    if user:
        return JsonResponse(
            {
                "id": user.pk,
                "email": user.email or "",
                "username": user.username,
            }
        )
    return JsonResponse({"id": None}, status=403)
