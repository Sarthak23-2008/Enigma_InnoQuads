"""Image preprocessing for label OCR: orientation, scale, contrast, deskew, table-rule removal."""
from __future__ import annotations

import io

import numpy as np
from PIL import Image, ImageFilter, ImageOps

Image.MAX_IMAGE_PIXELS = 40_000_000  # decompression-bomb guard


def _deskew_angle(gray: Image.Image) -> float:
    """Projection-profile deskew: the angle that makes text rows sharpest."""
    small = gray.copy()
    small.thumbnail((800, 800))
    arr = np.asarray(small, dtype=np.uint8)
    thr = arr.mean() - 30
    best, best_score = 0.0, -1.0
    for a in np.arange(-3.0, 3.01, 0.25):
        rot = np.asarray(small.rotate(a, fillcolor=255, resample=Image.BILINEAR), dtype=np.uint8)
        prof = (rot < thr).sum(axis=1).astype(float)
        score = float(np.var(prof))
        if score > best_score:
            best, best_score = float(a), score
    return best


def _remove_rules(gray: Image.Image) -> Image.Image:
    """Blank out long horizontal/vertical lines (nutrition-table rules) that confuse OCR."""
    arr = np.asarray(gray, dtype=np.uint8).copy()
    dark = arr < 160
    h, w = arr.shape
    rows = dark.mean(axis=1) > 0.45
    cols = dark.mean(axis=0) > 0.45
    for y in np.where(rows)[0]:
        arr[max(0, y - 1): y + 2, :] = 255
    for x in np.where(cols)[0]:
        arr[:, max(0, x - 1): x + 2] = 255
    return Image.fromarray(arr)


def prepare(image_bytes: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img)
    img = img.convert("L")
    w, h = img.size
    long_side = max(w, h)
    if long_side < 1400:  # upscale small photos; tesseract likes ~300dpi text
        scale = 1400 / long_side
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    elif long_side > 3200:
        scale = 3200 / long_side
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    img = ImageOps.autocontrast(img, cutoff=1)
    angle = _deskew_angle(img)
    if abs(angle) >= 0.25:
        img = img.rotate(angle, expand=True, fillcolor=255, resample=Image.BICUBIC)
    img = _remove_rules(img)
    img = img.filter(ImageFilter.SHARPEN)
    return img
