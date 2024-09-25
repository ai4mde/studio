from ninja import Router

from .views import projects, systems, interfaces
from metadata.specification import ClassifierSchema, RelationSchema

metadata_router = Router()
metadata_router.add_router("projects", projects, tags=["management"])
metadata_router.add_router("systems", systems, tags=["management"])
metadata_router.add_router("interfaces", interfaces, tags=["management"])


@metadata_router.get("/classifier.schema.json")
def classifier_schema(request):
    return ClassifierSchema.model_json_schema()


@metadata_router.get("/relation.schema.json")
def relation_schema(request):
    return RelationSchema.model_json_schema()


__all__ = ["metadata_router"]
