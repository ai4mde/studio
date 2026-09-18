from ninja import Router

from metadata.api.routes.projects import router as project_router

router = Router()
router.add_router("/projects/", project_router)