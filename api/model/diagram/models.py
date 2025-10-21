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
        old_id = str(classifier.get('id')) if classifier.get('id') else None

        # If the original classifier was already added to this diagram, reuse it
        # Check via id
        if old_id:
            existing_cls_id = (
                Node.objects
                .filter(diagram=self, data__origin_id=old_id)
                .values_list('cls_id', flat=True)
                .first()
            )
            if existing_cls_id:
                if id_map is not None:
                    id_map[old_id] = str(existing_cls_id)
                return str(existing_cls_id)
            
        # Check via name + type
        name = classifier.get('data', {}).get('name')
        ctype = classifier.get('data', {}).get('type')
        if name and ctype:
            existing_by_semantics = (
                Node.objects
                .filter(
                    diagram=self,
                    cls__data__name=name,
                    cls__data__type=ctype,
                )
                .values_list('cls_id', flat=True)
                .first()
            )
            if existing_by_semantics:
                if id_map is not None and old_id:
                    id_map[old_id] = str(existing_by_semantics)
                return str(existing_by_semantics)
        
        # Otherwise clone a new classifier
        cls = Classifier.objects.create(
            system = self.system,
            data = classifier['data']
        )

        node_data = {"position": {"x": 0, "y": 0}}
        # Save old-new id mapping
        if id_map is not None and old_id:
            id_map[old_id] = old_id

        Node.objects.create(
            diagram = self,
            cls = cls,
            data = node_data,
        )

        if id_map is not None and old_id:
            id_map[old_id] = str(cls.id)

        return str(cls.id)


    def add_edge_and_relation(self, relation: dict, id_map: dict | None = None):
        # Remap old ids of classifiers to new ones
        existing_rel_id = str(relation.get('id')) if relation.get('id') else None
        source_old = str(relation['source'])
        target_old = str(relation['target'])
        source_new = id_map.get(source_old, source_old) if id_map else source_old
        target_new = id_map.get(target_old, target_old) if id_map else target_old

        # If this relation was already added to the diagram, skip
        if existing_rel_id and Edge.objects.filter(diagram=self, data__origin_id=existing_rel_id).exists():
                return
            
        # Guard against duplicates by checking nodes and relation type/multiplicity
        rel_type = relation['data'].get('type')
        mult_source = relation['data'].get('multiplicity', {}).get('source')
        mult_target = relation['data'].get('multiplicity', {}).get('target')

        # Find an existing endge that connects the same nodes and has the same type
        exists_same = (
            Edge.objects
            .select_related('rel')
            .filter(
                diagram=self,
                rel__source_id=source_new,
                rel__target_id=target_new,
                rel__data__type=rel_type,
                rel__data__multiplicity__source=mult_source,
                rel__data__multiplicity__target=mult_target,
            )
            .exists()
        )
        if exists_same:
            return

        # Create new relation
        rel = Relation.objects.create(
            system = self.system,
            source = Classifier.objects.get(pk=source_new),
            target = Classifier.objects.get(pk=target_new),
            data = relation['data']
        )

        edge_data = {}
        if existing_rel_id:
            edge_data['origin_id'] = existing_rel_id

        Edge.objects.create(
            diagram = self,
            rel = rel,
            data = edge_data,
        )

        return str(rel.id)


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
