from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from ..runtime import app_data_root


@dataclass(slots=True)
class Settings:
    audio_path: str = ""
    media_dir: str = ""
    transcript_path: str = ""
    output_dir: str = ""
    project_name: str = "Video Baru"
    source: str = "auto"
    canvas_width: int = 1920
    canvas_height: int = 1080
    fps: int = 30
    shot_seconds: str = "6"
    language: str = "auto"
    model: str = "small"
    motion: bool = True
    captions: bool = True


def settings_file() -> Path:
    return app_data_root() / "settings.json"


def load() -> Settings:
    path = settings_file()
    settings = Settings()
    if not path.is_file():
        return settings
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return settings
    known = {item.name for item in fields(Settings)}
    for key, value in payload.items():
        if key in known and value is not None:
            setattr(settings, key, value)
    return settings


def save(settings: Settings) -> None:
    path = settings_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(settings)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
