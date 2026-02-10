from ninja import Router, Query
from pydantic import BaseModel
from django.http import HttpRequest

from metadata.api.schemas import MetaClassifiersSchema
from metadata.specification import ClassifierSchema

from metadata.models import System, Classifier

classifiers = Router()


class ClassifierExistsResponse(BaseModel):
    exists: bool


@classifiers.get("/exists/", response=ClassifierExistsResponse)
def classifier_exists(request: HttpRequest, name: str = Query(...), ctype: str | None = Query(None)):
    if not request.resolver_match:
        return 500, "Resolver match not found"

    system_id = request.resolver_match.kwargs.get("system_id")
    system = System.objects.get(id=system_id)

    normalized = (name or "").strip()
    if not normalized:
        return {"exists": False}

    q = system.classifiers.filter(data__name__iexact=normalized)
    if ctype:
        q = q.filter(data__type=ctype.strip())
        
    return {"exists": q.exists()}


@classifiers.get("/", response=MetaClassifiersSchema)
def get_classifiers(request: HttpRequest):
    if not request.resolver_match:
        return 500, "Resolver match not found"

    system_id = request.resolver_match.kwargs.get("system_id")
    system = System.objects.get(id=system_id)
    project = system.project

    if not project:
        return {"classifiers": []}

    return {
        "classifiers": project.classifiers.all(),
    }


@classifiers.get("/{classifier_id}/", response=ClassifierSchema)
def read_classifier(request: HttpRequest, classifier_id: str):
    if not request.resolver_match:
        return 500, "Resolver match not found"

    system_id = request.resolver_match.kwargs.get("system_id")
    system = System.objects.get(id=system_id)

    if not system:
        return 404, "System not found"
    
    try:
        classifier = system.classifiers.get(id=classifier_id)
    except Classifier.DoesNotExist:
        return 404, "Classifier not found"

    return { 
        "id": classifier.id,
        "data": classifier.data,
    }


classes = Router()

@classes.get("/", response=MetaClassifiersSchema)
def read_classes(request: HttpRequest):
    if not request.resolver_match:
        return 500, "Resolver match not found"

    system_id = request.resolver_match.kwargs.get("system_id")
    system = System.objects.get(id=system_id)

    if not system:
        return 404, "System not found"

    return {
        "classifiers": system.classifiers.filter(data__type='class').order_by('id'),
    }


actors = Router()

@actors.get("/", response=MetaClassifiersSchema)
def read_actors(request: HttpRequest):
    if not request.resolver_match:
        return 500, "Resolver match not found"

    system_id = request.resolver_match.kwargs.get("system_id")
    system = System.objects.get(id=system_id)

    if not system:
        return 404, "System not found"

    return {
        "classifiers": system.classifiers.filter(data__type='actor'),
    }


__all__ = [
    "classifiers",
    "classes",
    "actors",
]
