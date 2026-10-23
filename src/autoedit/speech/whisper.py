from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..core.manifest import seconds_to_us
from ..runtime import app_data_root, report_progress, resource_path
from .aligned import TimedWord

ProgressCallback = Callable[[float, str], None]

try:
    import faster_whisper as _faster_whisper
except ImportError:
    _faster_whisper = None


class TranscriptionError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class WhisperConfig:
    model: str = "small"
    language: str | None = None


LANGUAGE_ALIASES = {
    "id": "id",
    "indonesia": "id",
    "indonesian": "id",
    "en": "en",
    "english": "en",
    "inggris": "en",
    "ja": "ja",
    "japanese": "ja",
    "jp": "ja",
    "jepang": "ja",
    "ko": "ko",
    "korean": "ko",
    "kr": "ko",
    "korea": "ko",
    "zh": "zh",
    "chinese": "zh",
    "cn": "zh",
    "mandarin": "zh",
}


def whisper_available() -> bool:
    return _faster_whisper is not None


def transcribe(
    audio_path: str | Path,
    *,
    transcript_hint: str,
    config: WhisperConfig | None = None,
    progress_callback: ProgressCallback | None = None,
) -> list[TimedWord]:
    if _faster_whisper is None:
        raise TranscriptionError(
            "faster-whisper belum terpasang; jalankan: pip install faster-whisper"
        )

    cfg = config or WhisperConfig()
    source = Path(audio_path).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"file audio tidak ditemukan: {source}")

    cache_dir = _model_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    bundled = _bundled_model_dir(cfg.model)
    if bundled is None and getattr(sys, "_MEIPASS", None):
        raise TranscriptionError(
            "Model Whisper tidak ditemukan di dalam paket aplikasi."
        )
    model_source = str(bundled) if bundled is not None else cfg.model

    report_progress(progress_callback, 0.02, "Memuat model Whisper…")
    try:
        model = _faster_whisper.WhisperModel(
            model_source,
            device="cpu",
            compute_type="int8",
            cpu_threads=max(1, min(4, os.cpu_count() or 1)),
            num_workers=1,
            download_root=str(cache_dir),
            local_files_only=bundled is not None,
        )
    except (OSError, RuntimeError, ValueError, MemoryError) as error:
        raise TranscriptionError(
            "Model Whisper tidak bisa dimuat. Periksa koneksi internet pada pemakaian "
            "pertama, RAM kosong minimal 1 GB, dan hak akses folder data."
        ) from error

    prompt = re.sub(r"\s+", " ", transcript_hint).strip()[:2000] or None
    report_progress(progress_callback, 0.05, "Mengambil timestamp dari audio…")
    try:
        segments, info = model.transcribe(
            str(source),
            language=_normalize_language(cfg.language) if cfg.language else None,
            word_timestamps=True,
            initial_prompt=prompt,
            vad_filter=False,
        )
        audio_seconds = float(getattr(info, "duration", 0.0) or 0.0)
        if audio_seconds <= 0:
            audio_seconds = 600.0
        words: list[TimedWord] = []
        for segment in segments:
            segment_words = getattr(segment, "words", None) or []
            if segment_words:
                for word in segment_words:
                    start_us = seconds_to_us(float(word.start))
                    end_us = seconds_to_us(float(word.end))
                    if str(word.word).strip() and end_us > start_us:
                        words.append(TimedWord(str(word.word).strip(), start_us, end_us))
            elif str(segment.text).strip():
                start_us = seconds_to_us(float(segment.start))
                end_us = seconds_to_us(float(segment.end))
                if end_us > start_us:
                    words.append(TimedWord(str(segment.text).strip(), start_us, end_us))
            ratio = min(1.0, float(getattr(segment, "end", 0.0)) / audio_seconds)
            report_progress(
                progress_callback,
                0.06 + 0.88 * ratio,
                f"Whisper sedang membaca audio… {int(ratio * 100)}%",
            )
    except TranscriptionError:
        raise
    except Exception as error:
        raise TranscriptionError(f"Whisper gagal memproses audio: {error}") from error

    if not words:
        raise TranscriptionError("Whisper tidak mengenali satu kata pun pada audio")
    report_progress(progress_callback, 1.0, "Timestamp audio selesai")
    return sorted(words, key=lambda word: (word.start_us, word.end_us))


def _normalize_language(language: str) -> str:
    normalized = language.strip().lower().replace("_", "-")
    return LANGUAGE_ALIASES.get(normalized, normalized.split("-", 1)[0])


def _model_cache_dir() -> Path:
    return app_data_root() / "cache" / "whisper"


def _bundled_model_dir(model: str) -> Path | None:
    for relative in (f"assets/models/{model}", f"models/{model}"):
        candidate = resource_path(relative)
        if candidate.is_dir() and all(
            (candidate / filename).is_file()
            for filename in ("config.json", "model.bin", "tokenizer.json")
        ):
            return candidate
    return None
