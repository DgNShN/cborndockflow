# cborn-docflow

Yerel belge işleme: OCR (Tesseract), kural tabanlı etiketleme. **Ücretli API yok** — çekirdek offline.

## Kurulum

1. Python 3.11+ önerilir.
2. Sanal ortam:

```bash
cd c:\AI_PROJECTS\cborn-docflow
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

3. **Tesseract** Windows’ta ayrı kurulmalı; PATH’te `tesseract` görünmeli.  
   - [Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki) (Alman paketi sık kullanılır)  
   - Türkçe dil paketi: kurulumda `tur` seçin veya `tessdata` içine ekleyin.

## Çalıştırma

```bash
python main.py
```

## PyCharm

**File → Open** ile `cborn-docflow` klasörünü açın. Interpreter olarak `.venv` içindeki `python.exe` seçin.
