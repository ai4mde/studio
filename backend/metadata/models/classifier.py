from typing import Any
import uuid

from django.db import models

from .general import System
from .typed_data_model import TypedDataModel
from .types import ClassifierType


class Classifier(TypedDataModel):
    data_type_enum = ClassifierType
    data_parent_field = "classifier"

    data_model_aliases = {
        ClassifierType.CLASS: "ClassClassifier",
        ClassifierType.INTERFACE: "InterfaceClassifier",
        ClassifierType.SYSTEM: "SystemClassifier",
    }

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
    )

    system = models.ForeignKey(
        System,
        on_delete=models.CASCADE,
        related_name="classifiers",
    )

    type = models.CharField(
        max_length=32,
        choices=ClassifierType.choices,
        editable=False,
    )

    @classmethod
    def create(
        cls,
        *,
        system_id,
        classifier_type,
        data: dict[str, Any],
    ):
        return cls.create_typed(
            data_type=classifier_type,
            data=data,
            system_id=system_id,
        )


# Inherit from this class when making a new node type. Make sure to use the same class name as defined in ClassifierType
class ClassifierDataModel(models.Model):
    classifier = models.OneToOneField(
        Classifier,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="%(class)s",
    )

    class Meta:
        abstract = True