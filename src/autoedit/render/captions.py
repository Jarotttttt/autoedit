from __future__ import annotations

from pathlib import Path

from ..core.manifest import TimelineProject

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{font_size},&H00FFFFFF,&H00FFFFFF,&H00101010,&H80101010,-1,0,0,0,100,100,0,0,1,3,1,2,{margin_l},{margin_r},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def build_ass(project: TimelineProject) -> str:
    font_size = max(24, round(project.canvas.height * 42 / 1080))
    margin_v = max(24, round(project.canvas.height * 70 / 1080))
    header = ASS_HEADER.format(
        width=project.canvas.width,
        height=project.canvas.height,
        font=font_name(),
        font_size=font_size,
        margin_l=60,
        margin_r=60,
        margin_v=margin_v,
    )
    events = [
        f"Dialogue: 0,{ass_timestamp(caption.start_us)},{ass_timestamp(caption.end_us)},"
        f"Default,,0,0,0,,{escape_text(caption.text)}"
        for caption in project.captions
    ]
    return "\n".join([header.strip(), *events, ""])


def font_name() -> str:
    return "Arial"


def write_ass(project: TimelineProject, destination: Path) -> Path:
    destination.write_text(build_ass(project), encoding="utf-8")
    return destination


def ass_timestamp(value_us: int) -> str:
    centiseconds = max(0, round(value_us / 10_000))
    hours, remainder = divmod(centiseconds, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    seconds, centis = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centis:02d}"


def escape_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("\r\n", "\\N")
        .replace("\n", "\\N")
    )


def escape_filter_path(path: Path) -> str:
    return (
        path.resolve()
        .as_posix()
        .replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
    )
