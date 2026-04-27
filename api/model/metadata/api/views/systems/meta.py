from ninja import Router, Schema
from django.http import HttpRequest

from metadata.api.schemas import MetaSchema

from metadata.models import System

meta = Router()


class ErrorSchema(Schema):
    detail: str


@meta.get("/", response={200: MetaSchema, 404: ErrorSchema, 500: ErrorSchema})
def get_meta(request: HttpRequest):
    if not request.resolver_match:
        return 500, {"detail": "Resolver match not found"}

    system_id = request.resolver_match.kwargs.get("system_id")
    system = System.objects.get(id=system_id)

    if not system:
        return 404, {"detail": "System not found"}

    return {
        "classifiers": system.classifiers.all(),
        "relations": system.relations.all(),
    }


__all__ = [
    "meta",
]
