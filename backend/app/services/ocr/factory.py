from __future__ import annotations

import logging

from app.config import get_settings
from app.services.ocr.base import OCRError, OCRProvider, OCRResult

log = logging.getLogger("safebite.ocr")


def get_provider(name: str | None = None) -> OCRProvider:
    name = (name or get_settings().OCR_PROVIDER).lower()
    if name == "gemini":
        from app.services.ocr.gemini_provider import GeminiOCR
        return GeminiOCR()
    if name == "demo":
        from app.services.ocr.demo_provider import DemoOCR
        return DemoOCR()
    from app.services.ocr.tesseract_provider import TesseractOCR
    return TesseractOCR()


def run_ocr(image_bytes: bytes, lang: str = "eng") -> OCRResult:
    """Primary provider; in DEMO_MODE falls back to the sample-label recogniser if the engine is missing."""
    s = get_settings()
    provider = get_provider()
    try:
        if not provider.available():
            raise OCRError("OCR engine unavailable.")
        return provider.extract_text(image_bytes, lang=lang)
    except OCRError:
        if s.DEMO_MODE and provider.name != "demo":
            from app.services.ocr.demo_provider import DemoOCR
            try:
                return DemoOCR().extract_text(image_bytes, lang)
            except OCRError:
                pass
        raise
