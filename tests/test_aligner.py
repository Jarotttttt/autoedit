from pathlib import Path

import pytest

from autoedit.core.manifest import seconds_to_us
from autoedit.speech.aligned import AlignedLine, TimedWord
from autoedit.speech.aligner import AlignmentError, align_lines, words_from_segments
from autoedit.speech.normalizer import normalize_ranges
from autoedit.speech.tokenizer import tokenize


def test_tokenizer_splits_cjk_per_character():
    assert tokenize("朝です") == ["朝", "で", "す"]


def test_tokenizer_lowercases_latin():
    assert tokenize("Halo, Dunia!") == ["halo", "dunia"]


def test_align_lines_splits_at_matching_word():
    lines = ["Halo dunia.", "Selamat pagi."]
    words = [
        TimedWord("Halo", 0, 400_000),
        TimedWord("dunia", 400_000, 900_000),
        TimedWord("Selamat", 1_200_000, 1_500_000),
        TimedWord("pagi", 1_500_000, 2_000_000),
    ]
    result = align_lines(lines, words, 2_000_000)
    assert len(result) == 2
    assert result[0].start_us == 0
    assert 900_000 <= result[0].end_us <= 1_200_000
    assert result[1].end_us == 2_000_000


def test_align_covers_full_audio():
    lines = ["satu dua.", "tiga empat.", "lima."]
    words = [
        TimedWord("satu", 0, 500_000),
        TimedWord("dua", 500_000, 1_000_000),
        TimedWord("tiga", 1_000_000, 1_500_000),
        TimedWord("empat", 1_500_000, 2_000_000),
        TimedWord("lima", 2_000_000, 3_000_000),
    ]
    result = align_lines(lines, words, 3_000_000)
    assert result[0].start_us == 0
    assert result[-1].end_us == 3_000_000
    for previous, current in zip(result, result[1:]):
        assert previous.end_us <= current.start_us


def test_align_requires_words():
    with pytest.raises(AlignmentError):
        align_lines(["halo."], [], 1_000_000)


def test_normalizer_closes_gaps_and_trims_overlap():
    lines = [
        AlignedLine("satu", 0, 1_000_000),
        AlignedLine("dua", 1_500_000, 1_000_000),
        AlignedLine("tiga", 2_000_000, 1_000_000),
    ]
    report = normalize_ranges(lines, 3_000_000)
    assert report.gaps_closed == 1
    assert report.overlaps_trimmed == 1
    assert [line.start_us for line in report.lines] == [0, 1_000_000, 2_000_000]
    assert report.lines[-1].end_us == 3_000_000


def test_normalizer_trims_tail_beyond_audio():
    lines = [AlignedLine("panjang", 0, 5_000_000)]
    report = normalize_ranges(lines, 3_000_000)
    assert report.lines[0].end_us == 3_000_000
    assert report.trimmed_tail_us == 2_000_000


def test_normalizer_rejects_zero_duration():
    with pytest.raises(ValueError):
        normalize_ranges([], 1_000_000)


def test_words_from_segments_uses_word_timestamps():
    class Word:
        word = "halo"
        start = 0.5
        end = 1.0

    class Segment:
        words = [Word()]
        text = "halo"
        start = 0.5
        end = 1.0

    words = words_from_segments([Segment()])
    assert words[0].start_us == seconds_to_us(0.5)
    assert words[0].end_us == seconds_to_us(1.0)
