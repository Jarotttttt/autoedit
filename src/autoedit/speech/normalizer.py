from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .aligned import AlignedLine


@dataclass(frozen=True, slots=True)
class NormalizeReport:
    lines: tuple[AlignedLine, ...]
    gaps_closed: int
    overlaps_trimmed: int
    trimmed_tail_us: int


def normalize_ranges(
    lines: Sequence[AlignedLine],
    audio_duration_us: int,
) -> NormalizeReport:
    if audio_duration_us <= 0:
        raise ValueError("durasi audio harus positif")
    if not lines:
        raise ValueError("tidak ada baris transcript untuk disusun")

    ordered = sorted(lines, key=lambda line: (line.start_us, line.end_us))
    result: list[AlignedLine] = []
    for line in ordered:
        start = result[-1].end_us if result else 0
        result.append(
            AlignedLine(line.text, start, max(1, line.end_us - line.start_us))
        )

    gaps = sum(
        1 for previous, current in zip(ordered, ordered[1:]) if current.start_us > previous.end_us
    )
    overlaps = sum(
        1 for previous, current in zip(ordered, ordered[1:]) if current.start_us < previous.end_us
    )

    trimmed = 0
    if result and result[-1].end_us > audio_duration_us:
        last = result[-1]
        trimmed = last.end_us - audio_duration_us
        available = audio_duration_us - last.start_us
        if available <= 0:
            raise ValueError("subtitle terakhir dimulai melewati durasi audio")
        result[-1] = AlignedLine(last.text, last.start_us, available)

    return NormalizeReport(
        lines=tuple(result),
        gaps_closed=gaps,
        overlaps_trimmed=overlaps,
        trimmed_tail_us=max(0, trimmed),
    )
