from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..core.manifest import seconds_to_us


class SrtError(ValueError):
    """Dilempar ketika file SRT tidak bisa dibaca atau rusak."""


@dataclass(frozen=True, slots=True)
class SrtCue:
    index: int
    text: str
    start_us: int
    end_us: int

    @property
    def duration_us(self) -> int:
        return self.end_us - self.start_us


TIMESTAMP_RE = re.compile(
    r"(?:(?P<sh>\d{1,3}):)?(?P<sm>\d{1,2}):(?P<ss>\d{1,2})(?:[,.](?P<sms>\d{1,3}))?"
    r"\s*-->\s*"
    r"(?:(?P<eh>\d{1,3}):)?(?P<em>\d{1,2}):(?P<es>\d{1,2})(?:[,.](?P<ems>\d{1,3}))?"
)
ARROW_RE = re.compile(r"\s*-->")
TAG_RE = re.compile(r"<[^>]+>")
INDEX_RE = re.compile(r"^\d+$")


def parse_srt(content: str) -> list[SrtCue]:
    normalized = re.sub(r"\r+\n?", "\n", content.replace("\ufeff", ""))
    lines = [line.strip() for line in normalized.split("\n")]
    cues: list[SrtCue] = []
    position = 0
    total = len(lines)
    while position < total:
        if not lines[position]:
            position += 1
            continue

        label = lines[position]
        cursor = position
        if INDEX_RE.match(label) and cursor + 1 < total and ARROW_RE.search(
            lines[cursor + 1]
        ):
            cursor += 1
        elif not ARROW_RE.search(lines[cursor]):
            cursor = _find_timing(lines, position)
            if cursor is None:
                raise SrtError(
                    f"baris {position + 1} bukan bagian dari subtitle yang valid: {label!r}"
                )

        timing = _parse_timing(lines[cursor])
        if timing is None:
            raise SrtError(
                f"baris {cursor + 1} memiliki format waktu yang tidak dikenali: "
                f"{lines[cursor]!r}"
            )
        start_us, end_us = timing
        if end_us <= start_us:
            raise SrtError(
                f"subtitle pada baris {cursor + 1} selesai sebelum waktu mulai"
            )

        cursor += 1
        text_lines: list[str] = []
        while cursor < total and lines[cursor]:
            if INDEX_RE.match(lines[cursor]) and cursor + 1 < total and ARROW_RE.search(
                lines[cursor + 1]
            ):
                break
            text_lines.append(lines[cursor])
            cursor += 1
        text = " ".join(TAG_RE.sub("", line).strip() for line in text_lines).strip()
        text = re.sub(r"\s+", " ", text)
        if not text:
            raise SrtError(f"subtitle pada baris {cursor} tidak memiliki teks")

        cues.append(
            SrtCue(
                index=len(cues) + 1,
                text=text,
                start_us=start_us,
                end_us=end_us,
            )
        )
        position = cursor

    if not cues:
        raise SrtError("file SRT tidak memuat satu subtitle pun")
    return cues


def read_srt(path: str | Path) -> list[SrtCue]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"file SRT tidak ditemukan: {source}")
    if source.suffix.lower() != ".srt":
        raise SrtError(f"file bukan SRT: {source.name}")
    return parse_srt(_decode(source.read_bytes()))


def _decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


def _find_timing(lines: list[str], start: int) -> int | None:
    limit = min(len(lines), start + 4)
    for cursor in range(start, limit):
        if ARROW_RE.search(lines[cursor]):
            return cursor
    return None


def _parse_timing(line: str) -> tuple[int, int] | None:
    match = TIMESTAMP_RE.search(line)
    if not match:
        return None
    return (
        _to_us(
            match.group("sh"), match.group("sm"), match.group("ss"), match.group("sms")
        ),
        _to_us(
            match.group("eh"), match.group("em"), match.group("es"), match.group("ems")
        ),
    )


def _to_us(
    hours: str | None,
    minutes: str | None,
    seconds: str | None,
    fraction: str | None,
) -> int:
    total_seconds = int(hours or 0) * 3600 + int(minutes or 0) * 60 + int(seconds or 0)
    total_us = total_seconds * 1_000_000
    if fraction:
        total_us += int(fraction.ljust(3, "0")) * 1000
    return total_us
