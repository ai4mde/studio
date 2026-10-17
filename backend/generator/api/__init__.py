from ninja import Router

from .views import prototypes

generator_router = Router()
generator_router.add_router("prototypes", prototypes, tags=["generation"])


__all__ = ["generator_router"]
