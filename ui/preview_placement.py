"""Smart hover-preview sizing and placement next to a grid tile."""

from __future__ import annotations

from PySide6.QtCore import QRect


def media_aspect(width: int, height: int, *, default: float = 16 / 9) -> float:
    if width > 0 and height > 0:
        return width / height
    return default


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


def compute_hover_preview_layout(
    tile_global: QRect,
    screen_available: QRect,
    aspect: float,
    *,
    gap: int = 8,
    margin: int = 8,
    frame_pad: int = 4,
    min_content_w: int = 200,
    min_content_h: int = 120,
) -> tuple[int, int, int, int]:
    """
    Return content width/height and global (x, y) for a hover popup.

    Picks the side (left, right, above, below) with the most room, sizes the
    preview up to the screen edge without overlapping the anchor tile.
    """
    if aspect <= 0:
        aspect = 16 / 9

    vert_span = screen_available.height() - 2 * margin
    horiz_span = screen_available.width() - 2 * margin

    placements: list[tuple[int, int, int, QRect]] = []

    # Right of tile — use horizontal space to screen edge.
    max_w = screen_available.right() - tile_global.right() - gap - margin
    content_w, content_h = _fit_aspect(
        max_w, vert_span, aspect, min_w=min_content_w, min_h=min_content_h
    )
    if content_w > 0:
        popup = QRect(0, 0, content_w + frame_pad * 2, content_h + frame_pad * 2)
        popup.moveTo(tile_global.right() + gap, tile_global.top())
        placements.append((content_w, content_h, popup.width() * popup.height(), popup))

    # Left of tile
    max_w = tile_global.left() - screen_available.left() - gap - margin
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
    max_h = screen_available.bottom() - tile_global.bottom() - gap - margin
    content_w, content_h = _fit_aspect(
        horiz_span, max_h, aspect, min_w=min_content_w, min_h=min_content_h
    )
    if content_w > 0:
        popup = QRect(0, 0, content_w + frame_pad * 2, content_h + frame_pad * 2)
        popup.moveTo(screen_available.left() + margin, tile_global.bottom() + gap)
        placements.append((content_w, content_h, popup.width() * popup.height(), popup))

    # Above tile
    max_h = tile_global.top() - screen_available.top() - gap - margin
    content_w, content_h = _fit_aspect(
        horiz_span, max_h, aspect, min_w=min_content_w, min_h=min_content_h
    )
    if content_w > 0:
        popup_w = content_w + frame_pad * 2
        popup_h = content_h + frame_pad * 2
        popup = QRect(0, 0, popup_w, popup_h)
        popup.moveTo(screen_available.left() + margin, tile_global.top() - gap - popup_h)
        placements.append((content_w, content_h, popup.width() * popup.height(), popup))

    if not placements:
        content_w = min_content_w
        content_h = max(min_content_h, round(content_w / aspect))
        popup_w = content_w + frame_pad * 2
        popup_h = content_h + frame_pad * 2
        x = min(
            tile_global.right() + gap,
            screen_available.right() - popup_w - margin,
        )
        y = max(screen_available.top() + margin, tile_global.top())
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
    popup_w = popup_rect.width()
    popup_h = popup_rect.height()

    if x < screen_available.left() + margin:
        x = screen_available.left() + margin
    if x + popup_w > screen_available.right() - margin:
        x = screen_available.right() - margin - popup_w
    if y < screen_available.top() + margin:
        y = screen_available.top() + margin
    if y + popup_h > screen_available.bottom() - margin:
        y = screen_available.bottom() - margin - popup_h

    final = QRect(x, y, popup_w, popup_h)
    if _rects_intersect(final, tile_global):
        if screen_available.right() - tile_global.right() >= tile_global.left() - screen_available.left():
            x = tile_global.right() + gap
        else:
            x = tile_global.left() - gap - popup_w
        y = max(
            screen_available.top() + margin,
            min(tile_global.top(), screen_available.bottom() - margin - popup_h),
        )

    return content_w, content_h, x, y