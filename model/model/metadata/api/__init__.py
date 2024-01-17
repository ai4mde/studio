from ninja import Router
from .views import projects, systems

metadata_router = Router()
metadata_router.add_router('projects', projects, tags=['management'])
metadata_router.add_router('projects/{uuid:project}/systems', systems, tags=['management'])

__all__ = [
    'metadata_router'
]