from django.db import models


class DiagramType(models.TextChoices):
    classes = "class"
    usecase = "usecase"
    activity = "activity"
    component = "component"
