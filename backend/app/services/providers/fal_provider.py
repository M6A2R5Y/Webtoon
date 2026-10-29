"""
Official fal.ai Queue API Video Provider (`FalVideoProvider`).

Connects to `https://queue.fal.run` using the user's `FAL_KEY` environment variable.
Supports:
- Asynchronous Text-to-Video (`FAL_T2V_MODEL`, default `fal-ai/wan-t2v`)
- Asynchronous Image-to-Video (`FAL_I2V_MODEL`, default `fal-ai/wan-i2v`)
- Automatic base64 data-URI encoding when the user uploads a local image on `localhost`,
  so fal.ai's cloud servers can read the image even without a public domain!
- Queue status polling (`IN_QUEUE`, `IN_PROGRESS`, `COMPLETED`, `FAILED`)
- Extracting the completed MP4 URL (`video.url`)
"""

import base64
import mimetypes
from pathlib import Path
from typing import Optional
import httpx

from app.config import settings
from app.services.providers.base import BaseVideoProvider, ProviderError, ProviderJobResult


class FalVideoProvider(BaseVideoProvider):
    QUEUE_BASE_URL = "https://queue.fal.run"

    def __init__(self, api_key: str, t2v_model: str = "fal-ai/wan-t2v", i2v_model: str = "fal-ai/wan-i2v"):
        self.api_key = api_key
        self.t2v_model = t2v_model.strip("/")
        self.i2v_model = i2v_model.strip("/")

    @property
    def provider_name(self) -> str:
        return "fal"

    @property
    def display_name(self) -> str:
        return f"fal.ai Live API ({self.t2v_model})"

    @property
    def is_demo(self) -> bool:
        return False

    def _headers(self) -> dict:
        return {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def estimate_cost(self, duration_seconds: int, aspect_ratio: str, generation_type: str) -> tuple[float, str]:
        # Wan 2.5 / standard fal video models average ~$0.05 per second of output
        rate_per_sec = 0.05
        cost = round(duration_seconds * rate_per_sec, 2)
        explanation = (
            f"Live fal.ai API ({self.t2v_model if generation_type == 'text_to_video' else self.i2v_model}): "
            f"Estimated ~${cost:.2f} USD for a {duration_seconds}s ({aspect_ratio}) clip (~$0.05/sec)."
        )
        return cost, explanation

    def _resolve_image_for_external_api(self, image_url: str) -> str:
        """
        Mentor Note:
        When running on `localhost:8000`, an external cloud API like fal.ai cannot download
        `http://localhost:8000/uploads/abc.png` because `localhost` points to its own server!
        To make local Image-to-Video work seamlessly with cloud APIs, we convert local files
        into a standard Base64 Data URI (`data:image/png;base64,...`).
        """
        if "/uploads/" in image_url and ("localhost" in image_url or "127.0.0.1" in image_url):
            filename = image_url.rsplit("/uploads/", 1)[-1]
            local_file: Path = settings.storage_path / filename
            if local_file.exists():
                mime_type, _ = mimetypes.guess_type(str(local_file))
                mime_type = mime_type or "image/png"
                encoded = base64.b64encode(local_file.read_bytes()).decode("utf-8")
                return f"data:{mime_type};base64,{encoded}"
        return image_url

    async def submit_text_to_video(
        self,
        prompt: str,
        aspect_ratio: str,
        duration_seconds: int,
    ) -> ProviderJobResult:
        url = f"{self.QUEUE_BASE_URL}/{self.t2v_model}"
        payload = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "duration": str(duration_seconds),
        }
        return await self._submit_to_fal_queue(url, payload, self.t2v_model)

    async def submit_image_to_video(
        self,
        prompt: str,
        image_url: str,
        aspect_ratio: str,
        duration_seconds: int,
    ) -> ProviderJobResult:
        url = f"{self.QUEUE_BASE_URL}/{self.i2v_model}"
        resolved_image = self._resolve_image_for_external_api(image_url)
        payload = {
            "prompt": prompt,
            "image_url": resolved_image,
            "aspect_ratio": aspect_ratio,
            "duration": str(duration_seconds),
        }
        return await self._submit_to_fal_queue(url, payload, self.i2v_model)

    async def _submit_to_fal_queue(self, url: str, payload: dict, model_id: str) -> ProviderJobResult:
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                response = await client.post(url, headers=self._headers(), json=payload)
        except httpx.RequestError as exc:
            raise ProviderError(
                f"Network error while connecting to fal.ai API: {str(exc)}",
                status_code=503,
            ) from exc

        if response.status_code in (401, 403):
            raise ProviderError(
                "fal.ai rejected your FAL_KEY (Unauthorized). Please check your API key and credit balance at https://fal.ai/dashboard.",
                status_code=401,
            )
        if response.status_code == 429:
            raise ProviderError(
                "fal.ai rate limit reached. Please wait a moment before submitting another video.",
                status_code=429,
            )
        if response.status_code >= 400:
            detail = response.text[:300]
            raise ProviderError(
                f"fal.ai returned HTTP {response.status_code}: {detail}",
                status_code=response.status_code,
            )

        data = response.json()
        request_id = data.get("request_id")
        if not request_id:
            raise ProviderError("fal.ai did not return a valid request_id.", status_code=502)

        # Store `model_id::request_id` so we know which endpoint to poll
        composite_job_id = f"{model_id}::{request_id}"
        return ProviderJobResult(
            provider_job_id=composite_job_id,
            status="queued",
            progress_percent=10,
        )

    async def check_job_status(self, provider_job_id: str, created_at_timestamp: float) -> ProviderJobResult:
        if "::" in provider_job_id:
            model_id, request_id = provider_job_id.split("::", 1)
        else:
            model_id, request_id = self.t2v_model, provider_job_id

        status_url = f"{self.QUEUE_BASE_URL}/{model_id}/requests/{request_id}/status"
        result_url = f"{self.QUEUE_BASE_URL}/{model_id}/requests/{request_id}"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(status_url, headers=self._headers())
                if resp.status_code >= 400:
                    return ProviderJobResult(
                        provider_job_id=provider_job_id,
                        status="failed",
                        progress_percent=0,
                        error_message=f"Provider status check failed (HTTP {resp.status_code}).",
                    )

                status_data = resp.json()
                fal_status = status_data.get("status", "IN_QUEUE").upper()

                if fal_status == "IN_QUEUE":
                    queue_pos = status_data.get("queue_position", 1)
                    progress = 15 if queue_pos > 1 else 25
                    return ProviderJobResult(
                        provider_job_id=provider_job_id,
                        status="queued",
                        progress_percent=progress,
                    )

                if fal_status == "IN_PROGRESS":
                    return ProviderJobResult(
                        provider_job_id=provider_job_id,
                        status="processing",
                        progress_percent=65,
                    )

                if fal_status == "COMPLETED":
                    res_resp = await client.get(result_url, headers=self._headers())
                    if res_resp.status_code >= 400:
                        return ProviderJobResult(
                            provider_job_id=provider_job_id,
                            status="failed",
                            progress_percent=0,
                            error_message="Job completed on fal.ai, but retrieving the video URL failed.",
                        )
                    res_json = res_resp.json()
                    video_url = self._extract_video_url(res_json)
                    if not video_url:
                        return ProviderJobResult(
                            provider_job_id=provider_job_id,
                            status="failed",
                            progress_percent=0,
                            error_message="Provider response did not contain a video URL.",
                        )
                    return ProviderJobResult(
                        provider_job_id=provider_job_id,
                        status="completed",
                        progress_percent=100,
                        video_url=video_url,
                    )

                return ProviderJobResult(
                    provider_job_id=provider_job_id,
                    status="failed",
                    progress_percent=0,
                    error_message=status_data.get("error") or f"Generation ended with status: {fal_status}",
                )
        except httpx.RequestError as exc:
            # Transient network hiccup during polling shouldn't permanently fail the job
            return ProviderJobResult(
                provider_job_id=provider_job_id,
                status="processing",
                progress_percent=50,
                error_message=f"Temporary network retry while polling: {str(exc)}",
            )

    @staticmethod
    def _extract_video_url(payload: dict) -> Optional[str]:
        """Extracts the MP4 URL across different fal.ai model output schemas."""
        if isinstance(payload.get("video"), dict) and payload["video"].get("url"):
            return payload["video"]["url"]
        if isinstance(payload.get("video_url"), str):
            return payload["video_url"]
        if isinstance(payload.get("videos"), list) and len(payload["videos"]) > 0:
            first = payload["videos"][0]
            if isinstance(first, dict) and first.get("url"):
                return first["url"]
            if isinstance(first, str):
                return first
        return None
