"""
Prompt Enhancement Router (`/api/prompts/enhance`).
"""

from fastapi import APIRouter
from app.schemas import PromptEnhanceRequest, PromptEnhanceResponse
from app.services.prompt_enhancer import enhance_video_prompt

router = APIRouter(prefix="/api/prompts", tags=["Prompts"])


@router.post("/enhance", response_model=PromptEnhanceResponse)
async def enhance_prompt_endpoint(payload: PromptEnhanceRequest) -> PromptEnhanceResponse:
    """
    Transforms a simple scene description into a detailed cinematic video prompt
    including camera movement, lighting, subject motion, and style directives.
    """
    enhanced_text, source = await enhance_video_prompt(
        raw_prompt=payload.prompt,
        style_preset=payload.style_preset,
        aspect_ratio=payload.aspect_ratio,
    )
    return PromptEnhanceResponse(
        original_prompt=payload.prompt,
        enhanced_prompt=enhanced_text,
        style_preset=payload.style_preset,
        enhancer_source=source,
    )
