from __future__ import annotations

import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ..app import pipeline, settings
from ..core.manifest import CanvasSpec, seconds_to_us
from ..core.planner import PlannerConfig
from ..core.scanner import scan_media
from ..render.ffmpeg import ffmpeg_available
from ..speech.aligned import TimestampSource
from ..speech.whisper import WhisperConfig, whisper_available
from .theme import COLORS, apply_theme, set_windows_app_id
from .widgets.media_table import ActionBar, MediaTable, PreviewPanel
from .widgets.settings_panel import OutputPanel, SettingsPanel, SourcePanel
from .worker import Worker

CANVAS_PRESETS = {
    "1920×1080 (16:9)": CanvasSpec(1920, 1080),
    "1280×720 (16:9)": CanvasSpec(1280, 720),
    "1080×1920 (9:16)": CanvasSpec(1080, 1920),
    "1080×1080 (1:1)": CanvasSpec(1080, 1080),
    "3840×2160 (4K)": CanvasSpec(3840, 2160, 30),
}

LANGUAGE_CHOICES = (
    "auto",
    "Indonesia",
    "English",
    "Jepang",
    "Korea",
    "Mandarin",
)


class AutoEditApp(ttk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, style="TFrame", padding=(18, 14, 18, 0))
        self.master = master
        self.pack(fill="both", expand=True)
        self.worker = Worker()
        self._prefs = settings.load()

        self.audio_var = tk.StringVar(value=self._prefs.audio_path)
        self.media_dir_var = tk.StringVar(value=self._prefs.media_dir)
        self.transcript_var = tk.StringVar(value=self._prefs.transcript_path)
        self.output_var = tk.StringVar(
            value=self._prefs.output_dir or str(Path.home() / "Videos" / "autoedit")
        )
        self.name_var = tk.StringVar(value=self._prefs.project_name)
        self.source_var = tk.StringVar(value=self._prefs.source)
        self.canvas_var = tk.StringVar(value=self._initial_canvas())
        self.fps_var = tk.StringVar(value=str(self._prefs.fps))
        self.shot_var = tk.StringVar(value=self._prefs.shot_seconds)
        self.language_var = tk.StringVar(value=self._prefs.language)
        self.model_var = tk.StringVar(value=self._prefs.model)
        self.motion_var = tk.BooleanVar(value=self._prefs.motion)
        self.captions_var = tk.BooleanVar(value=self._prefs.captions)
        self.runtime_var = tk.StringVar(value="")

        self.canvas_choices = tuple(CANVAS_PRESETS)
        self.language_choices = LANGUAGE_CHOICES

        self._build_header()
        self._build_body()
        self.action_bar = ActionBar(self, self)
        self.action_bar.pack(fill="x", pady=(12, 0))

        self.refresh_source_hint()
        self.detect_runtime()
        if self.media_dir_var.get().strip():
            self.reload_media()

    def _initial_canvas(self) -> str:
        wanted = (self._prefs.canvas_width, self._prefs.canvas_height)
        for label, spec in CANVAS_PRESETS.items():
            if (spec.width, spec.height) == wanted:
                return label
        return next(iter(CANVAS_PRESETS))

    def _build_header(self) -> None:
        header = ttk.Frame(self, style="TFrame")
        header.pack(fill="x", pady=(0, 12))

        left = ttk.Frame(header, style="TFrame")
        left.pack(side="left", fill="x", expand=True)
        ttk.Label(left, text="autoedit", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            left,
            text="Narasi audio + media berurutan + transcript → video siap pakai",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        self.runtime_badge = ttk.Label(
            header, textvariable=self.runtime_var, style="Badge.TLabel"
        )
        self.runtime_badge.pack(side="right")

    def _build_body(self) -> None:
        body = ttk.Frame(self, style="TFrame")
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=0, minsize=380)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(body, style="TFrame", width=380)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        sidebar.grid_propagate(False)

        sidebar_canvas = tk.Canvas(
            sidebar,
            background=COLORS["background"],
            highlightthickness=0,
            bd=0,
            width=366,
        )
        sidebar_scroll = ttk.Scrollbar(
            sidebar,
            orient="vertical",
            command=sidebar_canvas.yview,
            style="Vertical.TScrollbar",
        )
        sidebar_canvas.configure(yscrollcommand=sidebar_scroll.set)
        sidebar_canvas.pack(side="left", fill="both", expand=True)
        sidebar_scroll.pack(side="right", fill="y")

        sidebar_inner = ttk.Frame(sidebar_canvas, style="TFrame")
        sidebar_window = sidebar_canvas.create_window(
            (0, 0), window=sidebar_inner, anchor="nw"
        )

        def resize_sidebar(event) -> None:
            sidebar_canvas.itemconfigure(sidebar_window, width=event.width)

        sidebar_inner.bind(
            "<Configure>",
            lambda _event: sidebar_canvas.configure(
                scrollregion=sidebar_canvas.bbox("all")
            ),
        )
        sidebar_canvas.bind("<Configure>", resize_sidebar)
        sidebar_canvas.bind(
            "<Enter>",
            lambda _event: sidebar_canvas.bind_all(
                "<MouseWheel>", lambda event: sidebar_canvas.yview_scroll(
                    int(-event.delta / 120), "units"
                )
            ),
        )
        sidebar_canvas.bind("<Leave>", lambda _event: sidebar_canvas.unbind_all("<MouseWheel>"))

        self.source_panel = SourcePanel(sidebar_inner, self)
        self.source_panel.pack(fill="x", pady=(0, 12))
        self.settings_panel = SettingsPanel(sidebar_inner, self)
        self.settings_panel.pack(fill="x", pady=(0, 12))
        self.output_panel = OutputPanel(sidebar_inner, self)
        self.output_panel.pack(fill="x")

        right = ttk.Frame(body, style="TFrame")
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        self.media_table = MediaTable(right, self)
        self.media_table.grid(row=0, column=0, sticky="nsew")

        self.preview = PreviewPanel(right, self)
        self.preview.grid(row=1, column=0, sticky="ew", pady=(12, 0))

    def detect_runtime(self) -> None:
        has_ffmpeg = ffmpeg_available()
        has_whisper = whisper_available()
        if has_ffmpeg and has_whisper:
            self.runtime_var.set("● FFmpeg + Whisper siap")
            self.runtime_badge.configure(style="Badge.TLabel")
        elif has_ffmpeg:
            self.runtime_var.set("! Whisper belum terpasang")
            self.runtime_badge.configure(style="WarningBadge.TLabel")
        else:
            self.runtime_var.set("! FFmpeg belum ditemukan")
            self.runtime_badge.configure(style="WarningBadge.TLabel")

    def refresh_source_hint(self) -> None:
        transcript = self.transcript_var.get().strip()
        source = TimestampSource(self.source_var.get())
        if not transcript:
            self.source_panel.set_hint(
                "Pilih file transcript .txt (Whisper) atau .srt (timestamp langsung)."
            )
            return
        suffix = Path(transcript).suffix.lower()
        effective = pipeline_source(source, Path(transcript))
        if source is TimestampSource.SRT and suffix != ".srt":
            self.source_panel.set_hint(
                "Mode SRT memerlukan file .srt. Ubah ke Otomatis atau Whisper.", "danger"
            )
            return
        if effective is TimestampSource.SRT:
            self.source_panel.set_hint(
                "Mode SRT aktif: timestamp diambil langsung dari file, tanpa Whisper.", "success"
            )
        else:
            self.source_panel.set_hint(
                "Mode Whisper aktif: audio akan ditranskripsi ulang, model "
                f"{self.model_var.get()} dijalankan di CPU.",
                "warning",
            )

    def choose_audio(self) -> None:
        path = filedialog.askopenfilename(
            title="Pilih audio narasi",
            filetypes=[
                ("Audio", "*.mp3 *.wav *.m4a *.aac *.flac *.ogg"),
                ("Semua file", "*.*"),
            ],
        )
        if path:
            self.audio_var.set(path)
            if not self.name_var.get().strip() or self.name_var.get() == "Video Baru":
                self.name_var.set(Path(path).stem[:60])

    def choose_media_dir(self) -> None:
        path = filedialog.askdirectory(title="Pilih folder media")
        if path:
            self.media_dir_var.set(path)
            self.reload_media()

    def choose_transcript(self) -> None:
        path = filedialog.askopenfilename(
            title="Pilih transcript",
            filetypes=[("Transcript", "*.txt *.srt"), ("Semua file", "*.*")],
        )
        if path:
            self.transcript_var.set(path)
            self.refresh_source_hint()

    def choose_output(self) -> None:
        path = filedialog.askdirectory(title="Pilih folder output")
        if path:
            self.output_var.set(path)

    def reload_media(self) -> None:
        folder_value = self.media_dir_var.get().strip()
        folder = Path(folder_value) if folder_value else None
        if folder is not None and not folder.is_dir():
            messagebox.showerror("Folder tidak ditemukan", folder_value, parent=self.master)
            return
        self.media_table.load(folder)
        self.media_table.probe_all()
        self.preview.show(None)

    def move_media(self, delta: int) -> None:
        index = self.media_table.selected_index()
        if index is None:
            return
        target = index + delta
        if not 0 <= target < len(self.media_table.paths):
            return
        paths = self.media_table.paths
        paths[index], paths[target] = paths[target], paths[index]
        self.media_table.refresh(selected=target)

    def on_media_selected(self) -> None:
        index = self.media_table.selected_index()
        if index is None:
            self.preview.show(None)
            return
        self.preview.show(self.media_table.paths[index])

    def start_build(self) -> None:
        if self.worker.running:
            return
        try:
            request = self._collect_request()
        except (OSError, ValueError) as error:
            messagebox.showerror("Data belum lengkap", str(error), parent=self.master)
            return

        self._save_prefs()
        self.action_bar.set_running(True)
        self.action_bar.set_progress(0.0)
        self.action_bar.set_status("Menyiapkan project…")

        self.worker.start(
            lambda: pipeline.build(request, progress_callback=self.worker.progress)
        )
        self.worker.poll(
            on_progress=self._on_progress,
            on_done=self._on_done,
            on_error=self._on_error,
            schedule=self.after,
        )

    def _collect_request(self) -> pipeline.BuildRequest:
        name = self.name_var.get().strip()
        if not name:
            raise ValueError("Nama project tidak boleh kosong")

        audio = self.audio_var.get().strip()
        media_dir = self.media_dir_var.get().strip()
        transcript = self.transcript_var.get().strip()
        output = self.output_var.get().strip()
        if not audio:
            raise ValueError("Audio narasi belum dipilih")
        if not media_dir:
            raise ValueError("Folder media belum dipilih")
        if not transcript:
            raise ValueError("Transcript belum dipilih")
        if not output:
            raise ValueError("Folder output belum dipilih")
        pipeline.validate_paths(audio, media_dir, transcript)

        if self.media_table.paths:
            media_paths = tuple(self.media_table.paths)
        else:
            media_paths = tuple(scan_media(media_dir))

        source = TimestampSource(self.source_var.get())
        transcript_path = Path(transcript)
        if source is TimestampSource.SRT and transcript_path.suffix.lower() != ".srt":
            raise ValueError("Mode SRT memerlukan file transcript berekstensi .srt")

        try:
            shot_seconds = float(self.shot_var.get().replace(",", "."))
        except ValueError as error:
            raise ValueError("Durasi per shot gambar harus berupa angka") from error
        if shot_seconds <= 0:
            raise ValueError("Durasi per shot gambar harus lebih dari 0 detik")

        canvas = CANVAS_PRESETS[self.canvas_var.get()]
        canvas = CanvasSpec(canvas.width, canvas.height, int(self.fps_var.get()))
        language = self.language_var.get()
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
                add_captions=self.captions_var.get(),
                motion_enabled=self.motion_var.get(),
            ),
            whisper_config=WhisperConfig(
                model=self.model_var.get(),
                language=None if language == "auto" else language,
            ),
            burn_captions=self.captions_var.get(),
        )

    def _on_progress(self, value: float, message: str) -> None:
        self.action_bar.set_progress(value)
        self.action_bar.set_status(message)

    def _on_done(self, result: pipeline.BuildResult) -> None:
        self.action_bar.set_running(False)
        self.action_bar.set_progress(1.0)
        self.action_bar.set_status("Selesai · video sudah dibuat", "success")
        timeline = result.timeline
        lines = [
            f"Video\n{result.video}",
            f"Manifest\n{result.manifest}",
            "",
            f"Sumber timestamp: {timeline.source.value.upper()}",
            f"Clip visual: {len(timeline.project.clips)}",
            f"Durasi: {timeline.project.duration_us / 1_000_000:.2f} detik",
        ]
        if timeline.closed_gaps:
            lines.append(f"Celah subtitle dirapatkan: {timeline.closed_gaps}")
        if timeline.trimmed_overlaps:
            lines.append(f"Subtitle bertumpuk dirapikan: {timeline.trimmed_overlaps}")
        messagebox.showinfo("Video selesai", "\n".join(lines), parent=self.master)

    def _on_error(self, error: BaseException) -> None:
        self.action_bar.set_running(False)
        self.action_bar.set_progress(0.0)
        self.action_bar.set_status("Gagal · periksa data masukan", "danger")
        messagebox.showerror("Video gagal dibuat", str(error), parent=self.master)

    def open_output(self) -> None:
        folder = Path(self.output_var.get().strip() or ".")
        folder.mkdir(parents=True, exist_ok=True)
        if hasattr(os, "startfile"):
            os.startfile(folder)
        else:
            messagebox.showinfo("Folder output", str(folder), parent=self.master)

    def _save_prefs(self) -> None:
        canvas = CANVAS_PRESETS[self.canvas_var.get()]
        prefs = settings.Settings(
            audio_path=self.audio_var.get(),
            media_dir=self.media_dir_var.get(),
            transcript_path=self.transcript_var.get(),
            output_dir=self.output_var.get(),
            project_name=self.name_var.get(),
            source=self.source_var.get(),
            canvas_width=canvas.width,
            canvas_height=canvas.height,
            fps=int(self.fps_var.get()),
            shot_seconds=self.shot_var.get(),
            language=self.language_var.get(),
            model=self.model_var.get(),
            motion=self.motion_var.get(),
            captions=self.captions_var.get(),
        )
        try:
            settings.save(prefs)
        except OSError:
            pass


def pipeline_source(mode: TimestampSource, transcript: Path) -> TimestampSource:
    if mode is TimestampSource.AUTO:
        return TimestampSource.SRT if transcript.suffix.lower() == ".srt" else TimestampSource.WHISPER
    return mode


def launch() -> int:
    set_windows_app_id()
    root = tk.Tk()
    root.title("autoedit")
    root.geometry(_geometry(root))
    root.minsize(1180, 720)
    apply_theme(root)
    AutoEditApp(root)

    def on_close() -> None:
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
    return 0


def _geometry(root: tk.Tk) -> str:
    width = 1440
    height = 860
    try:
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        width = min(width, max(1180, screen_width - 80))
        height = min(height, max(720, screen_height - 120))
    except Exception:
        pass
    x = 40
    y = 40
    return f"{width}x{height}+{x}+{y}"
