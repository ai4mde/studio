from ninja import Router

from .views import pipelines, audio

prose_router = Router()
prose_router.add_router("/pipelines", pipelines, tags=["prose"])
prose_router.add_router("/audio", audio, tags=["prose"])


__all__ = ["prose_router"]
