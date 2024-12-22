from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.api.v1.api import api_router
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CHATFRONT_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully!")
    logger.info("Checking critical settings...")
    logger.info(f"QDRANT_HOST: {settings.QDRANT_HOST}")
    logger.info(f"QDRANT_PORT: {settings.QDRANT_PORT}")
    logger.info(f"OPENAI_API_KEY exists: {bool(settings.OPENAI_API_KEY)}")

@app.get("/")
async def root():
    return {"message": "Welcome to AI4MDE Chat API"}

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"} 