"""
File upload validation utilities.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, UploadFile, status

# =====================================================
# Allowed File Extensions
# =====================================================

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
}

# =====================================================
# Allowed MIME Types
# =====================================================

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
}

# =====================================================
# Upload Limits
# =====================================================

MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20 MB
AVATAR_MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
IMAGE_CONTENT_TYPES = {"image/png", "image/jpeg"}


# =====================================================
# Validation
# =====================================================

async def validate_upload(file: UploadFile) -> str:
    """
    Validate uploaded file.

    Returns:
        Sanitized filename.

    Raises:
        HTTPException
    """

    if file.filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing.",
        )

    # Prevent path traversal
    filename = Path(file.filename).name

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file extension '{extension}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported content type '{file.content_type}'."
            ),
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File exceeds maximum size of "
                f"{MAX_UPLOAD_SIZE // (1024 * 1024)} MB."
            ),
        )

    # Reset stream for downstream consumers
    await file.seek(0)

    return filename


async def validate_image_upload(file: UploadFile) -> str:
    """
    Validate an image upload for avatars and profile photos.
    """
    if file.filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing.",
        )

    filename = Path(file.filename).name
    extension = Path(filename).suffix.lower()

    if extension not in IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported image extension '{extension}'. "
                f"Allowed: {', '.join(sorted(IMAGE_EXTENSIONS))}"
            ),
        )

    if file.content_type not in IMAGE_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported content type '{file.content_type}'.",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(contents) > AVATAR_MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds maximum size of {AVATAR_MAX_UPLOAD_SIZE // (1024 * 1024)} MB.",
        )

    await file.seek(0)
    return filename