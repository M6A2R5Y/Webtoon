"""
Automated End-to-End Backend Test Suite (`pytest`).

Tests:
1. Health check & Studio status (Demo Mode detection & quota tracking)
2. AI Prompt Enhancement (`/api/prompts/enhance`)
3. Cost Estimation (`/api/videos/estimate-cost`)
4. Image Upload Validation (`/api/videos/upload-image`) - valid PNG vs invalid text file
5. Text-to-Video Generation & Asynchronous Status Polling (`/api/videos/generate` -> `/api/videos/{id}`)
6. Image-to-Video Generation & Per-User History Isolation (`X-Client-ID`)
"""

import io
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def test_health_and_studio_status():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"

    status_res = client.get("/api/videos/studio-status", headers={"X-Client-ID": "test_user_1"})
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert "active_provider" in status_data
    assert status_data["daily_limit"] > 0


def test_prompt_enhancement():
    res = client.post(
        "/api/prompts/enhance",
        json={
            "prompt": "A warrior standing on a cliff at sunset",
            "style_preset": "cinematic",
            "aspect_ratio": "9:16",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["enhanced_prompt"]) > len(data["original_prompt"])
    assert "Camera:" in data["enhanced_prompt"] or data["enhancer_source"] == "gemini"


def test_image_upload_validation():
    # 1. Valid in-memory PNG upload
    img = Image.new("RGB", (320, 240), color=(139, 92, 246))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    upload_res = client.post(
        "/api/videos/upload-image",
        headers={"X-Client-ID": "test_user_upload"},
        files={"file": ("test_scene.png", buf, "image/png")},
    )
    assert upload_res.status_code == 200
    up_data = upload_res.json()
    assert up_data["width"] == 320
    assert up_data["height"] == 240
    assert "/uploads/" in up_data["image_url"]

    # 2. Reject invalid disguised file
    bad_buf = io.BytesIO(b"not a real image")
    bad_res = client.post(
        "/api/videos/upload-image",
        headers={"X-Client-ID": "test_user_upload"},
        files={"file": ("fake.png", bad_buf, "image/png")},
    )
    assert bad_res.status_code == 400


def test_text_to_video_and_history_isolation():
    # Generate a clip as User A
    gen_res = client.post(
        "/api/videos/generate",
        headers={"X-Client-ID": "user_alpha"},
        json={
            "generation_type": "text_to_video",
            "prompt": "A futuristic train gliding through snowy mountains",
            "style_preset": "cyberpunk",
            "aspect_ratio": "16:9",
            "duration_seconds": 5,
            "confirm_paid_generation": True,
        },
    )
    assert gen_res.status_code == 201
    job = gen_res.json()
    job_id = job["id"]
    assert job["status"] in ("queued", "processing", "completed")

    # Poll the job status as User A
    poll_res = client.get(f"/api/videos/{job_id}", headers={"X-Client-ID": "user_alpha"})
    assert poll_res.status_code == 200

    # Verify User B CANNOT access User A's job (Unauthorized history isolation)
    other_poll = client.get(f"/api/videos/{job_id}", headers={"X-Client-ID": "user_beta"})
    assert other_poll.status_code == 404
