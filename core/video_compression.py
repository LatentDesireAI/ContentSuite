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
        "Максимальное",
        32,
        40,
        "faster",
        "Минимальный размер файла, заметная потеря качества",
    ),
    CompressionPreset(
        "high",
        "Высокое",
        28,
        34,
        "medium",
        "Сильное сжатие, подходит для превью и веба",
    ),
    CompressionPreset(
        "medium",
        "Среднее",
        23,
        28,
        "medium",
        "Баланс размера и качества",
    ),
    CompressionPreset(
        "near_lossless",
        "Почти без потерь",
        18,
        22,
        "slow",
        "Высокое качество, умеренный размер",
    ),
    CompressionPreset(
        "minimal",
        "Минимальное",
        14,
        16,
        "slower",
        "Почти без потерь, максимальный размер",
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