from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from ...core.numbering import inspect_numbering
from ...core.probe import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
from ...core.scanner import scan_media
from .card import Card, StatusLabel
from ..theme import TEXT_MUTED


def format_duration(duration_us: int) -> str:
    if duration_us <= 0:
        return "—"
    total = duration_us / 1_000_000
    minutes = int(total // 60)
    seconds = total - minutes * 60
    return f"{minutes:02d}:{seconds:05.2f}"


class MediaTable(Card):
    def __init__(self, app) -> None:
        super().__init__("Urutan media", subtitle="0 file")
        self.app = app
        self.paths: list[Path] = []
        self._durations: dict[Path, str] = {}
        self._kinds: dict[Path, str] = {}

        self.up_button = QPushButton("↑ Naik")
        self.up_button.setObjectName("Small")
        self.up_button.clicked.connect(lambda: app.move_media(-1))
        self.down_button = QPushButton("↓ Turun")
        self.down_button.setObjectName("Small")
        self.down_button.clicked.connect(lambda: app.move_media(1))
        self.reload_button = QPushButton("↻ Muat ulang")
        self.reload_button.setObjectName("Small")
        self.reload_button.clicked.connect(app.reload_media)

        self.add_header_widget(self.reload_button)
        self.add_header_widget(self.down_button)
        self.add_header_widget(self.up_button)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["#", "Nama file", "Jenis", "Durasi"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.table.verticalHeader().setDefaultSectionSize(28)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 48)
        self.table.setColumnWidth(2, 86)
        self.table.setColumnWidth(3, 96)

        self.table.itemSelectionChanged.connect(app.on_media_selected)
        self.body.addWidget(self.table, 1)

        self.warning = StatusLabel("Pilih folder media untuk memuat file.")
        self.body.addWidget(self.warning)

    def set_count(self, count: int) -> None:
        if self.subtitle_label is not None:
            self.subtitle_label.setText(f"{count} file")

    def load(self, folder: Path | None) -> None:
        self.paths = []
        self._durations.clear()
        self._kinds.clear()
        if folder is not None and folder.is_dir():
            try:
                self.paths = scan_media(folder)
            except FileNotFoundError:
                self.paths = []
        self.refresh()

    def refresh(self, selected: int | None = None) -> None:
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self.table.setRowCount(len(self.paths))
        for index, path in enumerate(self.paths):
            order = QTableWidgetItem(str(index + 1))
            order.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            name = QTableWidgetItem(path.name)
            kind = QTableWidgetItem(self._kinds.get(path, self._guess_kind(path)))
            kind.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            duration = QTableWidgetItem(self._durations.get(path, "—"))
            duration.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            for column, item in enumerate((order, name, kind, duration)):
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.table.setItem(index, column, item)
        self.table.blockSignals(False)
        self.set_count(len(self.paths))
        if selected is not None and 0 <= selected < len(self.paths):
            self.table.selectRow(selected)
        self._update_warning()

    def update_probe(self, index: int, duration_us: int, kind: str) -> None:
        if not 0 <= index < len(self.paths):
            return
        path = self.paths[index]
        self._durations[path] = format_duration(duration_us)
        self._kinds[path] = kind
        kind_item = self.table.item(index, 2)
        duration_item = self.table.item(index, 3)
        if kind_item is not None:
            kind_item.setText(kind)
        if duration_item is not None:
            duration_item.setText(self._durations[path])

    def selected_index(self) -> int | None:
        rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        if not rows:
            return None
        return rows[0].row()

    def _update_warning(self) -> None:
        if not self.paths:
            self.warning.setText("Pilih folder media untuk memuat file.")
            self.warning.set_tone("muted")
            return
        report = inspect_numbering(self.paths)
        messages: list[str] = []
        if report.missing_numbers:
            numbers = ", ".join(f"{number:03d}" for number in report.missing_numbers)
            messages.append(f"Nomor urut hilang: {numbers}")
        if report.duplicate_numbers:
            numbers = ", ".join(f"{number:03d}" for number in report.duplicate_numbers)
            messages.append(f"Nomor urut ganda: {numbers}")
        if report.unnumbered:
            messages.append(f"{len(report.unnumbered)} file tanpa nomor di awal nama")
        if messages:
            self.warning.setText(" · ".join(messages))
            self.warning.set_tone("warning")
        else:
            self.warning.setText("Urutan media sesuai nomor pada nama file.")
            self.warning.set_tone("success")

    @staticmethod
    def _guess_kind(path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in VIDEO_EXTENSIONS:
            return "Video"
        if suffix in IMAGE_EXTENSIONS:
            return "Gambar"
        return "?"


class PreviewPanel(Card):
    def __init__(self, app) -> None:
        super().__init__("Pratinjau")
        self.app = app
        self._pixmap: QPixmap | None = None
        self._path: Path | None = None

        self.image = QLabel("Pilih file media untuk melihat pratinjau")
        self.image.setObjectName("Muted")
        self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image.setMinimumHeight(170)
        self.image.setStyleSheet(
            f"background-color: #1d2531; border-radius: 8px; color: {TEXT_MUTED};"
        )
        self.body.addWidget(self.image, 1)

    def show_path(self, path: Path | None) -> None:
        self._path = path
        if path is None or not path.is_file():
            self._pixmap = None
            self.image.setPixmap(QPixmap())
            self.image.setText("Pilih file media untuk melihat pratinjau")
            return
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            self._pixmap = None
            self.image.setPixmap(QPixmap())
            self.image.setText(f"🎞  {path.name}\n(video)")
            return
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self._pixmap = None
            self.image.setPixmap(QPixmap())
            self.image.setText(f"Gagal memuat pratinjau: {path.name}")
            return
        self._pixmap = pixmap
        self._render()

    def _render(self) -> None:
        if self._pixmap is None:
            return
        size = self.image.size()
        target = self._pixmap.scaled(
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image.setPixmap(target)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._render()


class ActionBar(Card):
    def __init__(self, app) -> None:
        super().__init__("")
        self.app = app
        self.setObjectName("ActionCard")
        self.layout().removeItem(self.header)
        self.layout().setContentsMargins(4, 6, 4, 6)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(14)

        self.open_button = QPushButton("Buka folder output")
        self.open_button.clicked.connect(app.open_output)
        row.addWidget(self.open_button, 0, Qt.AlignmentFlag.AlignVCenter)

        self.status = StatusLabel("Siap")
        self.status.setWordWrap(False)
        row.addWidget(self.status, 1, Qt.AlignmentFlag.AlignVCenter)

        self.build_button = QPushButton("Buat video  →")
        self.build_button.setObjectName("Primary")
        self.build_button.clicked.connect(app.start_build)
        row.addWidget(self.build_button, 0, Qt.AlignmentFlag.AlignVCenter)

        self.body.addLayout(row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(4)
        self.body.addWidget(self.progress)
