from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from ...core.numbering import inspect_numbering
from ...core.probe import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, ProbeError, probe_media
from ...core.scanner import scan_media
from ..theme import COLORS
from .card import card
from .settings_panel import format_duration


class MediaTable(ttk.Frame):
    def __init__(self, master: tk.Misc, app) -> None:
        super().__init__(master, style="TFrame")
        self.app = app
        self.paths: list[Path] = []
        self._durations: dict[Path, str] = {}
        self._kinds: dict[Path, str] = {}

        frame = card(self, "Urutan media", padding=14)

        header = ttk.Frame(frame, style="Card.TFrame")
        header.pack(fill="x", pady=(0, 10))
        ttk.Label(header, text="Urutan media", style="CardTitle.TLabel").pack(side="left")
        self.count_label = ttk.Label(header, text="0 file", style="CardMuted.TLabel")
        self.count_label.pack(side="left", padx=(8, 0), pady=(2, 0))

        buttons = ttk.Frame(header, style="Card.TFrame")
        buttons.pack(side="right")
        ttk.Button(buttons, text="↑ Naik", width=8, command=lambda: app.move_media(-1)).pack(
            side="left", padx=(0, 4)
        )
        ttk.Button(
            buttons, text="↓ Turun", width=8, command=lambda: app.move_media(1)
        ).pack(side="left", padx=(0, 4))
        ttk.Button(
            buttons, text="↻ Muat ulang", width=12, command=app.reload_media
        ).pack(side="left")

        body = frame.body  # type: ignore[attr-defined]
        wrapper = tk.Frame(
            body,
            background=COLORS["surface_raised"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            bd=0,
        )
        wrapper.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            wrapper,
            columns=("order", "name", "kind", "duration"),
            show="headings",
            style="Media.Treeview",
            selectmode="browse",
        )
        self.tree.heading("order", text="#")
        self.tree.heading("name", text="NAMA FILE")
        self.tree.heading("kind", text="JENIS")
        self.tree.heading("duration", text="DURASI")
        self.tree.column("order", width=48, anchor="center", stretch=False)
        self.tree.column("name", width=380, anchor="w")
        self.tree.column("kind", width=80, anchor="center", stretch=False)
        self.tree.column("duration", width=96, anchor="center", stretch=False)
        self.tree.tag_configure("odd", background=COLORS["surface_raised"])
        self.tree.tag_configure("even", background="#232c39")
        self.tree.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(
            wrapper, orient="vertical", command=self.tree.yview, style="Vertical.TScrollbar"
        )
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind("<<TreeviewSelect>>", lambda _event: app.on_media_selected())

        self.warning = ttk.Label(body, text="", style="CardMuted.TLabel", wraplength=760)
        self.warning.pack(fill="x", pady=(8, 0))

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

    def set_paths(self, paths: list[Path]) -> None:
        self.paths = list(paths)
        self.refresh()

    def refresh(self, selected: int | None = None) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for index, path in enumerate(self.paths):
            self.tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    index + 1,
                    path.name,
                    self._kinds.get(path, self._guess_kind(path)),
                    self._durations.get(path, "—"),
                ),
                tags=("even" if index % 2 else "odd",),
            )
        self.count_label.configure(text=f"{len(self.paths)} file")
        if selected is not None and 0 <= selected < len(self.paths):
            self.tree.selection_set(str(selected))
            self.tree.see(str(selected))
        self._update_warning()

    def update_probe(self, index: int, duration_us: int, kind: str) -> None:
        if not 0 <= index < len(self.paths):
            return
        path = self.paths[index]
        self._durations[path] = format_duration(duration_us)
        self._kinds[path] = kind
        item = str(index)
        if self.tree.exists(item):
            values = list(self.tree.item(item, "values"))
            if len(values) == 4:
                values[2] = kind
                values[3] = self._durations[path]
                self.tree.item(item, values=values)

    def probe_all(self, on_done=None, on_error=None) -> None:
        import threading

        paths = list(self.paths)

        def runner() -> None:
            for index, path in enumerate(paths):
                try:
                    info = probe_media(path)
                    kind = "Video" if path.suffix.lower() in VIDEO_EXTENSIONS else "Gambar"
                    self.app.after(
                        0,
                        lambda i=index, d=info.duration_us, k=kind: self.update_probe(i, d, k),
                    )
                except ProbeError:
                    self.app.after(
                        0,
                        lambda i=index: self.update_probe(i, 0, "?"),
                    )
            if on_done is not None:
                self.app.after(0, on_done)

        threading.Thread(target=runner, daemon=True).start()

    def selected_index(self) -> int | None:
        selection = self.tree.selection()
        if not selection:
            return None
        return int(selection[0])

    def _update_warning(self) -> None:
        if not self.paths:
            self.warning.configure(text="Pilih folder media untuk memuat file.", style="CardMuted.TLabel")
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
            self.warning.configure(text=" · ".join(messages), style="Warning.TLabel")
        else:
            self.warning.configure(
                text="Urutan media sesuai nomor pada nama file.", style="Success.TLabel"
            )

    @staticmethod
    def _guess_kind(path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in VIDEO_EXTENSIONS:
            return "Video"
        if suffix in IMAGE_EXTENSIONS:
            return "Gambar"
        return "?"


class PreviewPanel(ttk.Frame):
    def __init__(self, master: tk.Misc, app) -> None:
        super().__init__(master, style="TFrame")
        self.app = app
        frame = card(self, "Pratinjau", padding=12)
        body = frame.body  # type: ignore[attr-defined]
        self.canvas = tk.Canvas(
            body,
            background=COLORS["surface_raised"],
            highlightthickness=0,
            bd=0,
            height=190,
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_text(
            10,
            10,
            anchor="nw",
            text="Pilih file media untuk melihat pratinjau",
            fill=COLORS["muted"],
            font=("Segoe UI", 9),
            tags="placeholder",
        )
        self._image = None
        self._path: Path | None = None
        self.canvas.bind("<Configure>", lambda _event: self._redraw())

    def show(self, path: Path | None) -> None:
        self._path = path
        self._redraw()

    def _redraw(self) -> None:
        self.canvas.delete("all")
        width = max(1, self.canvas.winfo_width())
        height = max(1, self.canvas.winfo_height())
        if self._path is None or not self._path.is_file():
            self.canvas.create_text(
                10,
                10,
                anchor="nw",
                text="Pilih file media untuk melihat pratinjau",
                fill=COLORS["muted"],
                font=("Segoe UI", 9),
            )
            return
        if self._path.suffix.lower() not in IMAGE_EXTENSIONS:
            self.canvas.create_text(
                width / 2,
                height / 2,
                text=f"🎞  {self._path.name}\n(video)",
                fill=COLORS["muted"],
                font=("Segoe UI", 10),
                justify="center",
            )
            return
        try:
            from PIL import Image, ImageTk

            with Image.open(self._path) as source:
                image = source.convert("RGB")
                image.thumbnail((width - 12, height - 12), Image.LANCZOS)
                self._image = ImageTk.PhotoImage(image)
            self.canvas.create_image(width / 2, height / 2, image=self._image)
        except Exception as error:
            self.canvas.create_text(
                10,
                10,
                anchor="nw",
                text=f"Gagal memuat pratinjau: {error}",
                fill=COLORS["danger"],
                font=("Segoe UI", 9),
                width=width - 20,
            )


class ActionBar(ttk.Frame):
    def __init__(self, master: tk.Misc, app) -> None:
        super().__init__(master, style="TFrame")
        wrapper = tk.Frame(
            self,
            background=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            bd=0,
        )
        wrapper.pack(fill="x")

        inner = ttk.Frame(wrapper, style="Card.TFrame", padding=(16, 12))
        inner.pack(fill="x")

        top = ttk.Frame(inner, style="Card.TFrame")
        top.pack(fill="x")

        ttk.Button(top, text="Buka folder output", command=app.open_output).pack(side="left")

        self.status = ttk.Label(top, text="Siap", style="CardMuted.TLabel")
        self.status.pack(side="left", padx=(14, 0))

        self.build_button = ttk.Button(
            top, text="Buat video  →", style="Accent.TButton", command=app.start_build
        )
        self.build_button.pack(side="right")

        self.progress = ttk.Progressbar(
            inner,
            orient="horizontal",
            mode="determinate",
            maximum=100,
            style="Accent.Horizontal.TProgressbar",
        )
        self.progress.pack(fill="x", pady=(10, 0))

    def set_status(self, text: str, tone: str = "muted") -> None:
        style = {
            "muted": "CardMuted.TLabel",
            "success": "Success.TLabel",
            "warning": "Warning.TLabel",
            "danger": "Danger.TLabel",
        }[tone]
        self.status.configure(text=text, style=style)

    def set_progress(self, value: float) -> None:
        self.progress.configure(value=max(0.0, min(1.0, value)) * 100)

    def set_running(self, running: bool) -> None:
        self.build_button.configure(
            state="disabled" if running else "normal",
            text="Sedang memproses…" if running else "Buat video  →",
        )
