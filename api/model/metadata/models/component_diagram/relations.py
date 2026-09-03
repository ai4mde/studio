from django.db import models

from ..relation import RelationDataModel


class Interface(RelationDataModel):
    required = models.ForeignKey(
        "Interface",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="required_interfaces",
    )
    provided = models.ForeignKey(
        "Interface",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="provided_interfaces",
    )
