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

    def delete(self, *args, **kwargs):
        nodes = self.nodes.all()
        edges = self.edges.all()

        cls = set(nodes.values_list('cls', flat=True))
        rel = set(edges.values_list('rel', flat=True))
        nodes.delete()
        edges.delete()

        for cls_id in cls:
            if not Node.objects.filter(cls_id=cls_id).exists():
                Classifier.objects.filter(id=cls_id).delete()

        for rel_id in rel:
            if not Edge.objects.filter(rel_id=rel_id).exists():
                Relation.objects.filter(id=rel_id).delete()

        super().delete(*args, **kwargs)


class Node(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    diagram = models.ForeignKey(Diagram, on_delete=models.CASCADE, related_name="nodes")
    cls = models.ForeignKey(Classifier, on_delete=models.CASCADE)
    data = models.JSONField()

    def delete(self, *args, **kwargs):
        classifier = self.cls
        super().delete(*args, **kwargs)
        if not Node.objects.filter(cls=classifier).exists():
            classifier.delete()


class Edge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    diagram = models.ForeignKey(Diagram, on_delete=models.CASCADE, related_name="edges")
    rel = models.ForeignKey(Relation, on_delete=models.CASCADE)
    data = models.JSONField()

    def delete(self, *args, **kwargs):
        relation = self.rel
        super().delete(*args, **kwargs)
        if not Edge.objects.filter(rel=relation).exists():
            relation.delete()

    @property
    def source(self):
        return self.diagram.nodes.filter(cls=self.rel.source).first()

    @property
    def target(self):
        return self.diagram.nodes.filter(cls=self.rel.target).first()
