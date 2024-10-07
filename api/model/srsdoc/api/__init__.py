from ninja import Router

from .views import srsdocs

srsdoc_router = Router()
srsdoc_router.add_router("srsdocs", srsdocs, tags=["srs document"])


__all__ = ["srsdoc_router"]