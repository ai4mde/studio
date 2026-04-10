from ninja import Router

from .views import prototypes
from .views.pipeline import pipeline_router

generator_router = Router()
generator_router.add_router("prototypes", prototypes, tags=["generation"])
generator_router.add_router("pipeline", pipeline_router, tags=["pipeline"])


__all__ = ["generator_router"]
