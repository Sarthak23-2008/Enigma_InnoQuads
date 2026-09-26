"""OCR service abstraction. Swap providers with OCR_PROVIDER without touching callers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class OCRResult:
    text: str
    confidence: float          # 0..1
    provider: str
    warnings: list[str]


class OCRError(Exception):
    """Raised when a label cannot be read. Message is safe to show to users."""


class OCRProvider(ABC):
    name = "base"

    @abstractmethod
    def extract_text(self, image_bytes: bytes, lang: str = "eng") -> OCRResult: ...

    def available(self) -> bool:
        return True
