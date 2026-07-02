import secrets
import uuid
from datetime import datetime, timedelta, timezone

from diagram.api import diagram_router
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from generator.api import generator_router
from jwt import encode
from llm.api import llm_router
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
api.add_router("/llm/", llm_router)


class GetTokenSchema(Schema):
    username: str
    password: str


class TokenResponseSchema(Schema):
    token: str
    id: str
    email: str
    username: str


class MessageResponseSchema(Schema):
    message: str


@api.post(
    "/auth/token",
    auth=None,
    tags=["authentication"],
    response={200: TokenResponseSchema, 403: MessageResponseSchema},
)
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
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
        }
    return 403, {"message": "User not found."}


@api.post(
    "/auth/demo",
    auth=None,
    tags=["authentication"],
    response={200: TokenResponseSchema},
)
def create_demo_session(request, response: HttpResponse):
    user_model = get_user_model()
    username = f"demo_{uuid.uuid4().hex[:8]}"
    password = secrets.token_urlsafe(16)
    user = user_model.objects.create_user(
        username=username,
        email=f"{username}@demo.localhost",
        password=password,
        is_staff=False,
        is_superuser=False,
    )
    token = encode(
        {
            "exp": datetime.now(tz=timezone.utc) + timedelta(days=1),
            "nbf": datetime.now(tz=timezone.utc),
            "iss": "urn:ai4mdestudio",
            "iat": datetime.now(tz=timezone.utc),
            "uid": user.id,
        },
        settings.SECRET_KEY,
    )
    response.set_cookie("key", token, httponly=True, secure=True, samesite="Lax")
    return {
        "token": token,
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
    }


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
