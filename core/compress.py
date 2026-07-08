"""Image compression and metadata stripping."""

from __future__ import annotations

import hashlib
import os
import re
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from PIL import Image

from core.media_scan import collect_media_files
from core.metadata import AuthorMetadata, build_exif

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff"}

_TRAILING_INDEX_RE = re.compile(r"_\d+$")


@dataclass
class ImageProbe:
    path: Path
    width: int
    height: int
    size_bytes: int
    format: str

    @property
    def summary(self) -> str:
        return (
            f"{self.format}, {self.width}×{self.height}, "
            f"{self.size_bytes / 1024 / 1024:.1f} MB"
        )


def image_thumbnail_cache_dir() -> Path:
    from core.config_store import config_path

    cache = config_path().parent / "image_thumbs"
    cache.mkdir(parents=True, exist_ok=True)
    return cache


def image_thumbnail_cache_path(image_path: Path) -> Path:
    stat = image_path.stat()
    digest = hashlib.sha1(
        f"{image_path.resolve()}|{stat.st_mtime_ns}|{stat.st_size}".encode()
    ).hexdigest()[:16]
    return image_thumbnail_cache_dir() / f"{digest}.jpg"


def probe_image(path: Path) -> ImageProbe:
    with Image.open(path) as img:
        fmt = (img.format or path.suffix.lstrip(".")).upper()
        return ImageProbe(
            path=path,
            width=img.width,
            height=img.height,
            size_bytes=path.stat().st_size,
            format=fmt,
        )


def extract_image_thumbnail(
    image_path: Path,
    output_path: Path,
    *,
    max_width: int = 360,
) -> None:
    with Image.open(image_path) as img:
        img = img.convert("RGB")
        if img.width > max_width:
            ratio = max_width / img.width
            img = img.resize(
                (max_width, max(1, int(img.height * ratio))),
                Image.Resampling.LANCZOS,
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "JPEG", quality=85, optimize=True)


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / 1024 / 1024:.1f} MB"


@dataclass
class ImageProcessResult:
    index: int
    source_name: str
    output_name: str = ""
    success: bool = False
    original_size: int = 0
    new_size: int = 0
    original_res: str = ""
    new_res: str = ""
    resized: bool = False
    error: str | None = None


@dataclass
class PackSummary:
    total_files: int = 0
    processed: int = 0
    failed: int = 0
    original_bytes: int = 0
    output_bytes: int = 0
    results: list[ImageProcessResult] = field(default_factory=list)


def normalize_image_stem(stem: str) -> str:
    """Strip a trailing _NNN suffix; the source file may carry a wrong index."""
    normalized = _TRAILING_INDEX_RE.sub("", stem)
    return normalized or stem


def plan_output_names(
    image_files: list[Path],
    base_name: str,
    *,
    keep_original_name: bool = False,
) -> list[str]:
    if not keep_original_name:
        base = base_name.strip()
        return [f"{base}_{index:03d}.jpg" for index, _ in enumerate(image_files, start=1)]

    normalized = [normalize_image_stem(file_path.stem) for file_path in image_files]
    totals: dict[str, int] = defaultdict(int)
    for stem in normalized:
        totals[stem] += 1

    seen: dict[str, int] = defaultdict(int)
    names: list[str] = []
    for stem in normalized:
        if totals[stem] == 1:
            names.append(f"{stem}.jpg")
            continue
        seen[stem] += 1
        names.append(f"{stem}_{seen[stem]:03d}.jpg")
    return names


def collect_images(folder: Path) -> list[Path]:
    return collect_media_files(folder, IMAGE_EXTENSIONS)


def _resize_if_needed(img: Image.Image, max_res: int) -> tuple[Image.Image, bool]:
    if max(img.width, img.height) <= max_res:
        return img, False

    if img.width > img.height:
        new_width = max_res
        new_height = int(img.height * (max_res / img.width))
    else:
        new_height = max_res
        new_width = int(img.width * (max_res / img.height))

    return img.resize((new_width, new_height), Image.Resampling.LANCZOS), True


def process_single_image(
    file_path: Path,
    output_folder: Path,
    output_name: str,
    index: int,
    quality: int = 98,
    max_res: int = 2560,
    author_meta: AuthorMetadata | dict | None = None,
) -> ImageProcessResult:
    result = ImageProcessResult(
        index=index,
        source_name=file_path.name,
        original_size=os.path.getsize(file_path),
    )

    try:
        with Image.open(file_path) as img:
            result.original_res = f"{img.width}x{img.height}"
            img, result.resized = _resize_if_needed(img, max_res)
            result.new_res = f"{img.width}x{img.height}"

            output_path = output_folder / output_name

            # Fresh RGB JPEG — strips ComfyUI/A1111 chunks; optional author EXIF below.
            clean = img.convert("RGB")
            meta = AuthorMetadata.from_dict(
                author_meta if isinstance(author_meta, dict) else None
            )
            exif = build_exif(meta)
            save_kwargs = {
                "quality": quality,
                "optimize": True,
                "subsampling": 0,
            }
            if exif is not None:
                save_kwargs["exif"] = exif
            clean.save(output_path, "JPEG", **save_kwargs)

            result.output_name = output_name
            result.new_size = os.path.getsize(output_path)
            result.success = True
    except Exception as exc:
        result.error = str(exc)

    return result


def default_worker_count() -> int:
    return os.cpu_count() or 4


def _process_task(args: tuple) -> ImageProcessResult:
    file_path, output_folder, output_name, index, quality, max_res, author_meta = args
    return process_single_image(
        Path(file_path),
        Path(output_folder),
        output_name,
        index,
        quality=quality,
        max_res=max_res,
        author_meta=author_meta,
    )


def process_pack(
    input_folder: str | Path,
    output_folder: str | Path,
    base_name: str,
    quality: int = 98,
    max_res: int = 2560,
    workers: int | None = None,
    author_meta: AuthorMetadata | dict | None = None,
    sources: list[Path] | None = None,
    keep_original_name: bool = False,
    on_progress: Callable[[int, int, ImageProcessResult], None] | None = None,
) -> PackSummary:
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    if sources is not None:
        image_files = [p for p in sources if p.is_file()]
    else:
        image_files = collect_images(input_path)
    summary = PackSummary(total_files=len(image_files))

    if not image_files:
        return summary

    if not keep_original_name and not base_name.strip():
        raise ValueError("Specify pack name (base name).")

    worker_count = max(1, workers or default_worker_count())
    output_names = plan_output_names(
        image_files,
        base_name,
        keep_original_name=keep_original_name,
    )
    total = len(image_files)

    if isinstance(author_meta, AuthorMetadata):
        meta_dict = author_meta.to_dict()
    else:
        meta_dict = AuthorMetadata.from_dict(author_meta).to_dict()

    tasks = [
        (
            str(file_path),
            str(output_path),
            output_name,
            index,
            quality,
            max_res,
            meta_dict,
        )
        for index, (file_path, output_name) in enumerate(
            zip(image_files, output_names, strict=True),
            start=1,
        )
    ]

    with ProcessPoolExecutor(max_workers=worker_count) as executor:
        for done, result in enumerate(executor.map(_process_task, tasks), start=1):
            summary.results.append(result)

            if result.success:
                summary.processed += 1
                summary.original_bytes += result.original_size
                summary.output_bytes += result.new_size
            else:
                summary.failed += 1

            if on_progress:
                on_progress(done, total, result)

    return summary