from ninja import Router

from .views import pipelines

prose_router = Router()
prose_router.add_router("", pipelines, tags=["prose"])


__all__ = ["prose_router"]
