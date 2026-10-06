from ninja import Router

from diagram.api.routes.diagram import router as diagram_router
from diagram.api.routes.node import router as node_router
from diagram.api.routes.edge import router as edge_router

router = Router()
router.add_router("/", node_router)
router.add_router("/", edge_router)
router.add_router("/", diagram_router)
