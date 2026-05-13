import os
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from jwt import decode, encode
from ninja.security import APIKeyCookie, HttpBearer


def create_token(username: str, password: str):
    user = authenticate(username=username, password=password)
    if user:
        return user, encode(
            {
                "exp": datetime.now(tz=timezone.utc) + timedelta(days=1),
                "nbf": datetime.now(tz=timezone.utc),
                "iss": "urn:ai4mdestudio",
                "iat": datetime.now(tz=timezone.utc),
                "uid": user.id,
            },
            settings.SECRET_KEY,
        )
    return None, None


def user_from_token(token: str):
    if token:
        try:
            payload = decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            if payload:
                user_cls = get_user_model()
                return user_cls.objects.get(id=payload.get("uid"))
        except Exception:
            return None


class CookieToken(APIKeyCookie):
    def authenticate(self, _, key):
        return user_from_token(key)


class BearerToken(HttpBearer):
    def authenticate(self, _, key):
        return user_from_token(key)


class _ServicePrincipal:
    """Sentinel returned for internal service-to-service calls."""
    is_authenticated = True
    id = None
    username = "internal-service"


class InternalServiceKey(HttpBearer):
    def authenticate(self, _, key):
        internal_key = os.environ.get("INTERNAL_API_KEY")
        if internal_key and key == internal_key:
            return _ServicePrincipal()
        return None


auth = [CookieToken(csrf=False), BearerToken(), InternalServiceKey()]

__all__ = [
    "create_token",
    "auth",
]
