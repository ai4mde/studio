from uuid import UUID
from typing import Literal, Optional
from pydantic import BaseModel, model_validator
from django.core.exceptions import ObjectDoesNotExist

from metadata.models import Classifier
from metadata.specification.kernel import NamedElement, NamespacedElement

class Event(NamedElement, NamespacedElement, BaseModel):
    type: Literal["event"] = "event"
    role: Literal["event"] = "event"
    signal: UUID
    signalName: Optional[str] = None

    @model_validator(mode="after")
    def set_signal_name(self):
        if not self.signal:
            return self

        try:
            classifier = Classifier.objects.get(pk=self.signal)

            self.signalName = (
                getattr(classifier, "name", None)
                or getattr(classifier, "key", None)
                or classifier.data.get("name")
                or "Unknown signal"
            )

        except ObjectDoesNotExist:
            self.signalName = "Unknown signal"

        return self
    
EventClassifier = Event

__all__ = ["EventClassifier"]