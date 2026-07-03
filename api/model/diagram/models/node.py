import uuid

from django.db import models
from metadata.models import Classifier, ImportMixin
from diagram.models.diagram import Diagram

class Node(ImportMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    diagram = models.ForeignKey(Diagram, on_delete=models.CASCADE, related_name="nodes")
    cls = models.ForeignKey(Classifier, on_delete=models.CASCADE)
    data = models.JSONField()
