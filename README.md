# cborn DocFlow

![cborn DocFlow overview](assets/overview.svg)

cborn DocFlow, PDF ve görselleri yerelde OCR’dan geçirip kural bazlı etiketleyen masaüstü uygulamasıdır. Çekirdek akış offline çalışır; Gmail ve Outlook eklerini sonradan içe aktarma desteği de vardır.

## Ne yapar

- Tek dosya OCR: PDF veya görsel seç, metni çıkar.
- Klasör izleme: yeni gelen dosyaları otomatik kuyruğa al.
- Kural bazlı etiketleme: `fatura`, `sozlesme` gibi etiketleri regex ile eşleştir.
- Çıktı yönlendirme: istenirse etiket klasörlerine kopyala.
- E-posta içe aktarma: Gmail ve Outlook eklerini indir.

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

## Calistirma

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

## PyCharm

**File -> Open** ile `cborn-docflow` klasörünü açın. Interpreter olarak `.venv` içindeki `python.exe` seçin.
