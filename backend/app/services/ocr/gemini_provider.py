"""Optional multimodal OCR via the Gemini API (set OCR_PROVIDER=gemini and OCR_API_KEY).
Used only for text transcription; the deterministic Risk Engine remains the safety authority."""
from __future__ import annotations

import base64

import httpx

from app.config import get_settings
from app.services.ocr.base import OCRError, OCRProvider, OCRResult
from app.utils.uploads import sniff_image_type

PROMPT = ("Transcribe all text on this food package label exactly as printed, preserving line breaks. "
          "Include the ingredients list, allergen statements and the nutrition table. "
          "Do not add commentary, do not translate, do not guess missing words.")


class GeminiOCR(OCRProvider):
    name = "gemini"

    def available(self) -> bool:
        return bool(get_settings().OCR_API_KEY)

    def extract_text(self, image_bytes: bytes, lang: str = "eng") -> OCRResult:
        s = get_settings()
        if not s.OCR_API_KEY:
            raise OCRError("OCR service is not configured.")
        mime = {"jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}[sniff_image_type(image_bytes)]
        body = {"contents": [{"parts": [{"text": PROMPT},
                                        {"inline_data": {"mime_type": mime, "data": base64.b64encode(image_bytes).decode()}}]}],
                "generationConfig": {"temperature": 0}}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{s.GEMINI_MODEL}:generateContent"
        try:
            r = httpx.post(url, params={"key": s.OCR_API_KEY}, json=body, timeout=45)
            r.raise_for_status()
            parts = r.json()["candidates"][0]["content"]["parts"]
            text = "\n".join(p.get("text", "") for p in parts).strip()
        except Exception as e:  # network / quota / schema errors -> friendly message
            raise OCRError("The OCR service couldn't process this image. Try again or enter the ingredients manually.") from e
        if len(text) < 20:
            raise OCRError("We couldn't read this label clearly. Try another photo or enter the ingredients manually.")
        # LLM transcription has no per-word confidence; report medium and ask the user to review
        return OCRResult(text=text, confidence=0.75, provider=self.name,
                         warnings=["Some information may not have been detected. Please review the extracted ingredients."])
