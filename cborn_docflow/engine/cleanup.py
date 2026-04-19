"""OCR sonrası hafif metin düzeltmeleri (Türkçe fatura benzeri yaygın hatalar)."""

from __future__ import annotations

import re


def cleanup_ocr_text(text: str) -> str:
    """
    Aşırı agresif olmayan kurallar; yanlış pozitif riski düşük tutulur.
    """
    if not text:
        return text

    # '%' işareti bazen '9' veya '90' + '20' gibi okunur (örn. KDV %20 -> KDV 9020)
    text = re.sub(r"\bKDV\s+9020\b", "KDV %20", text, flags=re.IGNORECASE)
    text = re.sub(r"\bKDV\s+90\s*20\b", "KDV %20", text, flags=re.IGNORECASE)

    return text
