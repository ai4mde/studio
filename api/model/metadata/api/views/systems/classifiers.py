from ninja import Router
from django.http import HttpRequest

from metadata.api.schemas import MetaClassifiersSchema

from metadata.models import System

classifiers = Router()


@classifiers.get("/", response=MetaClassifiersSchema)
def get_classifiers(request: HttpRequest):
    if not request.resolver_match:
        return 500, "Resolver match not found"

    system_id = request.resolver_match.kwargs.get("system_id")
    system = System.objects.get(id=system_id)

    if not system:
        return 404, "System not found"

    return {
        "classifiers": system.classifiers.all(),
    }


classes = Router()

@classes.get("/", response=MetaClassifiersSchema)
def get_classes(request: HttpRequest):
    if not request.resolver_match:
        return 500, "Resolver match not found"

    system_id = request.resolver_match.kwargs.get("system_id")
    system = System.objects.get(id=system_id)

    if not system:
        return 404, "System not found"

    return {
        "classifiers": system.classifiers.filter(data__type='class'),
    }


__all__ = [
    "classifiers",
    "classes",
]
