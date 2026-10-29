"""
Pydantic Schemas for Request Validation and API Responses.

Mentor Note:
Pydantic automatically checks that the user's input is valid (e.g., aspect ratio
is one of 9:16, 16:9, or 1:1; prompt is not empty or overly long) before our code runs.
"""

from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


AspectRatioType = Literal["9:16", "16:9", "1:1"]
DurationType = Literal[5, 10]
GenerationModeType = Literal["text_to_video", "image_to_video"]
StylePresetType = Literal[
    "cinematic",
    "anime",
    "cyberpunk",
    "3d_animation",
    "photorealistic",
    "vintage_film",
    "dark_fantasy",
    "commercial",
]
JobStatusType = Literal["queued", "processing", "completed", "failed"]


class PromptEnhanceRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=600, description="Simple idea to enhance")
    style_preset: StylePresetType = Field(default="cinematic")
    aspect_ratio: AspectRatioType = Field(default="9:16")


class PromptEnhanceResponse(BaseModel):
    original_prompt: str
    enhanced_prompt: str
    style_preset: str
    enhancer_source: str = Field(description="'gemini' or 'cinematic_engine'")


class CostEstimateRequest(BaseModel):
    generation_type: GenerationModeType = "text_to_video"
    duration_seconds: DurationType = 5
    aspect_ratio: AspectRatioType = "9:16"
    style_preset: StylePresetType = "cinematic"


class CostEstimateResponse(BaseModel):
    provider_name: str
    is_demo: bool
    duration_seconds: int
    estimated_cost_usd: float
    cost_explanation: str


class VideoGenerateRequest(BaseModel):
    generation_type: GenerationModeType = Field(default="text_to_video")
    prompt: str = Field(..., min_length=3, max_length=1500, description="Scene description")
    style_preset: StylePresetType = Field(default="cinematic")
    aspect_ratio: AspectRatioType = Field(default="9:16")
    duration_seconds: DurationType = Field(default=5)
    source_image_url: Optional[str] = Field(default=None, description="Required for image_to_video")
    confirm_paid_generation: bool = Field(
        default=False,
        description="Explicit user consent flag when running with a live paid provider",
    )


class VideoJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    client_id: str
    generation_type: str
    prompt: str
    enhanced_prompt: Optional[str] = None
    style_preset: str
    aspect_ratio: str
    duration_seconds: int
    source_image_url: Optional[str] = None
    provider_name: str
    is_demo: bool
    estimated_cost_usd: float
    status: JobStatusType
    progress_percent: int
    video_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class StudioStatusResponse(BaseModel):
    active_provider: str
    is_demo_mode: bool
    provider_display_name: str
    daily_limit: int
    generations_used_today: int
    generations_remaining_today: int
    total_estimated_spend_today_usd: float
    max_upload_size_mb: int


class UploadImageResponse(BaseModel):
    filename: str
    image_url: str
    width: int
    height: int
    size_kb: float


class HistoryListResponse(BaseModel):
    items: List[VideoJobResponse]
    total: int
