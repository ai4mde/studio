from ninja import Router

from .views import projects, systems, interfaces, releases
from metadata.specification import ClassifierSchema, RelationSchema

metadata_router = Router()
metadata_router.add_router("projects", projects, tags=["management"])
metadata_router.add_router("systems", systems, tags=["management"])
metadata_router.add_router("releases", releases, tags=["management"])
metadata_router.add_router("interfaces", interfaces, tags=["interfaces"])


@metadata_router.get("", auth=None)
def metadata_index(request):
    return {
        "resources": {
            "projects": "/api/v1/metadata/projects/",
            "systems": "/api/v1/metadata/systems/",
            "releases": "/api/v1/metadata/releases/",
            "interfaces": "/api/v1/metadata/interfaces/",
            "classifier_schema": "/api/v1/metadata/classifier.schema.json",
            "relation_schema": "/api/v1/metadata/relation.schema.json",
        }
    }


@metadata_router.get("/classifier.schema.json")
def classifier_schema(request):
    return ClassifierSchema.model_json_schema()


@metadata_router.get("/relation.schema.json")
def relation_schema(request):
    return RelationSchema.model_json_schema()


__all__ = ["metadata_router"]
