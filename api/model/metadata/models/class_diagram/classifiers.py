from django.db import models

from ..classifier import ClassifierDataModel
from ..fields import PythonField
from ..types import DataType


class Class(ClassifierDataModel):
    name = models.CharField(max_length=255)


class Enum(models.Model):
    name = models.CharField(max_length=255)


class EnumLiteral(models.Model):
    enum = models.ForeignKey(
        Enum,
        on_delete=models.CASCADE,
        related_name="literals",
    )
    value = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ["order"]


class Attribute(models.Model):
    uml_class = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name="attributes",
    )
    name = models.CharField(max_length=255)
    type = models.CharField(
      max_length=16,
      choices=DataType.choices,  
    )
    derived = models.BooleanField(default=False)
    enum = models.ForeignKey(
        Enum,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attributes",
    )
    description = models.TextField(
        null=True,
        blank=True,
    )
    body = PythonField(
        null=True,
        blank=True,
    )


class Operation(models.Model):
    uml_class = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name="methods",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(
        null=True,
        blank=True,
    )
    type = models.CharField(
        max_length=16,
        choices=DataType.choices,
    )
    body = PythonField(
        null=True,
        blank=True,
    )


class Interface(ClassifierDataModel):
    name = models.CharField(max_length=255)


class Signal(ClassifierDataModel):
    name = models.CharField(max_length=255)
