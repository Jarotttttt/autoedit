from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from ...speech.aligned import TimestampSource
from .card import Card, FieldLabel, PathRow, StatusLabel


class SourcePanel(Card):
    def __init__(self, app) -> None:
        super().__init__("Sumber bahan")
        self.app = app

        self.audio_edit = QLineEdit()
        self.audio_edit.setPlaceholderText("Pilih file audio narasi")
        self.body.addWidget(FieldLabel("Audio narasi"))
        self.body.addWidget(PathRow(self.audio_edit, "Pilih…", app.choose_audio))

        self.media_edit = QLineEdit()
        self.media_edit.setPlaceholderText("Pilih folder berisi gambar atau video")
        self.body.addWidget(FieldLabel("Folder media"))
        self.body.addWidget(PathRow(self.media_edit, "Pilih…", app.choose_media_dir))

        self.transcript_edit = QLineEdit()
        self.transcript_edit.setPlaceholderText("transcript.txt atau transcript.srt")
        self.body.addWidget(FieldLabel("Transcript (.txt / .srt)"))
        self.body.addWidget(
            PathRow(self.transcript_edit, "Pilih…", app.choose_transcript)
        )

        self.body.addWidget(FieldLabel("Sumber timestamp"))
        self.source_group = QWidget()
        self.source_group.setObjectName("Plain")
        self.source_layout = QVBoxLayout(self.source_group)
        self.source_layout.setContentsMargins(0, 0, 0, 0)
        self.source_layout.setSpacing(4)
        self.source_buttons: dict[TimestampSource, QRadioButton] = {}
        for source, text in (
            (TimestampSource.AUTO, "Otomatis (.srt → SRT, .txt → Whisper)"),
            (TimestampSource.WHISPER, "Whisper (audio → timestamp)"),
            (TimestampSource.SRT, "File SRT (timestamp asli)"),
        ):
            button = QRadioButton(text)
            button.toggled.connect(app.on_source_changed)
            self.source_buttons[source] = button
            self.source_layout.addWidget(button)
        self.body.addWidget(self.source_group)

        self.hint = StatusLabel()
        self.body.addWidget(self.hint)

    def current_source(self) -> TimestampSource:
        for source, button in self.source_buttons.items():
            if button.isChecked():
                return source
        return TimestampSource.AUTO

    def set_source(self, source: TimestampSource) -> None:
        self.source_buttons[source].setChecked(True)

    def set_paths(self, audio: str, media: str, transcript: str) -> None:
        self.audio_edit.setText(audio)
        self.media_edit.setText(media)
        self.transcript_edit.setText(transcript)
        for edit in (self.audio_edit, self.media_edit, self.transcript_edit):
            edit.setCursorPosition(0)


class SettingsPanel(Card):
    def __init__(self, app) -> None:
        super().__init__("Pengaturan video")
        self.app = app

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(1, 1)

        self.canvas_combo = QComboBox()
        self.canvas_combo.addItems(app.canvas_choices)
        self.canvas_combo.currentTextChanged.connect(app.on_canvas_changed)
        grid.addWidget(FieldLabel("Resolusi"), 0, 0)
        grid.addWidget(self.canvas_combo, 0, 1)

        self.fps_combo = QComboBox()
        self.fps_combo.addItems(("24", "25", "30", "60"))
        grid.addWidget(FieldLabel("FPS"), 1, 0)
        grid.addWidget(self.fps_combo, 1, 1)

        shot_row = QWidget()
        shot_row.setObjectName("Plain")
        shot_layout = QHBoxLayout(shot_row)
        shot_layout.setContentsMargins(0, 0, 0, 0)
        shot_layout.setSpacing(6)
        self.shot_edit = QLineEdit()
        self.shot_edit.setFixedWidth(64)
        shot_layout.addWidget(self.shot_edit)
        shot_layout.addWidget(QLabel("detik"))
        shot_layout.addStretch(1)
        grid.addWidget(FieldLabel("Durasi per shot"), 2, 0)
        grid.addWidget(shot_row, 2, 1)

        self.language_combo = QComboBox()
        self.language_combo.addItems(app.language_choices)
        grid.addWidget(FieldLabel("Bahasa audio"), 3, 0)
        grid.addWidget(self.language_combo, 3, 1)

        self.model_combo = QComboBox()
        self.model_combo.addItems(("tiny", "base", "small", "medium"))
        self.model_combo.currentTextChanged.connect(app.on_source_changed)
        grid.addWidget(FieldLabel("Model Whisper"), 4, 0)
        grid.addWidget(self.model_combo, 4, 1)

        self.body.addLayout(grid)

        self.motion_check = QCheckBox("Gerakan halus (zoom / pan)")
        self.captions_check = QCheckBox("Tempel caption ke video")
        self.body.addWidget(self.motion_check)
        self.body.addWidget(self.captions_check)

    def values(self) -> dict[str, object]:
        return {
            "canvas": self.canvas_combo.currentText(),
            "fps": int(self.fps_combo.currentText()),
            "shot": self.shot_edit.text().strip(),
            "language": self.language_combo.currentText(),
            "model": self.model_combo.currentText(),
            "motion": self.motion_check.isChecked(),
            "captions": self.captions_check.isChecked(),
        }

    def apply_values(
        self,
        *,
        canvas: str,
        fps: int,
        shot: str,
        language: str,
        model: str,
        motion: bool,
        captions: bool,
    ) -> None:
        if canvas:
            self.canvas_combo.setCurrentText(canvas)
        self.fps_combo.setCurrentText(str(fps))
        self.shot_edit.setText(shot)
        self.language_combo.setCurrentText(language)
        self.model_combo.setCurrentText(model)
        self.motion_check.setChecked(motion)
        self.captions_check.setChecked(captions)


class OutputPanel(Card):
    def __init__(self, app) -> None:
        super().__init__("Hasil")
        self.app = app

        self.name_edit = QLineEdit()
        self.body.addWidget(FieldLabel("Nama project"))
        self.body.addWidget(self.name_edit)

        self.output_edit = QLineEdit()
        self.body.addWidget(FieldLabel("Folder output"))
        self.body.addWidget(PathRow(self.output_edit, "Pilih…", app.choose_output))

        note = QLabel("Video dan manifest timeline disimpan di folder ini.")
        note.setObjectName("Muted")
        note.setWordWrap(True)
        self.body.addWidget(note)
