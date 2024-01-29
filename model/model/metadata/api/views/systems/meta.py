from ninja import Router
from django.http import HttpRequest

from metadata.api.schemas import MetaSchema

from metadata.models import System

meta = Router()


@meta.get("/", response=MetaSchema)
def get_meta(request: HttpRequest):
    if not request.resolver_match:
        return 500, "Resolver match not found"

    system_id = request.resolver_match.kwargs.get("system_id")
    system = System.objects.get(id=system_id)

    if not system:
        return 404, "System not found"

    return {
        "classifiers": system.classifiers.all(),
        "relations": system.relations.all(),
    }


__all__ = [
    "meta",
]
