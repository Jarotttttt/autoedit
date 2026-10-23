from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..core.manifest import TimelineProject
from ..core.planner import PlannerConfig, TimelineResult, build_timeline
from ..core.probe import MEDIA_EXTENSIONS
from ..render.renderer import RenderConfig, render
from ..runtime import ProgressCallback, report_progress
from ..speech.aligned import TimestampSource
from ..speech.whisper import WhisperConfig

INVALID_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


@dataclass(frozen=True, slots=True)
class BuildRequest:
    name: str
    audio_path: Path
    media_paths: tuple[Path, ...]
    transcript_path: Path
    output_dir: Path
    source: TimestampSource = TimestampSource.AUTO
    config: PlannerConfig = PlannerConfig()
    whisper_config: WhisperConfig = WhisperConfig()
    burn_captions: bool = True
    render_config: RenderConfig = RenderConfig()


@dataclass(frozen=True, slots=True)
class BuildResult:
    video: Path
    manifest: Path
    timeline: TimelineResult


def build(
    request: BuildRequest,
    *,
    progress_callback: ProgressCallback | None = None,
) -> BuildResult:
    name = unique_project_name(request.name, request.output_dir)
    output = Path(request.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)

    report_progress(progress_callback, 0.01, "Menyiapkan project…")
    timeline = build_timeline(
        project_name=name,
        audio_path=request.audio_path,
        media_paths=list(request.media_paths),
        transcript_path=request.transcript_path,
        source=request.source,
        config=request.config,
        whisper_config=request.whisper_config,
        progress_callback=lambda value, message: report_progress(
            progress_callback, 0.02 + value * 0.20, message
        ),
    )

    project = timeline.project
    manifest = project.write_json(output / f"{file_stem(name)}.timeline.json")
    video = render(
        project,
        output / f"{file_stem(name)}.mp4",
        burn_captions=request.burn_captions,
        config=request.render_config,
        progress_callback=lambda value, message: report_progress(
            progress_callback, 0.22 + value * 0.78, message
        ),
    )
    report_progress(progress_callback, 1.0, "Selesai")
    return BuildResult(video=video, manifest=manifest, timeline=timeline)


def file_stem(value: str) -> str:
    cleaned = INVALID_FILENAME.sub("_", value).strip(" .")
    return cleaned or "video"


def unique_project_name(value: str, output_dir: Path) -> str:
    base = value.strip() or "Video Baru"
    output = Path(output_dir)
    candidate = base
    index = 1
    while (output / f"{file_stem(candidate)}.mp4").exists() or (
        output / f"{file_stem(candidate)}.timeline.json"
    ).exists():
        index += 1
        candidate = f"{base} ({index})"
    return candidate


def validate_paths(
    audio_path: str | Path,
    media_dir: str | Path,
    transcript_path: str | Path,
) -> None:
    audio = Path(audio_path)
    if not audio.is_file():
        raise FileNotFoundError(f"file audio tidak ditemukan: {audio}")
    folder = Path(media_dir)
    if not folder.is_dir():
        raise FileNotFoundError(f"folder media tidak ditemukan: {folder}")
    if not any(
        path.is_file() and path.suffix.lower() in MEDIA_EXTENSIONS
        for path in folder.iterdir()
    ):
        raise FileNotFoundError(f"folder media kosong atau tidak didukung: {folder}")
    transcript = Path(transcript_path)
    if not transcript.is_file():
        raise FileNotFoundError(f"file transcript tidak ditemukan: {transcript}")
    if transcript.suffix.lower() not in {".txt", ".srt"}:
        raise ValueError("transcript harus berupa file .txt atau .srt")
