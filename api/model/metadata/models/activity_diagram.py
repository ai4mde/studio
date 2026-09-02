from django.core.exceptions import ValidationError
from django.db import models

from .classifier import ClassifierDataModel
from .fields import CronField, PythonField
from .types import ActivityScope, ClassifierType
from .utils import ValidationMixin

class Swimlane(ValidationMixin, ClassifierDataModel):
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    actor = models.ForeignKey(
        "Actor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="swimlanes",
    )
    component = models.ForeignKey(
        "Classifier",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="component_swimlanes",
    )

    def clean(self):
        super().clean()
        
        self.mutually_exclusive(
            "actor",
            "component",
        )
        
        self.require_related_type(
            "component",
            {
                ClassifierType.SYSTEM,
                ClassifierType.CONTAINER,
                ClassifierType.COMPONENT,
            },
            message=(
                "Component must reference a System, "
                "Container or Component."
            ),
        )
        
        if not self._state.adding:
            self.forbid_if(
                self.children.exists(),
                "actor",
                "A swimlane with children cannot have an actor.",
            )

        if self.parent and self.parent.actor:
            raise ValidationError({
                "parent":
                    "Cannot add a child to a swimlane that has an actor."
            })


class Action(ValidationMixin, ClassifierDataModel):
    name = models.CharField(max_length=255)
    is_automatic = models.BooleanField(default=False)
    custom_code = PythonField(
        blank=True,
        null=True,
    )
    swimlane = models.ForeignKey(                       # TODO THIS SHOULD NOT DECIDE NODE POSITION, THIS SHOULD BE HANDLED IN VISUAL NODE ATTRIBUTES
        Swimlane,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actions",
    )

    def clean(self):
        super().clean()
        
        self.forbid_if(
            not self.is_automatic,
            "custom_code",
            "A non-automatic action cannot have custom code.",
        )


class Object(ClassifierDataModel):
    name = models.CharField(max_length=255)
    uml_class = models.ForeignKey(
        "Class",
        on_delete=models.SET_NULL,                     # An Object node should not be valid without a class attached, however,
        null=True,                                     # We want the user to be able to re-attach a new class if the old one is deleted
        blank=True,                                    # So this should be able to exist in this state
        related_name="objects",
    )
    state = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )


class Event(ClassifierDataModel):
    name = models.CharField(max_length=255)
    signal = models.ForeignKey(
        "Signal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )


# Decision, Fork, Join and Merge do not have any additional data
# If this chagnes in the future add them here

class Final(ClassifierDataModel):
    activity_scope = models.CharField(
        max_length=16,
        choices=ActivityScope.choices,
        default=ActivityScope.ACTIVITY,
    )


class Initial(ClassifierDataModel):
    scheduled = models.BooleanField(default=False)
    schedule = CronField(
        blank=True,
        default="",
    )
