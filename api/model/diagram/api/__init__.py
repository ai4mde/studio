from ninja import Router, Schema

from metadata.specification import Classifier, Relation

from .views import diagrams
from .views import c4gen

diagram_router = Router()
diagram_router.add_router("", diagrams, tags=["diagrams"])
diagram_router.add_router("", c4gen, tags=["diagrams", "c4gen"])


class SimpleNodeSchema(Schema):
    data: Classifier


@diagram_router.get("/specification/node.schema.json", tags=["specification"])
def get_node_schema(request):
    return SimpleNodeSchema.model_json_schema()


class SimpleEdgeSchema(Schema):
    data: Relation


@diagram_router.get("/specification/edge.schema.json", tags=["specification"])
def get_edge_schema(request):
    return SimpleEdgeSchema.model_json_schema()


__all__ = ["diagram_router"]
