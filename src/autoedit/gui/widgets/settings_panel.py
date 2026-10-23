from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from ...speech.aligned import TimestampSource
from ..theme import COLORS
from .card import card, field_label, path_row


class SourcePanel(ttk.Frame):
    def __init__(self, master: tk.Misc, app) -> None:
        super().__init__(master, style="TFrame")
        self.app = app
        frame = card(self, "Sumber bahan")
        body = frame.body  # type: ignore[attr-defined]

        self._label(body, "Audio narasi")
        path_row(body, app.audio_var, app.choose_audio).pack(fill="x", pady=(4, 10))

        self._label(body, "Folder media")
        path_row(body, app.media_dir_var, app.choose_media_dir).pack(fill="x", pady=(4, 10))

        self._label(body, "Transcript (.txt / .srt)")
        path_row(
            body, app.transcript_var, app.choose_transcript, button_text="Pilih…"
        ).pack(fill="x", pady=(4, 10))

        self._label(body, "Sumber timestamp")
        options = ttk.Frame(body, style="Card.TFrame")
        options.pack(fill="x", pady=(4, 8))
        for value, text in (
            (TimestampSource.AUTO.value, "Otomatis (.srt → SRT, .txt → Whisper)"),
            (TimestampSource.WHISPER.value, "Whisper (audio → timestamp)"),
            (TimestampSource.SRT.value, "File SRT (timestamp asli)"),
        ):
            ttk.Radiobutton(
                options,
                text=text,
                value=value,
                variable=app.source_var,
                style="Dark.TRadiobutton",
                command=app.refresh_source_hint,
            ).pack(anchor="w")

        self.hint = ttk.Label(body, text="", style="CardMuted.TLabel", wraplength=320)
        self.hint.pack(fill="x", pady=(2, 0))
        self._hint_body = body

    @staticmethod
    def _label(parent: tk.Misc, text: str) -> None:
        field_label(parent, text).pack(anchor="w")

    def set_hint(self, text: str, tone: str = "muted") -> None:
        style = {
            "muted": "CardMuted.TLabel",
            "warning": "Warning.TLabel",
            "success": "Success.TLabel",
            "danger": "Danger.TLabel",
        }[tone]
        self.hint.configure(text=text, style=style)


class SettingsPanel(ttk.Frame):
    def __init__(self, master: tk.Misc, app) -> None:
        super().__init__(master, style="TFrame")
        frame = card(self, "Pengaturan video")
        body = frame.body  # type: ignore[attr-defined]

        grid = ttk.Frame(body, style="Card.TFrame")
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)

        field_label(grid, "Resolusi").grid(row=0, column=0, sticky="w", pady=(0, 6))
        canvas = ttk.Combobox(
            grid,
            textvariable=app.canvas_var,
            values=app.canvas_choices,
            state="readonly",
            width=16,
        )
        canvas.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=(0, 6))

        field_label(grid, "FPS").grid(row=1, column=0, sticky="w", pady=(0, 6))
        ttk.Combobox(
            grid,
            textvariable=app.fps_var,
            values=("24", "25", "30", "60"),
            state="readonly",
            width=16,
        ).grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(0, 6))

        field_label(grid, "Durasi per shot gambar").grid(
            row=2, column=0, sticky="w", pady=(0, 6)
        )
        shot = ttk.Frame(grid, style="Card.TFrame")
        shot.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=(0, 6))
        ttk.Entry(shot, textvariable=app.shot_var, width=6).pack(side="left")
        ttk.Label(shot, text="detik", style="CardMuted.TLabel").pack(
            side="left", padx=(6, 0)
        )

        field_label(grid, "Bahasa audio").grid(row=3, column=0, sticky="w", pady=(0, 6))
        ttk.Combobox(
            grid,
            textvariable=app.language_var,
            values=app.language_choices,
            state="readonly",
            width=16,
        ).grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=(0, 6))

        field_label(grid, "Model Whisper").grid(row=4, column=0, sticky="w")
        ttk.Combobox(
            grid,
            textvariable=app.model_var,
            values=("tiny", "base", "small", "medium"),
            state="readonly",
            width=16,
        ).grid(row=4, column=1, sticky="ew", padx=(8, 0))

        toggles = ttk.Frame(body, style="Card.TFrame")
        toggles.pack(fill="x", pady=(12, 0))
        ttk.Checkbutton(
            toggles,
            text="Gerakan halus (zoom / pan)",
            variable=app.motion_var,
            style="Dark.TCheckbutton",
        ).pack(anchor="w")
        ttk.Checkbutton(
            toggles,
            text="Tempel caption ke video",
            variable=app.captions_var,
            style="Dark.TCheckbutton",
        ).pack(anchor="w")


class OutputPanel(ttk.Frame):
    def __init__(self, master: tk.Misc, app) -> None:
        super().__init__(master, style="TFrame")
        frame = card(self, "Hasil")
        body = frame.body  # type: ignore[attr-defined]

        field_label(body, "Nama project").pack(anchor="w")
        ttk.Entry(body, textvariable=app.name_var).pack(fill="x", pady=(4, 10))

        field_label(body, "Folder output").pack(anchor="w")
        path_row(body, app.output_var, app.choose_output, width=28).pack(
            fill="x", pady=(4, 0)
        )
        ttk.Label(
            body,
            text="Video dan manifest timeline disimpan di folder ini.",
            style="CardMuted.TLabel",
            wraplength=320,
        ).pack(fill="x", pady=(8, 0))
        self._body = body


def severity_color(tone: str) -> str:
    return {
        "muted": COLORS["muted"],
        "warning": COLORS["warning"],
        "success": COLORS["success"],
        "danger": COLORS["danger"],
    }[tone]


def format_duration(duration_us: int) -> str:
    if duration_us <= 0:
        return "—"
    total = duration_us / 1_000_000
    minutes = int(total // 60)
    seconds = total - minutes * 60
    return f"{minutes:02d}:{seconds:05.2f}"


def parse_media_paths(paths: list[Path]) -> list[Path]:
    return [Path(path) for path in paths]
