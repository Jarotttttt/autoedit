import pytest

from autoedit.speech.srt_parser import SrtError, parse_srt, read_srt

SIMPLE = """1
00:00:00,000 --> 00:00:04,200
Selamat pagi semuanya.

2
00:00:04,200 --> 00:00:09,800
Hari ini kita belajar fotografi.
"""


def test_parse_simple_srt():
    cues = parse_srt(SIMPLE)
    assert len(cues) == 2
    assert cues[0].text == "Selamat pagi semuanya."
    assert cues[0].start_us == 0
    assert cues[0].end_us == 4_200_000
    assert cues[1].duration_us == 5_600_000


def test_accepts_dot_fraction():
    content = "1\n00:00:01.500 --> 00:00:03.000\nHalo.\n"
    cues = parse_srt(content)
    assert cues[0].start_us == 1_500_000
    assert cues[0].end_us == 3_000_000


def test_accepts_two_digit_fraction():
    content = "1\n00:00:01,5 --> 00:00:02,25\nHalo.\n"
    cues = parse_srt(content)
    assert cues[0].start_us == 1_500_000
    assert cues[0].end_us == 2_250_000


def test_multiline_cue_is_joined():
    content = "1\n00:00:00,000 --> 00:00:02,000\nBaris satu\nbaris dua.\n"
    assert parse_srt(content)[0].text == "Baris satu baris dua."


def test_strips_style_tags():
    content = "1\n00:00:00,000 --> 00:00:02,000\n<i>Miring</i> saja.\n"
    assert parse_srt(content)[0].text == "Miring saja."


def test_handles_crlf_and_bom(tmp_path):
    path = tmp_path / "uji.srt"
    content = SIMPLE.replace("\n", "\r\n").replace("\r\r\n", "\r\n")
    path.write_bytes(b"\xef\xbb\xbf" + content.encode("utf-8"))
    cues = read_srt(path)
    assert len(cues) == 2


def test_numbering_is_optional():
    content = "00:00:00,000 --> 00:00:01,000\nTanpa nomor.\n"
    cues = parse_srt(content)
    assert cues[0].index == 1


def test_rejects_end_before_start():
    content = "1\n00:00:05,000 --> 00:00:01,000\nSalah.\n"
    with pytest.raises(SrtError):
        parse_srt(content)


def test_rejects_empty_text():
    content = "1\n00:00:00,000 --> 00:00:01,000\n\n"
    with pytest.raises(SrtError):
        parse_srt(content)


def test_rejects_broken_timing():
    content = "1\n00:00:00 --> xx\nHalo.\n"
    with pytest.raises(SrtError):
        parse_srt(content)


def test_rejects_empty_file():
    with pytest.raises(SrtError):
        parse_srt("   \n")


def test_supports_hour_component_beyond_99():
    content = "1\n00:00:00,000 --> 00:00:01,000\nA.\n2\n100:00:00,000 --> 100:00:01,000\nB.\n"
    cues = parse_srt(content)
    assert cues[1].start_us == 360_000_000_000
