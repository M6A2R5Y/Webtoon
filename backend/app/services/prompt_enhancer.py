"""
AI-Assisted Video Prompt Enhancement Service.

Transforms a beginner's short idea (e.g., "a cat walking in the rain") into a rich,
director-grade video generation prompt specifying:
1. Subject action & micro-movements
2. Camera movement & lens choice
3. Lighting & atmosphere
4. Visual style & texture

If `GEMINI_API_KEY` is configured in `.env`, it calls Google's Gemini API.
Otherwise, it uses our deterministic Cinematic Director Engine so it works 100% free out-of-the-box.
"""

import httpx
from typing import Tuple
from app.config import settings

STYLE_DIRECTIVES = {
    "cinematic": {
        "camera": "Smooth gimbal tracking shot, 35mm anamorphic lens, shallow depth of field with cinematic bokeh",
        "lighting": "Dramatic golden-hour rim lighting, volumetric atmospheric haze, rich contrast and natural shadows",
        "aesthetic": "Hollywood blockbuster color grade, 4K film grain, ultra-detailed textures, fluid natural motion",
    },
    "anime": {
        "camera": "Dynamic anime keyframe pan, expressive perspective shift, subtle parallax background movement",
        "lighting": "Vibrant Makoto Shinkai-inspired sky glow, luminous god rays, crisp cel-shaded highlights",
        "aesthetic": "High-budget modern Japanese animation style, hand-painted background details, sakuga fluid motion",
    },
    "cyberpunk": {
        "camera": "Low-angle dolly push-in, wide-angle lens with subtle neon lens flare",
        "lighting": "Electric magenta and cyan neon reflections on wet pavement, volumetric fog, moody cyberpunk night",
        "aesthetic": "Futuristic sci-fi metropolis aesthetic, hyper-detailed techwear and holographic lighting, high contrast",
    },
    "3d_animation": {
        "camera": "Playful smooth crane camera movement, soft depth of field, expressive framing",
        "lighting": "Warm global illumination, subsurface scattering on textures, soft studio rim lights",
        "aesthetic": "Pixar and DreamWorks feature-film 3D render quality, tactile materials, lively expressive animation",
    },
    "photorealistic": {
        "camera": "Steadicam eye-level following shot, ARRI Alexa 65 sensor look, 50mm prime lens",
        "lighting": "True-to-life natural daylight, physically accurate reflections and soft ambient occlusion",
        "aesthetic": "National Geographic documentary realism, razor-sharp 8K micro-details, lifelike physics",
    },
    "vintage_film": {
        "camera": "Gentle handheld 16mm film camera movement, subtle organic frame weave",
        "lighting": "Warm nostalgic sunlit glow, halation around bright highlights, soft vintage contrast",
        "aesthetic": "1970s Kodak Ektachrome analog film look, authentic dust and grain texture, timeless mood",
    },
    "dark_fantasy": {
        "camera": "Slow ominous creeping dolly shot, dramatic wide framing",
        "lighting": "Flickering torchlight and cold moonlight cutting through dense mist, chiaroscuro shadows",
        "aesthetic": "Epic dark fantasy cinema, weathered gothic textures, atmospheric embers floating in the air",
    },
    "commercial": {
        "camera": "High-speed phantom flex slow-motion orbit shot, razor-sharp macro focus transition",
        "lighting": "Crisp studio key lighting, specular rim highlights, clean luxury product reflections",
        "aesthetic": "High-end commercial advertisement look, vibrant punchy colors, ultra-smooth 60fps motion",
    },
}

ASPECT_COMPOSITION = {
    "9:16": "vertical 9:16 framing optimized for mobile reels with strong central subject focus",
    "16:9": "widescreen 16:9 theatrical composition with expansive environmental depth",
    "1:1": "balanced 1:1 square composition with centered symmetry",
}


async def enhance_video_prompt(
    raw_prompt: str,
    style_preset: str = "cinematic",
    aspect_ratio: str = "9:16",
) -> Tuple[str, str]:
    """
    Returns (enhanced_prompt, enhancer_source) where enhancer_source is 'gemini' or 'cinematic_engine'.
    """
    cleaned = raw_prompt.strip().rstrip(".")
    style_info = STYLE_DIRECTIVES.get(style_preset, STYLE_DIRECTIVES["cinematic"])
    composition = ASPECT_COMPOSITION.get(aspect_ratio, ASPECT_COMPOSITION["9:16"])

    # If user configured a Gemini API key, use LLM enhancement first
    if settings.GEMINI_API_KEY.strip():
        try:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY.strip()}"
            )
            system_instruction = (
                "You are an expert AI video director. Rewrite the user's idea into a vivid, "
                "concise 3-sentence video generation prompt (max 90 words). Include specific subject motion, "
                f"camera movement, lighting, and a '{style_preset}' visual style for {composition}. "
                "Output ONLY the final prompt text without quotes or explanations."
            )
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": f"{system_instruction}\n\nUser Idea: {cleaned}"}
                        ]
                    }
                ]
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    text = (
                        data.get("candidates", [{}])[0]
                        .get("content", {})
                        .get("parts", [{}])[0]
                        .get("text", "")
                        .strip()
                    )
                    if text:
                        return text, "gemini"
        except Exception:
            # Fall back gracefully to our built-in Cinematic Director Engine
            pass

    # Deterministic Cinematic Director Engine
    enhanced = (
        f"{cleaned}, featuring fluid and natural subject movement with expressive micro-details. "
        f"Camera: {style_info['camera']}, composed for {composition}. "
        f"Lighting & Atmosphere: {style_info['lighting']}. "
        f"Style: {style_info['aesthetic']}."
    )
    return enhanced, "cinematic_engine"


def build_final_generation_prompt(prompt: str, style_preset: str) -> str:
    """Ensures the style preset is woven into the prompt sent to the video provider."""
    style_info = STYLE_DIRECTIVES.get(style_preset)
    if not style_info:
        return prompt.strip()
    # If prompt already contains our camera/style directives, don't duplicate
    if "Camera:" in prompt and "Style:" in prompt:
        return prompt.strip()
    return f"{prompt.strip()}. Visual style: {style_info['aesthetic']}, {style_info['lighting']}."
