"""
cborn DocFlow test seti: 5 fatura PDF + desteklenen tüm görüntü uzantılarında örnek.
Çalıştır: python scripts/generate_test_batch.py
"""

from __future__ import annotations

import random
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

_ROOT = Path(__file__).resolve().parents[1]
_OUT = _ROOT / "samples" / "test_batch"
_ARIAL = Path(r"C:\Windows\Fonts\arial.ttf")

PDF_SPECS: list[tuple[str, str]] = [
    (
        "batch_fatura_01.pdf",
        """FATURA — Ticari Örnek A
INVOICE No: TR-2026-0001 | Tarih: 18.04.2026
Müşteri: Demo A.Ş. | Vergi No: 1234567890

Açıklama                         Tutar (TRY)
Danışmanlık hizmeti              8.900,00
KDV %20                           1.780,00
GENEL TOPLAM                     10.680,00

Ödeme vadesi: 30 gün. SÖZLEŞME No: SOZ-88 referanslıdır.
İmza: _________________""",
    ),
    (
        "batch_fatura_02.pdf",
        """COMMERCIAL INVOICE
invoice number: INV-GB-2026-42
VAT registration: TR-VAT-OK
Line items include VAT and invoice totals in TRY.

Description              Amount
Software license         3.200,00
VAT                      640,00
Total due                3.840,00

contract appendix: see annex B (contract keyword test).""",
    ),
    (
        "batch_fatura_03.pdf",
        """PROFORMA FATURA
No: PF-2026-155 | Tarih 01.05.2026

Bu belge fatura niteliğinde örnektir.
KDV oranı %20 uygulanmıştır.

Ürün satışı           22.000,00 TRY
KDV %20                4.400,00
TOPLAM                26.400,00

Not: sözleşme maddeleri ekte. Müşteri onayı alınmıştır.""",
    ),
    (
        "batch_fatura_04.pdf",
        """e-FATURA ÖRNEĞİ (TEST)
UUID: 550e8400-e29b-41d4-a716-446655440000
Senaryo: Temel fatura

Mal hizmet: Eğitim
Matrah: 1.000,00 | KDV %20: 200,00 | Ödenecek: 1.200,00

invoice data synthetic — vat kdv fatura keywords
İmza ve kaşe alanı boş bırakılmıştır.""",
    ),
    (
        "batch_fatura_05.pdf",
        """MINI FATURA
No: M-9 | Tarih: 12.12.2026
Tek satır: Hizmet bedeli 500,00 + KDV %20 100,00 = 600,00 TRY
contract / sözleşme yok; sadece fatura kelimesi yoğun.""",
    ),
]


def _pdf_font_kw() -> dict:
    if _ARIAL.is_file():
        return {"fontfile": str(_ARIAL), "fontname": "arial"}
    return {}


def write_pdf(name: str, body: str) -> Path:
    path = _OUT / name
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    rect = fitz.Rect(40, 40, 555, 800)
    kw = _pdf_font_kw()
    rc = page.insert_textbox(
        rect,
        body.strip(),
        fontsize=10,
        align=fitz.TEXT_ALIGN_LEFT,
        **kw,
    )
    if rc < 0:
        page.insert_textbox(rect, body.strip(), fontsize=8, align=fitz.TEXT_ALIGN_LEFT, **kw)
    doc.save(path)
    doc.close()
    return path


def _font() -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if _ARIAL.is_file():
        try:
            return ImageFont.truetype(str(_ARIAL), 17)
        except OSError:
            pass
    return ImageFont.load_default()


def write_image(path: Path, lines: list[str]) -> None:
    w, h = 720, max(420, 40 + len(lines) * 28)
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = _font()
    y = 24
    for line in lines:
        draw.text((24, y), line, fill=(20, 20, 20), font=font)
        y += 26
    ext = path.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        img.save(path, "JPEG", quality=90)
    elif ext == ".png":
        img.save(path, "PNG")
    elif ext in (".tif", ".tiff"):
        img.save(path, "TIFF", compression="tiff_lzw")
    elif ext == ".bmp":
        img.save(path, "BMP")
    elif ext == ".webp":
        img.save(path, "WEBP", quality=85)
    else:
        img.save(path)


def image_line_sets() -> list[list[str]]:
    base = [
        [
            "GÖRÜNTÜ FATURA TESTİ — PNG/JPG vb.",
            "No: IMG-2026-R" + str(random.randint(10, 99)),
            "FATURA satırı | KDV %20 | invoice keyword",
            "Tutar örnek: 1.234,56 TRY",
        ],
        [
            "Ekran görüntüsü simülasyonu",
            "VAT / KDV içeren kısa metin",
            "SÖZLEŞME ibaresi: ek protokol",
        ],
        [
            "Kargo irsaliyesi + fatura referansı",
            "INV-REF-5566 | contract no: C-01",
        ],
        [
            "Basit satış belgesi",
            "Toplam 99,00 + KDV %20",
        ],
        [
            "Çok satırlı örnek",
            "Açıklama | fatura | invoice",
            "Müşteri demo | vat dahil",
        ],
        [
            "Son test görseli",
            "FATURA ve KDV anahtar kelimeleri",
        ],
        [
            "Ek stok: random varyasyon",
            f"Seri: {random.randint(1000, 9999)}",
            "sözleşme eki olabilir",
        ],
    ]
    random.shuffle(base)
    return base


def main() -> None:
    _OUT.mkdir(parents=True, exist_ok=True)
    print("Çıktı:", _OUT)

    for name, body in PDF_SPECS:
        p = write_pdf(name, body)
        print("PDF:", p.name)

    # Her desteklenen görüntü uzantısı için bir dosya
    exts = [".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"]
    line_sets = image_line_sets()
    for i, ext in enumerate(exts):
        lines = line_sets[i]
        fname = f"batch_gorsel_{i + 1:02d}{ext}"
        outp = _OUT / fname
        write_image(outp, lines)
        print("Görüntü:", outp.name)

    readme = _OUT / "OKU.txt"
    readme.write_text(
        """cborn DocFlow — test_batch klasörü

İçerik:
  - 5 adet örnek fatura PDF (farklı metin/kelime dağılımı)
  - 7 adet görüntü: .png .jpg .jpeg .tif .tiff .bmp .webp

Klasör izleme:
  İzleme başlatılmadan önce bu klasörde duran dosyalar atlanır.
  Test: dosyaları başka klasöre taşı, izlemeyi başlat, sonra geri kopyala
  VEYA «Mevcut PDF/görüntüleri şimdi işle» kullan.

Tek dosya:
  «Dosya seç ve OCR» ile buradan tek tek seçebilirsin.

""",
        encoding="utf-8",
    )
    print("OK:", readme)


if __name__ == "__main__":
    main()
