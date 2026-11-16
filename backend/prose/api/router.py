from ninja import Router

from prose.api.routes.pipeline import router as pipeline_router

router = Router()
router.add_router("/pipeline", pipeline_router, tags=["prose"])
