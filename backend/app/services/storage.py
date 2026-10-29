"""
Secure Image Upload & Storage Service.

Mentor Note:
Never trust a file extension alone! A malicious user could rename `virus.exe` to `cat.png`.
Here we:
1. Check the MIME type and extension (.jpg, .jpeg, .png, .webp).
2. Enforce the maximum file size (`MAX_UPLOAD_SIZE_MB`, default 10 MB).
3. Open the bytes with Pillow (`PIL.Image`) to verify it is a genuine, uncorrupted image.
4. Strip out original filenames and save under a random UUID name so path-traversal attacks are impossible.
"""

import io
import uuid
from typing import Tuple
from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.config import settings

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


async def validate_and_save_image(file: UploadFile, base_url: str) -> Tuple[str, str, int, int, float]:
    """
    Validates an uploaded image and stores it in `backend/uploads/`.
    Returns (saved_filename, public_image_url, width, height, size_kb).
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided in upload.",
        )

    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: JPG, PNG, WEBP.",
        )

    if file.content_type and file.content_type.lower() not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type '{file.content_type}'. Please upload a valid image.",
        )

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    raw_bytes = await file.read()

    if len(raw_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(raw_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB maximum limit.",
        )

    # Verify image integrity and dimensions using Pillow
    try:
        with Image.open(io.BytesIO(raw_bytes)) as img:
            img.verify()
        with Image.open(io.BytesIO(raw_bytes)) as img:
            width, height = img.size
            # Convert RGBA/P to RGB if saving as JPEG, or keep clean PNG/WEBP
            rgb_img = img.convert("RGB") if ext in {".jpg", ".jpeg"} else img.copy()
            safe_filename = f"{uuid.uuid4().hex}{ext}"
            dest_path = settings.storage_path / safe_filename
            rgb_img.save(dest_path, quality=92)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file could not be verified as a valid image.",
        ) from exc

    size_kb = round(len(raw_bytes) / 1024.0, 2)
    clean_base = base_url.rstrip("/")
    public_url = f"{clean_base}/uploads/{safe_filename}"

    return safe_filename, public_url, width, height, size_kb
