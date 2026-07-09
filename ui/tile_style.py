"""Shared selection styling for preview grid tiles."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel


def apply_tile_selection_style(
    frame: QFrame,
    *,
    selected: bool,
    name_label: QLabel,
    meta_label: QLabel | None = None,
    class_name: str = "GridTile",
) -> None:
    if selected:
        border = "2px solid #2563eb"
        bg = "#ffffff"
        name_color = "#111827"
        meta_color = "#64748b"
    else:
        border = "2px solid transparent"
        bg = "#1a1a1a"
        name_color = "#ffffff"
        meta_color = "#a3a3a3"
    frame.setStyleSheet(
        f"{class_name} {{ background: {bg}; border: {border}; border-radius: 10px; "
        f"padding: 4px; }}"
        f"{class_name}:hover {{ border: 2px solid #94a3b8; }}"
    )
    name_label.setStyleSheet(
        f"color: {name_color}; font-size: 11px; background: transparent;"
    )
    if meta_label is not None:
        meta_label.setStyleSheet(
            f"color: {meta_color}; font-size: 10px; background: transparent;"
        )