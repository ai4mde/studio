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
        # This will allow the Classifier to get the correct data model for the classifier type
        # If this name is already taken, you can add a new entry to the CLASSIFIER_DATA_FIELDS dictionary below to map the ClassifierType to the correct related name
        CLASSIFIER_DATA_FIELDS = {
            ClassifierType.INTERFACE: "interfaceclassifier",
            ClassifierType.SYSTEM: "systemclassifier",
            ClassifierType.CLASS: "classclassifier",
        }
        field = CLASSIFIER_DATA_FIELDS.get(self.type) or self.type
        
        try:
            return getattr(self, field)
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