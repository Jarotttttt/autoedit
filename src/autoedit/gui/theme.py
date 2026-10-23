from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

BACKGROUND = "#0f1319"
SURFACE = "#161c25"
SURFACE_RAISED = "#1d2531"
SURFACE_HOVER = "#232d3b"
BORDER = "#28323f"
BORDER_FOCUS = "#4f8cff"
TEXT = "#e9eef6"
TEXT_MUTED = "#8b98a9"
ACCENT = "#4f8cff"
ACCENT_HOVER = "#6ba0ff"
ACCENT_PRESSED = "#3c72db"
SUCCESS = "#43bf7c"
WARNING = "#f0b429"
DANGER = "#ef5b5b"
SELECTION = "#2b3a4f"

FONT_FAMILY = "Segoe UI"

ASSET_ROOT = Path(__file__).resolve().parent.parent / "assets"
ICON_CHEVRON = (ASSET_ROOT / "chevron-down.png").as_posix()
ICON_CHEVRON_HOVER = (ASSET_ROOT / "chevron-down-hover.png").as_posix()
ICON_CHECK = (ASSET_ROOT / "check.png").as_posix()

STYLESHEET = f"""
QWidget {{
    background-color: {BACKGROUND};
    color: {TEXT};
    font-family: "{FONT_FAMILY}";
    font-size: 9pt;
}}

QFrame#Card {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}

QFrame#ActionCard {{
    background: transparent;
    border: none;
}}

QLabel {{
    background: transparent;
}}

QLabel#Title {{
    font-size: 18pt;
    font-weight: 700;
    color: {TEXT};
}}

QLabel#Subtitle {{
    font-size: 9pt;
    color: {TEXT_MUTED};
}}

QLabel#CardTitle {{
    font-size: 10pt;
    font-weight: 700;
    color: {TEXT};
}}

QLabel#FieldLabel {{
    font-size: 8pt;
    font-weight: 600;
    color: {TEXT_MUTED};
}}

QLabel#Muted {{
    color: {TEXT_MUTED};
}}

QLabel#Success {{
    color: {SUCCESS};
}}

QLabel#Warning {{
    color: {WARNING};
}}

QLabel#Danger {{
    color: {DANGER};
}}

QLabel#Badge {{
    background-color: {SURFACE_RAISED};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 5px 12px;
    color: {SUCCESS};
    font-weight: 600;
}}

QLabel#BadgeWarning {{
    background-color: {SURFACE_RAISED};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 5px 12px;
    color: {WARNING};
    font-weight: 600;
}}

QLineEdit {{
    background-color: {SURFACE_RAISED};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 6px 9px;
    selection-background-color: {ACCENT};
    selection-color: #ffffff;
}}

QLineEdit:focus {{
    border: 1px solid {BORDER_FOCUS};
}}

QLineEdit:disabled {{
    color: {TEXT_MUTED};
}}

QComboBox {{
    background-color: {SURFACE_RAISED};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 5px 9px;
}}

QComboBox:hover {{
    border: 1px solid {SURFACE_HOVER};
}}

QComboBox:focus {{
    border: 1px solid {BORDER_FOCUS};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    image: url({ICON_CHEVRON});
    width: 12px;
    height: 12px;
    margin-right: 6px;
}}

QComboBox::down-arrow:hover {{
    image: url({ICON_CHEVRON_HOVER});
}}

QComboBox QAbstractItemView {{
    background-color: {SURFACE_RAISED};
    border: 1px solid {BORDER};
    border-radius: 7px;
    selection-background-color: {ACCENT};
    selection-color: #ffffff;
    outline: none;
    padding: 3px;
}}

QPushButton {{
    background-color: {SURFACE_RAISED};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 7px 14px;
    color: {TEXT};
}}

QPushButton:hover {{
    background-color: {SURFACE_HOVER};
    border: 1px solid {BORDER_FOCUS};
}}

QPushButton:pressed {{
    background-color: {BORDER};
}}

QPushButton:disabled {{
    color: {TEXT_MUTED};
    background-color: {SURFACE};
    border: 1px solid {BORDER};
}}

QPushButton#Primary {{
    background-color: {ACCENT};
    border: 1px solid {ACCENT};
    color: #ffffff;
    font-size: 10pt;
    font-weight: 700;
    padding: 10px 26px;
    border-radius: 8px;
}}

QPushButton#Primary:hover {{
    background-color: {ACCENT_HOVER};
    border: 1px solid {ACCENT_HOVER};
}}

QPushButton#Primary:pressed {{
    background-color: {ACCENT_PRESSED};
}}

QPushButton#Primary:disabled {{
    background-color: {BORDER};
    border: 1px solid {BORDER};
    color: {TEXT_MUTED};
}}

QPushButton#Small {{
    padding: 5px 10px;
    font-size: 8pt;
}}

QWidget#Plain {{
    background: transparent;
}}

QCheckBox {{
    background: transparent;
    spacing: 8px;
    padding: 2px 0;
}}

QRadioButton {{
    background: transparent;
    spacing: 8px;
    padding: 2px 0;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {BORDER};
    border-radius: 4px;
    background-color: {SURFACE_RAISED};
    image: none;
}}

QCheckBox::indicator:unchecked {{
    border: 1px solid {BORDER};
    border-radius: 4px;
    background-color: {SURFACE_RAISED};
    image: none;
}}

QCheckBox::indicator:unchecked:hover {{
    border: 1px solid {BORDER_FOCUS};
    border-radius: 4px;
    background-color: {SURFACE_HOVER};
    image: none;
}}

QCheckBox::indicator:checked {{
    border: 1px solid {ACCENT};
    border-radius: 4px;
    background-color: {ACCENT};
    image: url({ICON_CHECK});
}}

QCheckBox::indicator:checked:hover {{
    border: 1px solid {ACCENT_HOVER};
    border-radius: 4px;
    background-color: {ACCENT_HOVER};
    image: url({ICON_CHECK});
}}

QCheckBox::indicator:checked:disabled {{
    border: 1px solid {BORDER};
    border-radius: 4px;
    background-color: {BORDER};
    image: none;
}}

QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {BORDER};
    border-radius: 8px;
    background-color: {SURFACE_RAISED};
    image: none;
}}

QRadioButton::indicator:unchecked {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    background-color: {SURFACE_RAISED};
    image: none;
}}

QRadioButton::indicator:unchecked:hover {{
    border: 1px solid {BORDER_FOCUS};
    border-radius: 8px;
    background-color: {SURFACE_HOVER};
    image: none;
}}

QRadioButton::indicator:checked {{
    border: 1px solid {ACCENT};
    border-radius: 8px;
    background-color: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 {SURFACE}, stop:0.42 {SURFACE}, stop:0.5 {ACCENT}, stop:1 {ACCENT});
    image: none;
}}

QRadioButton::indicator:checked:hover {{
    border: 1px solid {ACCENT_HOVER};
    border-radius: 8px;
    background-color: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 {SURFACE}, stop:0.42 {SURFACE}, stop:0.5 {ACCENT_HOVER}, stop:1 {ACCENT_HOVER});
    image: none;
}}

QRadioButton::indicator:checked:disabled {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    background-color: {BORDER};
    image: none;
}}

QCheckBox:disabled, QRadioButton:disabled {{
    color: {TEXT_MUTED};
}}

QTableWidget {{
    background-color: {SURFACE_RAISED};
    border: 1px solid {BORDER};
    border-radius: 8px;
    gridline-color: transparent;
    selection-background-color: {ACCENT};
    selection-color: #ffffff;
    outline: none;
    alternate-background-color: #212a36;
}}

QTableWidget::item {{
    padding: 4px 6px;
    border: none;
}}

QTableWidget::item:selected {{
    background-color: {ACCENT};
    color: #ffffff;
}}

QHeaderView::section {{
    background-color: {SURFACE};
    color: {TEXT_MUTED};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 7px 6px;
    font-size: 8pt;
    font-weight: 700;
}}

QTableCornerButton::section {{
    background-color: {SURFACE};
    border: none;
}}

QProgressBar {{
    background-color: {SURFACE_RAISED};
    border: 1px solid {BORDER};
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: transparent;
}}

QProgressBar::chunk {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT_PRESSED}, stop:1 {ACCENT_HOVER});
    border-radius: 3px;
    margin: 0;
}}

QScrollArea {{
    background: transparent;
    border: none;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {SURFACE_HOVER};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: #2f3c4d;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
}}

QScrollBar::handle:horizontal {{
    background-color: {SURFACE_HOVER};
    border-radius: 5px;
    min-width: 30px;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

QToolTip {{
    background-color: {SURFACE_RAISED};
    color: {TEXT};
    border: 1px solid {BORDER};
    padding: 5px;
    border-radius: 5px;
}}

QMessageBox {{
    background-color: {SURFACE};
}}

QMessageBox QLabel {{
    color: {TEXT};
}}

QSplitter::handle {{
    background: transparent;
}}

QStatusBar {{
    background: {SURFACE};
}}
"""


def apply(app: QApplication) -> None:
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(BACKGROUND))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Base, QColor(SURFACE_RAISED))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(SURFACE))
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Button, QColor(SURFACE_RAISED))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(SURFACE_RAISED))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(TEXT))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)
