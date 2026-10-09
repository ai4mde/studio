from uuid import UUID

from django.db import transaction
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError
from pydantic import ValidationError

from diagram.api.schemas.edge import (
    EdgeCreate,
    EdgeRead,
    EdgeUpdate,
)
from diagram.models import (
    Diagram,
    Edge,
    Node,
)
from metadata.api.schemas.relation import get_relation_schemas
from metadata.models import Relation


router = Router()


@router.post("/{diagram_id}/edge/", response=EdgeRead)
@transaction.atomic
def create_edge(
    request,
    diagram_id: UUID,
    payload: EdgeCreate,
):
    data = payload.model_dump(exclude_unset=True)

    relation_data = data.pop("relation")
    source_id = data.pop("source_id")
    target_id = data.pop("target_id")

    diagram = get_object_or_404(
        Diagram,
        id=diagram_id,
    )

    source = get_object_or_404(
        Node,
        id=source_id,
        diagram=diagram,
    )

    target = get_object_or_404(
        Node,
        id=target_id,
        diagram=diagram,
    )

    relation = Relation.create(
        system_id=diagram.system.id,
        source_id=source.classifier.id,
        target_id=target.classifier.id,
        relation_type=relation_data["type"],
        data=relation_data["data"],
    )

    edge = Edge(
        diagram=diagram,
        relation=relation,
        **data,
    )

    edge.full_clean()
    edge.save()

    return edge


@router.patch("/edge/{edge_id}/", response=EdgeRead)
@transaction.atomic
def update_edge(
    request,
    edge_id: UUID,
    payload: EdgeUpdate,
):
    edge = get_object_or_404(
        Edge,
        id=edge_id,
    )

    data = payload.model_dump(exclude_unset=True)

    relation_data = data.pop(
        "relation",
        None,
    )

    if relation_data is not None:
        data_payload = relation_data.get("data")

        if data_payload is not None:
            schemas = get_relation_schemas(
                edge.relation.type,
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

            edge.relation.update(
                data=validated_data.model_dump(
                    exclude_unset=True,
                )
            )

    for field, value in data.items():
        setattr(edge, field, value)

    edge.full_clean()
    edge.save()

    return edge


@router.delete("/edge/{edge_id}/", response={204: None})
@transaction.atomic
def delete_edge(
    request,
    edge_id: UUID,
):
    edge = get_object_or_404(
        Edge,
        id=edge_id,
    )

    relation = edge.relation

    edge.delete()

    # Delete the relation when no other edge is using it
    if not relation.edges.exists():
        relation.delete()

    return 204, None