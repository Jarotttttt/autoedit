from pathlib import Path

import pytest

from autoedit.core.manifest import CanvasSpec, MediaType, MotionPreset
from autoedit.core.planner import (
    PlannerConfig,
    align_scenes,
    build_timeline,
)
from autoedit.speech.aligned import AlignedLine


def test_align_scenes_pairs_by_order(tmp_path: Path):
    media = [tmp_path / "001.png", tmp_path / "002.png"]
    lines = [AlignedLine("satu", 0, 1_000_000), AlignedLine("dua", 1_000_000, 1_000_000)]
    scenes = align_scenes(media, lines)
    assert [scene.path for scene in scenes] == media
    assert [scene.text for scene in scenes] == ["satu", "dua"]


def test_align_scenes_rejects_count_mismatch(tmp_path: Path):
    media = [tmp_path / "001.png"]
    lines = [AlignedLine("satu", 0, 1_000_000), AlignedLine("dua", 1_000_000, 1_000_000)]
    with pytest.raises(ValueError):
        align_scenes(media, lines)


def test_planner_config_rejects_zero_shot():
    with pytest.raises(ValueError):
        PlannerConfig(image_shot_duration_us=0)


def test_canvas_validation():
    with pytest.raises(ValueError):
        CanvasSpec(0, 1080)
    with pytest.raises(ValueError):
        CanvasSpec(1920, 1080, 0)


def test_motion_cycle_has_expected_members():
    assert MotionPreset.ZOOM_IN in MotionPreset
    assert MediaType.IMAGE.value == "image"
