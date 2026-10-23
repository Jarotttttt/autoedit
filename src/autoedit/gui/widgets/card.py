from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Card(QFrame):
    def __init__(
        self,
        title: str,
        *,
        subtitle: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Card")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 16)
        outer.setSpacing(10)

        self.header = QHBoxLayout()
        self.header.setContentsMargins(0, 0, 0, 0)
        self.header.setSpacing(8)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("CardTitle")
        self.header.addWidget(self.title_label)

        self.subtitle_label: QLabel | None = None
        if subtitle:
            self.subtitle_label = QLabel(subtitle)
            self.subtitle_label.setObjectName("Muted")
            self.header.addWidget(self.subtitle_label)

        self.header.addStretch(1)
        outer.addLayout(self.header)

        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(8)
        outer.addLayout(self.body, 1)

    def add_header_widget(self, widget: QWidget) -> None:
        self.header.addWidget(widget, 0, Qt.AlignmentFlag.AlignRight)


class FieldLabel(QLabel):
    def __init__(self, text: str) -> None:
        super().__init__(text.upper())
        self.setObjectName("FieldLabel")


class StatusLabel(QLabel):
    def __init__(self, text: str = "", tone: str = "muted") -> None:
        super().__init__(text)
        self.setWordWrap(True)
        self.set_tone(tone)

    def set_tone(self, tone: str) -> None:
        self.setObjectName(
            {
                "muted": "Muted",
                "success": "Success",
                "warning": "Warning",
                "danger": "Danger",
            }[tone]
        )
        self.style().unpolish(self)
        self.style().polish(self)


class PathRow(QWidget):
    def __init__(
        self,
        line_edit: QLineEdit,
        button_text: str,
        command,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.line_edit = line_edit
        self.line_edit.setCursorPosition(0)
        self.line_edit.textChanged.connect(
            lambda value: self.line_edit.setToolTip(value)
        )
        layout.addWidget(line_edit, 1)
        self.button = QPushButton(button_text)
        self.button.setObjectName("Small")
        self.button.clicked.connect(command)
        layout.addWidget(self.button, 0)
