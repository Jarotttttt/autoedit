from __future__ import annotations

import re
from pathlib import Path

from .probe import IMAGE_EXTENSIONS, MEDIA_EXTENSIONS, VIDEO_EXTENSIONS

NUMBERED_MEDIA_RE = re.compile(
    r"^(?:(?:img|image|vid|video|clip|scene|shot|gambar)(?:[-_ ]+|(?=\d)))?(\d+)(?=$|[-_. ])",
    re.IGNORECASE,
)
NATURAL_NUMBER_RE = re.compile(r"(\d+)")


def scan_media(folder: str | Path) -> list[Path]:
    root = Path(folder)
    if not root.is_dir():
        raise FileNotFoundError(f"folder media tidak ditemukan: {root}")
    files = [
        path
        for path in root.iterdir()
        if path.is_file() and path.suffix.lower() in MEDIA_EXTENSIONS
    ]
    if not files:
        raise FileNotFoundError(f"tidak ada gambar atau video di folder: {root}")
    return sort_media(files)


def sort_media(paths: list[Path]) -> list[Path]:
    numbered: list[tuple[int, Path]] = []
    unnumbered: list[Path] = []
    for path in paths:
        number = media_number(path)
        if number is None:
            unnumbered.append(path)
        else:
            numbered.append((number, path))

    numbered.sort(key=lambda item: (_natural_key(item[1].name), item[1].name.casefold()))
    unnumbered.sort(key=lambda path: (_natural_key(path.name), path.name.casefold()))
    return [path for _number, path in numbered] + unnumbered


def media_number(path: Path) -> int | None:
    match = NUMBERED_MEDIA_RE.match(path.stem)
    return int(match.group(1)) if match else None


def _natural_key(value: str) -> tuple[tuple[int, object], ...]:
    return tuple(
        (0, int(part)) if part.isdigit() else (1, part.casefold())
        for part in NATURAL_NUMBER_RE.split(value)
        if part
    )
