from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TimestampSource(str, Enum):
    AUTO = "auto"
    WHISPER = "whisper"
    SRT = "srt"


@dataclass(frozen=True, slots=True)
class AlignedLine:
    text: str
    start_us: int
    duration_us: int

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("teks baris transcript tidak boleh kosong")
        if self.start_us < 0:
            raise ValueError("awal baris transcript tidak boleh negatif")
        if self.duration_us <= 0:
            raise ValueError("durasi baris transcript harus positif")

    @property
    def end_us(self) -> int:
        return self.start_us + self.duration_us


@dataclass(frozen=True, slots=True)
class TimedWord:
    text: str
    start_us: int
    end_us: int

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("teks kata tidak boleh kosong")
        if self.start_us < 0 or self.end_us <= self.start_us:
            raise ValueError("rentang waktu kata tidak valid")
