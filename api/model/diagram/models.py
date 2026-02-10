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

    def _find_or_create_classifier(self, classifier: dict) -> Classifier:
        """
            Reuse a Classifier in this system if possible (search by id and by name + type).
            Otherwise create a new Classifier.
        """
        cls_id = str(classifier.get("id")) if classifier.get("id") else None
        data = classifier.get("data", {}) or {}

        # Search by id
        if cls_id:
            existing = Classifier.objects.filter(id=cls_id, system=self.system).first()
            if existing:
                return existing
            
        # Search by name and type
        name = data.get("name")
        ctype = data.get("type")
        if name and ctype:
            existing = Classifier.objects.filter(system=self.system, data__name=name, data__type=ctype).first()
            if existing:
                return existing
            
        # If not existing, create Classifier
        return Classifier.objects.create(project=self.system.project, system=self.system, data=data)

    def _find_or_create_relation(self, relation: dict) -> Relation:
        """
            Reuse a Relation in this system if possible (search by id and by source + target + type + multiplicity).
            Otherwise create a new Relation.
        """
        rel_id = str(relation.get("id")) if relation.get("id") else None
        data = relation.get("data", {}) or {}

        source_id = str(relation["source"])
        target_id = str(relation["target"])

        # Search by id
        if rel_id:
            existing = Relation.objects.filter(id=rel_id, system=self.system).first()
            if existing:
                return existing
            
        # Find source and target
        try:
            source = Classifier.objects.get(pk=source_id, system=self.system)
            target = Classifier.objects.get(pk=target_id, system=self.system)
        except Classifier.DoesNotExist:
            raise Classifier.DoesNotExist(f"Relation source and/or target not found in system: {source_id}, {target_id}")
        
        # Search by source, target, type
        r = Relation.objects.filter(system=self.system, source=source, target=target)
        rtype = data.get("type")
        if rtype is not None:
            r = r.filter(data__type=rtype)

        # Filter by multiplicity
        multiplicity = data.get("multiplicity") or {}
        m_source = multiplicity.get("source")
        m_target = multiplicity.get("target")
        if m_source is not None:
            r = r.filter(data__multiplicity__source=m_source)
        if m_target is not None:
            r = r.filter(data__multiplicity__target=m_target)

        existing = r.first()
        if existing:
            return existing
        
        # If not existing, create Relation
        return Relation.objects.create(system=self.system, source=source, target=target, data=data)

    def add_node_and_classifier(self, classifier: dict, id_map: dict | None = None):
        """
        Ensure classifier exists in the system. Create a node in this diagram pointing to classifier.
        Update id_map[old_id] -> system_id so relations can remap endpoints.
        """
        old_id = str(classifier.get('id') or "")
        cls_obj = self._find_or_create_classifier(classifier)

        if id_map is not None and old_id:
            id_map[old_id] = str(cls_obj.id)

        # One node per (diagram, classifier)
        Node.objects.get_or_create(
            diagram=self,
            cls=cls_obj,
            defaults={"data": {"position": {"x": 0, "y": 0}}}
        )

        return str(cls_obj.id)


    def add_edge_and_relation(self, relation: dict, id_map: dict | None = None):
        """
        Ensure relation exists in the system. Create an edge in this diagram pointing to relation.
        """
        # Make a shallow copy so we can safely tweak ids before handing to the helper
        rel_payload = dict(relation)

        if id_map:
            rel_payload['source'] = id_map.get(str(relation['source']), str(relation['source']))
            rel_payload['target'] = id_map.get(str(relation['target']), str(relation['target']))

        rel_obj = self._find_or_create_relation(rel_payload)

        # Prevent duplicate edges for the same relation in this diagram
        Edge.objects.get_or_create(
            diagram=self,
            rel=rel_obj,
            defaults={"data": {}}
        )

        return str(rel_obj.id)

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
