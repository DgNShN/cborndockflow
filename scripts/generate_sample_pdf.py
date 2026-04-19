"""Örnek PDF üretir (cborn DocFlow OCR / kural testi için)."""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF

# Helvetica Türkçe harfleri PDF’de düzgün gömmez; raster OCR’da ? üretir.
# Windows’ta Arial genelde yüklüdür.
_ARIAL = Path(r"C:\Windows\Fonts\arial.ttf")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out = root / "samples" / "cborn_ornek_fatura.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4

    body = """
cborn DocFlow — ÖRNEK BELGE (TEST)

FATURA / INVOICE No: INV-2026-0418
Tarih: 18.04.2026

Sayın Müşteri,
Bu belge OCR ve etiket kurallarını denemek için üretilmiştir.

Açıklama                    Tutar (TRY)
----------------------------------------
Yazılım danışmanlığı        12.500,00
KDV %20                      2.500,00
----------------------------------------
GENEL TOPLAM                15.000,00

Not: KDV dahil fiyatlandırma örneğidir.

İmza: _________________
SÖZLEŞME ekine bakınız (örnek anahtar kelime).

— cborn
""".strip()

    rect = fitz.Rect(50, 50, 545, 790)
    font_kw: dict = {}
    if _ARIAL.is_file():
        font_kw = {"fontfile": str(_ARIAL), "fontname": "arial"}

    rc = page.insert_textbox(
        rect,
        body,
        fontsize=11,
        align=fitz.TEXT_ALIGN_LEFT,
        **font_kw,
    )
    if rc < 0:
        page.insert_textbox(
            rect,
            body,
            fontsize=9,
            align=fitz.TEXT_ALIGN_LEFT,
            **font_kw,
        )

    doc.save(out)
    doc.close()
    print(out)


if __name__ == "__main__":
    main()
