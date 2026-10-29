"""
FastAPI Application Entry Point (`app.main`).

Sets up:
- Automatic database table creation on startup
- Secure CORS middleware so our Next.js frontend (`localhost:3000`) can talk to FastAPI (`localhost:8000`)
- Static file serving for uploaded reference images (`/uploads/...`)
- API routers for Prompts (`/api/prompts`) and Videos (`/api/videos`)
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine
import app.models  # noqa: F401 - Ensure models are registered on Base.metadata
from app.routers import prompts, videos

# Create SQLite / PostgreSQL tables immediately on import as well as in lifespan
Base.metadata.create_all(bind=engine)

# Configure clean logging that never prints secret API keys
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("ai_video_studio")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create SQLite / PostgreSQL tables automatically if they don't exist yet
    Base.metadata.create_all(bind=engine)
    # Ensure local uploads directory exists
    _ = settings.storage_path
    logger.info(
        "AI Video Studio Backend started | Active Provider: %s (Demo Mode: %s)",
        settings.active_provider_name,
        settings.is_demo_mode,
    )
    yield


app = FastAPI(
    title="AI Short-Video Studio API",
    description="Backend API for Text-to-Video, Image-to-Video, Prompt Enhancement, and Job History.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount `/uploads` so uploaded reference images can be previewed in the UI
app.mount("/uploads", StaticFiles(directory=str(settings.storage_path)), name="uploads")

# Register API routers
app.include_router(prompts.router)
app.include_router(videos.router)


@app.get("/api/health", tags=["Health"])
def health_check():
    """Simple health check endpoint."""
    return {
        "status": "ok",
        "active_provider": settings.active_provider_name,
        "is_demo_mode": settings.is_demo_mode,
    }
