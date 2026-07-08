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


def get_compression_preset(level_id: str) -> CompressionPreset:
    for preset in COMPRESSION_PRESETS:
        if preset.id == level_id:
            return preset
    return COMPRESSION_PRESETS[2]


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
    return [
        "-c:v",
        "libx264",
        "-crf",
        str(preset.x264_crf),
        "-preset",
        preset.x264_preset,
    ]