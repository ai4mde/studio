from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Router

from metadata.api.schemas.classifier import ClassifierRead
from metadata.api.schemas.class_members import (
    AttributeCreate,
    AttributeRead,
    AttributeUpdate,
    OperationCreate,
    OperationRead,
    OperationUpdate,
)
from metadata.models import Attribute, ClassClassifier, Classifier, Enum, Operation


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

# ============================================================
# Helpers
# ============================================================
def get_class(classifier_id: UUID) -> ClassClassifier:
    # 404 when the classifier doesn't exist or isn't a class
    return get_object_or_404(ClassClassifier, pk=classifier_id)


def get_enum(uml_class: ClassClassifier, enum_id: UUID | None) -> Enum | None:
    if enum_id is None:
        return None

    # Only enums from the same system as the class
    return get_object_or_404(
        Enum,
        pk=enum_id,
        classifier__system_id=uml_class.classifier.system_id,
    )

# ============================================================
# Attributes
# ============================================================
@router.get("/{classifier_id}/attributes/", response=list[AttributeRead])
def list_attributes(request, classifier_id: UUID):
    return get_class(classifier_id).attributes.all()


@router.post("/{classifier_id}/attributes/", response=AttributeRead)
def create_attribute(request, classifier_id: UUID, payload: AttributeCreate):
    uml_class = get_class(classifier_id)
    data = payload.model_dump()
    enum = get_enum(uml_class, data.pop("enum_id"))

    attribute = Attribute(uml_class=uml_class, enum=enum, **data)
    attribute.full_clean()
    attribute.save()

    return attribute

@router.patch("/attributes/{attribute_id}/", response=AttributeRead)
def update_attribute(request, attribute_id: UUID, payload: AttributeUpdate):
    attribute = get_object_or_404(Attribute, id=attribute_id)
    data = payload.model_dump(exclude_unset=True)

    if "enum_id" in data:
        attribute.enum = get_enum(attribute.uml_class, data.pop("enum_id"))

    for field, value in data.items():
        setattr(attribute, field, value)

    attribute.full_clean()
    attribute.save()

    return attribute

@router.delete("/attributes/{attribute_id}/", response={204: None})
def delete_attribute(request, attribute_id: UUID):
    get_object_or_404(Attribute, id=attribute_id).delete()
    return 204, None

# ============================================================
# Operations
# ============================================================
@router.get("/{classifier_id}/operations/", response=list[OperationRead])
def list_operations(request, classifier_id: UUID):
    return get_class(classifier_id).methods.all()

@router.post("/{classifier_id}/operations/", response=OperationRead)
def create_operation(request, classifier_id: UUID, payload: OperationCreate):
    operation = Operation(uml_class=get_class(classifier_id), **payload.model_dump())
    operation.full_clean()
    operation.save()

    return operation

@router.patch("/operations/{operation_id}/", response=OperationRead)
def update_operation(request, operation_id: UUID, payload: OperationUpdate):
    operation = get_object_or_404(Operation, id=operation_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(operation, field, value)

    operation.full_clean()
    operation.save()

    return operation

@router.delete("/operations/{operation_id}/", response={204: None})
def delete_operation(request, operation_id: UUID):
    get_object_or_404(Operation, id=operation_id).delete()
    return 204, None