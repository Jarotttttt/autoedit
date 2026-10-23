from pathlib import Path

from autoedit.core.numbering import inspect_numbering
from autoedit.core.scanner import media_number, scan_media, sort_media


def test_numbered_files_sort_first():
    paths = [
        Path("zzz.png"),
        Path("video_10.mp4"),
        Path("img-01.png"),
        Path("002.jpg"),
    ]
    ordered = [path.name for path in sort_media(paths)]
    assert ordered == ["002.jpg", "img-01.png", "video_10.mp4", "zzz.png"]


def test_numbered_files_ignore_zero_padding():
    paths = [Path("10.png"), Path("2.png"), Path("001.png")]
    ordered = [path.name for path in sort_media(paths)]
    assert ordered == ["001.png", "2.png", "10.png"]


def test_natural_sort_without_numbers():
    paths = [Path("scene10.png"), Path("scene2.png"), Path("scene1.png")]
    ordered = [path.name for path in sort_media(paths)]
    assert ordered == ["scene1.png", "scene2.png", "scene10.png"]


def test_media_number_parsing():
    assert media_number(Path("img-7.png")) == 7
    assert media_number(Path("gambar 12.jpg")) == 12
    assert media_number(Path("cover.png")) is None


def test_inspect_numbering_reports_missing_and_duplicates():
    paths = [Path("001.png"), Path("002.png"), Path("002_v2.png"), Path("004.png")]
    report = inspect_numbering(paths)
    assert report.missing_numbers == (3,)
    assert report.duplicate_numbers == (2,)
    assert report.fully_numbered is True


def test_scan_media_ignores_unsupported_files(tmp_path: Path):
    (tmp_path / "001.png").write_bytes(b"x")
    (tmp_path / "002.mp4").write_bytes(b"x")
    (tmp_path / "catatan.txt").write_text("abaikan")
    names = [path.name for path in scan_media(tmp_path)]
    assert names == ["001.png", "002.mp4"]
