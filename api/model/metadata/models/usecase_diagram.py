from django.db import models

from .classifier import ClassifierDataModel


class SystemBoundary(ClassifierDataModel):
    name = models.CharField(max_length=255)
    system = models.ForeignKey(
        "System",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="system_boundaries",
    )


class Actor(ClassifierDataModel):
    name = models.CharField(max_length=255)
    boundary = models.ForeignKey(
        SystemBoundary,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actors",
    )


class Usecase(ClassifierDataModel):
    name = models.CharField(max_length=255)
    boundary = models.ForeignKey(
        SystemBoundary,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usecases",
    )
    