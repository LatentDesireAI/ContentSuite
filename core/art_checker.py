"""Compare prompt-book JSON entries vs rendered image files on disk."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from core.compress import IMAGE_EXTENSIONS

_STRIP_INDEX_SUFFIX = re.compile(r"_\d+$")


@dataclass
class ArtRow:
    index: int
    name: str
    section: str
    status: str  # "present" | "missing"
    expected_path: str
    files: list[str] = field(default_factory=list)


@dataclass
class ArtScanResult:
    json_path: Path
    scan_root: Path
    total_in_json: int
    total_files_unique: int
    present_count: int
    missing_count: int
    extra_files_not_in_json: list[str]
    all_arts: list[ArtRow] = field(default_factory=list)

    @property
    def missing(self) -> list[ArtRow]:
        return [row for row in self.all_arts if row.status == "missing"]

    @property
    def present(self) -> list[ArtRow]:
        return [row for row in self.all_arts if row.status == "present"]


def art_file_mtime(row: ArtRow, scan_root: Path) -> float:
    """Latest modification time among files mapped to this art."""
    if not row.files or not scan_root.is_dir():
        return 0.0
    latest = 0.0
    for rel in row.files:
        path = scan_root / rel
        if path.is_file():
            latest = max(latest, path.stat().st_mtime)
    return latest


def sort_art_rows(rows: list[ArtRow], mode: str, scan_root: Path) -> list[ArtRow]:
    if mode == "missing_first":
        return sorted(
            rows,
            key=lambda row: (0 if row.status == "missing" else 1, row.name.lower()),
        )
    if mode == "date":
        return sorted(
            rows,
            key=lambda row: (-art_file_mtime(row, scan_root), row.name.lower()),
        )
    return sorted(rows, key=lambda row: row.name.lower())


def strip_index_suffix(stem: str) -> str:
    return _STRIP_INDEX_SUFFIX.sub("", stem)


def scan_arts(json_path: Path, scan_root: Path) -> ArtScanResult:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    arts = data.get("arts") or data.get("characters") or data.get("prompts") or []
    if not arts:
        raise ValueError(f"No arts in {json_path.name}")

    existing: dict[str, list[str]] = {}
    if scan_root.is_dir():
        for path in scan_root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            base = strip_index_suffix(path.stem)
            existing.setdefault(base, []).append(str(path.relative_to(scan_root)))

    json_names = {str(art.get("name", "")) for art in arts if art.get("name")}
    all_arts: list[ArtRow] = []
    present_count = 0
    missing_count = 0

    for index, art in enumerate(arts, start=1):
        name = str(art.get("name", ""))
        section = str(art.get("section", ""))
        status = "present" if name in existing else "missing"
        row = ArtRow(
            index=index,
            name=name,
            section=section,
            status=status,
            expected_path=f"{section}/{name}.png" if section else f"{name}.png",
            files=sorted(existing.get(name, [])),
        )
        all_arts.append(row)
        if status == "present":
            present_count += 1
        else:
            missing_count += 1

    return ArtScanResult(
        json_path=json_path,
        scan_root=scan_root,
        total_in_json=len(arts),
        total_files_unique=len(existing),
        present_count=present_count,
        missing_count=missing_count,
        extra_files_not_in_json=sorted(k for k in existing if k not in json_names),
        all_arts=all_arts,
    )