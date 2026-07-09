"""Video compression presets for re-encoding."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompressionPreset:
    id: str
    label: str
    x264_crf: int
    vp9_crf: int
    x264_preset: str
    hint: str


COMPRESSION_PRESETS: tuple[CompressionPreset, ...] = (
    CompressionPreset(
        "maximum",
        "Maximum",
        32,
        40,
        "faster",
        "Smallest file size, noticeable quality loss",
    ),
    CompressionPreset(
        "high",
        "High",
        28,
        34,
        "medium",
        "Strong compression, good for previews and web",
    ),
    CompressionPreset(
        "medium",
        "Medium",
        23,
        28,
        "medium",
        "Balance of size and quality",
    ),
    CompressionPreset(
        "near_lossless",
        "Near lossless",
        18,
        22,
        "slow",
        "High quality, moderate file size",
    ),
    CompressionPreset(
        "minimal",
        "Minimal",
        14,
        16,
        "slower",
        "Near lossless, largest file size",
    ),
)

DEFAULT_COMPRESSION_ID = "medium"

_MP4_COPY_SAFE_VIDEO_CODECS = frozenset({"h264", "mpeg4", "mpeg2video"})
_MP4_COPY_SAFE_PIX_FMT = frozenset({"yuv420p", "yuvj420p"})


def is_mp4_video_copy_safe(
    video_codec: str,
    *,
    pix_fmt: str = "",
    profile: str = "",
) -> bool:
    """Whether remuxing the video stream into MP4/MOV is safe for mobile players."""
    if video_codec.lower() not in _MP4_COPY_SAFE_VIDEO_CODECS:
        return False
    if pix_fmt and pix_fmt not in _MP4_COPY_SAFE_PIX_FMT:
        return False
    if profile and "10" in str(profile):
        return False
    return True


def get_compression_preset(level_id: str) -> CompressionPreset:
    for preset in COMPRESSION_PRESETS:
        if preset.id == level_id:
            return preset
    return COMPRESSION_PRESETS[2]


def ffmpeg_mobile_video_prep_args(output_format: str) -> list[str]:
    """Normalize pixel format, dimensions, and color tags for phone players."""
    fmt = output_format.lower().lstrip(".")
    if fmt not in ("mp4", "mov", "m4v"):
        return []
    return [
        "-vf",
        "format=yuv420p,scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-colorspace",
        "bt709",
        "-color_primaries",
        "bt709",
        "-color_trc",
        "bt709",
    ]


def ffmpeg_container_mux_args(output_format: str) -> list[str]:
    """Muxer flags for reliable playback on phones and browsers."""
    fmt = output_format.lower().lstrip(".")
    if fmt in ("mp4", "mov", "m4v"):
        return ["-movflags", "+faststart"]
    return []


def ffmpeg_audio_encode_args(output_format: str) -> list[str]:
    """Audio codec compatible with the target container."""
    fmt = output_format.lower().lstrip(".")
    if fmt == "webm":
        return ["-c:a", "libopus", "-b:a", "128k"]
    if fmt in ("mp4", "mov", "m4v"):
        return ["-c:a", "aac", "-b:a", "192k"]
    return ["-c:a", "copy"]


def ffmpeg_video_encode_args(output_format: str, level_id: str) -> list[str]:
    preset = get_compression_preset(level_id)
    fmt = output_format.lower().lstrip(".")
    if fmt == "webm":
        return [
            "-c:v",
            "libvpx-vp9",
            "-crf",
            str(preset.vp9_crf),
            "-b:v",
            "0",
        ]
    args = [
        "-c:v",
        "libx264",
        "-crf",
        str(preset.x264_crf),
        "-preset",
        preset.x264_preset,
    ]
    if fmt in ("mp4", "mov", "m4v"):
        args.extend([
            "-pix_fmt",
            "yuv420p",
            "-profile:v",
            "high",
            "-level:v",
            "4.1",
            "-tag:v",
            "avc1",
        ])
    return args