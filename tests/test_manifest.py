from pathlib import Path

import pytest

from autoedit.core.manifest import (
    AudioTrack,
    CanvasSpec,
    MediaType,
    TimelineCaption,
    TimelineClip,
    TimelineProject,
    seconds_to_us,
    us_to_seconds,
)


def make_project(clips=None, captions=None, duration=10_000_000):
    return TimelineProject(
        name="Uji",
        canvas=CanvasSpec(1920, 1080, 30),
        audio=AudioTrack(Path("audio.mp3"), duration),
        clips=clips or [TimelineClip(MediaType.IMAGE, Path("a.png"), 0, duration)],
        captions=captions or [],
    )


def test_seconds_to_us_rounds():
    assert seconds_to_us(1.2345678) == 1_234_568
    assert us_to_seconds(1_500_000) == 1.5


def test_seconds_to_us_rejects_nan():
    with pytest.raises(ValueError):
        seconds_to_us(float("nan"))


def test_clip_overlap_is_rejected():
    clips = [
        TimelineClip(MediaType.IMAGE, Path("a.png"), 0, 6_000_000),
        TimelineClip(MediaType.IMAGE, Path("b.png"), 5_000_000, 5_000_000),
    ]
    with pytest.raises(ValueError):
        make_project(clips)


def test_clip_beyond_duration_is_rejected():
    clips = [TimelineClip(MediaType.IMAGE, Path("a.png"), 0, 12_000_000)]
    with pytest.raises(ValueError):
        make_project(clips)


def test_caption_beyond_duration_is_rejected():
    captions = [TimelineCaption("halo", 9_000_000, 2_000_000)]
    with pytest.raises(ValueError):
        make_project(captions=captions)


def test_roundtrip_json(tmp_path: Path):
    project = make_project(
        clips=[
            TimelineClip(MediaType.IMAGE, Path("a.png"), 0, 4_000_000),
            TimelineClip(
                MediaType.VIDEO,
                Path("b.mp4"),
                4_000_000,
                6_000_000,
                source_duration_us=3_000_000,
                speed=0.5,
                scene_index=2,
            ),
        ],
        captions=[TimelineCaption("kalimat", 0, 4_000_000)],
    )
    destination = project.write_json(tmp_path / "uji.timeline.json")
    restored = TimelineProject.read_json(destination)
    assert restored.to_dict() == project.to_dict()


def test_manifest_rejects_wrong_version():
    data = make_project().to_dict()
    data["schemaVersion"] = 99
    with pytest.raises(ValueError):
        TimelineProject.from_dict(data)
