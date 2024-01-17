from ninja import Router
from .views import projects, systems

metadata_router = Router()
metadata_router.add_router('projects', projects)
metadata_router.add_router('projects/{uuid:project}/systems', systems)

__all__ = [
    'metadata_router'
]