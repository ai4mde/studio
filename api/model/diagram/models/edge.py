import uuid

from django.db import models
from metadata.models import Relation, ImportMixin

class Edge(ImportMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    diagram = models.ForeignKey("diagram.Diagram", on_delete=models.CASCADE, related_name="edges")
    rel = models.ForeignKey(Relation, on_delete=models.CASCADE)
    data = models.JSONField()

    @property
    def source(self):
        return self.diagram.nodes.filter(cls=self.rel.source).first()

    @source.setter
    def source(self, value):
        self.rel.source = value
        self.rel.save()

    @property
    def target(self):
        return self.diagram.nodes.filter(cls=self.rel.target).first()

    @target.setter
    def target(self, value):
        self.rel.target = value
        self.rel.save()
