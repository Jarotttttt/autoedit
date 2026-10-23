from pathlib import Path

import pytest

from autoedit.app.pipeline import file_stem, unique_project_name
from autoedit.render.captions import ass_timestamp, build_ass, escape_text
from autoedit.render.renderer import timeline_frame_count
from autoedit.core.manifest import AudioTrack, CanvasSpec, MediaType, TimelineCaption, TimelineClip, TimelineProject


def test_ass_timestamp_format():
    assert ass_timestamp(0) == "0:00:00.00"
    assert ass_timestamp(3_725_000_000) == "1:02:05.00"


def test_escape_text_handles_braces_and_newlines():
    escaped = escape_text("a{b}\nc")
    assert escaped == "a\\{b\\}\\Nc"


def test_build_ass_contains_events():
    project = TimelineProject(
        name="Uji",
        canvas=CanvasSpec(1280, 720, 25),
        audio=AudioTrack(Path("a.mp3"), 5_000_000),
        clips=[TimelineClip(MediaType.IMAGE, Path("a.png"), 0, 5_000_000)],
        captions=[TimelineCaption("halo dunia", 0, 2_000_000)],
    )
    ass = build_ass(project)
    assert "[Script Info]" in ass
    assert "Dialogue: 0,0:00:00.00,0:00:02.00" in ass
    assert "halo dunia" in ass


def test_file_stem_replaces_invalid_characters():
    assert file_stem('a<b>c:d"e/f') == "a_b_c_d_e_f"


def test_unique_project_name_increments(tmp_path: Path):
    (tmp_path / "Video.mp4").write_bytes(b"x")
    assert unique_project_name("Video", tmp_path) == "Video (2)"


def test_timeline_frame_count_last_clip_uses_project_duration():
    project = TimelineProject(
        name="Uji",
        canvas=CanvasSpec(1920, 1080, 30),
        audio=AudioTrack(Path("a.mp3"), 1_000_000),
        clips=[TimelineClip(MediaType.IMAGE, Path("a.png"), 0, 1_000_000)],
    )
    clip = project.clips[0]
    assert timeline_frame_count(project, clip, True) == 30


def test_planner_config_defaults():
    from autoedit.core.planner import PlannerConfig

    config = PlannerConfig()
    assert config.canvas.width == 1920
    assert config.add_captions is True
