from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Body, Router
from ninja.errors import HttpError
from pydantic import ValidationError

from metadata.api.schemas.classifier.registry import get_classifier_schemas
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
    classifiers = Classifier.objects.all()

    if system_id:
        return classifiers.filter(system_id=system_id)

    if project_id:
        return classifiers.filter(system__project_id=project_id)

    return classifiers


@router.get("/{classifier_id}/", response=ClassifierRead)
def read_classifier(request, classifier_id: UUID):
    return get_object_or_404(Classifier, id=classifier_id)


@router.post("/", response=ClassifierRead)
def create_classifier(
    request,
    payload: ClassifierCreate,
):
    data = payload.model_dump()
    
    return Classifier.create(
        system_id=data["system"],
        classifier_type=data["type"],
        data=data["data"],
    )


@router.patch("/{classifier_id}/", response=ClassifierRead)
def update_classifier(
    request,
    classifier_id: UUID,
    payload: ClassifierUpdate,
):
    classifier = get_object_or_404(Classifier, id=classifier_id)
    
    if payload.data is None:
        return classifier

    schemas = get_classifier_schemas(classifier.type)
    update_schema = schemas["update"]
    
    try:
        validated_data = update_schema.model_validate(payload.data)
    except ValidationError as e:
        raise HttpError(
            422,
            str(e),
        )
    validated_data = update_schema.model_validate(payload.data)
    
    classifier.update(
        data=validated_data.model_dump(exclude_unset=True)
    )
    
    return classifier
    

@router.delete("/{classifier_id}/", response={204: None})
def delete_classifier(request, classifier_id: UUID):
    classifier = get_object_or_404(Classifier, id=classifier_id)
    classifier.delete()

    return 204, None
