from ninja import Router

from .views import requirements

requirement_router = Router()
requirement_router.add_router("requirements", requirements, tags=["functional requirements"])


__all__ = ["requirement_router"]