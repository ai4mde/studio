from ninja import Router

from .views import diagrams

diagram_router = Router()
diagram_router.add_router("", diagrams, tags=["diagrams"])


__all__ = ["diagram_router"]
