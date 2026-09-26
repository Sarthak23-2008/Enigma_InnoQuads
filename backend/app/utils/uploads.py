"""Secure image upload validation: extension-agnostic magic-byte sniffing, size cap, Pillow verify."""
from __future__ import annotations

import io

from PIL import Image

ALLOWED = {"jpeg", "png", "webp"}


class UploadError(ValueError):
    pass


def sniff_image_type(b: bytes) -> str | None:
    if b[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return "webp"
    return None


def validate_image(data: bytes, max_mb: int) -> str:
    if not data:
        raise UploadError("The file is empty.")
    if len(data) > max_mb * 1024 * 1024:
        raise UploadError(f"Image is too large. The limit is {max_mb} MB.")
    kind = sniff_image_type(data)
    if kind not in ALLOWED:
        raise UploadError("Only JPEG, PNG or WEBP images are accepted.")
    try:
        with Image.open(io.BytesIO(data)) as im:
            im.verify()
    except Exception as e:
        raise UploadError("The image file appears to be damaged.") from e
    return kind
