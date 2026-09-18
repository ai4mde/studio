from ninja import Router

from diagram.api.routes.diagram import router as diagram_router

router = Router()
router.add_router("/diagram/", diagram_router)