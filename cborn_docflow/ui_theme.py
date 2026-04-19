"""Uygulama genelinde QSS ile renk temaları."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

# (ayar anahtarı, Türkçe ad)
THEME_CHOICES: tuple[tuple[str, str], ...] = (
    ("default", "Varsayılan (mavi)"),
    ("ocean", "Okyanus"),
    ("forest", "Orman"),
    ("sunset", "Gün batımı"),
    ("violet", "Mor"),
    ("dark", "Koyu"),
)


def _sheet_light(
    bg: str,
    surface: str,
    text: str,
    muted: str,
    accent: str,
    accent_hover: str,
    border: str,
) -> str:
    return f"""
    QWidget {{
        background-color: {bg};
        color: {text};
        font-size: 13px;
    }}
    QMainWindow {{
        background-color: {bg};
    }}
    QTabWidget::pane {{
        border: 1px solid {border};
        border-radius: 10px;
        top: -1px;
        background: {surface};
        padding: 4px;
    }}
    QTabBar::tab {{
        background: {bg};
        color: {text};
        padding: 10px 18px;
        margin-right: 3px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        border: 1px solid {border};
        border-bottom: none;
    }}
    QTabBar::tab:selected {{
        background: {accent};
        color: #ffffff;
        font-weight: 600;
        border-color: {accent};
    }}
    QTabBar::tab:hover:!selected {{
        background: {surface};
    }}
    QPushButton {{
        background-color: {accent};
        color: #ffffff;
        border: none;
        padding: 9px 18px;
        border-radius: 8px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {accent_hover};
    }}
    QPushButton:pressed {{
        background-color: {accent_hover};
    }}
    QPushButton:disabled {{
        background-color: #94a3b8;
        color: #e2e8f0;
    }}
    QLineEdit, QSpinBox, QPlainTextEdit, QTextEdit {{
        background: {surface};
        color: {text};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 6px 10px;
    }}
    QListWidget {{
        background: {surface};
        color: {text};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 4px;
    }}
    QListWidget::item {{
        padding: 6px;
        border-radius: 4px;
    }}
    QListWidget::item:selected {{
        background: {accent};
        color: #ffffff;
    }}
    QListWidget::item:hover:!selected {{
        background: {bg};
    }}
    QLabel[class="hint"] {{
        color: {muted};
        font-size: 12px;
    }}
    QCheckBox {{
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 2px solid {border};
    }}
    QCheckBox::indicator:checked {{
        background: {accent};
        border-color: {accent};
    }}
    QComboBox {{
        background: {surface};
        color: {text};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 8px 12px;
        min-width: 160px;
    }}
    QComboBox:hover {{
        border-color: {accent};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 28px;
    }}
    QComboBox QAbstractItemView {{
        background: {surface};
        color: {text};
        selection-background-color: {accent};
        selection-color: #ffffff;
        border: 1px solid {border};
        border-radius: 6px;
    }}
    QLabel#configFooter {{
        font-size: 11px;
        color: {muted};
    }}
    QLabel#mailNotice {{
        font-size: 12px;
        color: {muted};
    }}
    """


def _sheet_dark() -> str:
    bg = "#1a1b26"
    surface = "#24283b"
    text = "#c0caf5"
    muted = "#565f89"
    accent = "#7aa2f7"
    accent_hover = "#89b4fa"
    border = "#3b4261"
    return f"""
    QWidget {{
        background-color: {bg};
        color: {text};
        font-size: 13px;
    }}
    QMainWindow {{ background-color: {bg}; }}
    QTabWidget::pane {{
        border: 1px solid {border};
        border-radius: 10px;
        background: {surface};
        padding: 4px;
    }}
    QTabBar::tab {{
        background: {bg};
        color: {text};
        padding: 10px 18px;
        margin-right: 3px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        border: 1px solid {border};
        border-bottom: none;
    }}
    QTabBar::tab:selected {{
        background: {accent};
        color: #1a1b26;
        font-weight: 600;
        border-color: {accent};
    }}
    QTabBar::tab:hover:!selected {{ background: {surface}; }}
    QPushButton {{
        background-color: {accent};
        color: #1a1b26;
        border: none;
        padding: 9px 18px;
        border-radius: 8px;
        font-weight: 600;
    }}
    QPushButton:hover {{ background-color: {accent_hover}; color: #1a1b26; }}
    QPushButton:pressed {{ background-color: {accent_hover}; }}
    QLineEdit, QSpinBox, QPlainTextEdit, QTextEdit {{
        background: {bg};
        color: {text};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 6px 10px;
    }}
    QListWidget {{
        background: {bg};
        color: {text};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 4px;
    }}
    QListWidget::item {{ padding: 6px; border-radius: 4px; }}
    QListWidget::item:selected {{ background: {accent}; color: #1a1b26; }}
    QListWidget::item:hover:!selected {{ background: {surface}; }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 2px solid {border};
    }}
    QCheckBox::indicator:checked {{
        background: {accent};
        border-color: {accent};
    }}
    QComboBox {{
        background: {surface};
        color: {text};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 8px 12px;
        min-width: 160px;
    }}
    QComboBox:hover {{ border-color: {accent}; }}
    QComboBox QAbstractItemView {{
        background: {surface};
        color: {text};
        selection-background-color: {accent};
        selection-color: #1a1b26;
        border: 1px solid {border};
    }}
    QLabel#configFooter {{
        font-size: 11px;
        color: {muted};
    }}
    QLabel#mailNotice {{
        font-size: 12px;
        color: {muted};
    }}
    """


def build_stylesheet(theme_id: str) -> str:
    if theme_id == "dark":
        return _sheet_dark()
    if theme_id == "ocean":
        return _sheet_light(
            "#f0f9ff",
            "#ffffff",
            "#0c4a6e",
            "#0369a1",
            "#0284c7",
            "#0369a1",
            "#bae6fd",
        )
    if theme_id == "forest":
        return _sheet_light(
            "#f0fdf4",
            "#ffffff",
            "#14532d",
            "#166534",
            "#16a34a",
            "#15803d",
            "#bbf7d0",
        )
    if theme_id == "sunset":
        return _sheet_light(
            "#fff7ed",
            "#ffffff",
            "#7c2d12",
            "#c2410c",
            "#ea580c",
            "#c2410c",
            "#fed7aa",
        )
    if theme_id == "violet":
        return _sheet_light(
            "#f5f3ff",
            "#ffffff",
            "#4c1d95",
            "#6d28d9",
            "#7c3aed",
            "#6d28d9",
            "#ddd6fe",
        )
    # default
    return _sheet_light(
        "#f1f5f9",
        "#ffffff",
        "#0f172a",
        "#64748b",
        "#2563eb",
        "#1d4ed8",
        "#e2e8f0",
    )


def apply_theme(app: QApplication, theme_id: str) -> None:
    """Geçerli tema anahtarına göre global stil uygular."""
    valid = {t[0] for t in THEME_CHOICES}
    tid = theme_id if theme_id in valid else "default"
    app.setStyleSheet(build_stylesheet(tid))
