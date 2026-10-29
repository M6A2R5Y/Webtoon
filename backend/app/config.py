"""
Configuration and Environment Settings for the AI Video Studio Backend.

Uses pydantic-settings to load values from `backend/.env` safely.
Never expose secret keys (FAL_KEY, GEMINI_API_KEY) to the frontend!
"""

from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Provider selection: "auto" | "fal" | "demo"
    VIDEO_PROVIDER: str = "auto"

    # Official fal.ai API key & model endpoints
    FAL_KEY: str = ""
    FAL_T2V_MODEL: str = "fal-ai/wan-t2v"
    FAL_I2V_MODEL: str = "fal-ai/wan-i2v"

    # Optional Gemini API key for AI prompt enhancement
    GEMINI_API_KEY: str = ""

    # Database connection URL (SQLite for local dev, PostgreSQL for production)
    DATABASE_URL: str = "sqlite:///./studio.db"

    # File upload limits & local storage path
    MAX_UPLOAD_SIZE_MB: int = 10
    STORAGE_DIR: str = "./uploads"

    # Security, rate limits & daily cost controls
    DAILY_GENERATION_LIMIT: int = 20
    MAX_REQUESTS_PER_MINUTE: int = 10
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def active_provider_name(self) -> str:
        """Determines whether we are running 'fal' (live paid API) or 'demo' (sample mode)."""
        mode = self.VIDEO_PROVIDER.strip().lower()
        if mode == "fal":
            return "fal" if self.FAL_KEY.strip() else "demo"
        if mode == "demo":
            return "demo"
        # "auto" mode: use fal if FAL_KEY is configured, otherwise safe demo mode
        return "fal" if bool(self.FAL_KEY.strip()) else "demo"

    @property
    def is_demo_mode(self) -> bool:
        return self.active_provider_name == "demo"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def storage_path(self) -> Path:
        base_dir = Path(__file__).resolve().parent.parent
        path = (base_dir / self.STORAGE_DIR).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
