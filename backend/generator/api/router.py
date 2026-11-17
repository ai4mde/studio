from ninja import Router

from generator.api.routes.prototype import router as prototype_router

router = Router()
router.add_router("/prototypes/", prototype_router)