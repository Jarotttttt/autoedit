from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..theme import COLORS


def card(
    parent: tk.Misc,
    title: str,
    *,
    subtitle: str | None = None,
    padding: int = 16,
) -> ttk.Frame:
    outer = tk.Frame(
        parent,
        background=COLORS["surface"],
        highlightbackground=COLORS["border"],
        highlightthickness=1,
        bd=0,
    )
    inner = ttk.Frame(outer, style="Card.TFrame", padding=padding)
    inner.pack(fill="both", expand=True)

    header = ttk.Frame(inner, style="Card.TFrame")
    header.pack(fill="x", pady=(0, 10))
    ttk.Label(header, text=title, style="CardTitle.TLabel").pack(side="left")
    if subtitle:
        ttk.Label(header, text=subtitle, style="CardMuted.TLabel").pack(
            side="left", padx=(8, 0), pady=(2, 0)
        )
    inner.body = ttk.Frame(inner, style="Card.TFrame")  # type: ignore[attr-defined]
    inner.body.pack(fill="both", expand=True)  # type: ignore[attr-defined]
    return inner


def field_label(parent: tk.Misc, text: str) -> ttk.Label:
    return ttk.Label(parent, text=text.upper(), style="Field.TLabel")


def path_row(
    parent: tk.Misc,
    variable: tk.StringVar,
    command,
    *,
    button_text: str = "Pilih…",
    width: int = 34,
) -> ttk.Frame:
    row = ttk.Frame(parent, style="Card.TFrame")
    entry = ttk.Entry(row, textvariable=variable, width=width)
    entry.pack(side="left", fill="x", expand=True)
    ttk.Button(row, text=button_text, command=command, width=8).pack(
        side="left", padx=(6, 0)
    )
    return row
