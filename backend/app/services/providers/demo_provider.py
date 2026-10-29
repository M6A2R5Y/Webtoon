"""
Honest Demo Mode Video Provider (`DemoVideoProvider`).

Used automatically when no paid API key (`FAL_KEY`) is configured in `.env`.
- Simulates real asynchronous job progression over ~12 seconds:
  - 0-4s: "queued" (15% - 30%)
  - 4-11s: "processing" (40% - 88%)
  - 11s+: "completed" (100%)
- Returns reliable, curated public-domain MP4 sample clips so the user can test
  video previewing, aspect ratios, downloading, and history at $0.00 cost.
- Clearly marks `is_demo = True` so the frontend displays a prominent
  "DEMO SAMPLE - NO API KEY CONFIGURED" badge and never misleads the user.
"""

import time
import uuid
from app.services.providers.base import BaseVideoProvider, ProviderJobResult

# Reliable, fast-loading sample MP4 videos hosted on Google/Wikimedia/MDN CDNs for Demo Mode testing
DEMO_SAMPLE_VIDEOS = [
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoy.mp4",
]


class DemoVideoProvider(BaseVideoProvider):
    @property
    def provider_name(self) -> str:
        return "demo"

    @property
    def display_name(self) -> str:
        return "Demo Mode (Sample Videos - $0.00)"

    @property
    def is_demo(self) -> bool:
        return True

    def estimate_cost(self, duration_seconds: int, aspect_ratio: str, generation_type: str) -> tuple[float, str]:
        live_equivalent = round(duration_seconds * 0.05, 2)
        explanation = (
            f"Demo Mode is active ($0.00 charged). With a live fal.ai key (Wan 2.5), "
            f"a {duration_seconds}s {aspect_ratio} clip costs ~${live_equivalent:.2f} USD."
        )
        return 0.0, explanation

    async def submit_text_to_video(
        self,
        prompt: str,
        aspect_ratio: str,
        duration_seconds: int,
    ) -> ProviderJobResult:
        # Encode a sample index based on the prompt hash so different prompts pick varied sample clips
        sample_idx = abs(hash(prompt)) % len(DEMO_SAMPLE_VIDEOS)
        job_id = f"demo_t2v_{sample_idx}_{uuid.uuid4().hex[:10]}"
        return ProviderJobResult(
            provider_job_id=job_id,
            status="queued",
            progress_percent=12,
        )

    async def submit_image_to_video(
        self,
        prompt: str,
        image_url: str,
        aspect_ratio: str,
        duration_seconds: int,
    ) -> ProviderJobResult:
        sample_idx = abs(hash(prompt + image_url)) % len(DEMO_SAMPLE_VIDEOS)
        job_id = f"demo_i2v_{sample_idx}_{uuid.uuid4().hex[:10]}"
        return ProviderJobResult(
            provider_job_id=job_id,
            status="queued",
            progress_percent=12,
        )

    async def check_job_status(self, provider_job_id: str, created_at_timestamp: float) -> ProviderJobResult:
        elapsed = max(0.0, time.time() - created_at_timestamp)

        # Extract sample video index from the demo job_id
        parts = provider_job_id.split("_")
        sample_idx = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
        sample_url = DEMO_SAMPLE_VIDEOS[sample_idx % len(DEMO_SAMPLE_VIDEOS)]

        if elapsed < 3.5:
            return ProviderJobResult(
                provider_job_id=provider_job_id,
                status="queued",
                progress_percent=min(30, int(12 + elapsed * 5)),
            )
        elif elapsed < 10.5:
            progress = min(92, int(35 + (elapsed - 3.5) * 8))
            return ProviderJobResult(
                provider_job_id=provider_job_id,
                status="processing",
                progress_percent=progress,
            )
        else:
            return ProviderJobResult(
                provider_job_id=provider_job_id,
                status="completed",
                progress_percent=100,
                video_url=sample_url,
            )
