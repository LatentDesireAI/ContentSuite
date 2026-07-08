"""Pixiv-style mosaic censorship for video and images."""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw

from core.compress import IMAGE_EXTENSIONS, collect_images
from core.config_store import config_path
from core.ffmpeg_wrapper import (
    FfmpegError,
    VIDEO_EXTENSIONS,
    collect_videos,
    probe_video,
    run_ffmpeg,
)
from core.metadata import (
    AuthorMetadata,
    build_exif,
    build_ffmpeg_metadata_flags,
    should_strip_media_metadata,
)
from core.video_compression import DEFAULT_COMPRESSION_ID, ffmpeg_video_encode_args


@dataclass
class CensorZone:
    x: int
    y: int
    width: int
    height: int
    block_size: int = 16
    polygon: list[list[int]] = field(default_factory=list)

    @property
    def is_lasso(self) -> bool:
        return len(self.polygon) >= 3

    def clamp(self, media_w: int, media_h: int) -> CensorZone:
        if self.is_lasso:
            pts = [
                [
                    max(0, min(int(p[0]), media_w - 1)),
                    max(0, min(int(p[1]), media_h - 1)),
                ]
                for p in self.polygon
                if isinstance(p, (list, tuple)) and len(p) >= 2
            ]
            if len(pts) < 3:
                return CensorZone(0, 0, 8, 8, max(4, min(64, self.block_size)))
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            left, right = min(xs), max(xs)
            top, bottom = min(ys), max(ys)
            w = max(8, right - left + 1)
            h = max(8, bottom - top + 1)
            block = max(4, min(64, self.block_size))
            return CensorZone(left, top, w, h, block, pts)

        x = max(0, min(self.x, media_w - 1))
        y = max(0, min(self.y, media_h - 1))
        w = max(8, min(self.width, media_w - x))
        h = max(8, min(self.height, media_h - y))
        block = max(4, min(64, self.block_size))
        return CensorZone(x, y, w, h, block)

    def to_dict(self) -> dict:
        data = asdict(self)
        if not self.is_lasso:
            data.pop("polygon", None)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> CensorZone:
        raw_poly = data.get("polygon")
        polygon: list[list[int]] = []
        if isinstance(raw_poly, list):
            for point in raw_poly:
                if isinstance(point, (list, tuple)) and len(point) >= 2:
                    polygon.append([int(point[0]), int(point[1])])
        return cls(
            x=int(data.get("x", 0)),
            y=int(data.get("y", 0)),
            width=int(data.get("width", 32)),
            height=int(data.get("height", 32)),
            block_size=int(data.get("block_size", 16)),
            polygon=polygon,
        )


def is_video_path(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS


def is_image_path(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS


def collect_censor_media(folder: Path) -> list[Path]:
    """Videos first, then images — both from the input folder."""
    return collect_videos(folder) + collect_images(folder)


def censor_store_path() -> Path:
    return config_path().parent / "censor_zones.json"


def media_preset_key(media_path: Path) -> str:
    stat = media_path.stat()
    digest = hashlib.sha1(
        f"{media_path.resolve()}|{stat.st_mtime_ns}|{stat.st_size}".encode()
    ).hexdigest()[:16]
    return digest


video_preset_key = media_preset_key


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

    def get_zones(self, media_path: Path) -> list[CensorZone]:
        key = media_preset_key(media_path)
        entry = self._data.get("videos", {}).get(key, {})
        raw = entry.get("zones", [])
        if not isinstance(raw, list):
            return []
        return [CensorZone.from_dict(z) for z in raw if isinstance(z, dict)]

    def set_zones(self, media_path: Path, zones: list[CensorZone]) -> None:
        key = media_preset_key(media_path)
        self._data.setdefault("videos", {})[key] = {
            "path": str(media_path.resolve()),
            "zones": [z.to_dict() for z in zones],
        }
        self.save()

    def has_zones(self, media_path: Path) -> bool:
        return bool(self.get_zones(media_path))

    def clear_zones(self, media_path: Path) -> None:
        key = media_preset_key(media_path)
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
        f"contentsuite_censor_{media_preset_key(video_path)}.jpg",
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


def write_zone_mask(zone: CensorZone, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mask = Image.new("L", (zone.width, zone.height), 0)
    if zone.is_lasso:
        local = [(p[0] - zone.x, p[1] - zone.y) for p in zone.polygon]
        ImageDraw.Draw(mask).polygon(local, fill=255)
    else:
        ImageDraw.Draw(mask).rectangle((0, 0, zone.width - 1, zone.height - 1), fill=255)
    mask.save(output_path)


def _pixelate_region(region: Image.Image, block_size: int) -> Image.Image:
    block = max(4, block_size)
    w, h = region.size
    sw = max(1, w // block)
    sh = max(1, h // block)
    small = region.resize((sw, sh), Image.Resampling.NEAREST)
    return small.resize((w, h), Image.Resampling.NEAREST)


def _apply_zone_to_image(img: Image.Image, zone: CensorZone) -> None:
    crop = img.crop((zone.x, zone.y, zone.x + zone.width, zone.y + zone.height))
    pixelated = _pixelate_region(crop, zone.block_size)
    if zone.is_lasso:
        mask = Image.new("L", (zone.width, zone.height), 0)
        local = [(p[0] - zone.x, p[1] - zone.y) for p in zone.polygon]
        ImageDraw.Draw(mask).polygon(local, fill=255)
        img.paste(pixelated, (zone.x, zone.y), mask)
    else:
        img.paste(pixelated, (zone.x, zone.y))


def build_censor_filter_complex(
    zones: list[CensorZone],
    *,
    mask_count: int,
) -> tuple[str, str]:
    if not zones:
        return "", "[0:v]"
    if mask_count != len(zones):
        raise FfmpegError("Число масок не совпадает с числом зон цензуры.")

    parts: list[str] = []
    current = "0:v"
    last = len(zones) - 1
    for i, zone in enumerate(zones):
        block = max(4, zone.block_size)
        sw = max(1, zone.width // block)
        sh = max(1, zone.height // block)
        mask_idx = 1 + i
        out_label = "out" if i == last else f"v{i}"
        parts.append(
            f"[{current}]split[b{i}][s{i}];"
            f"[s{i}]crop={zone.width}:{zone.height}:{zone.x}:{zone.y},"
            f"scale={sw}:{sh}:flags=neighbor,"
            f"scale={zone.width}:{zone.height}:flags=neighbor[pix{i}];"
            f"[{mask_idx}:v]format=gray,scale={zone.width}:{zone.height}[msk{i}];"
            f"[pix{i}][msk{i}]alphamerge[zm{i}];"
            f"[b{i}][zm{i}]overlay={zone.x}:{zone.y}[{out_label}]"
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
    clamped = [z.clamp(probe.width, probe.height) for z in zones]
    fmt = output_format.lower().lstrip(".")

    with tempfile.TemporaryDirectory(prefix="contentsuite_censor_") as tmp:
        tmp_path = Path(tmp)
        mask_paths: list[Path] = []
        for i, zone in enumerate(clamped):
            mask_path = tmp_path / f"mask_{i}.png"
            write_zone_mask(zone, mask_path)
            mask_paths.append(mask_path)

        args = ["-i", str(input_path)]
        for mask_path in mask_paths:
            args.extend(["-i", str(mask_path)])

        filt, out_label = build_censor_filter_complex(
            clamped, mask_count=len(mask_paths)
        )
        args.extend(["-filter_complex", filt, "-map", out_label])
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


def apply_image_censor(
    input_path: Path,
    output_path: Path,
    zones: list[CensorZone],
    *,
    jpeg_quality: int = 95,
    remove_metadata: bool = True,
    author_meta: dict | None = None,
) -> None:
    if not zones:
        raise FfmpegError("Нет зон цензуры — откройте редактор и отметьте области.")

    with Image.open(input_path) as src:
        img = src.convert("RGB")
        media_w, media_h = img.size
        clamped = [z.clamp(media_w, media_h) for z in zones]
        for zone in clamped:
            _apply_zone_to_image(img, zone)

        save_kwargs: dict = {"format": "JPEG", "quality": jpeg_quality, "optimize": True}
        if not should_strip_media_metadata(remove_metadata, author_meta):
            meta = AuthorMetadata.from_dict(author_meta) if author_meta else AuthorMetadata()
            exif = build_exif(meta)
            if exif is not None:
                save_kwargs["exif"] = exif

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, **save_kwargs)