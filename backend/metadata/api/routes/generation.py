from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Router

from metadata.api.schemas.generation import GenerateAttribute, GenerateMethod
from metadata.models import Classifier
from metadata.services.generation import (
    generate_attribute as generate_attribute_service,
    generate_method as generate_method_service,
)


router = Router()


@router.post("/{classifier_id}/attribute/", response={200: str, 422: str})
def generate_attribute(
    request,
    classifier_id: UUID,
    payload: GenerateAttribute,
):
    classifier = get_object_or_404(Classifier, pk=classifier_id)

    result = generate_attribute_service(
        classifier=classifier,
        **payload.dict(),
    )

    if result is None:
        return 422, "Classifier is not a class"

    return result


@router.post("/{classifier_id}/method/", response={200: str, 422: str})
def generate_method(
    request,
    classifier_id: UUID,
    payload: GenerateMethod,
):
    classifier = get_object_or_404(Classifier, pk=classifier_id)

    result = generate_method_service(
        classifier=classifier,
        **payload.dict(),
    )

    if result is None:
        return 422, "Classifier is not a class"

    return result
