"""Multi-page PDF export via Pillow (no external PDF tools)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PIL import Image

from core.compress import collect_images
from core.metadata import AuthorMetadata, build_pdf_save_kwargs


@dataclass
class PdfExportResult:
    output_path: Path
    page_count: int = 0
    file_size: int = 0
    source_folder: str = ""


def _load_rgb_page(path: Path) -> Image.Image:
    with Image.open(path) as img:
        if img.mode in ("RGBA", "LA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            return background
        if img.mode == "P":
            converted = img.convert("RGBA")
            background = Image.new("RGB", converted.size, (255, 255, 255))
            background.paste(converted, mask=converted.split()[-1])
            return background
        if img.mode != "RGB":
            return img.convert("RGB")
        return img.copy()


def export_folder_to_pdf(
    source_folder: str | Path,
    output_path: str | Path,
    title: str,
    dpi: float = 150.0,
    author_meta: AuthorMetadata | dict | None = None,
    on_progress: Callable[[int, int, str], None] | None = None,
) -> PdfExportResult:
    source_path = Path(source_folder)
    output_file = Path(output_path)
    image_files = collect_images(source_path)

    if not image_files:
        raise ValueError("No images in the selected folder.")

    if not title.strip():
        raise ValueError("Specify pack name for PDF.")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    pages: list[Image.Image] = []
    total = len(image_files)

    try:
        for index, file_path in enumerate(image_files, start=1):
            pages.append(_load_rgb_page(file_path))
            if on_progress:
                on_progress(index, total, file_path.name)

        save_kwargs = build_pdf_save_kwargs(title.strip(), author_meta, dpi)
        first, *rest = pages
        first.save(
            output_file,
            "PDF",
            save_all=True,
            append_images=rest,
            **save_kwargs,
        )
    finally:
        for page in pages:
            page.close()

    return PdfExportResult(
        output_path=output_file,
        page_count=total,
        file_size=os.path.getsize(output_file),
        source_folder=str(source_path),
    )