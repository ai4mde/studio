from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.routers.interview import router as interview_router
from app.api.v1.routers.document import router as document_router
from app.api.v1.routers.review import router as review_router
from app.api.v1.routers.converter import router as converter_router
from app.api.v1.routers.modification import router as modification_router
from app.api.v1.routers.diagram import router as diagram_router

api_router = APIRouter()

# Core routes
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])

# Agent routes
api_router.include_router(interview_router, prefix="/agents")
api_router.include_router(document_router, prefix="/agents")
api_router.include_router(review_router, prefix="/agents")
api_router.include_router(converter_router, prefix="/agents")
api_router.include_router(modification_router, prefix="/agents")
api_router.include_router(diagram_router, prefix="/agents")

@api_router.get("/health-check")
def health_check():
    return {"status": "ok"} 