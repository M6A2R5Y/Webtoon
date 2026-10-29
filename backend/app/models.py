"""
SQLAlchemy Database Models for storing Video Generation Jobs and User History.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VideoJob(Base):
    """
    Stores every video generation request, its settings, cost estimate,
    real-time status, and final video URL.
    """

    __tablename__ = "video_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    client_id = Column(String(64), nullable=False, index=True, default="anonymous")

    # Mode: "text_to_video" or "image_to_video"
    generation_type = Column(String(32), nullable=False, default="text_to_video")

    # Prompts & Style
    prompt = Column(Text, nullable=False)
    enhanced_prompt = Column(Text, nullable=True)
    style_preset = Column(String(50), nullable=False, default="cinematic")

    # Video Parameters
    aspect_ratio = Column(String(16), nullable=False, default="9:16")  # "9:16", "16:9", "1:1"
    duration_seconds = Column(Integer, nullable=False, default=5)      # 5 or 10

    # Input image reference (for image-to-video)
    source_image_url = Column(String(512), nullable=True)

    # Provider & Cost tracking
    provider_name = Column(String(32), nullable=False, default="demo")
    provider_job_id = Column(String(256), nullable=True, index=True)
    is_demo = Column(Boolean, nullable=False, default=True)
    estimated_cost_usd = Column(Float, nullable=False, default=0.0)

    # Job Lifecycle: "queued" -> "processing" -> "completed" | "failed"
    status = Column(String(32), nullable=False, default="queued", index=True)
    progress_percent = Column(Integer, nullable=False, default=5)
    video_url = Column(String(1024), nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
