"""Persistent user settings stored in %APPDATA%/ContentSuite/config.json."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any


APP_NAME = "ContentSuite"

DEFAULT_CONFIG: dict[str, Any] = {
    "last_input_folder": "",
    "last_output_folder": "",
    "images_input_folder": "",
    "images_output_folder": "",
    "video_input_folder": "",
    "video_output_folder": "",
    "pixiv_input_folder": "",
    "pixiv_censor_input_folder": "",
    "pixiv_censor_output_folder": "",
    "pixiv_censor_base_name": "",
    "pixiv_censor_block_size": 18,
    "watermark_files": [],
    "watermark_alpha": 50,
    "watermark_x": 0.85,
    "watermark_y": 0.85,
    "image_base_name": "",
    "video_base_name": "",
    "image_quality": 98,
    "image_max_res": 2560,
    "image_workers": 0,
    "image_keep_original_name": False,
    "ui_language": "en",
    "gif_fps": 24,
    "gif_width": 720,
    "watermark_height": 120,
    "watermark_height_pct": 8.0,
    "watermark_margin": 10,
    "video_workers": 0,
    "video_output_format": "webm",
    "video_compression_level": "medium",
    "video_remove_metadata": True,
    "video_keep_audio": True,
    "video_reencode": False,
    "video_patch_in_place": True,
    "ugoira_chunk_sec": 10,
    "ugoira_fps": 20,
    "ugoira_auto_fps": True,
    "ugoira_max_frames": 150,
    "ugoira_quality": 80,
    "ugoira_auto_fit_size": True,
    "ugoira_max_chunk_mb": 30,
    "ugoira_max_width": 1200,
    "ugoira_watermark": True,
    "pdf_dpi": 150,
    "pdf_source": "input",
    "embed_author_metadata": False,
    "author_name": "",
    "author_website": "",
    "author_copyright": "",
    "author_description": "",
    "pixiv_canvas_size": 1200,
    "pixiv_padding": 24,
    "pixiv_gap": 16,
    "pixiv_layout": "auto",
    "pixiv_cover_name": "pixiv_cover",
    "pixiv_output_folder": "",
    "pixiv_crop_fill": True,
    "pixiv_frame_width": 4,
    "pixiv_frame_color": "#2d2d2d",
}


def config_path() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        appdata = str(Path.home())
    return Path(appdata) / APP_NAME / "config.json"


class ConfigStore:
    def __init__(self) -> None:
        self._path = config_path()
        self._data = deepcopy(DEFAULT_CONFIG)
        self.load()

    def load(self) -> None:
        if not self._path.exists():
            return
        try:
            with self._path.open(encoding="utf-8") as f:
                stored = json.load(f)
            if isinstance(stored, dict):
                self._data.update(stored)
                self._migrate_legacy_folders()
        except (json.JSONDecodeError, OSError):
            pass

    def _migrate_legacy_folders(self) -> None:
        """Copy shared folder paths into per-tab keys on first run after upgrade."""
        legacy_in = self._data.get("last_input_folder", "")
        legacy_out = self._data.get("last_output_folder", "")
        changed = False
        if legacy_in:
            for key in (
                "images_input_folder",
                "video_input_folder",
                "pixiv_input_folder",
                "pixiv_censor_input_folder",
            ):
                if not self._data.get(key):
                    self._data[key] = legacy_in
                    changed = True
        if legacy_out:
            for key in (
                "images_output_folder",
                "video_output_folder",
                "pixiv_output_folder",
                "pixiv_censor_output_folder",
            ):
                if not self._data.get(key):
                    self._data[key] = legacy_out
                    changed = True
        if not self._data.get("pixiv_censor_input_folder") and self._data.get(
            "video_input_folder"
        ):
            self._data["pixiv_censor_input_folder"] = self._data["video_input_folder"]
            changed = True
        if not self._data.get("pixiv_censor_output_folder") and self._data.get(
            "video_output_folder"
        ):
            self._data["pixiv_censor_output_folder"] = self._data["video_output_folder"]
            changed = True
        if changed:
            self.save()

    def folder(self, key: str) -> str:
        return str(self.get(key, "") or "")

    def watermark_height_pct(self) -> float:
        pct = self.get("watermark_height_pct")
        if pct not in (None, ""):
            return max(1.0, min(50.0, float(pct)))
        px = int(self.get("watermark_height", 120) or 120)
        return max(1.0, min(50.0, px / 1080.0 * 100.0))

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()

    def update(self, values: dict[str, Any]) -> None:
        self._data.update(values)
        self.save()

    def get_author_metadata(self) -> dict[str, Any]:
        return {
            "enabled": bool(self.get("embed_author_metadata", False)),
            "author": self.get("author_name", ""),
            "website": self.get("author_website", ""),
            "copyright": self.get("author_copyright", ""),
            "description": self.get("author_description", ""),
        }