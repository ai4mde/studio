import uuid

from django.db import models
from metadata.models import Classifier, Relation, System


class Diagram(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    type = models.CharField()
    name = models.CharField()
    description = models.TextField(blank=True)
    system = models.ForeignKey(
        System, on_delete=models.CASCADE, related_name="diagrams"
    )


class Node(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    diagram = models.ForeignKey(Diagram, on_delete=models.CASCADE, related_name="nodes")
    cls = models.ForeignKey(Classifier, on_delete=models.RESTRICT)
    data = models.JSONField()


class Edge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    diagram = models.ForeignKey(Diagram, on_delete=models.CASCADE, related_name="edges")
    rel = models.ForeignKey(Relation, on_delete=models.RESTRICT)
    data = models.JSONField()

    @property
    def source(self):
        return self.diagram.nodes.filter(cls=self.rel.source).first()

    @property
    def target(self):
        return self.diagram.nodes.filter(cls=self.rel.target).first()
