from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QSize, Qt, QThread, QThreadPool, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..app import pipeline, settings
from ..core.manifest import CanvasSpec, seconds_to_us
from ..core.planner import PlannerConfig
from ..core.probe import VIDEO_EXTENSIONS, ProbeError, probe_media
from ..core.scanner import scan_media
from ..render.ffmpeg import ffmpeg_available
from ..runtime import resource_path
from ..speech.aligned import TimestampSource
from ..speech.whisper import WhisperConfig, whisper_available
from . import theme
from .widgets.media_table import ActionBar, MediaTable, PreviewPanel
from .widgets.settings_panel import OutputPanel, SettingsPanel, SourcePanel

CANVAS_PRESETS = {
    "1920×1080 (16:9)": CanvasSpec(1920, 1080),
    "1280×720 (16:9)": CanvasSpec(1280, 720),
    "1080×1920 (9:16)": CanvasSpec(1080, 1920),
    "1080×1080 (1:1)": CanvasSpec(1080, 1080),
    "3840×2160 (4K)": CanvasSpec(3840, 2160, 30),
}

LANGUAGE_CHOICES = ("auto", "Indonesia", "English", "Jepang", "Korea", "Mandarin")

SOURCE_LABELS = {
    TimestampSource.AUTO: "Otomatis",
    TimestampSource.WHISPER: "Whisper",
    TimestampSource.SRT: "SRT",
}


class BuildThread(QThread):
    progress = Signal(float, str)
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, request: pipeline.BuildRequest) -> None:
        super().__init__()
        self.request = request

    def run(self) -> None:
        try:
            result = pipeline.build(
                self.request,
                progress_callback=lambda value, message: self.progress.emit(
                    float(value), str(message)
                ),
            )
        except BaseException as error:
            self.failed.emit(str(error))
            return
        self.completed.emit(result)


class ProbeSignals(QObject):
    probed = Signal(int, int, str)
    finished = Signal(int)


class ProbeJob(QRunnable):
    def __init__(
        self, paths: list[Path], generation: int, signals: ProbeSignals
    ) -> None:
        super().__init__()
        self.paths = paths
        self.generation = generation
        self.signals = signals

    def run(self) -> None:
        for index, path in enumerate(self.paths):
            try:
                info = probe_media(path)
            except ProbeError:
                self.signals.probed.emit(index, 0, "?")
                continue
            kind = "Video" if path.suffix.lower() in VIDEO_EXTENSIONS else "Gambar"
            self.signals.probed.emit(index, info.duration_us, kind)
        self.signals.finished.emit(self.generation)


class AutoEditWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("autoedit")
        self.setMinimumSize(QSize(1180, 720))
        self.resize(1440, 860)

        preferences = settings.load()
        self.canvas_choices = tuple(CANVAS_PRESETS)
        self.language_choices = LANGUAGE_CHOICES
        self.worker: BuildThread | None = None
        self._paths: list[Path] = []
        self._probe_generation = 0
        self._probe_pool = QThreadPool(self)
        self._probe_pool.setMaxThreadCount(1)
        self._probe_signals = ProbeSignals(self)
        self._probe_signals.probed.connect(self._on_probed)
        self._probe_signals.finished.connect(self._on_probe_finished)

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 14, 18, 8)
        root.setSpacing(10)

        root.addLayout(self._build_header())

        content = QHBoxLayout()
        content.setSpacing(12)
        content.addWidget(self._build_sidebar(), 0)

        right = QVBoxLayout()
        right.setSpacing(10)
        self.media_table = MediaTable(self)
        right.addWidget(self.media_table, 1)
        self.preview = PreviewPanel(self)
        self.preview.setMaximumHeight(260)
        right.addWidget(self.preview, 0)
        content.addLayout(right, 1)
        root.addLayout(content, 1)

        self.action_bar = ActionBar(self)
        root.addWidget(self.action_bar, 0)

        self.setCentralWidget(central)
        self._apply_preferences(preferences)
        self.refresh_source_hint()
        self.detect_runtime()
        if self.source_panel.media_edit.text().strip():
            self.reload_media()

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(10)

        titles = QVBoxLayout()
        titles.setSpacing(2)
        title = QLabel("autoedit")
        title.setObjectName("Title")
        subtitle = QLabel(
            "Narasi audio + media berurutan + transcript → video siap pakai"
        )
        subtitle.setObjectName("Subtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header.addLayout(titles, 1)

        self.runtime_badge = QLabel("")
        self.runtime_badge.setObjectName("Badge")
        header.addWidget(self.runtime_badge, 0, Qt.AlignmentFlag.AlignVCenter)
        return header

    def _build_sidebar(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(12)

        self.source_panel = SourcePanel(self)
        layout.addWidget(self.source_panel)

        self.settings_panel = SettingsPanel(self)
        layout.addWidget(self.settings_panel)

        self.output_panel = OutputPanel(self)
        layout.addWidget(self.output_panel)

        layout.addStretch(1)
        scroll.setWidget(inner)

        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.addWidget(scroll)
        wrapper.setFixedWidth(404)
        return wrapper

    def _apply_preferences(self, preferences: settings.Settings) -> None:
        self.source_panel.set_paths(
            preferences.audio_path,
            preferences.media_dir,
            preferences.transcript_path,
        )
        known_sources = {item.value for item in TimestampSource}
        self.source_panel.set_source(
            TimestampSource(preferences.source)
            if preferences.source in known_sources
            else TimestampSource.AUTO
        )
        self.output_panel.name_edit.setText(preferences.project_name)
        self.output_panel.output_edit.setText(
            preferences.output_dir or str(Path.home() / "Videos" / "autoedit")
        )

        target = (preferences.canvas_width, preferences.canvas_height)
        canvas_label = next(
            (
                label
                for label, spec in CANVAS_PRESETS.items()
                if (spec.width, spec.height) == target
            ),
            next(iter(CANVAS_PRESETS)),
        )
        self.settings_panel.apply_values(
            canvas=canvas_label,
            fps=preferences.fps,
            shot=preferences.shot_seconds,
            language=preferences.language,
            model=preferences.model,
            motion=preferences.motion,
            captions=preferences.captions,
        )

    def detect_runtime(self) -> None:
        has_ffmpeg = ffmpeg_available()
        has_whisper = whisper_available()
        if has_ffmpeg and has_whisper:
            self.runtime_badge.setText("● FFmpeg + Whisper siap")
            self.runtime_badge.setObjectName("Badge")
        elif has_ffmpeg:
            self.runtime_badge.setText("! Whisper belum terpasang")
            self.runtime_badge.setObjectName("BadgeWarning")
        else:
            self.runtime_badge.setText("! FFmpeg belum ditemukan")
            self.runtime_badge.setObjectName("BadgeWarning")
        self.runtime_badge.style().unpolish(self.runtime_badge)
        self.runtime_badge.style().polish(self.runtime_badge)

    def effective_source(self) -> TimestampSource:
        transcript = self.source_panel.transcript_edit.text().strip()
        source = self.source_panel.current_source()
        if source is TimestampSource.AUTO:
            if transcript and Path(transcript).suffix.lower() == ".srt":
                return TimestampSource.SRT
            return TimestampSource.WHISPER
        return source

    def refresh_source_hint(self) -> None:
        transcript = self.source_panel.transcript_edit.text().strip()
        source = self.source_panel.current_source()
        hint = self.source_panel.hint
        if not transcript:
            hint.setText(
                "Pilih file transcript .txt (Whisper) atau .srt (timestamp langsung)."
            )
            hint.set_tone("muted")
            return
        suffix = Path(transcript).suffix.lower()
        if source is TimestampSource.SRT and suffix != ".srt":
            hint.setText(
                "Mode SRT memerlukan file .srt. Ubah ke Otomatis atau Whisper."
            )
            hint.set_tone("danger")
            return
        effective = self.effective_source()
        if effective is TimestampSource.SRT:
            hint.setText(
                "Mode SRT aktif: timestamp dibaca langsung dari file tanpa Whisper."
            )
            hint.set_tone("success")
            return
        model = self.settings_panel.values()["model"]
        hint.setText(
            f"Mode Whisper aktif: audio ditranskripsi ulang dengan model {model} di CPU."
        )
        hint.set_tone("warning")

    def on_source_changed(self, _value: object = None) -> None:
        if hasattr(self, "settings_panel"):
            self.refresh_source_hint()

    def on_canvas_changed(self, _value: str) -> None:
        pass

    def choose_audio(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih audio narasi",
            "",
            "Audio (*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.opus);;Semua file (*.*)",
        )
        if not path:
            return
        self.source_panel.audio_edit.setText(path)
        current = self.output_panel.name_edit.text().strip()
        if not current or current == "Video Baru":
            self.output_panel.name_edit.setText(Path(path).stem[:60])

    def choose_media_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Pilih folder media")
        if not path:
            return
        self.source_panel.media_edit.setText(path)
        self.reload_media()

    def choose_transcript(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Pilih transcript", "", "Transcript (*.txt *.srt);;Semua file (*.*)"
        )
        if not path:
            return
        self.source_panel.transcript_edit.setText(path)
        self.refresh_source_hint()

    def choose_output(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Pilih folder output")
        if path:
            self.output_panel.output_edit.setText(path)

    def reload_media(self) -> None:
        value = self.source_panel.media_edit.text().strip()
        folder = Path(value) if value else None
        if folder is not None and not folder.is_dir():
            QMessageBox.critical(self, "Folder tidak ditemukan", value)
            return
        self.media_table.load(folder)
        self._paths = list(self.media_table.paths)
        self.preview.show_path(None)
        self.refresh_source_hint()
        if self._paths:
            self._start_probe()

    def _start_probe(self) -> None:
        self._probe_generation += 1
        generation = self._probe_generation
        paths = list(self._paths)
        job = ProbeJob(paths, generation, self._probe_signals)
        self._probe_pool.start(job)

    def _on_probed(self, index: int, duration_us: int, kind: str) -> None:
        self.media_table.update_probe(index, duration_us, kind)

    def _on_probe_finished(self, generation: int) -> None:
        if generation == self._probe_generation:
            self.media_table.table.scrollToTop()

    def move_media(self, delta: int) -> None:
        index = self.media_table.selected_index()
        if index is None:
            return
        target = index + delta
        paths = self.media_table.paths
        if not 0 <= target < len(paths):
            return
        paths[index], paths[target] = paths[target], paths[index]
        self.media_table.refresh(selected=target)
        self._paths = list(paths)

    def on_media_selected(self) -> None:
        index = self.media_table.selected_index()
        if index is None or not 0 <= index < len(self.media_table.paths):
            self.preview.show_path(None)
            return
        self.preview.show_path(self.media_table.paths[index])

    def start_build(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            return
        try:
            request = self._collect_request()
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "Data belum lengkap", str(error))
            return

        self._save_preferences()
        self.action_bar.build_button.setEnabled(False)
        self.action_bar.build_button.setText("Sedang memproses…")
        self.action_bar.progress.setValue(0)
        self.action_bar.status.setText("Menyiapkan project…")
        self.action_bar.status.set_tone("muted")

        self.worker = BuildThread(request)
        self.worker.progress.connect(self._on_progress)
        self.worker.completed.connect(self._on_done)
        self.worker.failed.connect(self._on_error)
        self.worker.start()

    def _collect_request(self) -> pipeline.BuildRequest:
        values = self.settings_panel.values()
        name = self.output_panel.name_edit.text().strip()
        audio = self.source_panel.audio_edit.text().strip()
        media_dir = self.source_panel.media_edit.text().strip()
        transcript = self.source_panel.transcript_edit.text().strip()
        output = self.output_panel.output_edit.text().strip()

        if not name:
            raise ValueError("Nama project tidak boleh kosong")
        if not audio:
            raise ValueError("Audio narasi belum dipilih")
        if not media_dir:
            raise ValueError("Folder media belum dipilih")
        if not transcript:
            raise ValueError("Transcript belum dipilih")
        if not output:
            raise ValueError("Folder output belum dipilih")

        pipeline.validate_paths(audio, media_dir, transcript)

        media_paths = tuple(self.media_table.paths) or tuple(scan_media(media_dir))
        if not media_paths:
            raise ValueError("Folder media tidak berisi file gambar atau video")
        source = self.source_panel.current_source()
        transcript_path = Path(transcript)
        if source is TimestampSource.SRT and transcript_path.suffix.lower() != ".srt":
            raise ValueError("Mode SRT memerlukan file transcript berekstensi .srt")

        try:
            shot_seconds = float(str(values["shot"]).replace(",", "."))
        except ValueError as error:
            raise ValueError("Durasi per shot gambar harus berupa angka") from error
        if shot_seconds <= 0:
            raise ValueError("Durasi per shot gambar harus lebih dari 0 detik")

        preset = CANVAS_PRESETS[str(values["canvas"])]
        canvas = CanvasSpec(preset.width, preset.height, int(values["fps"]))
        language = str(values["language"])

        return pipeline.BuildRequest(
            name=name,
            audio_path=Path(audio),
            media_paths=media_paths,
            transcript_path=transcript_path,
            output_dir=Path(output),
            source=source,
            config=PlannerConfig(
                canvas=canvas,
                image_shot_duration_us=seconds_to_us(shot_seconds),
                add_captions=bool(values["captions"]),
                motion_enabled=bool(values["motion"]),
            ),
            whisper_config=WhisperConfig(
                model=str(values["model"]),
                language=None if language == "auto" else language,
            ),
            burn_captions=bool(values["captions"]),
        )

    def _on_progress(self, value: float, message: str) -> None:
        self.action_bar.progress.setValue(int(max(0.0, min(1.0, value)) * 1000))
        self.action_bar.status.setText(message)

    def _on_done(self, result: pipeline.BuildResult) -> None:
        self._finish()
        self.action_bar.progress.setValue(1000)
        self.action_bar.status.setText("Selesai · video sudah dibuat")
        self.action_bar.status.set_tone("success")
        timeline = result.timeline
        lines = [
            f"Video:\n{result.video}",
            f"Manifest:\n{result.manifest}",
            "",
            f"Sumber timestamp: {SOURCE_LABELS[timeline.source]}",
            f"Clip visual: {len(timeline.project.clips)}",
            f"Caption: {len(timeline.project.captions)}",
            f"Durasi: {timeline.project.duration_us / 1_000_000:.2f} detik",
        ]
        if timeline.closed_gaps:
            lines.append(f"Celah subtitle dirapatkan: {timeline.closed_gaps}")
        if timeline.trimmed_overlaps:
            lines.append(f"Subtitle bertumpuk dirapikan: {timeline.trimmed_overlaps}")
        QMessageBox.information(self, "Video selesai", "\n".join(lines))

    def _on_error(self, message: str) -> None:
        self._finish()
        self.action_bar.progress.setValue(0)
        self.action_bar.status.setText("Gagal · periksa data masukan")
        self.action_bar.status.set_tone("danger")
        QMessageBox.critical(self, "Video gagal dibuat", message)

    def _finish(self) -> None:
        self.action_bar.build_button.setEnabled(True)
        self.action_bar.build_button.setText("Buat video  →")
        self.worker = None

    def open_output(self) -> None:
        folder = Path(self.output_panel.output_edit.text().strip() or ".")
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            QMessageBox.critical(self, "Folder output tidak bisa dibuat", str(error))
            return
        if hasattr(os, "startfile"):
            os.startfile(folder)
        else:
            QMessageBox.information(self, "Folder output", str(folder))

    def _save_preferences(self) -> None:
        values = self.settings_panel.values()
        preset = CANVAS_PRESETS[str(values["canvas"])]
        preferences = settings.Settings(
            audio_path=self.source_panel.audio_edit.text(),
            media_dir=self.source_panel.media_edit.text(),
            transcript_path=self.source_panel.transcript_edit.text(),
            output_dir=self.output_panel.output_edit.text(),
            project_name=self.output_panel.name_edit.text(),
            source=self.source_panel.current_source().value,
            canvas_width=preset.width,
            canvas_height=preset.height,
            fps=int(values["fps"]),
            shot_seconds=str(values["shot"]),
            language=str(values["language"]),
            model=str(values["model"]),
            motion=bool(values["motion"]),
            captions=bool(values["captions"]),
        )
        try:
            settings.save(preferences)
        except OSError:
            pass

    def closeEvent(self, event) -> None:
        self._probe_generation += 1
        self._probe_pool.clear()
        if self.worker is not None and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait(3000)
        super().closeEvent(event)


def launch() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("autoedit")
    app.setOrganizationName("autoedit")
    app.setApplicationDisplayName("autoedit")
    theme.apply(app)

    icon_path = resource_path("assets/logo.png")
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = AutoEditWindow()
    window.show()
    return app.exec()
