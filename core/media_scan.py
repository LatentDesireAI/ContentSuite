"""Recursive media file discovery under an input folder."""

from __future__ import annotations

from pathlib import Path

_SKIP_DIR_NAMES = frozenset({
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
})


def _skip_path(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    for part in rel.parts[:-1]:
        if part in _SKIP_DIR_NAMES or part.startswith("."):
            return True
    return False


def collect_media_files(
    folder: Path,
    extensions: set[str],
    *,
    recursive: bool = True,
) -> list[Path]:
    if not folder.is_dir():
        return []

    root = folder.resolve()
    normalized = {ext.lower() for ext in extensions}
    files: list[Path] = []

    if recursive:
        candidates = root.rglob("*")
    else:
        candidates = root.iterdir()

    for path in candidates:
        if not path.is_file() or path.suffix.lower() not in normalized:
            continue
        if recursive and _skip_path(path, root):
            continue
        files.append(path)

    return sorted(files, key=lambda p: str(p.relative_to(root)).lower())


def media_file_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime if path.is_file() else 0.0
    except OSError:
        return 0.0


def sort_media_paths(paths: list[Path], mode: str) -> list[Path]:
    if mode == "date":
        return sorted(
            paths,
            key=lambda path: (-media_file_mtime(path), path.name.lower()),
        )
    return sorted(paths, key=lambda path: path.name.lower())