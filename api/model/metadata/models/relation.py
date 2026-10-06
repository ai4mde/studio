from typing import Any

from django.db import models

from .classifier import Classifier
from .general import System
from .typed_data_model import TypedDataModel
from .types import RelationType


class Relation(TypedDataModel):
    data_type_enum = RelationType
    data_parent_field = "relation"

    data_model_aliases = {
        RelationType.INTERFACE: "InterfaceRelation",
    }

    system = models.ForeignKey(
        System,
        on_delete=models.CASCADE,
        related_name="relations",
    )

    source = models.ForeignKey(
        Classifier,
        related_name="relations_to",
        on_delete=models.CASCADE,
    )

    target = models.ForeignKey(
        Classifier,
        related_name="relations_from",
        on_delete=models.CASCADE,
    )

    type = models.CharField(
        max_length=32,
        choices=RelationType.choices,
        editable=False,
    )

    @classmethod
    def create(
        cls,
        *,
        system_id,
        source_id,
        target_id,
        relation_type,
        data: dict[str, Any],
    ):
        return cls.create_typed(
            data_type=relation_type,
            data=data,
            system_id=system_id,
            source_id=source_id,
            target_id=target_id,
        )


class RelationDataModel(models.Model):
    relation = models.OneToOneField(
        Relation,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="%(class)s",
    )

    class Meta:
        abstract = True