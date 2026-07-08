"""Author metadata for JPEG, PDF, and video exports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

# Standard EXIF tag IDs
_EXIF_ARTIST = 315
_EXIF_COPYRIGHT = 33432
_EXIF_DESCRIPTION = 270
_EXIF_SOFTWARE = 305


@dataclass
class AuthorMetadata:
    enabled: bool = False
    author: str = ""
    website: str = ""
    copyright: str = ""
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict | None) -> AuthorMetadata:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", False)),
            author=str(data.get("author", "")).strip(),
            website=str(data.get("website", "")).strip(),
            copyright=str(data.get("copyright", "")).strip(),
            description=str(data.get("description", "")).strip(),
        )

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "author": self.author,
            "website": self.website,
            "copyright": self.copyright,
            "description": self.description,
        }

    def has_content(self) -> bool:
        return any([self.author, self.website, self.copyright, self.description])

    def build_copyright_line(self) -> str:
        if self.copyright:
            return self.copyright
        parts = []
        if self.author:
            parts.append(f"© {self.author}")
        if self.website:
            parts.append(self.website)
        return " — ".join(parts)


def build_exif(metadata: AuthorMetadata) -> Image.Exif | None:
    if not metadata.enabled or not metadata.has_content():
        return None

    exif = Image.Exif()

    if metadata.author:
        exif[_EXIF_ARTIST] = metadata.author

    copyright_line = metadata.build_copyright_line()
    if copyright_line:
        exif[_EXIF_COPYRIGHT] = copyright_line

    if metadata.description:
        exif[_EXIF_DESCRIPTION] = metadata.description
    elif metadata.website:
        exif[_EXIF_DESCRIPTION] = metadata.website

    exif[_EXIF_SOFTWARE] = "ContentSuite"
    return exif


def build_pdf_save_kwargs(
    title: str,
    metadata: AuthorMetadata | dict | None,
    dpi: float,
) -> dict:
    """PDF Info fields available via Pillow: title, author, subject, keywords, producer."""
    meta = (
        metadata
        if isinstance(metadata, AuthorMetadata)
        else AuthorMetadata.from_dict(metadata)
    )
    kwargs: dict = {
        "resolution": dpi,
        "creator": "ContentSuite",
        "title": title,
    }
    if not meta.enabled:
        return kwargs

    if meta.author:
        kwargs["author"] = meta.author
    if meta.description:
        kwargs["subject"] = meta.description

    copyright_line = meta.build_copyright_line()
    if copyright_line:
        kwargs["producer"] = copyright_line

    if meta.website:
        kwargs["keywords"] = meta.website

    return kwargs


def _meta_obj(metadata: AuthorMetadata | dict | None) -> AuthorMetadata:
    if isinstance(metadata, AuthorMetadata):
        return metadata
    return AuthorMetadata.from_dict(metadata)


def build_ffmpeg_metadata_flags(
    metadata: AuthorMetadata | dict | None,
    *,
    title: str = "",
) -> list[str]:
    """ffmpeg -metadata key=value pairs for video containers."""
    meta = _meta_obj(metadata)
    if not meta.enabled or not meta.has_content():
        return []

    flags: list[str] = []
    if title:
        flags.extend(["-metadata", f"title={title}"])
    if meta.author:
        flags.extend(["-metadata", f"artist={meta.author}"])
        flags.extend(["-metadata", f"author={meta.author}"])
    copyright_line = meta.build_copyright_line()
    if copyright_line:
        flags.extend(["-metadata", f"copyright={copyright_line}"])
    if meta.description:
        flags.extend(["-metadata", f"description={meta.description}"])
    if meta.website:
        flags.extend(["-metadata", f"comment={meta.website}"])
    flags.extend(["-metadata", "encoder=ContentSuite"])
    return flags


def should_strip_media_metadata(
    remove_metadata: bool,
    metadata: AuthorMetadata | dict | None,
) -> bool:
    meta = _meta_obj(metadata)
    return remove_metadata or meta.enabled


def embed_author_in_jpeg(
    path: Path,
    metadata: AuthorMetadata | dict | None,
    *,
    quality: int = 95,
) -> bool:
    meta = _meta_obj(metadata)
    exif = build_exif(meta)
    if exif is None:
        return False
    with Image.open(path) as img:
        img.convert("RGB").save(path, "JPEG", exif=exif, quality=quality)
    return True


def embed_author_in_folder(
    folder: Path,
    metadata: AuthorMetadata | dict | None,
    *,
    quality: int = 95,
) -> int:
    count = 0
    for jpg in sorted(folder.glob("*.jpg")):
        if embed_author_in_jpeg(jpg, metadata, quality=quality):
            count += 1
    return count