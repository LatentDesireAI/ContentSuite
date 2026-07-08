"""Shared watermark positioning for images (Pillow) and video (ffmpeg)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WatermarkSettings:
    """Position as fraction of frame (0–1), alpha 0–100, height as % of frame height."""

    x: float = 0.85
    y: float = 0.85
    alpha: int = 50
    height_pct: float = 8.0
    margin_px: int = 10

    def clamp(self) -> WatermarkSettings:
        return WatermarkSettings(
            x=max(0.0, min(1.0, self.x)),
            y=max(0.0, min(1.0, self.y)),
            alpha=max(0, min(100, self.alpha)),
            height_pct=max(1.0, min(50.0, float(self.height_pct))),
            margin_px=max(0, self.margin_px),
        )


def watermark_height_px(frame_height: int, settings: WatermarkSettings) -> int:
    s = settings.clamp()
    return max(8, round(frame_height * s.height_pct / 100.0))


def _overlay_position_exprs(settings: WatermarkSettings) -> tuple[str, str]:
    s = settings.clamp()
    x_expr = f"max(0\\,min(W-w-{s.margin_px}\\,W*{s.x:.4f}-w))"
    y_expr = f"max(0\\,min(H-h-{s.margin_px}\\,H*{s.y:.4f}-h))"
    return x_expr, y_expr


def _wm_prepare_chain(wm_height_px: int, settings: WatermarkSettings) -> str:
    s = settings.clamp()
    alpha = s.alpha / 100.0
    height = max(8, wm_height_px)
    return (
        f"[1:v]scale=-1:{height},format=rgba,"
        f"colorchannelmixer=aa={alpha:.3f}[wma]"
    )


def ffmpeg_overlay_filter(
    settings: WatermarkSettings,
    *,
    frame_height: int,
    out_label: str = "",
) -> str:
    """Build filter_complex fragment for watermark overlay on video."""
    wm_h = watermark_height_px(frame_height, settings)
    x_expr, y_expr = _overlay_position_exprs(settings)
    chain = _wm_prepare_chain(wm_h, settings)
    suffix = f"[{out_label}]" if out_label else ""
    return f"{chain};[0:v][wma]overlay={x_expr}:{y_expr}{suffix}"


def ffmpeg_overlay_on_label(
    main_label: str,
    settings: WatermarkSettings,
    *,
    frame_height: int,
    out_label: str = "out",
) -> str:
    """Overlay watermark on a prepared main stream (e.g. after fps/scale)."""
    wm_h = watermark_height_px(frame_height, settings)
    x_expr, y_expr = _overlay_position_exprs(settings)
    chain = _wm_prepare_chain(wm_h, settings)
    return f"{chain};[{main_label}][wma]overlay={x_expr}:{y_expr}[{out_label}]"


def pillow_position(
    frame_width: int,
    frame_height: int,
    wm_width: int,
    wm_height: int,
    settings: WatermarkSettings,
) -> tuple[int, int]:
    """Top-left paste coordinates for Pillow."""
    s = settings.clamp()
    x = int(frame_width * s.x - wm_width)
    y = int(frame_height * s.y - wm_height)
    x = max(s.margin_px, min(x, frame_width - wm_width - s.margin_px))
    y = max(s.margin_px, min(y, frame_height - wm_height - s.margin_px))
    return x, y