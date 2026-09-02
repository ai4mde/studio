import uuid

from django.db import models

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
    )
    
    @property
    def data(self):
        # When creating a new ClassifierType make sure the reverse relation related name is the same as the ClassifierType value
        try:
            return getattr(self, self.type)
        except AttributeError:
            return None


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