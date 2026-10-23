from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .manifest import seconds_to_us

IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"})
VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".wmv"})
MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


class ProbeError(RuntimeError):
    """Dilempar ketika metadata media tidak bisa dibaca."""


@dataclass(frozen=True, slots=True)
class MediaInfo:
    duration_us: int
    width: int | None = None
    height: int | None = None
    codec: str | None = None
    has_audio: bool = False
    fps: float | None = None


def probe_media(path: str | Path) -> MediaInfo:
    source = Path(path)
    if not source.is_file():
        raise ProbeError(f"file media tidak ditemukan: {source}")
    suffix = source.suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return _probe_image(source)
    if suffix in VIDEO_EXTENSIONS:
        return _probe_motion(source)
    if suffix in AUDIO_EXTENSIONS:
        return _probe_audio(source)
    raise ProbeError(f"ekstensi media tidak didukung: {source.name}")


AUDIO_EXTENSIONS = frozenset({".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"})


def _probe_image(source: Path) -> MediaInfo:
    try:
        from PIL import Image

        with Image.open(source) as image:
            width, height = image.size
            image.verify()
    except Exception as error:
        raise ProbeError(f"gambar tidak bisa dibaca: {source.name}") from error
    if width <= 0 or height <= 0:
        raise ProbeError(f"ukuran gambar tidak valid: {source.name}")
    return MediaInfo(
        duration_us=0, width=width, height=height, codec=source.suffix.lower().lstrip(".")
    )


def _probe_audio(source: Path) -> MediaInfo:
    container = _open_container(source)
    with container:
        streams = list(container.streams.audio)
        if not streams:
            raise ProbeError(f"file audio tidak memiliki stream audio: {source.name}")
        duration_us = _container_duration_us(container, streams[0])
        codec = streams[0].codec_context.name
    return MediaInfo(duration_us=duration_us, codec=codec, has_audio=True)


def _probe_motion(source: Path) -> MediaInfo:
    container = _open_container(source)
    with container:
        video_streams = list(container.streams.video)
        audio_streams = list(container.streams.audio)
        if not video_streams:
            raise ProbeError(f"file video tidak memiliki stream gambar: {source.name}")
        stream = video_streams[0]
        duration_us = _container_duration_us(container, stream)
        fps = _stream_fps(stream)
        return MediaInfo(
            duration_us=duration_us,
            width=int(stream.codec_context.width),
            height=int(stream.codec_context.height),
            codec=stream.codec_context.name,
            has_audio=bool(audio_streams),
            fps=fps,
        )


def _open_container(source: Path):
    try:
        import av
    except ImportError as error:
        raise ProbeError(
            "paket PyAV belum terpasang; jalankan: pip install av"
        ) from error
    try:
        return av.open(str(source), mode="r")
    except Exception as error:
        raise ProbeError(f"media tidak bisa dibuka: {source.name}") from error


def _container_duration_us(container, stream) -> int:
    duration = container.duration
    if duration:
        return int(duration)
    if stream.duration and stream.time_base:
        return seconds_to_us(float(stream.duration * stream.time_base))
    raise ProbeError("durasi media tidak tersedia")


def _stream_fps(stream) -> float | None:
    rate = stream.average_rate or stream.guessed_rate
    if not rate:
        return None
    value = float(rate)
    return value if value > 0 else None
