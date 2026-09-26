from typing import Any, Type
import uuid

from django.apps import apps
from django.db import models, transaction

from .general import System
from .types import ClassifierType


class Classifier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
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
    
    @property
    def data(self):
        data_model = self.get_data_model(self.type)
        
        if data_model is None:
            return None

        field = data_model._meta.model_name
        
        if field is None:
            return None

        try:
            return getattr(self, field)
        except AttributeError:
            return None

    @classmethod
    def get_data_model(cls, classifier_type) -> Type[models.Model] | None:
        classifier_type = ClassifierType(classifier_type)

        aliases = {
            ClassifierType.CLASS: "ClassClassifier",
            ClassifierType.INTERFACE: "InterfaceClassifier",
            ClassifierType.SYSTEM: "SystemClassifier",
        }

        model_name = aliases.get(
            classifier_type,
            "".join(
                part.title()
                for part in classifier_type.name.split("_")
            ),
        )

        try:
            return apps.get_model("metadata", model_name)
        except LookupError:
            return None

    @staticmethod
    def normalize_data(model, data) -> dict[str, Any]:
        normalized: dict[str, Any] = {}

        for name, value in data.items():
            field = next(
                (
                    field
                    for field in model._meta.fields
                    if field.name == name or field.attname == name
                ),
                None,
            )

            if field is None:
                normalized[name] = value
            elif isinstance(field, models.ForeignKey):
                normalized[field.attname] = value
            else:
                normalized[field.name] = value

        return normalized

    @classmethod
    @transaction.atomic
    def create(cls, *, system_id, classifier_type, data):
        classifier_type = ClassifierType(classifier_type)

        classifier = cls.objects.create(
            system_id=system_id,
            type=classifier_type,
        )
        
        data_model = cls.get_data_model(classifier_type)
        
        if data_model is not None:
            data = cls.normalize_data(data_model, data)
            classifier_data = data_model(
                classifier=classifier,
                **data,
            )
            classifier_data.full_clean()
            classifier_data.save()

        return classifier

    @transaction.atomic
    def update(self, *, data):
        classifier_data = self.data
        
        if classifier_data is None:
            return self

        data = self.normalize_data(type(classifier_data), data)

        for field, value in data.items():
            setattr(classifier_data, field, value)
    
        classifier_data.full_clean()
        classifier_data.save()

        return self


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