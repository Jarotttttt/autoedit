from __future__ import annotations

import math
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ..core.manifest import MediaType, TimelineClip, TimelineProject, us_to_seconds
from ..runtime import ProgressCallback, report_progress
from .captions import escape_filter_path, write_ass
from .ffmpeg import find_ffmpeg, run
from .filters import image_filter, video_filter


class RenderError(RuntimeError):
    """Dilempar ketika timeline tidak bisa dirender."""


@dataclass(frozen=True, slots=True)
class RenderConfig:
    crf: int = 18
    preset: str = "medium"
    audio_bitrate: str = "192k"

    def __post_init__(self) -> None:
        if not 0 <= self.crf <= 51:
            raise ValueError("CRF harus antara 0 dan 51")


def render(
    project: TimelineProject,
    destination: str | Path,
    *,
    burn_captions: bool = True,
    overwrite: bool = False,
    config: RenderConfig | None = None,
    progress_callback: ProgressCallback | None = None,
) -> Path:
    cfg = config or RenderConfig()
    output = Path(destination).resolve()
    if output.exists() and not overwrite:
        raise FileExistsError(f"file video sudah ada: {output}")
    if not project.clips:
        raise RenderError("timeline tidak memiliki clip visual")
    output.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg = find_ffmpeg()
    with tempfile.TemporaryDirectory(
        prefix=f".{output.stem}.", dir=output.parent
    ) as temporary_name:
        temporary = Path(temporary_name)
        parts: list[Path] = []
        total = len(project.clips)
        for index, clip in enumerate(project.clips):
            report_progress(
                progress_callback,
                0.02 + 0.66 * index / total,
                f"Merender media {index + 1}/{total}…",
            )
            part = temporary / f"part-{index:05d}.mp4"
            _render_clip(ffmpeg, project, clip, part, index == total - 1, cfg)
            parts.append(part)

        visual = temporary / "visual.mp4"
        report_progress(progress_callback, 0.70, "Menggabungkan potongan media…")
        _concat(ffmpeg, parts, visual, temporary / "parts.txt")

        if burn_captions and project.captions:
            captioned = temporary / "captioned.mp4"
            report_progress(progress_callback, 0.80, "Menempelkan caption ke video…")
            subtitle = write_ass(project, temporary / "captions.ass")
            run(
                [
                    ffmpeg,
                    "-y",
                    "-loglevel",
                    "error",
                    "-i",
                    str(visual),
                    "-an",
                    "-vf",
                    f"ass=filename='{escape_filter_path(subtitle)}'",
                    *_encoder(cfg),
                    str(captioned),
                ]
            )
            visual = captioned

        final = temporary / "final.mp4"
        report_progress(progress_callback, 0.92, "Menggabungkan audio narasi…")
        run(
            [
                ffmpeg,
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(visual),
                "-i",
                str(project.audio.path),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                cfg.audio_bitrate,
                "-t",
                f"{us_to_seconds(project.duration_us):.6f}",
                "-shortest",
                str(final),
            ]
        )
        os.replace(final, output)

    report_progress(progress_callback, 1.0, "Video selesai dibuat")
    return output


def _render_clip(
    ffmpeg: str,
    project: TimelineProject,
    clip: TimelineClip,
    output: Path,
    is_last: bool,
    config: RenderConfig,
) -> None:
    frame_count = timeline_frame_count(project, clip, is_last)
    if clip.media_type is MediaType.IMAGE:
        command = [
            ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-loop",
            "1",
            "-framerate",
            str(project.canvas.fps),
            "-i",
            str(clip.path),
            "-an",
            "-vf",
            image_filter(project, clip, frame_count),
            "-frames:v",
            str(frame_count),
            "-r",
            str(project.canvas.fps),
            *_encoder(config),
            str(output),
        ]
    else:
        source_duration = clip.source_duration_us or round(clip.duration_us * clip.speed)
        command = [
            ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-ss",
            f"{us_to_seconds(clip.source_start_us):.6f}",
            "-t",
            f"{us_to_seconds(source_duration):.6f}",
            "-i",
            str(clip.path),
            "-an",
            "-vf",
            video_filter(project, clip, frame_count),
            "-frames:v",
            str(frame_count),
            "-r",
            str(project.canvas.fps),
            *_encoder(config),
            str(output),
        ]
    run(command)


def _concat(ffmpeg: str, parts: list[Path], output: Path, list_file: Path) -> None:
    lines = [f"file '{_concat_escape(path)}'" for path in parts]
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    run(
        [
            ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c",
            "copy",
            str(output),
        ]
    )


def timeline_frame_count(
    project: TimelineProject, clip: TimelineClip, is_last: bool
) -> int:
    fps = project.canvas.fps
    start_frame = round(clip.start_us * fps / 1_000_000)
    if is_last:
        end_frame = math.ceil(project.duration_us * fps / 1_000_000)
    else:
        end_frame = round(clip.end_us * fps / 1_000_000)
    return max(1, end_frame - start_frame)


def _encoder(config: RenderConfig) -> list[str]:
    return [
        "-c:v",
        "libx264",
        "-crf",
        str(config.crf),
        "-preset",
        config.preset,
        "-pix_fmt",
        "yuv420p",
    ]


def _concat_escape(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "'\\''")
