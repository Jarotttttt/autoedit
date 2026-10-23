from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from ..runtime import ProgressCallback, report_progress
from ..speech.aligned import AlignedLine, TimestampSource
from ..speech.aligner import align_lines
from ..speech.normalizer import normalize_ranges
from ..speech.srt_parser import read_srt
from ..speech.splitter import split_sentences
from ..speech.whisper import WhisperConfig, transcribe
from .manifest import (
    AudioTrack,
    CanvasSpec,
    MediaType,
    MotionPreset,
    TimelineCaption,
    TimelineClip,
    TimelineProject,
)
from .probe import MediaInfo, probe_media
from .scanner import VIDEO_EXTENSIONS

MOTION_CYCLE = (
    MotionPreset.ZOOM_IN,
    MotionPreset.ZOOM_OUT,
    MotionPreset.PAN_LEFT_RIGHT,
    MotionPreset.PAN_RIGHT_LEFT,
    MotionPreset.PAN_TOP_BOTTOM,
    MotionPreset.PAN_BOTTOM_TOP,
)


@dataclass(frozen=True, slots=True)
class PlannerConfig:
    canvas: CanvasSpec = CanvasSpec()
    image_shot_duration_us: int = 6_000_000
    min_video_speed: float = 0.25
    max_video_speed: float = 4.0
    add_captions: bool = True
    motion_enabled: bool = True

    def __post_init__(self) -> None:
        if self.image_shot_duration_us <= 0:
            raise ValueError("durasi shot gambar harus positif")
        if not 0 < self.min_video_speed <= self.max_video_speed:
            raise ValueError("rentang kecepatan video tidak valid")


@dataclass(frozen=True, slots=True)
class SceneSpec:
    path: Path
    start_us: int
    duration_us: int
    text: str = ""
    scene_index: int = 1

    @property
    def end_us(self) -> int:
        return self.start_us + self.duration_us


@dataclass(frozen=True, slots=True)
class TimelineResult:
    project: TimelineProject
    audio_info: MediaInfo
    media_info: tuple[MediaInfo, ...]
    source: TimestampSource
    closed_gaps: int
    trimmed_overlaps: int


def resolve_source(mode: TimestampSource, transcript_path: Path) -> TimestampSource:
    if mode is not TimestampSource.AUTO:
        return mode
    return TimestampSource.SRT if transcript_path.suffix.lower() == ".srt" else TimestampSource.WHISPER


def load_lines(
    transcript_path: str | Path,
    source: TimestampSource,
    *,
    audio_path: str | Path,
    audio_duration_us: int,
    whisper_config: WhisperConfig | None = None,
    progress_callback: ProgressCallback | None = None,
) -> tuple[list[AlignedLine], int, int]:
    path = Path(transcript_path)
    if not path.is_file():
        raise FileNotFoundError(f"file transcript tidak ditemukan: {path}")
    if source is TimestampSource.SRT:
        cues = read_srt(path)
        report_progress(progress_callback, 1.0, f"SRT dibaca: {len(cues)} subtitle")
        report = normalize_ranges(
            [AlignedLine(cue.text, cue.start_us, cue.duration_us) for cue in cues],
            audio_duration_us,
        )
        return list(report.lines), report.gaps_closed, report.overlaps_trimmed

    text = path.read_text(encoding="utf-8-sig", errors="replace")
    sentences = split_sentences(text)
    words = transcribe(
        audio_path,
        transcript_hint="\n".join(sentences),
        config=whisper_config,
        progress_callback=progress_callback,
    )
    return align_lines(sentences, words, audio_duration_us), 0, 0


def build_timeline(
    *,
    project_name: str,
    audio_path: str | Path,
    media_paths: Sequence[str | Path],
    transcript_path: str | Path,
    source: TimestampSource = TimestampSource.AUTO,
    config: PlannerConfig | None = None,
    whisper_config: WhisperConfig | None = None,
    progress_callback: ProgressCallback | None = None,
) -> TimelineResult:
    cfg = config or PlannerConfig()
    audio = Path(audio_path).resolve()
    if not audio.is_file():
        raise FileNotFoundError(f"file audio tidak ditemukan: {audio}")
    media = [Path(item).resolve() for item in media_paths]
    if not media:
        raise ValueError("daftar media tidak boleh kosong")

    transcript = Path(transcript_path)
    active_source = resolve_source(source, transcript)

    report_progress(progress_callback, 0.01, "Membaca metadata audio…")
    audio_info = probe_media(audio)
    if audio_info.duration_us <= 0:
        raise ValueError("durasi audio tidak valid")

    lines, closed_gaps, trimmed_overlaps = load_lines(
        transcript,
        active_source,
        audio_path=audio,
        audio_duration_us=audio_info.duration_us,
        whisper_config=whisper_config,
        progress_callback=progress_callback,
    )
    _validate_pairing(lines, media)

    infos: list[MediaInfo] = [probe_media(path) for path in media]
    scenes = align_scenes(media, lines)

    clips: list[TimelineClip] = []
    captions: list[TimelineCaption] = []
    motion_index = 0
    for scene, info in zip(scenes, infos, strict=True):
        if scene.path.suffix.lower() in VIDEO_EXTENSIONS:
            produced = _plan_video(scene, cfg, info.duration_us, motion_index)
        else:
            produced = _plan_image(scene, cfg, motion_index)
        clips.extend(produced)
        motion_index += len(produced)
        if cfg.add_captions and scene.text.strip():
            captions.append(TimelineCaption(scene.text.strip(), scene.start_us, scene.duration_us))

    project = TimelineProject(
        name=project_name,
        canvas=cfg.canvas,
        audio=AudioTrack(audio, audio_info.duration_us),
        clips=clips,
        captions=captions,
    )
    _fill_gaps(project)
    report_progress(progress_callback, 1.0, "Timeline selesai disusun")
    return TimelineResult(
        project=project,
        audio_info=audio_info,
        media_info=tuple(infos),
        source=active_source,
        closed_gaps=closed_gaps,
        trimmed_overlaps=trimmed_overlaps,
    )


def align_scenes(media: Sequence[Path], lines: Sequence[AlignedLine]) -> list[SceneSpec]:
    _validate_pairing(lines, media)
    return [
        SceneSpec(
            path=path,
            start_us=line.start_us,
            duration_us=line.duration_us,
            text=line.text,
            scene_index=index + 1,
        )
        for index, (path, line) in enumerate(zip(media, lines, strict=True))
    ]


def _validate_pairing(lines: Sequence[AlignedLine], media: Sequence[Path]) -> None:
    if len(lines) == len(media):
        return
    details = [
        f"Transcript memiliki {len(lines)} kalimat tetapi media berisi {len(media)} file. "
        "Setiap kalimat membutuhkan tepat satu gambar atau video, dalam urutan yang sama."
    ]
    if len(lines) > len(media):
        details.append("\nKalimat yang belum memiliki media:")
        for index in range(len(media), len(lines)):
            details.append(f'- Kalimat {index + 1}: "{_preview(lines[index].text)}"')
    else:
        details.append("\nMedia yang belum memiliki kalimat:")
        for index in range(len(lines), len(media)):
            details.append(f"- File {index + 1}: {media[index].name}")
    raise ValueError("\n".join(details))


def _preview(text: str, limit: int = 110) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    return normalized if len(normalized) <= limit else normalized[: limit - 1].rstrip() + "…"


def _plan_image(scene: SceneSpec, config: PlannerConfig, motion_index: int) -> list[TimelineClip]:
    shot_count = max(1, round(scene.duration_us / config.image_shot_duration_us))
    ranges = _equal_ranges(scene.start_us, scene.duration_us, shot_count)
    return [
        TimelineClip(
            media_type=MediaType.IMAGE,
            path=scene.path,
            start_us=start,
            duration_us=end - start,
            motion=(
                MOTION_CYCLE[(motion_index + shot_index) % len(MOTION_CYCLE)]
                if config.motion_enabled
                else MotionPreset.NONE
            ),
            scene_index=scene.scene_index,
        )
        for shot_index, (start, end) in enumerate(ranges)
    ]


def _plan_video(
    scene: SceneSpec, config: PlannerConfig, source_duration_us: int, motion_index: int
) -> list[TimelineClip]:
    if source_duration_us <= 0:
        raise ValueError(f"durasi video tidak valid: {scene.path.name}")
    raw_speed = source_duration_us / scene.duration_us
    if raw_speed > config.max_video_speed:
        speed = config.max_video_speed
        used_source_us = max(1, round(scene.duration_us * speed))
        loop_count = 1
    elif raw_speed < config.min_video_speed:
        loop_count = max(
            1, math.ceil(config.min_video_speed * scene.duration_us / source_duration_us)
        )
        speed = source_duration_us * loop_count / scene.duration_us
        used_source_us = source_duration_us
    else:
        speed = raw_speed
        used_source_us = source_duration_us
        loop_count = 1

    ranges = _equal_ranges(scene.start_us, scene.duration_us, loop_count)
    return [
        TimelineClip(
            media_type=MediaType.VIDEO,
            path=scene.path,
            start_us=start,
            duration_us=end - start,
            source_duration_us=used_source_us,
            speed=speed,
            volume=0.0,
            motion=(
                MOTION_CYCLE[(motion_index + loop_index) % len(MOTION_CYCLE)]
                if config.motion_enabled
                else MotionPreset.NONE
            ),
            scene_index=scene.scene_index,
        )
        for loop_index, (start, end) in enumerate(ranges)
    ]


def _equal_ranges(start_us: int, duration_us: int, count: int) -> list[tuple[int, int]]:
    boundaries = [start_us + round(duration_us * index / count) for index in range(count)]
    boundaries.append(start_us + duration_us)
    return list(zip(boundaries, boundaries[1:], strict=True))


def _fill_gaps(project: TimelineProject) -> None:
    clips = project.clips
    if not clips:
        raise ValueError("timeline tidak memiliki clip visual")
    rebuilt: list[TimelineClip] = []
    previous_end = 0
    for clip in clips:
        if clip.start_us > previous_end:
            shifted = _stretch(clip, clip.start_us, clip.end_us)
            rebuilt.append(_stretch(shifted, previous_end, previous_end + clip.duration_us))
        elif clip.start_us < previous_end:
            end = max(clip.end_us, previous_end + 1)
            rebuilt.append(_stretch(clip, previous_end, end))
        else:
            rebuilt.append(clip)
        previous_end = rebuilt[-1].end_us
    if previous_end < project.duration_us:
        rebuilt[-1] = _stretch(rebuilt[-1], rebuilt[-1].start_us, project.duration_us)
    project.clips = rebuilt
    project.validate()


def _stretch(clip: TimelineClip, start_us: int, end_us: int) -> TimelineClip:
    duration_us = max(1, end_us - start_us)
    source_duration_us = clip.source_duration_us
    if source_duration_us is not None:
        source_duration_us = max(1, round(duration_us * clip.speed))
    return TimelineClip(
        media_type=clip.media_type,
        path=clip.path,
        start_us=start_us,
        duration_us=duration_us,
        source_start_us=clip.source_start_us,
        source_duration_us=source_duration_us,
        speed=clip.speed,
        volume=clip.volume,
        motion=clip.motion,
        scene_index=clip.scene_index,
    )
