from ninja import Router
from django.http import HttpRequest

from metadata.api.schemas import MetaRelationsSchema
from metadata.specification import RelationSchema

from metadata.models import System, Relation

relations = Router()


@relations.get("/", response=MetaRelationsSchema)
def get_relations(request: HttpRequest):
    if not request.resolver_match:
        return 500, "Resolver match not found"

    system_id = request.resolver_match.kwargs.get("system_id")
    system = System.objects.get(id=system_id)

    if not system:
        return 404, "System not found"

    return {
        "relations": system.relations.all(),
    }


@relations.get("/{relation_id}/", response=RelationSchema)
def read_relation(request: HttpRequest, relation_id: str):
    if not request.resolver_match:
        return 500, "Resolver match not found"

    system_id = request.resolver_match.kwargs.get("system_id")
    system = System.objects.get(id=system_id)

    if not system:
        return 404, "System not found"
    
    try:
        relation = system.relations.get(id=relation_id)
    except Relation.DoesNotExist:
        return 404, "Relation not found"

    return { 
        "id": relation.id,
        "data": relation.data,
    }


classifier_relations = Router()

@classifier_relations.get("/", response=MetaRelationsSchema)
def read_classifier_relations(request: HttpRequest):
    if not request.resolver_match:
        return 500, "Resolver match not found"

    system_id = request.resolver_match.kwargs.get("system_id")
    system = System.objects.get(id=system_id)

    if not system:
        return 404, "System not found"
    
    associations = system.relations.filter(data__type='association')
    generalizations = system.relations.filter(data__type='generalization')
    compositions = system.relations.filter(data__type='composition')
    dependencies = system.relations.filter(data__type='dependency')

    classifier_relations = associations | generalizations | compositions | dependencies

    return {
        "relations": classifier_relations.order_by('id')
    }

__all__ = [
    "relations",
    "classifier_relations"
]
