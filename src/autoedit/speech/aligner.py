from __future__ import annotations

from difflib import SequenceMatcher
from typing import Sequence

from ..core.manifest import seconds_to_us
from .aligned import AlignedLine, TimedWord
from .tokenizer import tokenize


class AlignmentError(RuntimeError):
    pass


def align_lines(
    lines: Sequence[str],
    words: Sequence[TimedWord],
    audio_duration_us: int,
) -> list[AlignedLine]:
    if audio_duration_us <= 0:
        raise ValueError("durasi audio harus positif")
    if not lines:
        raise ValueError("daftar kalimat transcript kosong")
    if not words:
        raise AlignmentError("timestamp kata dari Whisper kosong")

    reference_tokens: list[str] = []
    reference_boundaries = [0]
    for line in lines:
        tokens = tokenize(line)
        if not tokens:
            raise ValueError(f"kalimat tidak memiliki kata yang valid: {line!r}")
        reference_tokens.extend(tokens)
        reference_boundaries.append(len(reference_tokens))

    recognized_tokens: list[str] = []
    token_times: list[tuple[int, int]] = []
    for word in words:
        for token in tokenize(word.text):
            recognized_tokens.append(token)
            token_times.append((word.start_us, word.end_us))
    if not recognized_tokens:
        raise AlignmentError("timestamp Whisper tidak mengandung token yang valid")
    if len(lines) > 1 and len(recognized_tokens) < 2:
        raise AlignmentError("timestamp Whisper tidak cukup untuk membagi transcript")

    mapping = _matching_tokens(reference_tokens, recognized_tokens)
    boundaries = [0]
    total_lines = len(lines)
    for line_index, reference_boundary in enumerate(reference_boundaries[1:-1], 1):
        recognized_boundary = _recognized_boundary(
            reference_boundary,
            len(reference_tokens),
            len(recognized_tokens),
            mapping,
        )
        timestamp = _boundary_timestamp(recognized_boundary, token_times)
        minimum = boundaries[-1] + 1
        maximum = audio_duration_us - (total_lines - line_index)
        boundaries.append(max(minimum, min(timestamp, maximum)))
    boundaries.append(audio_duration_us)

    return [
        AlignedLine(line.strip(), start, end - start)
        for line, start, end in zip(lines, boundaries[:-1], boundaries[1:], strict=True)
    ]


def words_from_segments(segments) -> list[TimedWord]:
    words: list[TimedWord] = []
    for segment in segments:
        segment_words = getattr(segment, "words", None) or []
        if segment_words:
            for word in segment_words:
                start_us = seconds_to_us(float(word.start))
                end_us = seconds_to_us(float(word.end))
                if str(word.word).strip() and end_us > start_us:
                    words.append(TimedWord(str(word.word).strip(), start_us, end_us))
            continue
        start_us = seconds_to_us(float(segment.start))
        end_us = seconds_to_us(float(segment.end))
        if str(segment.text).strip() and end_us > start_us:
            words.append(TimedWord(str(segment.text).strip(), start_us, end_us))
    return sorted(words, key=lambda word: (word.start_us, word.end_us))


def _matching_tokens(reference: Sequence[str], recognized: Sequence[str]) -> dict[int, int]:
    mapping: dict[int, int] = {}
    matcher = SequenceMatcher(a=reference, b=recognized, autojunk=False)
    for block in matcher.get_matching_blocks():
        for offset in range(block.size):
            mapping[block.a + offset] = block.b + offset
    return mapping


def _recognized_boundary(
    reference_boundary: int,
    reference_count: int,
    recognized_count: int,
    mapping: dict[int, int],
) -> int:
    previous = [(ref, rec) for ref, rec in mapping.items() if ref < reference_boundary]
    following = [(ref, rec) for ref, rec in mapping.items() if ref >= reference_boundary]
    if previous and following:
        left = max(previous)[1] + 1
        right = min(following)[1]
        boundary = round((left + right) / 2)
    else:
        boundary = round(recognized_count * reference_boundary / reference_count)
    return max(1, min(boundary, recognized_count - 1))


def _boundary_timestamp(boundary: int, token_times: Sequence[tuple[int, int]]) -> int:
    before_end = token_times[boundary - 1][1]
    after_start = token_times[boundary][0]
    return round((before_end + after_start) / 2)
