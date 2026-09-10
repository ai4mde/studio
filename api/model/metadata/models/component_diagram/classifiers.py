from django.db import models

from ..classifier import ClassifierDataModel


class SystemComponent(ClassifierDataModel):         # Normally System, however, a class with that name already exists
    name = models.CharField(max_length=255)


class Container(ClassifierDataModel):
    name = models.CharField(max_length=255)


class Component(ClassifierDataModel):
    name = models.CharField(max_length=255)