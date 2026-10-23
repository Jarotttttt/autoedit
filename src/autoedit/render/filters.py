from __future__ import annotations

from ..core.manifest import MotionPreset, TimelineClip, TimelineProject

MOTION_INSET = "0.03"
MOTION_SPAN = "0.94"


def fill_filter(project: TimelineProject) -> str:
    width = project.canvas.width
    height = project.canvas.height
    return (
        f"scale={width}:{height}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={width}:{height},setsar=1"
    )


def image_filter(
    project: TimelineProject, clip: TimelineClip, frame_count: int
) -> str:
    base = fill_filter(project)
    motion = _motion(project, clip, frame_count)
    return f"{base},{motion},format=yuv420p"


def video_filter(
    project: TimelineProject, clip: TimelineClip, frame_count: int
) -> str:
    base = f"setpts=PTS/{clip.speed:.9f},{fill_filter(project)}"
    motion = _motion(project, clip, frame_count)
    return f"{base},{motion},format=yuv420p"


def _motion(project: TimelineProject, clip: TimelineClip, frame_count: int) -> str:
    fps = project.canvas.fps
    if clip.motion is MotionPreset.NONE:
        return f"fps={fps}"

    progress = f"min(1,in/{max(1, frame_count - 1)})"
    eased = f"({progress})*({progress})*(3-2*({progress}))"
    inset = MOTION_INSET
    span = MOTION_SPAN
    motions = {
        MotionPreset.ZOOM_IN: (
            f"W*{inset}*{eased}",
            f"H*{inset}*{eased}",
            f"W-W*{inset}*{eased}",
            f"H-H*{inset}*{eased}",
        ),
        MotionPreset.ZOOM_OUT: (
            f"W*{inset}*(1-{eased})",
            f"H*{inset}*(1-{eased})",
            f"W-W*{inset}*(1-{eased})",
            f"H-H*{inset}*(1-{eased})",
        ),
        MotionPreset.PAN_LEFT_RIGHT: (
            f"W*(1-{span})*{eased}",
            f"H*{inset}",
            f"W*(1-{span})*{eased}+W*{span}",
            f"H-H*{inset}",
        ),
        MotionPreset.PAN_RIGHT_LEFT: (
            f"W*(1-{span})*(1-{eased})",
            f"H*{inset}",
            f"W*(1-{span})*(1-{eased})+W*{span}",
            f"H-H*{inset}",
        ),
        MotionPreset.PAN_TOP_BOTTOM: (
            f"W*{inset}",
            f"H*(1-{span})*{eased}",
            f"W-W*{inset}",
            f"H*(1-{span})*{eased}+H*{span}",
        ),
        MotionPreset.PAN_BOTTOM_TOP: (
            f"W*{inset}",
            f"H*(1-{span})*(1-{eased})",
            f"W-W*{inset}",
            f"H*(1-{span})*(1-{eased})+H*{span}",
        ),
    }
    x0, y0, x1, y2 = motions[clip.motion]
    return (
        f"perspective=x0='{x0}':y0='{y0}':x1='{x1}':y1='{y0}'"
        f":x2='{x0}':y2='{y2}':x3='{x1}':y3='{y2}'"
        f":interpolation=cubic:sense=source:eval=frame,"
        f"fps={fps},settb=expr=1/{fps},setpts=N"
    )
