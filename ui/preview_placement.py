"""Smart hover-preview sizing and placement next to a grid tile."""

from __future__ import annotations

from PySide6.QtCore import QRect
from PySide6.QtGui import QGuiApplication


def media_aspect(width: int, height: int, *, default: float = 16 / 9) -> float:
    if width > 0 and height > 0:
        return width / height
    return default


def screen_available_for(global_rect: QRect) -> QRect:
    """Available geometry of the monitor that contains *global_rect*."""
    app = QGuiApplication.instance()
    if app is None:
        return global_rect
    screen = app.screenAt(global_rect.center())
    if screen is None:
        screen = app.primaryScreen()
    if screen is None:
        return global_rect
    return screen.availableGeometry()


def _inner_screen(screen: QRect, margin: int) -> QRect:
    return screen.adjusted(margin, margin, -margin, -margin)


def _fit_aspect(
    max_w: int,
    max_h: int,
    aspect: float,
    *,
    min_w: int = 200,
    min_h: int = 120,
) -> tuple[int, int]:
    if max_w < min_w or max_h < min_h:
        return 0, 0
    if aspect >= max_w / max_h:
        width = max_w
        height = max(1, round(width / aspect))
    else:
        height = max_h
        width = max(1, round(height * aspect))
    if width < min_w or height < min_h:
        return 0, 0
    return width, height


def _rects_intersect(a: QRect, b: QRect) -> bool:
    return a.intersects(b)


def _fit_popup_in_screen(
    content_w: int,
    content_h: int,
    x: int,
    y: int,
    *,
    frame_pad: int,
    screen: QRect,
    margin: int,
    aspect: float,
    min_content_w: int,
    min_content_h: int,
) -> tuple[int, int, int, int]:
    """Shrink and slide popup so it stays fully inside *screen*."""
    inner = _inner_screen(screen, margin)
    if inner.width() <= 0 or inner.height() <= 0:
        return content_w, content_h, x, y

    max_inner_w = max(1, inner.width() - frame_pad * 2)
    max_inner_h = max(1, inner.height() - frame_pad * 2)
    popup_w = content_w + frame_pad * 2
    popup_h = content_h + frame_pad * 2

    if popup_w > inner.width() or popup_h > inner.height():
        shrunk_w, shrunk_h = _fit_aspect(
            max_inner_w,
            max_inner_h,
            aspect,
            min_w=min(min_content_w, max_inner_w),
            min_h=min(min_content_h, max_inner_h),
        )
        if shrunk_w > 0 and shrunk_h > 0:
            content_w, content_h = shrunk_w, shrunk_h
            popup_w = content_w + frame_pad * 2
            popup_h = content_h + frame_pad * 2

    if popup_w > inner.width():
        popup_w = inner.width()
        content_w = max(1, popup_w - frame_pad * 2)
        content_h = max(1, round(content_w / aspect))
        popup_h = content_h + frame_pad * 2
        if popup_h > inner.height():
            popup_h = inner.height()
            content_h = max(1, popup_h - frame_pad * 2)
            content_w = max(1, round(content_h * aspect))

    if popup_h > inner.height():
        popup_h = inner.height()
        content_h = max(1, popup_h - frame_pad * 2)
        content_w = max(1, round(content_h * aspect))
        popup_w = content_w + frame_pad * 2

    x = max(inner.left(), min(x, inner.right() - popup_w + 1))
    y = max(inner.top(), min(y, inner.bottom() - popup_h + 1))

    return content_w, content_h, x, y


def compute_hover_preview_layout(
    tile_global: QRect,
    aspect: float,
    *,
    screen_available: QRect | None = None,
    gap: int = 8,
    margin: int = 8,
    frame_pad: int = 4,
    min_content_w: int = 200,
    min_content_h: int = 120,
) -> tuple[int, int, int, int]:
    """
    Return content width/height and global (x, y) for a hover popup.

    Picks the side (left, right, above, below) with the most room on the
    monitor that contains the tile, sizes the preview up to that edge, and
    clamps the result so nothing spills onto another monitor.
    """
    if aspect <= 0:
        aspect = 16 / 9

    screen = screen_available if screen_available is not None else screen_available_for(
        tile_global
    )
    inner = _inner_screen(screen, margin)
    vert_span = inner.height()
    horiz_span = inner.width()

    placements: list[tuple[int, int, int, QRect]] = []

    # Right of tile — use horizontal space to screen edge.
    max_w = screen.right() - tile_global.right() - gap - margin
    content_w, content_h = _fit_aspect(
        max_w, vert_span, aspect, min_w=min_content_w, min_h=min_content_h
    )
    if content_w > 0:
        popup = QRect(0, 0, content_w + frame_pad * 2, content_h + frame_pad * 2)
        popup.moveTo(tile_global.right() + gap, tile_global.top())
        placements.append((content_w, content_h, popup.width() * popup.height(), popup))

    # Left of tile
    max_w = tile_global.left() - screen.left() - gap - margin
    content_w, content_h = _fit_aspect(
        max_w, vert_span, aspect, min_w=min_content_w, min_h=min_content_h
    )
    if content_w > 0:
        popup_w = content_w + frame_pad * 2
        popup_h = content_h + frame_pad * 2
        popup = QRect(0, 0, popup_w, popup_h)
        popup.moveTo(tile_global.left() - gap - popup_w, tile_global.top())
        placements.append((content_w, content_h, popup.width() * popup.height(), popup))

    # Below tile — use vertical space to screen edge.
    max_h = screen.bottom() - tile_global.bottom() - gap - margin
    content_w, content_h = _fit_aspect(
        horiz_span - frame_pad * 2, max_h, aspect, min_w=min_content_w, min_h=min_content_h
    )
    if content_w > 0:
        popup = QRect(0, 0, content_w + frame_pad * 2, content_h + frame_pad * 2)
        popup.moveTo(inner.left(), tile_global.bottom() + gap)
        placements.append((content_w, content_h, popup.width() * popup.height(), popup))

    # Above tile
    max_h = tile_global.top() - screen.top() - gap - margin
    content_w, content_h = _fit_aspect(
        horiz_span - frame_pad * 2, max_h, aspect, min_w=min_content_w, min_h=min_content_h
    )
    if content_w > 0:
        popup_w = content_w + frame_pad * 2
        popup_h = content_h + frame_pad * 2
        popup = QRect(0, 0, popup_w, popup_h)
        popup.moveTo(inner.left(), tile_global.top() - gap - popup_h)
        placements.append((content_w, content_h, popup.width() * popup.height(), popup))

    if not placements:
        content_w, content_h, x, y = _fit_popup_in_screen(
            min_content_w,
            max(min_content_h, round(min_content_w / aspect)),
            tile_global.right() + gap,
            tile_global.top(),
            frame_pad=frame_pad,
            screen=screen,
            margin=margin,
            aspect=aspect,
            min_content_w=min_content_w,
            min_content_h=min_content_h,
        )
        return content_w, content_h, x, y

    valid = [
        item
        for item in placements
        if not _rects_intersect(item[3], tile_global)
    ]
    if not valid:
        valid = placements

    content_w, content_h, _area, popup_rect = max(valid, key=lambda item: item[2])

    x = popup_rect.x()
    y = popup_rect.y()

    content_w, content_h, x, y = _fit_popup_in_screen(
        content_w,
        content_h,
        x,
        y,
        frame_pad=frame_pad,
        screen=screen,
        margin=margin,
        aspect=aspect,
        min_content_w=min_content_w,
        min_content_h=min_content_h,
    )

    popup_w = content_w + frame_pad * 2
    popup_h = content_h + frame_pad * 2
    final = QRect(x, y, popup_w, popup_h)
    if _rects_intersect(final, tile_global):
        room_right = screen.right() - tile_global.right() - gap - margin
        room_left = tile_global.left() - screen.left() - gap - margin
        if room_right >= room_left:
            x = tile_global.right() + gap
        else:
            x = tile_global.left() - gap - popup_w
        y = max(
            inner.top(),
            min(tile_global.top(), inner.bottom() - popup_h + 1),
        )
        content_w, content_h, x, y = _fit_popup_in_screen(
            content_w,
            content_h,
            x,
            y,
            frame_pad=frame_pad,
            screen=screen,
            margin=margin,
            aspect=aspect,
            min_content_w=min_content_w,
            min_content_h=min_content_h,
        )

    return content_w, content_h, x, y