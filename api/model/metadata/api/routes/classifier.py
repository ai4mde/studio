from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Body, Router
from ninja.errors import HttpError
from pydantic import ValidationError

from metadata.api.schemas.classifier import get_classifier_schemas
from metadata.models import Classifier

from metadata.api.schemas.classifier import (
    ClassifierCreate,
    ClassifierRead,
    ClassifierUpdate,
)

router = Router()


@router.get("/", response=list[ClassifierRead])
def list_classifiers(
    request,
    project_id: UUID | None = None,
    system_id: UUID | None = None,
):
    # TODO: Add filtering logic
    # Maybe add this to the Node routes
    classifiers = Classifier.objects.all()

    if system_id:
        return classifiers.filter(system_id=system_id)

    if project_id:
        return classifiers.filter(system__project_id=project_id)

    return classifiers


@router.get("/{classifier_id}/", response=ClassifierRead)
def read_classifier(request, classifier_id: UUID):
    return get_object_or_404(Classifier, id=classifier_id)
