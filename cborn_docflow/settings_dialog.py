"""docflow.json düzenleme penceresi."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from cborn_docflow.engine.docflow_config import OutputSettings, load_docflow_raw, save_docflow_raw


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("cborn DocFlow — Ayarlar")
        self.resize(720, 480)

        layout = QVBoxLayout(self)

        rules_box = QGroupBox("Etiket kuralları (regex)")
        rules_layout = QVBoxLayout(rules_box)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(
            ["Ad", "Pattern (regex)", "Etiket", "Büyük/küçük harf yok say"]
        )
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        rules_layout.addWidget(self._table)

        row_btns = QHBoxLayout()
        btn_add = QPushButton("Satır ekle")
        btn_del = QPushButton("Satır sil")
        row_btns.addWidget(btn_add)
        row_btns.addWidget(btn_del)
        row_btns.addStretch()
        rules_layout.addLayout(row_btns)

        btn_add.clicked.connect(self._add_row)
        btn_del.clicked.connect(self._remove_row)

        layout.addWidget(rules_box)

        out_box = QGroupBox("İşlenen dosyayı kopyala (çıktı klasörü)")
        out_form = QFormLayout(out_box)
        self._out_on = QCheckBox("Aktif")
        self._out_dir = QLineEdit()
        btn_browse = QPushButton("Klasör…")
        w_dir = QWidget()
        dir_row = QHBoxLayout(w_dir)
        dir_row.addWidget(self._out_dir)
        dir_row.addWidget(btn_browse)
        out_form.addRow(self._out_on)
        out_form.addRow("Hedef klasör:", w_dir)
        self._out_by_tag = QCheckBox("Etiket alt klasörü oluştur")
        self._out_unmatched = QLineEdit()
        out_form.addRow(self._out_by_tag)
        out_form.addRow("Etiketsiz dosyalar alt klasörü:", self._out_unmatched)

        btn_browse.clicked.connect(self._browse_out)
        layout.addWidget(out_box)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._load_data()

    def _load_data(self) -> None:
        rules, out = load_docflow_raw()
        self._table.setRowCount(0)
        for r in rules:
            self._add_row_data(
                r.get("name", ""),
                r.get("pattern", ""),
                r.get("tag", ""),
                r.get("ignore_case", True),
            )
        if self._table.rowCount() == 0:
            self._add_row_data("örnek", r"fatura|invoice", "fatura", True)

        self._out_on.setChecked(out.enabled)
        self._out_dir.setText(out.directory)
        self._out_by_tag.setChecked(out.by_tag_subfolders)
        self._out_unmatched.setText(out.unmatched_subfolder)

    def _add_row_data(
        self,
        name: str,
        pattern: str,
        tag: str,
        ignore_case: bool,
    ) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setItem(row, 0, QTableWidgetItem(name))
        self._table.setItem(row, 1, QTableWidgetItem(pattern))
        self._table.setItem(row, 2, QTableWidgetItem(tag))
        chk = QTableWidgetItem()
        chk.setFlags(
            Qt.ItemFlag.ItemIsUserCheckable
            | Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
        )
        chk.setCheckState(
            Qt.CheckState.Checked if ignore_case else Qt.CheckState.Unchecked
        )
        self._table.setItem(row, 3, chk)

    def _add_row(self) -> None:
        self._add_row_data("", "", "", True)

    def _remove_row(self) -> None:
        r = self._table.currentRow()
        if r >= 0:
            self._table.removeRow(r)

    def _browse_out(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Çıktı klasörü", self._out_dir.text())
        if d:
            self._out_dir.setText(d)

    def _collect_rules(self) -> list[dict]:
        rules: list[dict] = []
        for row in range(self._table.rowCount()):
            def cell(col: int) -> str:
                it = self._table.item(row, col)
                return it.text().strip() if it else ""

            name = cell(0) or f"kural_{row + 1}"
            pattern = cell(1)
            tag = cell(2)
            if not pattern or not tag:
                continue
            ign_it = self._table.item(row, 3)
            ign = (
                ign_it.checkState() == Qt.CheckState.Checked
                if ign_it
                else True
            )
            rules.append(
                {
                    "name": name,
                    "pattern": pattern,
                    "tag": tag,
                    "ignore_case": ign,
                }
            )
        return rules

    def _on_save(self) -> None:
        rules = self._collect_rules()
        if not rules:
            QMessageBox.warning(
                self,
                "Ayarlar",
                "En az bir geçerli kural gerekli (pattern ve etiket dolu olsun).",
            )
            return
        out = OutputSettings(
            enabled=self._out_on.isChecked(),
            directory=self._out_dir.text().strip(),
            by_tag_subfolders=self._out_by_tag.isChecked(),
            unmatched_subfolder=self._out_unmatched.text().strip() or "_diger",
        )
        if out.enabled and not out.directory:
            QMessageBox.warning(
                self,
                "Ayarlar",
                "Çıktı aktifken hedef klasör yazılmalı.",
            )
            return
        try:
            save_docflow_raw(rules, out)
        except ValueError as e:
            QMessageBox.critical(self, "Kayıt hatası", str(e))
            return
        self.accept()
