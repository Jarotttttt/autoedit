from __future__ import annotations

import os
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Sequence

from ..runtime import hidden_subprocess_kwargs, resource_path


class FfmpegError(RuntimeError):
    """Dilempar ketika FFmpeg tidak ditemukan atau gagal menjalankan perintah."""


@lru_cache(maxsize=1)
def find_ffmpeg() -> str:
    override = os.environ.get("AUTOEDIT_FFMPEG")
    if override:
        candidate = Path(override).expanduser()
        if candidate.is_file():
            return str(candidate)

    for relative in ("assets/tools/ffmpeg.exe", "tools/ffmpeg.exe"):
        bundled = resource_path(relative)
        if bundled.is_file():
            return str(bundled)

    found = shutil.which("ffmpeg")
    if found:
        return found

    try:
        import imageio_ffmpeg

        candidate = Path(imageio_ffmpeg.get_ffmpeg_exe())
        if candidate.is_file():
            return str(candidate)
    except Exception:
        pass

    raise FfmpegError(
        "FFmpeg tidak ditemukan. Pasang FFmpeg lalu tambahkan ke PATH, atau jalankan "
        "pip install imageio-ffmpeg, atau set variabel AUTOEDIT_FFMPEG."
    )


def ffmpeg_available() -> bool:
    try:
        find_ffmpeg()
    except FfmpegError:
        return False
    return True


def run(command: Sequence[str]) -> None:
    try:
        subprocess.run(
            list(command),
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            **hidden_subprocess_kwargs(),
        )
    except FileNotFoundError as error:
        raise FfmpegError(f"FFmpeg tidak ditemukan: {command[0]}") from error
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "FFmpeg gagal tanpa pesan").strip()
        raise FfmpegError(detail) from error
