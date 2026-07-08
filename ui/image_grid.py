"""YouTube-style image grid with thumbnails and hover preview."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QCursor, QFontMetrics, QImageReader, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.app_log import get_logger
from core.i18n import I18n, tr
from core.compress import (
    ImageProbe,
    extract_image_thumbnail,
    format_file_size,
    image_thumbnail_cache_path,
    probe_image,
)

TILE_MIN_WIDTH = 148
TILE_MAX_WIDTH = 320
THUMB_ASPECT = 1.0
PREVIEW_MAX_WIDTH = 1680
PREVIEW_MAX_HEIGHT = 944
PREVIEW_FRAME_PAD = 4
HOVER_DELAY_MS = 380
HOVER_TRACK_MS = 50
RELAYOUT_DEBOUNCE_MS = 80


def _preview_dimensions(
    probe: ImageProbe | None,
    screen_width: int,
    screen_height: int,
) -> tuple[int, int]:
    """Fit preview inside max box, preserving the image aspect ratio."""
    if probe and probe.width > 0 and probe.height > 0:
        aspect = probe.width / probe.height
    else:
        aspect = 1.0

    max_w = min(PREVIEW_MAX_WIDTH, max(320, screen_width - 48))
    max_h = min(PREVIEW_MAX_HEIGHT, max(180, screen_height - 48))

    if aspect >= max_w / max_h:
        width = max_w
        height = round(max_w / aspect)
    else:
        height = max_h
        width = round(max_h * aspect)

    return max(200, width), max(120, height)


def _calc_grid_metrics(available_width: int, spacing: int = 10) -> tuple[int, int, int]:
    margins = 8
    usable = max(TILE_MIN_WIDTH, available_width - margins)
    cols = max(1, (usable + spacing) // (TILE_MIN_WIDTH + spacing))
    tile_w = (usable - spacing * (cols - 1)) // cols
    tile_w = max(TILE_MIN_WIDTH, min(TILE_MAX_WIDTH, tile_w))
    thumb_h = max(72, round(tile_w * THUMB_ASPECT))
    return cols, tile_w, thumb_h


def _elide(text: str, width_px: int) -> str:
    metrics = QFontMetrics(QLabel().font())
    return metrics.elidedText(text, Qt.TextElideMode.ElideRight, width_px)


class ImageLoadWorker(QThread):
    image_ready = Signal(object, object, str)
    finished_all = Signal()

    def __init__(self, sources: list[Path]) -> None:
        super().__init__()
        self.sources = sources

    def run(self) -> None:
        for path in self.sources:
            probe: ImageProbe | None = None
            thumb_path = ""
            try:
                probe = probe_image(path)
                cache = image_thumbnail_cache_path(path)
                if not cache.is_file():
                    extract_image_thumbnail(path, cache)
                if cache.is_file():
                    thumb_path = str(cache)
            except OSError as exc:
                get_logger().warning("Image preview failed for %s: %s", path.name, exc)
            self.image_ready.emit(path, probe, thumb_path)
        self.finished_all.emit()


class ImageHoverPreviewPopup(QFrame):
    entered = Signal()
    left = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            parent,
            Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.setStyleSheet(
            "ImageHoverPreviewPopup { background: #1a1a1a; border: 1px solid #555; "
            "border-radius: 6px; }"
        )

        self._image_label = QLabel(self)
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setMouseTracking(True)
        self._image_label.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            PREVIEW_FRAME_PAD, PREVIEW_FRAME_PAD, PREVIEW_FRAME_PAD, PREVIEW_FRAME_PAD
        )
        layout.setSpacing(0)
        layout.addWidget(self._image_label)

        self._current_path: Path | None = None
        self._showing_error = False

    def retranslate_ui(self) -> None:
        if self._showing_error and self.isVisible():
            self._image_label.setText(tr("grid.preview_load_failed"))

    def show_for_tile(self, path: Path, probe: ImageProbe | None, anchor: QWidget) -> None:
        self._current_path = path

        screen = anchor.screen().availableGeometry()
        img_w, img_h = _preview_dimensions(probe, screen.width(), screen.height())
        pad = PREVIEW_FRAME_PAD * 2
        popup_w = img_w + pad
        popup_h = img_h + pad

        self._image_label.setFixedSize(img_w, img_h)
        self.setFixedSize(popup_w, popup_h)

        pixmap = self._load_preview_pixmap(path, img_w, img_h)
        if pixmap.isNull():
            self._showing_error = True
            self._image_label.setText(tr("grid.preview_load_failed"))
            self._image_label.setPixmap(QPixmap())
        else:
            self._showing_error = False
            self._image_label.setText("")
            self._image_label.setPixmap(pixmap)

        tile_tl = anchor.mapToGlobal(anchor.rect().topLeft())
        tile_tr = anchor.mapToGlobal(anchor.rect().topRight())
        x = tile_tr.x() + 8
        y = tile_tl.y()

        if x + popup_w > screen.right():
            x = tile_tl.x() - popup_w - 8
        if x < screen.left():
            x = screen.left() + 8
        if y + popup_h > screen.bottom():
            y = max(screen.top() + 8, screen.bottom() - popup_h - 8)

        self.move(x, y)
        self.show()
        self.raise_()

    def _load_preview_pixmap(self, path: Path, max_w: int, max_h: int) -> QPixmap:
        reader = QImageReader(str(path.resolve()))
        reader.setAutoTransform(True)
        size = reader.size()
        if size.isValid() and size.width() > 0 and size.height() > 0:
            scale = min(max_w / size.width(), max_h / size.height(), 1.0)
            reader.setScaledSize(
                QSize(
                    max(1, int(size.width() * scale)),
                    max(1, int(size.height() * scale)),
                )
            )
        image = reader.read()
        if image.isNull():
            return QPixmap()
        return QPixmap.fromImage(image)

    def enterEvent(self, event) -> None:
        self.entered.emit()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.left.emit()
        super().leaveEvent(event)

    def stop(self) -> None:
        self._image_label.setPixmap(QPixmap())
        self._current_path = None
        self._showing_error = False
        self.hide()

    def current_path(self) -> Path | None:
        return self._current_path


class ImageTile(QFrame):
    clicked = Signal(object, object)
    hover_enter = Signal(object)
    hover_leave = Signal(object)

    def __init__(
        self,
        path: Path,
        *,
        tile_width: int = TILE_MIN_WIDTH,
        thumb_height: int = 148,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.path = path
        self.probe: ImageProbe | None = None
        self._selected = False
        self._thumb_path = ""
        self._tile_width = tile_width
        self._thumb_height = thumb_height

        self.setFixedWidth(tile_width)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        self.thumb_wrap = QFrame()
        self.thumb_wrap.setFixedSize(tile_width, thumb_height)
        self.thumb_wrap.setStyleSheet("background: #1a1a1a; border-radius: 8px;")
        thumb_layout = QVBoxLayout(self.thumb_wrap)
        thumb_layout.setContentsMargins(0, 0, 0, 0)

        self.thumb_label = QLabel()
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setFixedSize(tile_width, thumb_height)
        self.thumb_label.setStyleSheet("color: #666; border-radius: 8px;")
        self.thumb_label.setText("…")
        thumb_layout.addWidget(self.thumb_label)

        self.check_badge = QLabel("✓", self.thumb_wrap)
        self.check_badge.setStyleSheet(
            "background: #2563eb; color: white; font-weight: bold; "
            "padding: 2px 8px; border-radius: 10px; font-size: 11px;"
        )
        self.check_badge.hide()
        self.check_badge.adjustSize()

        self.name_label = QLabel(_elide(path.name, tile_width - 8))
        self.name_label.setToolTip(str(path))
        self.name_label.setStyleSheet("color: #222; font-size: 11px;")

        self.meta_label = QLabel()
        self.meta_label.setStyleSheet("color: #888; font-size: 10px;")
        self._meta_state = "loading"

        root.addWidget(self.thumb_wrap)
        root.addWidget(self.name_label)
        root.addWidget(self.meta_label)
        self.meta_label.setText(tr("grid.loading"))
        self._apply_style()

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.check_badge.setVisible(selected)
        self._apply_style()

    def is_selected(self) -> bool:
        return self._selected

    def set_probe(self, probe: ImageProbe | None) -> None:
        self.probe = probe
        if probe:
            self._meta_state = "ok"
            self.meta_label.setText(
                f"{probe.width}×{probe.height} · {format_file_size(probe.size_bytes)}"
            )
            self.setToolTip(probe.summary)
        else:
            self._meta_state = "failed"
            self.meta_label.setText(tr("grid.read_failed"))
            self.setToolTip(self.path.name)

    def retranslate_meta(self) -> None:
        if self._meta_state == "loading":
            self.meta_label.setText(tr("grid.loading"))
        elif self._meta_state == "failed":
            self.meta_label.setText(tr("grid.read_failed"))
        elif self.probe:
            self.set_probe(self.probe)

    def set_thumbnail(self, thumb_path: str) -> None:
        self._thumb_path = thumb_path
        if not thumb_path:
            self.thumb_label.setPixmap(QPixmap())
            self.thumb_label.setText("🖼")
        else:
            self._render_thumbnail()

    def resize_tile(self, tile_width: int, thumb_height: int) -> None:
        self._tile_width = tile_width
        self._thumb_height = thumb_height
        self.setFixedWidth(tile_width)
        self.thumb_wrap.setFixedSize(tile_width, thumb_height)
        self.thumb_label.setFixedSize(tile_width, thumb_height)
        self.name_label.setText(_elide(self.path.name, tile_width - 8))
        self._render_thumbnail()

    def _render_thumbnail(self) -> None:
        if not self._thumb_path:
            self.thumb_label.setPixmap(QPixmap())
            return
        pix = QPixmap(self._thumb_path)
        if pix.isNull():
            self.thumb_label.setText("🖼")
            return
        scaled = pix.scaled(
            self._tile_width,
            self._thumb_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.thumb_label.setPixmap(scaled)
        self.thumb_label.setText("")

    def _apply_style(self) -> None:
        if self._selected:
            border = "2px solid #2563eb"
            bg = "#eff6ff"
        else:
            border = "2px solid transparent"
            bg = "transparent"
        self.setStyleSheet(
            f"ImageTile {{ background: {bg}; border: {border}; border-radius: 10px; "
            f"padding: 4px; }}"
            "ImageTile:hover { border: 2px solid #94a3b8; }"
        )
        self.check_badge.move(6, 6)

    def enterEvent(self, event) -> None:
        self.hover_enter.emit(self)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.hover_leave.emit(self)
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self, event.modifiers())
        super().mouseReleaseEvent(event)


class ImageGrid(QWidget):
    selection_changed = Signal()
    load_finished = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tiles: dict[Path, ImageTile] = {}
        self._source_order: list[Path] = []
        self._anchor_path: Path | None = None
        self._load_worker: ImageLoadWorker | None = None
        self._interaction_enabled = True
        self._grid_cols = 0
        self._tile_width = TILE_MIN_WIDTH
        self._thumb_height = 148

        self._relayout_timer = QTimer(self)
        self._relayout_timer.setSingleShot(True)
        self._relayout_timer.timeout.connect(self._relayout_grid)

        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.timeout.connect(self._start_hover_preview)
        self._hover_tile: ImageTile | None = None

        self._hover_track_timer = QTimer(self)
        self._hover_track_timer.setInterval(HOVER_TRACK_MS)
        self._hover_track_timer.timeout.connect(self._update_hover_from_cursor)

        self._preview = ImageHoverPreviewPopup()

        toolbar = QHBoxLayout()
        self.select_all_btn = QPushButton()
        self.select_all_btn.clicked.connect(self.select_all)
        self.clear_sel_btn = QPushButton()
        self.clear_sel_btn.clicked.connect(self.clear_selection)
        self.count_label = QLabel()
        self.count_label.setStyleSheet("color: #666;")
        toolbar.addWidget(self.select_all_btn)
        toolbar.addWidget(self.clear_sel_btn)
        toolbar.addStretch()
        toolbar.addWidget(self.count_label)

        self._grid_host = QWidget()
        self._grid_layout = QGridLayout(self._grid_host)
        self._grid_layout.setContentsMargins(4, 4, 4, 4)
        self._grid_layout.setSpacing(10)
        self._grid_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setWidget(self._grid_host)
        self._scroll.setMinimumHeight(200)
        self._scroll.setFrameShape(QFrame.Shape.StyledPanel)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.viewport().installEventFilter(self)
        self._scroll.verticalScrollBar().valueChanged.connect(
            self._update_hover_from_cursor
        )
        self._scroll.horizontalScrollBar().valueChanged.connect(
            self._update_hover_from_cursor
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(toolbar)
        layout.addWidget(self._scroll, stretch=1)

        self._hint_label = QLabel()
        self._hint_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self._hint_label)

        I18n.instance().language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()
        self._hover_track_timer.start()
        app = QApplication.instance()
        if app is not None:
            app.focusChanged.connect(self._on_app_focus_changed)

    def _is_host_window_active(self) -> bool:
        host = self.window()
        return host is not None and host.isActiveWindow()

    def _on_app_focus_changed(self, _old: QWidget | None, _new: QWidget | None) -> None:
        if not self._is_host_window_active():
            self.stop_preview()

    def retranslate_ui(self) -> None:
        self.select_all_btn.setText(tr("grid.select_all"))
        self.clear_sel_btn.setText(tr("grid.clear_selection"))
        self._hint_label.setText(tr("grid.hint"))
        self._preview.retranslate_ui()
        for tile in self._tiles.values():
            tile.retranslate_meta()
        self._update_count_label()

    def _current_metrics(self) -> tuple[int, int, int]:
        width = self._scroll.viewport().width() if self._scroll else self.width()
        return _calc_grid_metrics(width, self._grid_layout.spacing())

    def _schedule_relayout(self) -> None:
        self._relayout_timer.start(RELAYOUT_DEBOUNCE_MS)

    def _relayout_grid(self) -> None:
        if not self._tiles:
            return
        cols, tile_w, thumb_h = self._current_metrics()
        if (
            cols == self._grid_cols
            and tile_w == self._tile_width
            and thumb_h == self._thumb_height
        ):
            return

        self._grid_cols = cols
        self._tile_width = tile_w
        self._thumb_height = thumb_h

        for tile in self._tiles.values():
            tile.resize_tile(tile_w, thumb_h)

        for idx, path in enumerate(self._source_order):
            if path not in self._tiles:
                continue
            tile = self._tiles[path]
            self._grid_layout.removeWidget(tile)
            row, col = divmod(idx, cols)
            self._grid_layout.addWidget(tile, row, col, Qt.AlignmentFlag.AlignTop)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._schedule_relayout()

    def eventFilter(self, watched, event) -> bool:
        if watched is self._scroll.viewport():
            if event.type() == QEvent.Type.Resize:
                self._schedule_relayout()
            elif event.type() in (
                QEvent.Type.MouseMove,
                QEvent.Type.Enter,
                QEvent.Type.Leave,
            ):
                self._update_hover_from_cursor()
        return super().eventFilter(watched, event)

    def _tile_under_cursor(self) -> ImageTile | None:
        pos = QCursor.pos()
        for path in self._source_order:
            tile = self._tiles.get(path)
            if tile is None or not tile.isVisible():
                continue
            origin = tile.mapToGlobal(QPoint(0, 0))
            if QRect(origin, tile.size()).contains(pos):
                return tile
        return None

    def _update_hover_from_cursor(self) -> None:
        if not self._interaction_enabled:
            return
        if not self._is_host_window_active():
            if self._hover_tile is not None or self._preview.isVisible():
                self.stop_preview()
            return

        tile = self._tile_under_cursor()
        if tile is None:
            if self._hover_tile is not None or self._preview.isVisible():
                self._hover_tile = None
                self._hover_timer.stop()
                self._preview.stop()
            return

        if tile is self._hover_tile:
            if (
                not self._preview.isVisible()
                and not self._hover_timer.isActive()
            ):
                self._hover_timer.start(HOVER_DELAY_MS)
            return

        previous = self._hover_tile
        self._hover_tile = tile
        self._hover_timer.stop()

        if self._preview.isVisible() and previous is not None:
            self._show_preview_for(tile)
        else:
            self._hover_timer.start(HOVER_DELAY_MS)

    def _show_preview_for(self, tile: ImageTile) -> None:
        if not self._interaction_enabled:
            return
        if self._tile_under_cursor() is not tile:
            return
        self._preview.show_for_tile(tile.path, tile.probe, tile)

    def set_sources(self, sources: list[Path]) -> None:
        self.stop_preview()
        if self._load_worker and self._load_worker.isRunning():
            self._load_worker.requestInterruption()
            self._load_worker.wait(2000)

        self._clear_tiles()
        self._source_order = list(sources)
        self._anchor_path = None
        if not sources:
            self._update_count_label()
            self.load_finished.emit(0)
            return

        self.count_label.setText(tr("grid.loading_count", count=len(sources)))
        get_logger().info("ImageGrid: loading %d images", len(sources))
        cols, tile_w, thumb_h = self._current_metrics()
        self._grid_cols = cols
        self._tile_width = tile_w
        self._thumb_height = thumb_h
        for idx, path in enumerate(sources):
            tile = ImageTile(path, tile_width=tile_w, thumb_height=thumb_h)
            tile.clicked.connect(self._on_tile_clicked)
            row, col = divmod(idx, cols)
            self._grid_layout.addWidget(tile, row, col, Qt.AlignmentFlag.AlignTop)
            self._tiles[path] = tile

        self._load_worker = ImageLoadWorker(sources)
        self._load_worker.image_ready.connect(self._on_image_ready)
        self._load_worker.finished_all.connect(self._on_load_finished)
        self._load_worker.start()
        self._schedule_relayout()

    def _clear_tiles(self) -> None:
        for tile in self._tiles.values():
            self._grid_layout.removeWidget(tile)
            tile.deleteLater()
        self._tiles.clear()

    def _on_image_ready(self, path: Path, probe: ImageProbe | None, thumb_path: str) -> None:
        tile = self._tiles.get(path)
        if not tile:
            return
        tile.set_probe(probe)
        tile.set_thumbnail(thumb_path)

    def _on_load_finished(self) -> None:
        self._update_count_label()
        self.load_finished.emit(len(self._tiles))

    def _on_tile_clicked(self, tile: ImageTile, modifiers: Qt.KeyboardModifier) -> None:
        if not self._interaction_enabled:
            return

        mods = Qt.KeyboardModifiers(modifiers)
        if mods & Qt.KeyboardModifier.ShiftModifier and self._anchor_path is not None:
            self._select_range(self._anchor_path, tile.path)
        elif mods & Qt.KeyboardModifier.ControlModifier:
            tile.set_selected(not tile.is_selected())
            self._anchor_path = tile.path
        else:
            for other in self._tiles.values():
                other.set_selected(other is tile)
            self._anchor_path = tile.path

        selected = len(self.selected_paths())
        get_logger().info(
            "ImageGrid selection: %d selected (anchor=%s)",
            selected,
            self._anchor_path.name if self._anchor_path else "-",
        )
        self._update_count_label()
        self.selection_changed.emit()

    def _select_range(self, anchor: Path, target: Path) -> None:
        try:
            start = self._source_order.index(anchor)
            end = self._source_order.index(target)
        except ValueError:
            tile = self._tiles.get(target)
            if tile:
                tile.set_selected(True)
            return
        lo, hi = sorted((start, end))
        for path in self._source_order[lo : hi + 1]:
            self._tiles[path].set_selected(True)

    def _start_hover_preview(self) -> None:
        tile = self._hover_tile
        if not tile or not self._interaction_enabled:
            return
        self._show_preview_for(tile)

    def stop_preview(self) -> None:
        self._hover_timer.stop()
        self._hover_tile = None
        self._preview.stop()

    def set_interaction_enabled(self, enabled: bool) -> None:
        self._interaction_enabled = enabled
        if enabled:
            self._hover_track_timer.start()
        else:
            self._hover_track_timer.stop()
            self.stop_preview()

    def select_all(self) -> None:
        for tile in self._tiles.values():
            tile.set_selected(True)
        if self._source_order:
            self._anchor_path = self._source_order[0]
        get_logger().info("ImageGrid: select all (%d)", len(self._tiles))
        self._update_count_label()
        self.selection_changed.emit()

    def clear_selection(self) -> None:
        for tile in self._tiles.values():
            tile.set_selected(False)
        self._anchor_path = None
        get_logger().info("ImageGrid: selection cleared")
        self._update_count_label()
        self.selection_changed.emit()

    def selected_paths(self) -> list[Path]:
        return [
            path
            for path in self._source_order
            if path in self._tiles and self._tiles[path].is_selected()
        ]

    def has_images(self) -> bool:
        return bool(self._tiles)

    def count(self) -> int:
        return len(self._tiles)

    def _update_count_label(self) -> None:
        count = len(self._tiles)
        if count == 0:
            self.count_label.setText(tr("grid.no_images"))
            return
        selected = len(self.selected_paths())
        if selected:
            self.count_label.setText(
                tr("grid.image_count_selected", count=count, selected=selected)
            )
        else:
            self.count_label.setText(tr("grid.image_count", count=count))