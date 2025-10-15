import uuid

from django.db import models
from metadata.models import Classifier, Relation, System
import networkx as nx


class Diagram(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    type = models.CharField()
    name = models.CharField()
    description = models.TextField(blank=True)
    system = models.ForeignKey(
        System, on_delete=models.CASCADE, related_name="diagrams"
    )


    def add_node_and_classifier(self, classifier: dict, id_map: dict | None = None):
        old_id = classifier.get('id')
        cls = Classifier.objects.create(
            system = self.system,
            data = classifier['data']
        )

        # Save old-new id mapping
        if id_map is not None and old_id:
            id_map[old_id] = cls.id

        Node.objects.create(
            diagram = self,
            cls = cls,
            data = {
            "position": {
              "x": 0,
              "y": 0
            }
          },
        )

        return cls.id


    def add_edge_and_relation(self, relation: dict, id_map: dict | None = None):
        # Remap old ids of classifiers to new ones
        source_old = relation['source']
        target_old = relation['target']
        source_new = id_map.get(source_old, source_old) if id_map else source_old
        target_new = id_map.get(target_old, target_old) if id_map else target_old

        rel = Relation.objects.create(
            system = self.system,
            source = Classifier.objects.get(pk=source_new),
            target = Classifier.objects.get(pk=target_new),
            data = relation['data']
        )

        Edge.objects.create(
            diagram = self,
            rel = rel,
            data = {}
        )
        
        return rel.id


    def auto_layout(self):
        graph = nx.Graph()
        
        for node in self.nodes.all():
            graph.add_node(node.id)
        for edge in self.edges.all():
            graph.add_edge(edge.source.id, edge.target.id)

        # We use the networkx spring_layout algorithm for autolayouting a diagram
        # scale=500 seems to do the job, but can be adjusted as needed
        positions = nx.spring_layout(G=graph, scale=500)

        for node in self.nodes.all():
            x, y = positions[node.id]
            node.data["position"]["x"], node.data["position"]["y"] = int(round(x)), int(round(y))
            node.save()

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

class Edge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    diagram = models.ForeignKey(Diagram, on_delete=models.CASCADE, related_name="edges")
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
