from __future__ import annotations

import queue
import re
import sys
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QSettings, Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from cborn_docflow.engine.config_paths import CONFIG_PATH, resolve_gmail_client_secret_path
from cborn_docflow.engine.docflow_config import copy_to_output_if_enabled, load_docflow
from cborn_docflow.engine.job import PDF_MAX_PAGES, run_ocr
from cborn_docflow.engine.rules import match_tags
from cborn_docflow.settings_dialog import SettingsDialog
from cborn_docflow.ui_theme import THEME_CHOICES, apply_theme

# QListWidget: kaynak dosya; +1 = çıktı kopyası (etiket klasörü)
_ROLE_FILE = Qt.ItemDataRole.UserRole
_ROLE_COPY = Qt.ItemDataRole.UserRole + 1


def _open_local_file(path: Path) -> None:
    try:
        rp = path.resolve()
    except OSError:
        rp = path
    if rp.is_file():
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(rp)))


_OUTLOOK_CLIENT_ID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

WATCH_EXTS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".bmp",
    ".webp",
}


def _snapshot_supported(folder: Path) -> set[str]:
    out: set[str] = set()
    if not folder.is_dir():
        return out
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() in WATCH_EXTS:
            try:
                out.add(str(p.resolve()))
            except OSError:
                continue
    return out


class OcrThread(QThread):
    """Görüntü veya PDF üzerinde OCR (arka plan)."""

    finished_ok = Signal(str, object)
    failed = Signal(str)

    def __init__(self, path: Path, pdf_mode: str | None = None) -> None:
        super().__init__()
        self._path = path
        self._pdf_mode = pdf_mode

    def run(self) -> None:
        try:
            result = run_ocr(self._path, self._pdf_mode)
            self.finished_ok.emit(result.text, result.confidence)
        except Exception as e:  # noqa: BLE001
            self.failed.emit(str(e))


class WatchWorker(QThread):
    """Klasör kuyruğu: PDF = ilk sayfa, görüntü = tam sayfa OCR."""

    # Metin; kaynak yol (çift tık); çıktı kopyası (sağ tık menüsü) veya None.
    line = Signal(str, object, object)
    _STOP = object()

    def __init__(self) -> None:
        super().__init__()
        self._q: queue.Queue[object] = queue.Queue()

    def enqueue(self, path: Path) -> None:
        self._q.put(path)

    def shutdown(self) -> None:
        """Uygulama kapanırken kuyruğu sonlandır."""
        self._q.put(self._STOP)

    def run(self) -> None:
        while True:
            item = self._q.get()
            if item is self._STOP:
                break
            p = item
            if not isinstance(p, Path):
                continue
            try:
                pdf_mode = "first" if p.suffix.lower() == ".pdf" else None
                r = run_ocr(p, pdf_mode)
                rules, out = load_docflow()
                tags = match_tags(r.text, rules)
                tag_s = ", ".join(tags) if tags else "-"
                conf = f"{r.confidence:.0%}" if r.confidence is not None else "?"
                line = f"OK  {p.name}  | güven {conf}  | etiket: {tag_s}"
                dest = copy_to_output_if_enabled(p, tags, out)
                copy_path: Path | None = None
                if dest:
                    line += f"  | kopya: {dest}"
                    copy_path = Path(dest)
                self.line.emit(line, p.resolve(), copy_path)
            except Exception as e:  # noqa: BLE001
                self.line.emit(f"HATA {p.name}: {e}", None, None)


class EmailPullThread(QThread):
    """Gmail veya Outlook'tan ek indirme (ağ)."""

    line = Signal(str)
    done = Signal(list)
    failed = Signal(str)

    def __init__(
        self,
        mode: str,
        *,
        gmail_creds: Path | None = None,
        outlook_client_id: str = "",
        dest: Path | None = None,
        max_messages: int = 20,
    ) -> None:
        super().__init__()
        self._mode = mode
        self._gmail_creds = gmail_creds
        self._outlook_id = outlook_client_id.strip()
        self._dest = dest
        self._max = max_messages

    def run(self) -> None:
        try:
            if self._mode == "gmail":
                if not self._gmail_creds or not self._dest:
                    self.failed.emit("Gmail: credentials yolu ve indirme klasörü gerekli.")
                    return
                from cborn_docflow.mail.gmail_client import download_attachments

                paths = download_attachments(
                    self._gmail_creds,
                    self._dest,
                    max_messages=self._max,
                )
                self.done.emit(paths)
                return
            if self._mode == "outlook":
                if not self._outlook_id or not self._dest:
                    self.failed.emit("Outlook: uygulama (istemci) kimliği ve indirme klasörü gerekli.")
                    return
                from cborn_docflow.mail.outlook_client import download_attachments as dl_out

                paths = dl_out(self._outlook_id, self._dest, max_messages=self._max)
                self.done.emit(paths)
                return
            self.failed.emit("Bilinmeyen mod.")
        except Exception as e:  # noqa: BLE001
            self.failed.emit(str(e))


def run() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("cborn DocFlow")
    app.setOrganizationName("cborn")
    settings = QSettings("cborn", "DocFlow")
    load_docflow()  # config/docflow.json yoksa oluşturur
    apply_theme(app, str(settings.value("ui/theme", "default", str)))

    win = QMainWindow()
    win.setWindowTitle("cborn DocFlow")
    win.resize(920, 640)

    tabs = QTabWidget()
    close_btn = QPushButton("Kapat")

    # --- Tab: Tek dosya ---
    tab_single = QWidget()
    single_layout = QVBoxLayout(tab_single)

    title = QLabel("cborn DocFlow — tek dosya")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    single_layout.addWidget(title)

    hint = QLabel(
        "Görüntü veya PDF seçin (PDF: en fazla "
        f"{PDF_MAX_PAGES} sayfa). Dil: tur+eng. "
        "Etiketler kural dosyasından; metni .txt kaydedebilirsin."
    )
    hint.setWordWrap(True)
    hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
    single_layout.addWidget(hint)

    status = QLabel("Hazır.")
    single_layout.addWidget(status)

    tags_line = QLabel("Etiketler: —")
    tags_line.setWordWrap(True)
    single_layout.addWidget(tags_line)

    out = QTextEdit()
    out.setReadOnly(True)
    out.setPlaceholderText("OCR çıktısı burada görünecek…")
    single_layout.addWidget(out, stretch=1)

    btn_row = QHBoxLayout()
    pick = QPushButton("Dosya seç ve OCR")
    save_btn = QPushButton("Metni kaydet…")
    save_btn.setEnabled(False)
    btn_row.addWidget(pick)
    btn_row.addWidget(save_btn)
    single_layout.addLayout(btn_row)

    ocr_thread: OcrThread | None = None
    last_single_path: Path | None = None

    def on_pick() -> None:
        nonlocal ocr_thread, last_single_path
        path, _ = QFileDialog.getOpenFileName(
            win,
            "Görüntü veya PDF seç",
            "",
            "Görüntü ve PDF (*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.webp *.pdf);;"
            "Görüntüler (*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.webp);;"
            "PDF (*.pdf);;Tüm dosyalar (*.*)",
        )
        if not path:
            return
        p = Path(path)

        pdf_mode: str | None = None
        if p.suffix.lower() == ".pdf":
            box = QMessageBox(win)
            box.setWindowTitle("PDF — cborn DocFlow")
            box.setText(f"{p.name}\nKaç sayfa OCR yapılsın?")
            box.setInformativeText(
                f"Tüm sayfalar uzun sürebilir; en fazla {PDF_MAX_PAGES} sayfa işlenir."
            )
            b_first = box.addButton("İlk sayfa", QMessageBox.AcceptRole)
            b_all = box.addButton("Tüm sayfalar", QMessageBox.ActionRole)
            b_cancel = box.addButton("İptal", QMessageBox.RejectRole)
            box.exec()
            clicked = box.clickedButton()
            if clicked is None or clicked == b_cancel:
                return
            if clicked == b_first:
                pdf_mode = "first"
            elif clicked == b_all:
                pdf_mode = "all"
            else:
                return

        if ocr_thread and ocr_thread.isRunning():
            QMessageBox.warning(win, "cborn DocFlow", "Önceki OCR bitene kadar bekle.")
            return

        out.clear()
        tags_line.setText("Etiketler: —")
        save_btn.setEnabled(False)
        label = "PDF" if pdf_mode else "Görüntü"
        status.setText(f"İşleniyor ({label}): {p.name} …")
        pick.setEnabled(False)

        last_single_path = p
        ocr_thread = OcrThread(p, pdf_mode=pdf_mode)

        def on_ok(text: str, conf: object) -> None:
            pick.setEnabled(True)
            out.setPlainText(text)
            rules, out_cfg = load_docflow()
            tags = match_tags(text, rules)
            if tags:
                tags_line.setText("Etiketler: " + ", ".join(tags))
            else:
                tags_line.setText("Etiketler: (henüz kural eşleşmedi)")

            extra = ""
            if last_single_path:
                dest = copy_to_output_if_enabled(last_single_path, tags, out_cfg)
                if dest:
                    extra = f" | Çıktı: {dest}"

            if conf is not None:
                status.setText(f"Tamam. Ortalama güven: {float(conf):.0%}{extra}")
            else:
                status.setText(f"Tamam. (Güven skoru alınamadı){extra}")
            save_btn.setEnabled(bool(text.strip()))

        def on_fail(msg: str) -> None:
            pick.setEnabled(True)
            status.setText("Hata.")
            out.setPlainText("")
            tags_line.setText("Etiketler: —")
            save_btn.setEnabled(False)
            QMessageBox.critical(win, "OCR hatası", msg)

        ocr_thread.finished_ok.connect(on_ok)
        ocr_thread.failed.connect(on_fail)
        ocr_thread.start()

    def on_save() -> None:
        text = out.toPlainText().strip()
        if not text:
            QMessageBox.information(win, "cborn DocFlow", "Kaydedilecek metin yok.")
            return
        path, _ = QFileDialog.getSaveFileName(
            win,
            "Metni kaydet",
            "",
            "Metin (*.txt);;Tüm dosyalar (*.*)",
        )
        if not path:
            return
        try:
            Path(path).write_text(text, encoding="utf-8")
        except OSError as e:
            QMessageBox.critical(win, "Kayıt hatası", str(e))
            return
        QMessageBox.information(win, "cborn DocFlow", f"Kaydedildi:\n{path}")

    pick.clicked.connect(on_pick)
    save_btn.clicked.connect(on_save)

    tabs.addTab(tab_single, "Tek dosya")

    # --- Tab: Klasör izleme ---
    tab_watch = QWidget()
    watch_layout = QVBoxLayout(tab_watch)

    watch_layout.addWidget(
        QLabel(
            "İzlenen klasöre yeni PDF veya görüntü düştüğünde otomatik OCR kuyruğa alınır.\n"
            "PDF: yalnızca ilk sayfa (hızlı). Görüntü: tek sayfa.\n"
            "İzleme başlayınca klasörde zaten duran dosyalar atlanır — test için alttaki "
            "«Mevcut…» düğmesini kullan veya dosyayı silip tekrar kopyala."
        )
    )

    folder_row = QHBoxLayout()
    watch_folder_edit = QLineEdit()
    watch_folder_edit.setPlaceholderText("Klasör yolu…")
    watch_folder_edit.setText(settings.value("watch/folder", "", str))
    browse_watch = QPushButton("Seç…")
    folder_row.addWidget(watch_folder_edit)
    folder_row.addWidget(browse_watch)
    watch_layout.addLayout(folder_row)

    watch_btns = QHBoxLayout()
    btn_watch_start = QPushButton("İzlemeyi başlat")
    btn_watch_stop = QPushButton("Durdur")
    btn_watch_stop.setEnabled(False)
    watch_btns.addWidget(btn_watch_start)
    watch_btns.addWidget(btn_watch_stop)
    watch_layout.addLayout(watch_btns)

    btn_enqueue_existing = QPushButton("Mevcut PDF/görüntüleri şimdi işle")
    watch_layout.addWidget(btn_enqueue_existing)

    watch_layout.addWidget(
        QLabel(
            "Çift tık: orijinal PDF/görüntüyü açar. Çıktı klasörüne kopya oluştuysa (ör. fatura) "
            "sağ tık → «Çıktı kopyasını aç»."
        )
    )
    watch_log = QListWidget()
    watch_log.setAlternatingRowColors(True)
    watch_log.setToolTip("Çift tık: kaynak dosya · Sağ tık: kopya varsa aç")
    watch_log.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    watch_layout.addWidget(watch_log, stretch=1)

    def watch_log_append(
        msg: str,
        file_path: Path | None = None,
        copy_path: Path | None = None,
    ) -> None:
        item = QListWidgetItem(msg)
        tip_parts: list[str] = []
        if file_path is not None:
            try:
                rp = file_path.resolve()
            except OSError:
                rp = file_path
            if rp.is_file():
                item.setData(_ROLE_FILE, str(rp))
                tip_parts.append(f"Kaynak:\n{rp}")
        if copy_path is not None:
            try:
                cp = copy_path.resolve()
            except OSError:
                cp = copy_path
            if cp.is_file():
                item.setData(_ROLE_COPY, str(cp))
                tip_parts.append(f"Çıktı kopyası:\n{cp}")
        if tip_parts:
            item.setToolTip("\n\n".join(tip_parts))
        watch_log.addItem(item)
        watch_log.scrollToItem(item)

    def on_watch_log_item_double_clicked(it: QListWidgetItem) -> None:
        raw = it.data(_ROLE_FILE)
        if not raw:
            return
        _open_local_file(Path(str(raw)))

    def on_watch_log_context_menu(pos) -> None:
        item = watch_log.itemAt(pos)
        if not item:
            return
        src = item.data(_ROLE_FILE)
        cpy = item.data(_ROLE_COPY)
        menu = QMenu(watch_log)
        if src:
            a = menu.addAction("Orijinal dosyayı aç")
            a.triggered.connect(lambda checked=False, p=str(src): _open_local_file(Path(p)))
        if cpy:
            b = menu.addAction("Çıktı kopyasını aç (fatura klasörü vb.)")
            b.triggered.connect(lambda checked=False, p=str(cpy): _open_local_file(Path(p)))
        if menu.actions():
            menu.exec(watch_log.mapToGlobal(pos))

    watch_log.itemDoubleClicked.connect(on_watch_log_item_double_clicked)
    watch_log.customContextMenuRequested.connect(on_watch_log_context_menu)

    watcher = QFileSystemWatcher()
    debounce = QTimer()
    debounce.setSingleShot(True)
    debounce.setInterval(600)

    baseline: set[str] = set()
    watch_worker = WatchWorker()

    def on_watch_worker_line(text: str, path_obj: object, copy_obj: object) -> None:
        src = path_obj if isinstance(path_obj, Path) else None
        cop = copy_obj if isinstance(copy_obj, Path) else None
        watch_log_append(text, src, cop)

    watch_worker.line.connect(on_watch_worker_line)

    def browse_watch_folder() -> None:
        d = QFileDialog.getExistingDirectory(win, "İzlenecek klasör", watch_folder_edit.text())
        if d:
            watch_folder_edit.setText(d)
            settings.setValue("watch/folder", d)

    def scan_inbox() -> None:
        nonlocal baseline
        raw = watch_folder_edit.text().strip()
        if not raw:
            return
        folder = Path(raw).expanduser().resolve()
        if not folder.is_dir():
            return
        current = _snapshot_supported(folder)
        new_paths = current - baseline
        baseline = current
        for s in sorted(new_paths):
            p = Path(s)
            try:
                if p.stat().st_size == 0:
                    continue
            except OSError:
                continue
            watch_worker.enqueue(p)
            watch_log_append(f"Kuyruk: {p.name}", p)

    def on_debounce() -> None:
        scan_inbox()

    debounce.timeout.connect(on_debounce)

    def on_dir_changed(_path: str) -> None:
        debounce.start()

    def start_watch() -> None:
        nonlocal baseline
        raw = watch_folder_edit.text().strip()
        if not raw:
            QMessageBox.warning(
                win,
                "cborn DocFlow",
                "Klasör yolu boş. «Seç…» ile bir klasör seç veya tam yolu yapıştır.",
            )
            return
        folder = Path(raw).expanduser().resolve()
        if not folder.is_dir():
            QMessageBox.warning(win, "cborn DocFlow", "Geçerli bir klasör seç.")
            return
        watch_folder_edit.setText(str(folder))
        settings.setValue("watch/folder", str(folder))
        baseline = _snapshot_supported(folder)
        watch_log_append(f"--- İzleme başladı: {folder} (mevcut dosyalar atlandı) ---")
        ok = watcher.addPath(str(folder))
        if not ok:
            QMessageBox.warning(win, "cborn DocFlow", "Klasör izlenemedi.")
            return
        btn_watch_start.setEnabled(False)
        btn_watch_stop.setEnabled(True)
        watch_folder_edit.setEnabled(False)
        browse_watch.setEnabled(False)

    def stop_watch() -> None:
        for p in watcher.directories():
            watcher.removePath(p)
        btn_watch_start.setEnabled(True)
        btn_watch_stop.setEnabled(False)
        watch_folder_edit.setEnabled(True)
        browse_watch.setEnabled(True)
        watch_log_append("--- İzleme durdu ---")

    watcher.directoryChanged.connect(on_dir_changed)

    def on_watch_start_clicked() -> None:
        if not watch_worker.isRunning():
            watch_worker.start()  # ilk kez; sonra hep aynı thread
        start_watch()

    def on_watch_stop_clicked() -> None:
        stop_watch()

    def on_enqueue_existing() -> None:
        raw = watch_folder_edit.text().strip()
        if not raw:
            QMessageBox.warning(
                win,
                "cborn DocFlow",
                "Önce bir klasör seç veya yol yaz.",
            )
            return
        folder = Path(raw).expanduser().resolve()
        if not folder.is_dir():
            QMessageBox.warning(win, "cborn DocFlow", "Geçerli bir klasör değil.")
            return
        if not watch_worker.isRunning():
            watch_worker.start()
        count = 0
        for p in sorted(folder.iterdir()):
            if not p.is_file() or p.suffix.lower() not in WATCH_EXTS:
                continue
            try:
                if p.stat().st_size == 0:
                    continue
            except OSError:
                continue
            rp = p.resolve()
            watch_worker.enqueue(rp)
            watch_log_append(f"Kuyruk (mevcut): {p.name}", rp)
            count += 1
        if count == 0:
            QMessageBox.information(
                win,
                "cborn DocFlow",
                "Bu klasörde işlenecek PDF veya görüntü yok.\n"
                f"Desteklenen uzantılar: {', '.join(sorted(WATCH_EXTS))}",
            )
        else:
            watch_log_append(f"--- {count} dosya kuyruğa alındı ---")

    browse_watch.clicked.connect(browse_watch_folder)
    btn_watch_start.clicked.connect(on_watch_start_clicked)
    btn_watch_stop.clicked.connect(on_watch_stop_clicked)
    btn_enqueue_existing.clicked.connect(on_enqueue_existing)

    tabs.addTab(tab_watch, "Klasör izleme")

    # --- Tab: E-posta (Gmail / Outlook ekleri) ---
    tab_mail = QWidget()
    mail_layout = QVBoxLayout(tab_mail)
    mail_help = QLabel(
        "Gmail veya Outlook gelen kutusundan (ekli) PDF ve görüntüleri indirir.\n"
        "«Gmail eklerini indir» veya «Outlook eklerini indir»e bastığınızda tarayıcı açılır; "
        "kendi hesabınızla giriş yapıp izin verirsiniz. Teknik kurulum yazılım sağlayıcısı içindir."
    )
    mail_help.setWordWrap(True)
    mail_layout.addWidget(mail_help)

    mail_notice = QLabel(
        "Bu alanlar yalnızca bu bilgisayardaki Windows kullanıcı hesabına kaydedilir; başka makineye "
        "veya müşteriye otomatik gitmez. İlk açılışta çoğu alan boştur — Gmail için OAuth yolunu "
        "genelde boş bırakın (paketlenmiş dosya kullanılır). Yanlış yapıştırmalardan kaçının."
    )
    mail_notice.setWordWrap(True)
    mail_notice.setObjectName("mailNotice")
    mail_layout.addWidget(mail_notice)

    mail_layout.addWidget(
        QLabel(
            "Gmail — isteğe bağlı özel OAuth dosyası (genelde boş; uygulama paketindeki istemci kullanılır):"
        )
    )
    gmail_row = QHBoxLayout()
    gmail_cred_edit = QLineEdit()
    gmail_cred_edit.setPlaceholderText("Boş = paket içi config/gmail_client_secret.json veya .exe yanı")
    gmail_cred_edit.setText(settings.value("mail/gmail_credentials", "", str))
    btn_gmail_cred = QPushButton("Gözat…")

    def browse_gmail_cred() -> None:
        p, _ = QFileDialog.getOpenFileName(
            win,
            "OAuth istemci JSON (yalnızca özel kurulumda)",
            "",
            "JSON (*.json);;Tüm dosyalar (*.*)",
        )
        if p:
            gmail_cred_edit.setText(p)
            settings.setValue("mail/gmail_credentials", p)

    btn_gmail_cred.clicked.connect(browse_gmail_cred)
    gmail_row.addWidget(gmail_cred_edit)
    gmail_row.addWidget(btn_gmail_cred)
    mail_layout.addLayout(gmail_row)

    mail_layout.addWidget(QLabel("Outlook — Azure uygulama (istemci) kimliği:"))
    outlook_id_edit = QLineEdit()
    outlook_id_edit.setPlaceholderText("xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
    outlook_id_edit.setText(settings.value("mail/outlook_client_id", "", str))
    mail_layout.addWidget(outlook_id_edit)

    dl_row = QHBoxLayout()
    mail_dl_edit = QLineEdit()
    _def_mail = str(Path.home() / "cborn-mail-in")
    mail_dl_edit.setText(settings.value("mail/download_folder", _def_mail, str))
    btn_mail_dl = QPushButton("İndirme klasörü…")

    def browse_mail_dl() -> None:
        d = QFileDialog.getExistingDirectory(win, "Eklerin kaydedileceği klasör", mail_dl_edit.text())
        if d:
            mail_dl_edit.setText(d)
            settings.setValue("mail/download_folder", d)

    btn_mail_dl.clicked.connect(browse_mail_dl)
    dl_row.addWidget(mail_dl_edit)
    dl_row.addWidget(btn_mail_dl)
    mail_layout.addLayout(dl_row)

    spin_mail_max = QSpinBox()
    spin_mail_max.setRange(1, 100)
    spin_mail_max.setValue(int(settings.value("mail/max_messages", 20, int)))
    mail_layout.addWidget(QLabel("Taranacak son mesaj sayısı (üst sınır):"))
    mail_layout.addWidget(spin_mail_max)

    chk_mail_queue = QCheckBox(
        "İndirilen dosyaları OCR kuyruğuna ekle (WatchWorker çalışıyor olmalı; gerekirse önce «İzlemeyi başlat»)"
    )
    chk_mail_queue.setChecked(False)
    mail_layout.addWidget(chk_mail_queue)

    mail_layout.addWidget(
        QLabel("İndirilen ek satırına çift tıklayınca PDF veya görüntü açılır (fatura ekleri dahil).")
    )
    mail_log = QListWidget()
    mail_log.setAlternatingRowColors(True)
    mail_log.setMinimumHeight(100)
    mail_log.setMaximumHeight(200)
    mail_log.setToolTip("Çift tık: indirilen dosyayı aç")
    mail_layout.addWidget(mail_log)

    def mail_log_append(msg: str, file_path: Path | None = None) -> None:
        item = QListWidgetItem(msg)
        if file_path is not None:
            try:
                rp = file_path.resolve()
            except OSError:
                rp = file_path
            if rp.is_file():
                item.setData(_ROLE_FILE, str(rp))
                item.setToolTip(str(rp))
        mail_log.addItem(item)
        mail_log.scrollToItem(item)

    def on_mail_log_double_clicked(it: QListWidgetItem) -> None:
        raw = it.data(_ROLE_FILE)
        if not raw:
            return
        _open_local_file(Path(str(raw)))

    mail_log.itemDoubleClicked.connect(on_mail_log_double_clicked)

    mail_btn_row = QHBoxLayout()
    btn_gmail_pull = QPushButton("Gmail eklerini indir")
    btn_outlook_pull = QPushButton("Outlook eklerini indir")
    mail_btn_row.addWidget(btn_gmail_pull)
    mail_btn_row.addWidget(btn_outlook_pull)
    mail_layout.addLayout(mail_btn_row)

    mail_pull_thread: EmailPullThread | None = None

    def on_mail_done(paths: object) -> None:
        pl = paths if isinstance(paths, list) else []
        mail_log_append(f"--- {len(pl)} dosya indi ---")
        for item in pl:
            pp = Path(item)
            label = str(pp) if pp.is_file() else str(item)
            mail_log_append(label, pp if pp.is_file() else None)
        if chk_mail_queue.isChecked() and pl:
            if not watch_worker.isRunning():
                watch_worker.start()
            for item in pl:
                watch_worker.enqueue(Path(item))
            mail_log_append("OCR kuyruğuna eklendi.")

    def on_mail_fail(msg: str) -> None:
        QMessageBox.critical(win, "E-posta", msg)

    def run_mail_pull(mode: str) -> None:
        nonlocal mail_pull_thread
        if mail_pull_thread and mail_pull_thread.isRunning():
            QMessageBox.warning(win, "E-posta", "Önceki indirme bitene kadar bekle.")
            return
        dest = Path(mail_dl_edit.text().strip())
        if not dest:
            QMessageBox.warning(win, "E-posta", "İndirme klasörü yazın veya seçin.")
            return
        settings.setValue("mail/download_folder", str(dest))
        settings.setValue("mail/max_messages", spin_mail_max.value())
        max_m = spin_mail_max.value()
        mail_log_append(f"--- Başlıyor: {mode} → {dest} ---")

        if mode == "gmail":
            gc = resolve_gmail_client_secret_path(gmail_cred_edit.text())
            if not gc:
                QMessageBox.warning(
                    win,
                    "Gmail",
                    "Gmail OAuth istemci dosyası bulunamadı. Uygulama ile birlikte gelen "
                    "gmail_client_secret.json beklenir (veya gelişmiş kullanımda dosya seçin). "
                    "Kurulum için yazılım sağlayıcınıza danışın.",
                )
                return
            settings.setValue("mail/gmail_credentials", gmail_cred_edit.text().strip())
            mail_pull_thread = EmailPullThread(
                "gmail",
                gmail_creds=gc,
                dest=dest,
                max_messages=max_m,
            )
        else:
            oid = outlook_id_edit.text().strip()
            if not oid:
                QMessageBox.warning(win, "Outlook", "Azure istemci kimliği girin.")
                return
            if not _OUTLOOK_CLIENT_ID_RE.match(oid):
                QMessageBox.warning(
                    win,
                    "Outlook",
                    "İstemci kimliği şu biçimde olmalıdır (tireler dahil):\n"
                    "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                )
                return
            settings.setValue("mail/outlook_client_id", oid)
            mail_pull_thread = EmailPullThread(
                "outlook",
                outlook_client_id=oid,
                dest=dest,
                max_messages=max_m,
            )

        mail_pull_thread.done.connect(on_mail_done)
        mail_pull_thread.failed.connect(on_mail_fail)
        mail_pull_thread.start()

    btn_gmail_pull.clicked.connect(lambda: run_mail_pull("gmail"))
    btn_outlook_pull.clicked.connect(lambda: run_mail_pull("outlook"))

    tabs.addTab(tab_mail, "E-posta")

    root = QWidget()
    root_layout = QVBoxLayout(root)
    root_layout.addWidget(tabs, stretch=1)
    cfg_lbl = QLabel(f"Ayar dosyası (kurallar + isteğe bağlı çıktı): {CONFIG_PATH}")
    cfg_lbl.setObjectName("configFooter")
    cfg_lbl.setWordWrap(True)
    root_layout.addWidget(cfg_lbl)

    close_row = QHBoxLayout()
    close_row.addWidget(QLabel("Renk teması:"))
    theme_combo = QComboBox()
    for tid, tlabel in THEME_CHOICES:
        theme_combo.addItem(tlabel, tid)
    saved_theme = str(settings.value("ui/theme", "default", str))
    theme_combo.blockSignals(True)
    for i in range(theme_combo.count()):
        if theme_combo.itemData(i) == saved_theme:
            theme_combo.setCurrentIndex(i)
            break
    else:
        theme_combo.setCurrentIndex(0)
    theme_combo.blockSignals(False)

    def on_theme_changed(_index: int) -> None:
        tid = theme_combo.currentData()
        if tid:
            settings.setValue("ui/theme", str(tid))
            apply_theme(app, str(tid))

    theme_combo.currentIndexChanged.connect(on_theme_changed)
    close_row.addWidget(theme_combo)
    close_row.addStretch()

    btn_settings = QPushButton("Ayarlar…")

    def open_settings() -> None:
        SettingsDialog(win).exec()

    close_row.addWidget(btn_settings)
    close_row.addWidget(close_btn)
    root_layout.addLayout(close_row)

    btn_settings.clicked.connect(open_settings)
    close_btn.clicked.connect(win.close)

    def on_about_to_quit() -> None:
        stop_watch()
        if watch_worker.isRunning():
            watch_worker.shutdown()
            watch_worker.wait(10_000)

    app.aboutToQuit.connect(on_about_to_quit)

    win.setCentralWidget(root)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
