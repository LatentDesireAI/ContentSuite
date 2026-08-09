"""Session trash for Art Checker — files moved here, folder cleared on app start."""

from __future__ import annotations

import shutil
from pathlib import Path

from core.app_log import get_logger
from core.config_store import app_data_dir

_TRASH_DIR_NAME = "tmp"


def trash_dir() -> Path:
    return app_data_dir() / _TRASH_DIR_NAME


def reset_trash_on_startup() -> int:
    """Delete all files in the session trash folder. Returns removed file count."""
    root = trash_dir()
    if not root.is_dir():
        root.mkdir(parents=True, exist_ok=True)
        return 0

    removed = 0
    for path in root.rglob("*"):
        if path.is_file():
            try:
                path.unlink()
                removed += 1
            except OSError as exc:
                get_logger().warning("Could not remove trash file %s: %s", path, exc)
    for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir():
            try:
                path.rmdir()
            except OSError:
                pass
    root.mkdir(parents=True, exist_ok=True)
    if removed:
        get_logger().info("Art checker trash cleared: %d file(s)", removed)
    return removed


def _unique_destination(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    for index in range(1, 10_000):
        candidate = directory / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
    raise OSError(f"Could not allocate trash name for {filename}")


def move_to_trash(source: Path) -> Path:
    """Move a file into the session trash folder."""
    if not source.is_file():
        raise FileNotFoundError(str(source))

    destination_root = trash_dir()
    destination_root.mkdir(parents=True, exist_ok=True)
    destination = _unique_destination(destination_root, source.name)

    try:
        shutil.move(str(source), str(destination))
    except OSError:
        shutil.copy2(source, destination)
        source.unlink()
    return destination