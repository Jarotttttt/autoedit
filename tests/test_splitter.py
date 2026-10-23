import pytest

from autoedit.speech.splitter import split_sentences


def test_splits_latin_sentences():
    text = "Pernahkah kamu membayangkan ini? Dunia akan gelap. Selesai!"
    assert split_sentences(text) == [
        "Pernahkah kamu membayangkan ini?",
        "Dunia akan gelap.",
        "Selesai!",
    ]


def test_ignores_line_breaks_as_separator():
    text = "Baris pertama\nmasih kalimat yang sama. Kalimat kedua."
    assert split_sentences(text) == [
        "Baris pertama masih kalimat yang sama.",
        "Kalimat kedua.",
    ]


def test_keeps_decimal_numbers():
    text = "Suhu naik 1.5 derajat. Lalu turun lagi."
    assert split_sentences(text) == ["Suhu naik 1.5 derajat.", "Lalu turun lagi."]


def test_supports_cjk_punctuation():
    text = "朝です。「元気ですか？」はい！"
    assert split_sentences(text) == ["朝です。", "「元気ですか？」", "はい！"]


def test_handles_ellipsis_run():
    text = "Tunggu… lalu pergi."
    assert split_sentences(text) == ["Tunggu…", "lalu pergi."]


def test_trailing_text_without_terminator():
    text = "Kalimat pertama. Kalimat tanpa titik"
    assert split_sentences(text) == ["Kalimat pertama.", "Kalimat tanpa titik"]


def test_empty_text_raises():
    with pytest.raises(ValueError):
        split_sentences("   \n  ")
