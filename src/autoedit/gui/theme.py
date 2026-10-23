from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk


COLORS = {
    "background": "#11151c",
    "surface": "#171d26",
    "surface_raised": "#1e2632",
    "border": "#2a3442",
    "text": "#e8edf4",
    "muted": "#8b98a9",
    "accent": "#4f8cff",
    "accent_light": "#7aa8ff",
    "accent_text": "#ffffff",
    "success": "#43bf7c",
    "warning": "#f0b429",
    "danger": "#ef5b5b",
}

FONT_FAMILY = "Segoe UI"


def apply_theme(root: tk.Tk) -> None:
    root.configure(background=COLORS["background"])
    root.option_add("*Font", f"{{{FONT_FAMILY}}} 9")
    root.option_add("*TCombobox*Listbox.background", COLORS["surface_raised"])
    root.option_add("*TCombobox*Listbox.foreground", COLORS["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", COLORS["accent"])
    root.option_add("*TCombobox*Listbox.selectForeground", COLORS["accent_text"])

    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("TFrame", background=COLORS["background"])
    style.configure("Card.TFrame", background=COLORS["surface"])
    style.configure(
        "TLabel", background=COLORS["background"], foreground=COLORS["text"]
    )
    style.configure("Card.TLabel", background=COLORS["surface"], foreground=COLORS["text"])
    style.configure(
        "CardMuted.TLabel", background=COLORS["surface"], foreground=COLORS["muted"]
    )
    style.configure(
        "Field.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["muted"],
        font=(FONT_FAMILY, 8),
    )
    style.configure(
        "Title.TLabel",
        background=COLORS["background"],
        foreground=COLORS["text"],
        font=(FONT_FAMILY, 17, "bold"),
    )
    style.configure(
        "Subtitle.TLabel",
        background=COLORS["background"],
        foreground=COLORS["muted"],
        font=(FONT_FAMILY, 9),
    )
    style.configure(
        "CardTitle.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        font=(FONT_FAMILY, 10, "bold"),
    )
    style.configure(
        "Status.TLabel",
        background=COLORS["background"],
        foreground=COLORS["muted"],
        font=(FONT_FAMILY, 9),
    )
    style.configure(
        "Warning.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["warning"],
        font=(FONT_FAMILY, 9),
    )
    style.configure(
        "Success.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["success"],
        font=(FONT_FAMILY, 9),
    )
    style.configure(
        "Danger.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["danger"],
        font=(FONT_FAMILY, 9),
    )
    style.configure(
        "Badge.TLabel",
        background=COLORS["surface_raised"],
        foreground=COLORS["success"],
        font=(FONT_FAMILY, 9),
        padding=(10, 4),
    )
    style.configure(
        "WarningBadge.TLabel",
        background=COLORS["surface_raised"],
        foreground=COLORS["warning"],
        font=(FONT_FAMILY, 9),
        padding=(10, 4),
    )

    style.configure(
        "TEntry",
        fieldbackground=COLORS["surface_raised"],
        background=COLORS["surface_raised"],
        foreground=COLORS["text"],
        insertcolor=COLORS["text"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["border"],
        darkcolor=COLORS["border"],
        padding=(6, 5),
    )
    style.map(
        "TEntry",
        bordercolor=[("focus", COLORS["accent"])],
        lightcolor=[("focus", COLORS["accent"])],
        darkcolor=[("focus", COLORS["accent"])],
    )

    style.configure(
        "TCombobox",
        fieldbackground=COLORS["surface_raised"],
        background=COLORS["surface_raised"],
        foreground=COLORS["text"],
        arrowcolor=COLORS["muted"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["border"],
        darkcolor=COLORS["border"],
        padding=(6, 4),
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", COLORS["surface_raised"])],
        foreground=[("readonly", COLORS["text"])],
        bordercolor=[("focus", COLORS["accent"])],
    )

    style.configure(
        "TButton",
        background=COLORS["surface_raised"],
        foreground=COLORS["text"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["surface_raised"],
        darkcolor=COLORS["surface_raised"],
        focuscolor=COLORS["surface_raised"],
        padding=(12, 6),
        font=(FONT_FAMILY, 9),
    )
    style.map(
        "TButton",
        background=[("active", COLORS["border"]), ("disabled", COLORS["surface"])],
        foreground=[("disabled", COLORS["muted"])],
    )

    style.configure(
        "Accent.TButton",
        background=COLORS["accent"],
        foreground=COLORS["accent_text"],
        bordercolor=COLORS["accent"],
        lightcolor=COLORS["accent"],
        darkcolor=COLORS["accent"],
        focuscolor=COLORS["accent"],
        padding=(20, 9),
        font=(FONT_FAMILY, 10, "bold"),
    )
    style.map(
        "Accent.TButton",
        background=[
            ("active", COLORS["accent_light"]),
            ("disabled", COLORS["border"]),
        ],
        foreground=[("disabled", COLORS["muted"])],
    )

    style.configure(
        "Dark.TCheckbutton",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        focuscolor=COLORS["surface"],
        padding=(0, 2),
    )
    style.map(
        "Dark.TCheckbutton",
        background=[("active", COLORS["surface"])],
        foreground=[("disabled", COLORS["muted"])],
    )
    style.configure(
        "Dark.TRadiobutton",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        focuscolor=COLORS["surface"],
        padding=(0, 1),
    )
    style.map(
        "Dark.TRadiobutton",
        background=[("active", COLORS["surface"])],
    )

    style.configure(
        "Media.Treeview",
        background=COLORS["surface_raised"],
        fieldbackground=COLORS["surface_raised"],
        foreground=COLORS["text"],
        bordercolor=COLORS["border"],
        rowheight=25,
        font=(FONT_FAMILY, 9),
    )
    style.map(
        "Media.Treeview",
        background=[("selected", COLORS["accent"])],
        foreground=[("selected", COLORS["accent_text"])],
    )
    style.configure(
        "Media.Treeview.Heading",
        background=COLORS["surface"],
        foreground=COLORS["muted"],
        font=(FONT_FAMILY, 8, "bold"),
        relief="flat",
        padding=(6, 4),
    )
    style.map(
        "Media.Treeview.Heading",
        background=[("active", COLORS["border"])],
    )

    style.configure(
        "Accent.Horizontal.TProgressbar",
        troughcolor=COLORS["surface_raised"],
        background=COLORS["accent"],
        bordercolor=COLORS["surface_raised"],
        lightcolor=COLORS["accent"],
        darkcolor=COLORS["accent"],
        thickness=8,
    )

    style.configure(
        "Vertical.TScrollbar",
        background=COLORS["surface_raised"],
        troughcolor=COLORS["surface"],
        bordercolor=COLORS["surface"],
        arrowcolor=COLORS["muted"],
        lightcolor=COLORS["surface_raised"],
        darkcolor=COLORS["surface_raised"],
        gripcount=0,
        arrowsize=12,
    )
    style.map("Vertical.TScrollbar", background=[("active", COLORS["border"])])

    style.configure(
        "TSeparator", background=COLORS["border"], bordercolor=COLORS["border"]
    )


def set_windows_app_id() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("autoedit.app")
    except Exception:
        pass
