from ninja import Router

from .views import prototypes
from .views.pipeline import pipeline_router
from .views.interface_gen import interface_gen_router

generator_router = Router()
generator_router.add_router("prototypes", prototypes, tags=["generation"])
generator_router.add_router("pipeline", pipeline_router, tags=["pipeline"])
generator_router.add_router("interface-gen", interface_gen_router, tags=["interface-gen"])


__all__ = ["generator_router"]
