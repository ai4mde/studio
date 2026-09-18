import logging

from django.http import HttpResponse
from ninja import NinjaAPI, Schema
from ninja.errors import ValidationError

from model.auth import auth, create_token

from diagram.api import router as diagram_router
from generator.api import generator_router
from metadata.api import router as metadata_router
from prose.api import prose_router


api = NinjaAPI(
    title="AI4MDE Studio",
    version="0.0.1",  # TODO: Use package-wide versioning
    description="AI4MDE Studio API",
    auth=auth,
    csrf=False,  # TODO: Ensure this works with Axios frontend / XSRF Header
)
api.add_router("/metadata/", metadata_router)
api.add_router("/", diagram_router)
api.add_router("/prose/", prose_router)
api.add_router("/generator/", generator_router)


logger = logging.getLogger(__name__)


@api.exception_handler(ValidationError)
def validation_error_handler(request, exc):
    for error in exc.errors:
        field = ".".join(str(part) for part in error["loc"])
        logger.warning(
            "%s %s: %s - %s",
            request.method,
            request.path,
            field,
            error["msg"]
        )

    return api.create_response(
        request,
        {"detail": exc.errors},
        status=422,
    )


class GetTokenSchema(Schema):
    username: str
    password: str


@api.post("/auth/token", auth=None, tags=["authentication"])
def get_token(request, body: GetTokenSchema, response: HttpResponse):
    user, token = create_token(body.username, body.password)
    if user and token:
        response.set_cookie(
            "key",
            token,
            httponly=True,
        )
        return {
            "token": token,
            "id": user.id,
            "email": user.email,
            "username": user.username,
        }
    return 403, {"message": "User not found."}


@api.post("/auth/logout", tags=["authentication"])
def logout(request, response: HttpResponse):
    response.delete_cookie("key")
    return {"message": "Logged out."}


@api.get("/auth/status", tags=["authentication"])
def get_auth(request):
    if user := request.auth:
        return 200, {
            "id": user.id,
            "email": user.email,
            "username": user.username,
        }
    return 403, {"id": None}
