from ninja import Router

from metadata.api.routes.project import router as project_router
from metadata.api.routes.system import router as system_router
from metadata.api.routes.classifier import router as classifier_router
from metadata.api.routes.interface import router as interface_router

router = Router()
router.add_router("/projects/", project_router)
router.add_router("/systems/", system_router)
router.add_router("/classifiers/", classifier_router)
router.add_router("/interfaces/", interface_router)