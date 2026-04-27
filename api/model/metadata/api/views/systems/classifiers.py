from ninja import Router, Query, Schema
from pydantic import BaseModel
from django.http import HttpRequest

from metadata.api.schemas import MetaClassifiersSchema
from metadata.specification import ClassifierSchema

from metadata.models import System, Classifier

classifiers = Router()


class ErrorSchema(Schema):
    detail: str


class ClassifierExistsResponse(BaseModel):
    exists: bool


@classifiers.get("/exists/", response={200: ClassifierExistsResponse, 500: ErrorSchema})
def classifier_exists(request: HttpRequest, name: str = Query(...), ctype: str | None = Query(None)):
    if not request.resolver_match:
        return 500, {"detail": "Resolver match not found"}

    system_id = request.resolver_match.kwargs.get("system_id")
    system = System.objects.get(id=system_id)

    normalized = (name or "").strip()
    if not normalized:
        return {"exists": False}

    q = system.classifiers.filter(data__name__iexact=normalized)
    if ctype:
        q = q.filter(data__type=ctype.strip())
        
    return {"exists": q.exists()}


@classifiers.get("/", response={200: MetaClassifiersSchema, 500: ErrorSchema})
def get_classifiers(request: HttpRequest):
    if not request.resolver_match:
        return 500, {"detail": "Resolver match not found"}

    system_id = request.resolver_match.kwargs.get("system_id")
    system = System.objects.get(id=system_id)
    project = system.project

    if not project:
        return {"classifiers": []}

    return {
        "classifiers": project.classifiers.all(),
    }


@classifiers.get("/{classifier_id}/", response={200: ClassifierSchema, 404: ErrorSchema, 500: ErrorSchema})
def read_classifier(request: HttpRequest, classifier_id: str):
    if not request.resolver_match:
        return 500, {"detail": "Resolver match not found"}

    system_id = request.resolver_match.kwargs.get("system_id")
    system = System.objects.get(id=system_id)

    if not system:
        return 404, {"detail": "System not found"}
    
    try:
        classifier = system.classifiers.get(id=classifier_id)
    except Classifier.DoesNotExist:
        return 404, {"detail": "Classifier not found"}

    return { 
        "id": classifier.id,
        "data": classifier.data,
    }


classes = Router()

@classes.get("/", response={200: MetaClassifiersSchema, 404: ErrorSchema, 500: ErrorSchema})
def read_classes(request: HttpRequest):
    if not request.resolver_match:
        return 500, {"detail": "Resolver match not found"}

    system_id = request.resolver_match.kwargs.get("system_id")
    system = System.objects.get(id=system_id)

    if not system:
        return 404, {"detail": "System not found"}

    return {
        "classifiers": system.classifiers.filter(data__type='class').order_by('id'),
    }


actors = Router()

@actors.get("/", response={200: MetaClassifiersSchema, 404: ErrorSchema, 500: ErrorSchema})
def read_actors(request: HttpRequest):
    if not request.resolver_match:
        return 500, {"detail": "Resolver match not found"}

    system_id = request.resolver_match.kwargs.get("system_id")
    system = System.objects.get(id=system_id)

    if not system:
        return 404, {"detail": "System not found"}

    return {
        "classifiers": system.classifiers.filter(data__type='actor'),
    }


__all__ = [
    "classifiers",
    "classes",
    "actors",
]
