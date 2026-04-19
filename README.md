# cborn DocFlow

![cborn DocFlow overview](assets/overview.svg)

## About

cborn DocFlow is a polished, local-first desktop app for OCR processing of PDFs and images, rule-based tagging, and optional Gmail/Outlook attachment import. It is designed for fast document intake workflows where privacy, control, and repeatable classification matter.

cborn DocFlow, PDF ve görselleri yerelde OCR’dan geçirip kural bazlı etiketleyen masaüstü uygulamasıdır. Çekirdek akış offline çalışır; Gmail ve Outlook eklerini sonradan içe aktarma desteği de vardır.

## Ne yapar

- Tek dosya OCR: PDF veya görsel seç, metni çıkar.
- Klasör izleme: yeni gelen dosyaları otomatik kuyruğa al.
- Kural bazlı etiketleme: `fatura`, `sozlesme` gibi etiketleri regex ile eşleştir.
- Çıktı yönlendirme: istenirse etiket klasörlerine kopyala.
- E-posta içe aktarma: Gmail ve Outlook eklerini indir.

## English

### What it does

- Single-file OCR: choose a PDF or image and extract text.
- Folder watching: automatically queue newly added files.
- Rule-based tagging: match labels like `fatura` and `sozlesme` with regex rules.
- Output routing: copy files into tag folders when enabled.
- Email import: download attachments from Gmail and Outlook.

## Kurulum

1. Python 3.11+ önerilir.
2. Sanal ortam kur:

```bash
cd c:\AI_PROJECTS\cborn-docflow
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

3. Windows'ta **Tesseract** ayrı kurulmalı ve `tesseract` PATH'te görünmelidir.
   - [Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki)
   - Türkçe dil paketi için `tur` seçeneğini ekleyin.

## English setup

1. Python 3.11+ is recommended.
2. Create a virtual environment:

```bash
cd c:\AI_PROJECTS\cborn-docflow
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

3. On Windows, install **Tesseract** separately and make sure `tesseract` is on PATH.
   - [Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki)
   - Add the Turkish language pack during installation if needed.

## Calistirma / Run

```bash
python main.py
```

## Yapilandirma

- Kural ve çıktı ayarları: `config/docflow.json`
- Gmail OAuth örneği: `config/gmail_client_secret.json.example`
- Gerçek OAuth dosyası gizli kalır ve Git'e girmez.

## Repo yapisi

- `cborn_docflow/`: uygulama kodu
- `config/`: varsayılan ayarlar ve OAuth örnekleri
- `samples/`: test PDF ve görseller
- `inbox-demo/`: örnek gelen kutusu materyalleri
- `scripts/`: örnek üretim yardımcıları

## Project structure

- `cborn_docflow/`: application code
- `config/`: default settings and OAuth examples
- `samples/`: test PDFs and images
- `inbox-demo/`: sample inbox assets
- `scripts/`: sample generation helpers

## PyCharm

**File -> Open** ile `cborn-docflow` klasörünü açın. Interpreter olarak `.venv` içindeki `python.exe` seçin.

Open the `cborn-docflow` folder with **File -> Open** and select the `.venv` `python.exe` as the interpreter.
