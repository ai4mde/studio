from ninja import Router

from metadata.api.routes.projects import router as project_router
from metadata.api.routes.systems import router as system_router

router = Router()
router.add_router("/projects/", project_router)
router.add_router("/systems/", system_router)