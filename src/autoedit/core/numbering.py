from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .scanner import media_number


@dataclass(frozen=True, slots=True)
class NumberingReport:
    numbered: tuple[tuple[int, tuple[Path, ...]], ...]
    unnumbered: tuple[Path, ...]
    missing_numbers: tuple[int, ...]
    duplicate_numbers: tuple[int, ...]

    @property
    def fully_numbered(self) -> bool:
        return bool(self.numbered) and not self.unnumbered


def inspect_numbering(paths: Sequence[Path]) -> NumberingReport:
    grouped: dict[int, list[Path]] = {}
    unnumbered: list[Path] = []
    for path in paths:
        number = media_number(path)
        if number is None:
            unnumbered.append(path)
        else:
            grouped.setdefault(number, []).append(path)
    positive = {number for number in grouped if number > 0}
    maximum = max(positive, default=0)
    missing = tuple(number for number in range(1, maximum + 1) if number not in grouped)
    duplicates = tuple(
        sorted(number for number, items in grouped.items() if len(items) > 1)
    )
    return NumberingReport(
        numbered=tuple((number, tuple(items)) for number, items in sorted(grouped.items())),
        unnumbered=tuple(unnumbered),
        missing_numbers=missing,
        duplicate_numbers=duplicates,
    )
