"""Thumbnail cache maintenance for image and video previews."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

MAX_CACHE_AGE_DAYS = 30
MAX_CACHE_FILES = 1500
MAX_CACHE_BYTES = 150 * 1024 * 1024


@dataclass
class PruneResult:
    directory: Path
    deleted_files: int = 0
    freed_bytes: int = 0


@dataclass
class PruneSummary:
    results: list[PruneResult]

    @property
    def deleted_files(self) -> int:
        return sum(r.deleted_files for r in self.results)

    @property
    def freed_bytes(self) -> int:
        return sum(r.freed_bytes for r in self.results)


def thumbnail_cache_dirs() -> list[Path]:
    from core.compress import image_thumbnail_cache_dir
    from core.ffmpeg_wrapper import thumbnail_cache_dir

    return [thumbnail_cache_dir(), image_thumbnail_cache_dir()]


def _cache_entries(cache_dir: Path) -> list[tuple[Path, float, int]]:
    if not cache_dir.is_dir():
        return []
    entries: list[tuple[Path, float, int]] = []
    for path in cache_dir.iterdir():
        if not path.is_file():
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        entries.append((path, stat.st_mtime, stat.st_size))
    return entries


def prune_cache_dir(
    cache_dir: Path,
    *,
    max_age_days: int = MAX_CACHE_AGE_DAYS,
    max_files: int = MAX_CACHE_FILES,
    max_bytes: int = MAX_CACHE_BYTES,
) -> PruneResult:
    result = PruneResult(directory=cache_dir)
    now = time.time()
    max_age_sec = max(1, max_age_days) * 86400

    entries = _cache_entries(cache_dir)
    if not entries:
        return result

    survivors: list[tuple[Path, float, int]] = []
    for path, mtime, size in entries:
        if now - mtime > max_age_sec:
            try:
                path.unlink()
                result.deleted_files += 1
                result.freed_bytes += size
            except OSError:
                survivors.append((path, mtime, size))
        else:
            survivors.append((path, mtime, size))

    survivors.sort(key=lambda item: item[1])
    total_size = sum(size for _, _, size in survivors)
    while survivors and (
        len(survivors) > max_files or total_size > max_bytes
    ):
        path, _, size = survivors.pop(0)
        try:
            path.unlink()
            result.deleted_files += 1
            result.freed_bytes += size
            total_size -= size
        except OSError:
            pass

    return result


def prune_all_thumbnail_caches(
    *,
    max_age_days: int = MAX_CACHE_AGE_DAYS,
    max_files: int = MAX_CACHE_FILES,
    max_bytes: int = MAX_CACHE_BYTES,
) -> PruneSummary:
    results = [
        prune_cache_dir(
            cache_dir,
            max_age_days=max_age_days,
            max_files=max_files,
            max_bytes=max_bytes,
        )
        for cache_dir in thumbnail_cache_dirs()
    ]
    return PruneSummary(results=results)