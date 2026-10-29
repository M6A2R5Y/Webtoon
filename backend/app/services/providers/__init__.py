"""
Provider Factory and Abstract Base Interface for AI Video Providers.

Mentor Note:
By using an Abstract Base Class (`BaseVideoProvider`), the rest of our FastAPI app
doesn't care whether we use fal.ai, Runway, Luma, Replicate, or Demo Mode.
Every provider implements the exact same 4 methods:
1. `estimate_cost()`
2. `submit_text_to_video()`
3. `submit_image_to_video()`
4. `check_job_status()`
"""

from app.config import settings
from app.services.providers.base import BaseVideoProvider, ProviderJobResult
from app.services.providers.demo_provider import DemoVideoProvider
from app.services.providers.fal_provider import FalVideoProvider


def get_video_provider() -> BaseVideoProvider:
    """Returns the configured video provider instance ('fal' if FAL_KEY is set, otherwise 'demo')."""
    if settings.active_provider_name == "fal":
        return FalVideoProvider(
            api_key=settings.FAL_KEY.strip(),
            t2v_model=settings.FAL_T2V_MODEL.strip(),
            i2v_model=settings.FAL_I2V_MODEL.strip(),
        )
    return DemoVideoProvider()


__all__ = [
    "BaseVideoProvider",
    "ProviderJobResult",
    "DemoVideoProvider",
    "FalVideoProvider",
    "get_video_provider",
]
