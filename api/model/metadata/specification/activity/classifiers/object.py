from uuid import UUID
from typing import Literal, Optional
from pydantic import BaseModel, model_validator
from django.core.exceptions import ObjectDoesNotExist

from metadata.models import Classifier
from metadata.specification.kernel import NamedElement, NamespacedElement

class Object(NamedElement, NamespacedElement, BaseModel):
    type: Literal["object"] = "object"
    role: Literal["object"] = "object"
    cls: UUID
    clsName: Optional[str] = None
    state: Optional[str] = None

    @model_validator(mode="after")
    def set_cls_name(self):
        if not self.cls:
            return self

        try:
            classifier = Classifier.objects.get(pk=self.cls)
            # adjust depending on your Classifier schema:
            self.clsName = (
                getattr(classifier, "name", None)
                or getattr(classifier, "key", None)
                or classifier.data.get("name")
                or "Unknown class"
            )

        except ObjectDoesNotExist:
            self.clsName = "Unknown class"

        return self
    
ObjectClassifier = Object

__all__ = ["ObjectClassifier"]
