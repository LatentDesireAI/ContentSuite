"""Pixiv-style mosaic censorship for video."""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from core.config_store import config_path
from core.ffmpeg_wrapper import FfmpegError, probe_video, run_ffmpeg
from core.metadata import build_ffmpeg_metadata_flags, should_strip_media_metadata
from core.video_compression import DEFAULT_COMPRESSION_ID, ffmpeg_video_encode_args


@dataclass
class CensorZone:
    x: int
    y: int
    width: int
    height: int
    block_size: int = 16

    def clamp(self, video_w: int, video_h: int) -> CensorZone:
        x = max(0, min(self.x, video_w - 1))
        y = max(0, min(self.y, video_h - 1))
        w = max(8, min(self.width, video_w - x))
        h = max(8, min(self.height, video_h - y))
        block = max(4, min(64, self.block_size))
        return CensorZone(x, y, w, h, block)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> CensorZone:
        return cls(
            x=int(data.get("x", 0)),
            y=int(data.get("y", 0)),
            width=int(data.get("width", 32)),
            height=int(data.get("height", 32)),
            block_size=int(data.get("block_size", 16)),
        )


def censor_store_path() -> Path:
    return config_path().parent / "censor_zones.json"


def video_preset_key(video_path: Path) -> str:
    stat = video_path.stat()
    digest = hashlib.sha1(
        f"{video_path.resolve()}|{stat.st_mtime_ns}|{stat.st_size}".encode()
    ).hexdigest()[:16]
    return digest


class CensorStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or censor_store_path()
        self._data: dict = {"videos": {}}
        self.load()

    def load(self) -> None:
        if not self._path.is_file():
            return
        try:
            with self._path.open(encoding="utf-8") as f:
                stored = json.load(f)
            if isinstance(stored, dict) and isinstance(stored.get("videos"), dict):
                self._data = stored
        except (json.JSONDecodeError, OSError):
            pass

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def get_zones(self, video_path: Path) -> list[CensorZone]:
        key = video_preset_key(video_path)
        entry = self._data.get("videos", {}).get(key, {})
        raw = entry.get("zones", [])
        if not isinstance(raw, list):
            return []
        return [CensorZone.from_dict(z) for z in raw if isinstance(z, dict)]

    def set_zones(self, video_path: Path, zones: list[CensorZone]) -> None:
        key = video_preset_key(video_path)
        self._data.setdefault("videos", {})[key] = {
            "path": str(video_path.resolve()),
            "zones": [z.to_dict() for z in zones],
        }
        self.save()

    def has_zones(self, video_path: Path) -> bool:
        return bool(self.get_zones(video_path))

    def clear_zones(self, video_path: Path) -> None:
        key = video_preset_key(video_path)
        videos = self._data.get("videos", {})
        if key in videos:
            del videos[key]
            self.save()


def extract_preview_frame(
    video_path: Path,
    time_sec: float,
    output_path: Path | None = None,
) -> Path:
    probe = probe_video(video_path)
    t = max(0.0, time_sec)
    if probe.duration > 0:
        t = min(t, max(0.0, probe.duration - 0.05))
    out = output_path or Path(
        tempfile.gettempdir(),
        f"contentsuite_censor_{video_preset_key(video_path)}.jpg",
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg([
        "-ss", str(t),
        "-i", str(video_path),
        "-vframes", "1",
        "-q:v", "2",
        str(out),
    ])
    return out


def build_censor_filter_complex(zones: list[CensorZone]) -> tuple[str, str]:
    if not zones:
        return "", "[0:v]"

    parts: list[str] = []
    current = "0:v"
    last = len(zones) - 1
    for i, zone in enumerate(zones):
        block = max(4, zone.block_size)
        sw = max(1, zone.width // block)
        sh = max(1, zone.height // block)
        out_label = "out" if i == last else f"v{i}"
        parts.append(
            f"[{current}]split[b{i}][s{i}];"
            f"[s{i}]crop={zone.width}:{zone.height}:{zone.x}:{zone.y},"
            f"scale={sw}:{sh}:flags=neighbor,"
            f"scale={zone.width}:{zone.height}:flags=neighbor[z{i}];"
            f"[b{i}][z{i}]overlay={zone.x}:{zone.y}[{out_label}]"
        )
        current = out_label
    return ";".join(parts), "[out]"


def apply_video_censor(
    input_path: Path,
    output_path: Path,
    zones: list[CensorZone],
    *,
    output_format: str = "mp4",
    compression_level: str = DEFAULT_COMPRESSION_ID,
    remove_metadata: bool = True,
    author_meta: dict | None = None,
    title: str = "",
) -> None:
    if not zones:
        raise FfmpegError("Нет зон цензуры — откройте редактор и отметьте области.")

    probe = probe_video(input_path)
    clamped = [
        z.clamp(probe.width, probe.height) for z in zones
    ]
    filt, out_label = build_censor_filter_complex(clamped)
    fmt = output_format.lower().lstrip(".")

    args = ["-i", str(input_path), "-filter_complex", filt, "-map", out_label]
    args.extend(ffmpeg_video_encode_args(fmt, compression_level))

    if probe.has_audio and fmt in ("mp4", "mov"):
        args.extend(["-map", "0:a?", "-c:a", "aac", "-b:a", "192k"])
    elif probe.has_audio:
        args.extend(["-map", "0:a?", "-c:a", "copy"])
    else:
        args.append("-an")

    if should_strip_media_metadata(remove_metadata, author_meta):
        args.extend(["-map_metadata", "-1", "-fflags", "+bitexact"])
    args.extend(
        build_ffmpeg_metadata_flags(author_meta, title=title or input_path.stem)
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    args.append(str(output_path))
    run_ffmpeg(args)