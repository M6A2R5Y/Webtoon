"""
Abstract Base Class (`BaseVideoProvider`) defining the contract that any
AI video provider must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProviderJobResult:
    """Standardized response returned by any provider when submitting or polling a job."""
    provider_job_id: str
    status: str  # "queued" | "processing" | "completed" | "failed"
    progress_percent: int
    video_url: Optional[str] = None
    error_message: Optional[str] = None


class ProviderError(Exception):
    """Raised when an AI video provider returns an API error or rate-limit failure."""
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class BaseVideoProvider(ABC):
    """Interface that all AI video generation providers must implement."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Internal identifier, e.g., 'fal' or 'demo'."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable label for the UI."""

    @property
    @abstractmethod
    def is_demo(self) -> bool:
        """True if this provider returns labeled sample videos instead of billing an API."""

    @abstractmethod
    def estimate_cost(self, duration_seconds: int, aspect_ratio: str, generation_type: str) -> tuple[float, str]:
        """Returns (estimated_cost_usd, explanation_text)."""

    @abstractmethod
    async def submit_text_to_video(
        self,
        prompt: str,
        aspect_ratio: str,
        duration_seconds: int,
    ) -> ProviderJobResult:
        """Submits an asynchronous text-to-video generation job."""

    @abstractmethod
    async def submit_image_to_video(
        self,
        prompt: str,
        image_url: str,
        aspect_ratio: str,
        duration_seconds: int,
    ) -> ProviderJobResult:
        """Submits an asynchronous image-to-video generation job."""

    @abstractmethod
    async def check_job_status(self, provider_job_id: str, created_at_timestamp: float) -> ProviderJobResult:
        """Checks the current status of a previously submitted job."""
