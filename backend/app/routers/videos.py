"""
Video Generation, Status Polling, Upload, Download Proxy, Quota & History Router (`/api/videos`).

Includes:
- Per-client sliding-window rate limiting (prevents accidental button spamming).
- Daily generation quota enforcement (`DAILY_GENERATION_LIMIT`).
- Explicit user consent check before spending money on a paid API (`confirm_paid_generation`).
- Per-user history isolation via `X-Client-ID` header.
"""

import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, File, Header, HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import VideoJob
from app.schemas import (
    CostEstimateRequest,
    CostEstimateResponse,
    HistoryListResponse,
    StudioStatusResponse,
    UploadImageResponse,
    VideoGenerateRequest,
    VideoJobResponse,
)
from app.services.prompt_enhancer import build_final_generation_prompt
from app.services.providers import get_video_provider
from app.services.providers.base import ProviderError
from app.services.storage import validate_and_save_image

router = APIRouter(prefix="/api/videos", tags=["Videos"])

# In-memory sliding window rate limiter: maps client_id -> deque of request timestamps
_rate_limit_buckets: dict[str, deque] = defaultdict(deque)


def get_client_id(x_client_id: Optional[str] = Header(default="default-local-user")) -> str:
    """Extracts and sanitizes the user's workspace session ID so users only see their own history."""
    cleaned = (x_client_id or "default-local-user").strip()[:64]
    return cleaned if cleaned else "default-local-user"


def check_rate_limit(client_id: str) -> None:
    """Enforces `MAX_REQUESTS_PER_MINUTE` per client to prevent accidental API spam."""
    now = time.time()
    window = 60.0
    bucket = _rate_limit_buckets[client_id]
    while bucket and (now - bucket[0]) > window:
        bucket.popleft()
    if len(bucket) >= settings.MAX_REQUESTS_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded ({settings.MAX_REQUESTS_PER_MINUTE} requests/minute). Please wait a few seconds.",
        )
    bucket.append(now)


def get_today_usage(db: Session, client_id: str) -> tuple[int, float]:
    """Returns (generations_count_today, total_estimated_spend_today_usd) for this client."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    jobs_today = (
        db.query(VideoJob)
        .filter(
            VideoJob.client_id == client_id,
            VideoJob.created_at >= today_start,
            VideoJob.status != "failed",
        )
        .all()
    )
    count = len(jobs_today)
    spend = round(sum(j.estimated_cost_usd for j in jobs_today), 2)
    return count, spend


@router.get("/studio-status", response_model=StudioStatusResponse)
def get_studio_status(
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
) -> StudioStatusResponse:
    """Returns current provider status (Demo vs Live), daily usage quota, and spend summary."""
    provider = get_video_provider()
    used_today, spend_today = get_today_usage(db, client_id)
    remaining = max(0, settings.DAILY_GENERATION_LIMIT - used_today)
    return StudioStatusResponse(
        active_provider=provider.provider_name,
        is_demo_mode=provider.is_demo,
        provider_display_name=provider.display_name,
        daily_limit=settings.DAILY_GENERATION_LIMIT,
        generations_used_today=used_today,
        generations_remaining_today=remaining,
        total_estimated_spend_today_usd=spend_today,
        max_upload_size_mb=settings.MAX_UPLOAD_SIZE_MB,
    )


@router.post("/estimate-cost", response_model=CostEstimateResponse)
def estimate_generation_cost(payload: CostEstimateRequest) -> CostEstimateResponse:
    """Calculates the estimated USD cost before the user clicks Generate."""
    provider = get_video_provider()
    cost, explanation = provider.estimate_cost(
        duration_seconds=payload.duration_seconds,
        aspect_ratio=payload.aspect_ratio,
        generation_type=payload.generation_type,
    )
    return CostEstimateResponse(
        provider_name=provider.provider_name,
        is_demo=provider.is_demo,
        duration_seconds=payload.duration_seconds,
        estimated_cost_usd=cost,
        cost_explanation=explanation,
    )


@router.post("/upload-image", response_model=UploadImageResponse)
async def upload_reference_image(
    request: Request,
    file: UploadFile = File(...),
    client_id: str = Depends(get_client_id),
) -> UploadImageResponse:
    """Validates and stores an uploaded reference image for Image-to-Video generation."""
    check_rate_limit(client_id)
    base_url = str(request.base_url).rstrip("/")
    filename, public_url, width, height, size_kb = await validate_and_save_image(file, base_url)
    return UploadImageResponse(
        filename=filename,
        image_url=public_url,
        width=width,
        height=height,
        size_kb=size_kb,
    )


@router.post("/generate", response_model=VideoJobResponse, status_code=status.HTTP_201_CREATED)
async def generate_video(
    payload: VideoGenerateRequest,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
) -> VideoJob:
    """
    Submits a Text-to-Video or Image-to-Video generation request.
    Enforces rate limits, daily quotas, image validation, and explicit paid-API consent.
    """
    check_rate_limit(client_id)

    # 1. Check daily quota
    used_today, _ = get_today_usage(db, client_id)
    if used_today >= settings.DAILY_GENERATION_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily generation quota reached ({settings.DAILY_GENERATION_LIMIT} videos/day). Adjust DAILY_GENERATION_LIMIT in backend/.env if needed.",
        )

    # 2. Validate Image-to-Video requirements
    if payload.generation_type == "image_to_video" and not payload.source_image_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a reference image before generating an Image-to-Video clip.",
        )

    provider = get_video_provider()
    cost_usd, _ = provider.estimate_cost(
        duration_seconds=payload.duration_seconds,
        aspect_ratio=payload.aspect_ratio,
        generation_type=payload.generation_type,
    )

    # 3. Never spend money without explicit user action
    if not provider.is_demo and cost_usd > 0 and not payload.confirm_paid_generation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Live API mode requires explicit confirmation to spend ~${cost_usd:.2f} USD.",
        )

    final_prompt = build_final_generation_prompt(payload.prompt, payload.style_preset)

    # 4. Submit asynchronous job to the configured provider
    try:
        if payload.generation_type == "image_to_video":
            provider_result = await provider.submit_image_to_video(
                prompt=final_prompt,
                image_url=payload.source_image_url or "",
                aspect_ratio=payload.aspect_ratio,
                duration_seconds=payload.duration_seconds,
            )
        else:
            provider_result = await provider.submit_text_to_video(
                prompt=final_prompt,
                aspect_ratio=payload.aspect_ratio,
                duration_seconds=payload.duration_seconds,
            )
    except ProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    # 5. Save job record in SQLite / PostgreSQL
    job = VideoJob(
        client_id=client_id,
        generation_type=payload.generation_type,
        prompt=payload.prompt.strip(),
        enhanced_prompt=final_prompt,
        style_preset=payload.style_preset,
        aspect_ratio=payload.aspect_ratio,
        duration_seconds=payload.duration_seconds,
        source_image_url=payload.source_image_url,
        provider_name=provider.provider_name,
        provider_job_id=provider_result.provider_job_id,
        is_demo=provider.is_demo,
        estimated_cost_usd=cost_usd,
        status=provider_result.status,
        progress_percent=provider_result.progress_percent,
        video_url=provider_result.video_url,
        error_message=provider_result.error_message,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/history", response_model=HistoryListResponse)
def list_generation_history(
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
) -> HistoryListResponse:
    """Returns the current user's video generation history, newest first."""
    jobs = (
        db.query(VideoJob)
        .filter(VideoJob.client_id == client_id)
        .order_by(VideoJob.created_at.desc())
        .limit(50)
        .all()
    )
    return HistoryListResponse(items=jobs, total=len(jobs))


@router.get("/{job_id}", response_model=VideoJobResponse)
async def get_and_poll_video_job(
    job_id: str,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
) -> VideoJob:
    """
    Polls the current status of a video generation job.
    If the job is still 'queued' or 'processing', queries the provider and updates the DB.
    """
    job = (
        db.query(VideoJob)
        .filter(VideoJob.id == job_id, VideoJob.client_id == client_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video generation job not found.")

    if job.status in ("queued", "processing") and job.provider_job_id:
        provider = get_video_provider()
        created_ts = job.created_at.timestamp() if job.created_at else time.time()
        poll_result = await provider.check_job_status(job.provider_job_id, created_ts)

        job.status = poll_result.status
        job.progress_percent = poll_result.progress_percent
        if poll_result.video_url:
            job.video_url = poll_result.video_url
        if poll_result.error_message:
            job.error_message = poll_result.error_message
        job.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(job)

    return job


@router.get("/{job_id}/download")
async def download_completed_video(
    job_id: str,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    """
    Streams the completed MP4 video with `Content-Disposition: attachment` so the browser
    cleanly downloads the file to the user's device instead of opening a new tab.
    """
    job = (
        db.query(VideoJob)
        .filter(VideoJob.id == job_id, VideoJob.client_id == client_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video job not found.")
    if job.status != "completed" or not job.video_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Video is not ready for download yet.")

    filename = f"aistudio-{job.style_preset}-{job.id[:8]}.mp4"

    async def stream_remote_video():
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            async with client.stream("GET", job.video_url) as response:
                if response.status_code >= 400:
                    raise HTTPException(status_code=502, detail="Could not stream video file from storage.")
                async for chunk in response.aiter_bytes(chunk_size=65536):
                    yield chunk

    return StreamingResponse(
        stream_remote_video(),
        media_type="video/mp4",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_history_item(
    job_id: str,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    """Allows a user to delete a clip from their personal generation history."""
    job = (
        db.query(VideoJob)
        .filter(VideoJob.id == job_id, VideoJob.client_id == client_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video job not found.")
    db.delete(job)
    db.commit()
    return None
