
from django.db import transaction

from diagram.models import Diagram, Node, Edge
from metadata.models import (
    Classifier,
    Attribute,
    Relation,
    Multiplicity,
    EndpointLabel,
)
from metadata.models.types import ClassifierType, RelationType


def _find_or_create_classifier(diagram, item):
    classifier = Classifier.objects.filter(
        pk=item["id"],
        system=diagram.system,
    ).first()

    if classifier:
        return classifier

    classifier = Classifier.objects.filter(
        system=diagram.system,
        type=ClassifierType.CLASS,
        classclassifier__name=item["name"],
    ).first()

    if classifier:
        return classifier

    classifier = Classifier.create(
        system_id=diagram.system_id,
        classifier_type=ClassifierType.CLASS,
        data={"name": item["name"]},
    )

    for attribute in item["attributes"]:
        Attribute.objects.create(
            uml_class=classifier.data,
            **attribute,
        )

    return classifier


def _find_or_create_relation(diagram, item, source, target):
    relation = Relation.objects.filter(
        pk=item["id"],
        system=diagram.system,
    ).first()

    if relation:
        return relation

    multiplicity = item["multiplicity"]

    relation = Relation.objects.filter(
        system=diagram.system,
        source=source,
        target=target,
        type=RelationType.ASSOCIATION,
        association__multiplicity__source_lower=multiplicity["source_lower"],
        association__multiplicity__source_upper=multiplicity["source_upper"],
        association__multiplicity__target_lower=multiplicity["target_lower"],
        association__multiplicity__target_upper=multiplicity["target_upper"],
    ).first()

    if relation:
        return relation

    multiplicity_obj = Multiplicity.objects.create(**multiplicity)
    labels = EndpointLabel.objects.create()

    return Relation.create(
        system_id=diagram.system_id,
        source_id=source.pk,
        target_id=target.pk,
        relation_type=RelationType.ASSOCIATION,
        data={
            "derived": item["derived"],
            "label": item["label"],
            "multiplicity_id": multiplicity_obj.pk,
            "labels_id": labels.pk,
        },
    )


@transaction.atomic
def add_to_diagram(
    diagram: Diagram,
    classifiers: list[dict],
    relations: list[dict],
) -> Diagram:
    id_map = {}

    for item in classifiers:
        if item["type"] != ClassifierType.CLASS:
            raise ValueError("Only class classifiers are supported.")

        if item["id"] in id_map:
            raise ValueError(f"Duplicate classifier ID: {item['id']}")

        classifier = _find_or_create_classifier(diagram, item)
        id_map[item["id"]] = classifier

        Node.objects.get_or_create(
            diagram=diagram,
            classifier=classifier,
        )

    for item in relations:
        if item["type"] != RelationType.ASSOCIATION:
            raise ValueError("Only associations are supported.")

        source = id_map.get(item["source"])
        target = id_map.get(item["target"])

        if source is None or target is None:
            raise ValueError("Relation references an unknown classifier.")

        relation = _find_or_create_relation(
            diagram, item, source, target
        )

        Edge.objects.get_or_create(
            diagram=diagram,
            relation=relation,
        )

    return diagram
