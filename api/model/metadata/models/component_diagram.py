from django.db import models

from .classifier import ClassifierDataModel


class System(ClassifierDataModel):
    name = models.CharField(max_length=255)


class Container(ClassifierDataModel):
    name = models.CharField(max_length=255)


class Component(ClassifierDataModel):
    name = models.CharField(max_length=255)