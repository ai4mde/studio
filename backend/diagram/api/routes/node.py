from uuid import UUID

from django.db import transaction
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError
from pydantic import ValidationError

from diagram.api.schemas.node import (
    NodeCreate,
    NodeRead,
    NodeUpdate,
)
from diagram.models import Diagram, Node
from metadata.api.schemas.classifier import get_classifier_schemas
from metadata.models import Classifier


router = Router()



@router.post("/{diagram_id}/node/", response=NodeRead)
@transaction.atomic
def create_node(
    request,
    diagram_id: UUID,
    payload: NodeCreate,
):
    data = payload.model_dump(exclude_unset=True)

    classifier_data = data.pop("classifier")

    diagram = get_object_or_404(
        Diagram,
        id=diagram_id,
    )

    classifier = Classifier.create(
        system_id=diagram.system.id,
        classifier_type=classifier_data["type"],
        data=classifier_data["data"],
    )

    node = Node(
        diagram=diagram,
        classifier=classifier,
        **data,
    )

    node.full_clean()
    node.save()

    return node


@router.patch("/node/{node_id}/", response=NodeRead)
@transaction.atomic
def update_node(
    request,
    node_id: UUID,
    payload: NodeUpdate,
):
    node = get_object_or_404(
        Node,
        id=node_id,
    )

    data = payload.model_dump(exclude_unset=True)

    classifier_data = data.pop(
        "classifier",
        None,
    )

    classifier_id = data.pop("classifier_id", None)

    if classifier_id is not None and classifier_id != node.classifier_id:
        new_classifier = get_object_or_404(
            Classifier,
            id=classifier_id,
            system=node.diagram.system,  # only classifiers from the same system
        )

        if new_classifier.type != node.classifier.type:
            raise HttpError(422, "The classifier must have the same type as the node")

        # Node has a unique (diagram, classifier) constraint
        if new_classifier.nodes.filter(diagram=node.diagram).exists():
            raise HttpError(409, "This classifier is already used in this diagram")

        old_classifier = node.classifier
        node.classifier = new_classifier
        node.save(update_fields=["classifier"])

        # Same cleanup as delete_node: drop the old classifier when nothing uses it
        if not old_classifier.nodes.exists():
            old_classifier.delete()

    if classifier_data is not None:
        data_payload = classifier_data.get("data")

        if data_payload is not None:
            schemas = get_classifier_schemas(
                node.classifier.type,
            )

            update_schema = schemas["update"]

            try:
                validated_data = update_schema.model_validate(
                    data_payload,
                )
            except ValidationError as e:
                raise HttpError(
                    422,
                    str(e),
                )

            node.classifier.update(
                data=validated_data.model_dump(
                    exclude_unset=True,
                )
            )

    for field, value in data.items():
        setattr(node, field, value)

    node.full_clean()
    node.save()

    return node


@router.delete("/node/{node_id}/", response={204: None})
@transaction.atomic
def delete_node(
    request,
    node_id: UUID,
):
    node = get_object_or_404(
        Node,
        id=node_id,
    )

    classifier = node.classifier

    node.delete()

    # Delete the classifier when no other node is using it
    if not classifier.nodes.exists():
        classifier.delete()

    return 204, None