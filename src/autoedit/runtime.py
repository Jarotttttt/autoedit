from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

ProgressCallback = Callable[[float, str], None]


def app_data_root() -> Path:
    override = os.environ.get("AUTOEDIT_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "data"
    return Path(__file__).resolve().parents[2] / "data"


def runtime_temp_dir() -> Path:
    return app_data_root() / "temp"


def configure_runtime_storage() -> Path:
    root = app_data_root()
    temporary = root / "temp"
    cache = root / "cache"
    for directory in (temporary, cache):
        directory.mkdir(parents=True, exist_ok=True)

    for name in ("TEMP", "TMP", "TMPDIR"):
        os.environ[name] = str(temporary)
    tempfile.tempdir = str(temporary)

    os.environ["HF_HOME"] = str(cache / "huggingface")
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(cache / "huggingface" / "hub")
    os.environ["XDG_CACHE_HOME"] = str(cache)
    os.environ["TORCH_HOME"] = str(cache / "torch")
    return root


def report_progress(
    callback: ProgressCallback | None, value: float, message: str
) -> None:
    if callback is not None:
        callback(max(0.0, min(1.0, value)), message)


def hidden_subprocess_kwargs() -> dict[str, object]:
    if os.name != "nt":
        return {}
    return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}


def resource_path(relative: str) -> Path:
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        return Path(bundle_root) / relative
    return Path(__file__).resolve().parents[2] / relative
