"""Mixed video + image grid for Pixiv censor tab (videos first, then images)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QEvent, QPoint, QRect, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QCursor, QFontMetrics, QPixmap
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
from core.censor import is_image_path, is_video_path
from core.compress import (
    ImageProbe,
    extract_image_thumbnail,
    format_file_size,
    image_thumbnail_cache_path,
    probe_image,
)
from core.ffmpeg_wrapper import (
    FfmpegError,
    VideoProbe,
    extract_thumbnail,
    format_duration,
    probe_video,
    thumbnail_cache_path,
)
from core.i18n import I18n, tr
from ui.clip_grid import HoverPreviewPopup, _calc_grid_metrics, _elide
from ui.image_grid import ImageHoverPreviewPopup

TILE_MIN_WIDTH = 148
TILE_MAX_WIDTH = 320
THUMB_ASPECT = 9 / 16
HOVER_DELAY_MS = 380
HOVER_TRACK_MS = 50
RELAYOUT_DEBOUNCE_MS = 80


@dataclass
class MediaTileData:
    path: Path
    is_video: bool
    video_probe: VideoProbe | None = None
    image_probe: ImageProbe | None = None
    thumb_path: str = ""


class CensorMediaLoadWorker(QThread):
    tile_ready = Signal(object)
    finished_all = Signal()

    def __init__(self, sources: list[Path]) -> None:
        super().__init__()
        self.sources = sources

    def run(self) -> None:
        for path in self.sources:
            data = MediaTileData(path=path, is_video=is_video_path(path))
            try:
                if data.is_video:
                    data.video_probe = probe_video(path)
                    cache = thumbnail_cache_path(path)
                    if not cache.is_file():
                        seek = 1.0
                        if data.video_probe.duration > 0:
                            seek = min(
                                max(0.5, data.video_probe.duration * 0.15),
                                data.video_probe.duration - 0.1,
                            )
                        extract_thumbnail(path, cache, time_sec=seek)
                    if cache.is_file():
                        data.thumb_path = str(cache)
                elif is_image_path(path):
                    data.is_video = False
                    data.image_probe = probe_image(path)
                    cache = image_thumbnail_cache_path(path)
                    if not cache.is_file():
                        extract_image_thumbnail(path, cache)
                    if cache.is_file():
                        data.thumb_path = str(cache)
            except (FfmpegError, OSError) as exc:
                get_logger().warning("Censor media preview failed for %s: %s", path.name, exc)
            self.tile_ready.emit(data)
        self.finished_all.emit()


class MediaTile(QFrame):
    clicked = Signal(object, object)

    def __init__(
        self,
        data: MediaTileData,
        *,
        tile_width: int = TILE_MIN_WIDTH,
        thumb_height: int = 84,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.data = data
        self.path = data.path
        self._selected = False
        self._tile_width = tile_width
        self._thumb_height = thumb_height
        self._meta_state = "loading"

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

        self.badge = QLabel(self.thumb_wrap)
        self.badge.setStyleSheet(
            "background: rgba(0,0,0,0.78); color: #fff; "
            "padding: 2px 6px; border-radius: 4px; font-size: 10px;"
        )
        self.badge.hide()

        self.check_badge = QLabel("✓", self.thumb_wrap)
        self.check_badge.setStyleSheet(
            "background: #2563eb; color: white; font-weight: bold; "
            "padding: 2px 8px; border-radius: 10px; font-size: 11px;"
        )
        self.check_badge.hide()

        self.name_label = QLabel(_elide(data.path.name, tile_width - 8))
        self.name_label.setToolTip(str(data.path))
        self.name_label.setStyleSheet("color: #222; font-size: 11px;")

        self.meta_label = QLabel()
        self.meta_label.setStyleSheet("color: #888; font-size: 10px;")
        self.meta_label.setText(tr("grid.loading"))

        root.addWidget(self.thumb_wrap)
        root.addWidget(self.name_label)
        root.addWidget(self.meta_label)
        self._apply_style()

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.check_badge.setVisible(selected)
        self._apply_style()

    def is_selected(self) -> bool:
        return self._selected

    def apply_data(self, data: MediaTileData) -> None:
        self.data = data
        if data.thumb_path:
            self._render_thumbnail(data.thumb_path)
        elif data.is_video:
            self.thumb_label.setPixmap(QPixmap())
            self.thumb_label.setText("▶")
        else:
            self.thumb_label.setPixmap(QPixmap())
            self.thumb_label.setText("🖼")

        if data.is_video and data.video_probe:
            self._meta_state = "ok"
            self.badge.setText(format_duration(data.video_probe.duration))
            self.badge.show()
            self._position_badge()
            self.meta_label.setText(
                f"{data.video_probe.width}×{data.video_probe.height} · "
                f"{data.video_probe.video_codec}"
            )
            self.setToolTip(data.video_probe.summary)
        elif data.image_probe:
            self._meta_state = "ok"
            self.badge.setText(tr("censor.badge_image"))
            self.badge.show()
            self._position_badge()
            self.meta_label.setText(
                f"{data.image_probe.width}×{data.image_probe.height} · "
                f"{format_file_size(data.image_probe.size_bytes)}"
            )
            self.setToolTip(data.image_probe.summary)
        else:
            self._meta_state = "failed"
            self.badge.hide()
            self.meta_label.setText(tr("grid.read_failed"))

    def retranslate_meta(self) -> None:
        if self._meta_state == "loading":
            self.meta_label.setText(tr("grid.loading"))
        elif self._meta_state == "failed":
            self.meta_label.setText(tr("grid.read_failed"))
        else:
            self.apply_data(self.data)

    def resize_tile(self, tile_width: int, thumb_height: int) -> None:
        self._tile_width = tile_width
        self._thumb_height = thumb_height
        self.setFixedWidth(tile_width)
        self.thumb_wrap.setFixedSize(tile_width, thumb_height)
        self.thumb_label.setFixedSize(tile_width, thumb_height)
        self.name_label.setText(_elide(self.path.name, tile_width - 8))
        if self.badge.isVisible():
            self._position_badge()
        if self.data.thumb_path:
            self._render_thumbnail(self.data.thumb_path)

    def _position_badge(self) -> None:
        self.badge.adjustSize()
        x = self.thumb_wrap.width() - self.badge.width() - 6
        y = self.thumb_wrap.height() - self.badge.height() - 6
        self.badge.move(max(4, x), max(4, y))

    def _render_thumbnail(self, thumb_path: str) -> None:
        pix = QPixmap(thumb_path)
        if pix.isNull():
            self.thumb_label.setPixmap(QPixmap())
            self.thumb_label.setText("▶" if self.data.is_video else "🖼")
            return
        scaled = pix.scaled(
            self._tile_width,
            self._thumb_height,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = max(0, (scaled.width() - self._tile_width) // 2)
        y = max(0, (scaled.height() - self._thumb_height) // 2)
        cropped = scaled.copy(x, y, self._tile_width, self._thumb_height)
        self.thumb_label.setPixmap(cropped)
        self.thumb_label.setText("")

    def _apply_style(self) -> None:
        if self._selected:
            border = "2px solid #2563eb"
            bg = "#eff6ff"
        else:
            border = "2px solid transparent"
            bg = "transparent"
        self.setStyleSheet(
            f"MediaTile {{ background: {bg}; border: {border}; border-radius: 10px; "
            f"padding: 4px; }}"
            "MediaTile:hover { border: 2px solid #94a3b8; }"
        )
        self.check_badge.move(6, 6)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self, event.modifiers())
        super().mouseReleaseEvent(event)


class CensorMediaGrid(QWidget):
    selection_changed = Signal()
    load_finished = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tiles: dict[Path, MediaTile] = {}
        self._source_order: list[Path] = []
        self._video_count = 0
        self._image_count = 0
        self._anchor_path: Path | None = None
        self._interaction_enabled = True
        self._grid_cols = 1
        self._tile_width = TILE_MIN_WIDTH
        self._thumb_height = 84
        self._load_worker: CensorMediaLoadWorker | None = None
        self._hover_tile: MediaTile | None = None
        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.timeout.connect(self._start_hover_preview)
        self._hover_track_timer = QTimer(self)
        self._hover_track_timer.setInterval(HOVER_TRACK_MS)
        self._hover_track_timer.timeout.connect(self._update_hover_from_cursor)
        self._relayout_timer = QTimer(self)
        self._relayout_timer.setSingleShot(True)
        self._relayout_timer.timeout.connect(self._relayout_grid)

        self._video_preview = HoverPreviewPopup()
        self._image_preview = ImageHoverPreviewPopup()

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
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setWidget(self._grid_host)
        self._scroll.setMinimumHeight(200)
        self._scroll.setFrameShape(QFrame.Shape.StyledPanel)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.viewport().installEventFilter(self)
        self._scroll.verticalScrollBar().valueChanged.connect(self._update_hover_from_cursor)

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

    def retranslate_ui(self) -> None:
        self.select_all_btn.setText(tr("grid.select_all"))
        self.clear_sel_btn.setText(tr("grid.clear_selection"))
        self._hint_label.setText(tr("censor.grid_hint"))
        for tile in self._tiles.values():
            tile.retranslate_meta()
        self._update_count_label()

    def _is_host_window_active(self) -> bool:
        host = self.window()
        return host is not None and host.isActiveWindow()

    def _on_app_focus_changed(self, _old: QWidget | None, _new: QWidget | None) -> None:
        if not self._is_host_window_active():
            self.stop_preview()

    def set_sources(self, sources: list[Path]) -> None:
        self.stop_preview()
        if self._load_worker and self._load_worker.isRunning():
            self._load_worker.requestInterruption()
            self._load_worker.wait(2000)

        self._clear_tiles()
        self._source_order = list(sources)
        self._video_count = sum(1 for p in sources if is_video_path(p))
        self._image_count = sum(1 for p in sources if is_image_path(p))
        self._anchor_path = None

        if not sources:
            self._update_count_label()
            self.load_finished.emit(0)
            return

        self.count_label.setText(tr("grid.loading_count", count=len(sources)))
        cols, tile_w, thumb_h = self._current_metrics()
        self._grid_cols = cols
        self._tile_width = tile_w
        self._thumb_height = thumb_h

        for idx, path in enumerate(sources):
            data = MediaTileData(path=path, is_video=is_video_path(path))
            tile = MediaTile(data, tile_width=tile_w, thumb_height=thumb_h)
            tile.clicked.connect(self._on_tile_clicked)
            row, col = divmod(idx, cols)
            self._grid_layout.addWidget(tile, row, col, Qt.AlignmentFlag.AlignTop)
            self._tiles[path] = tile

        self._load_worker = CensorMediaLoadWorker(sources)
        self._load_worker.tile_ready.connect(self._on_tile_ready)
        self._load_worker.finished_all.connect(self._on_load_finished)
        self._load_worker.start()
        self._schedule_relayout()

    def _clear_tiles(self) -> None:
        for tile in self._tiles.values():
            self._grid_layout.removeWidget(tile)
            tile.deleteLater()
        self._tiles.clear()

    def _on_tile_ready(self, data: MediaTileData) -> None:
        tile = self._tiles.get(data.path)
        if tile:
            tile.apply_data(data)

    def _on_load_finished(self) -> None:
        self._update_count_label()
        self.load_finished.emit(len(self._tiles))

    def _current_metrics(self) -> tuple[int, int, int]:
        width = self._scroll.viewport().width() if self._scroll else self.width()
        return _calc_grid_metrics(width, self._grid_layout.spacing())

    def _schedule_relayout(self) -> None:
        self._relayout_timer.start(RELAYOUT_DEBOUNCE_MS)

    def _relayout_grid(self) -> None:
        if not self._tiles:
            return
        cols, tile_w, thumb_h = self._current_metrics()
        if cols == self._grid_cols and tile_w == self._tile_width and thumb_h == self._thumb_height:
            return
        self._grid_cols = cols
        self._tile_width = tile_w
        self._thumb_height = thumb_h
        for tile in self._tiles.values():
            tile.resize_tile(tile_w, thumb_h)
        for idx, path in enumerate(self._source_order):
            tile = self._tiles.get(path)
            if tile is None:
                continue
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

    def _tile_under_cursor(self) -> MediaTile | None:
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
        if not self._interaction_enabled or not self._is_host_window_active():
            if self._hover_tile is not None:
                self.stop_preview()
            return

        tile = self._tile_under_cursor()
        if tile is None:
            if self._hover_tile is not None:
                self._hover_tile = None
                self._hover_timer.stop()
                self.stop_preview()
            return

        if tile is self._hover_tile:
            if not self._active_preview_visible() and not self._hover_timer.isActive():
                self._hover_timer.start(HOVER_DELAY_MS)
            return

        previous = self._hover_tile
        self._hover_tile = tile
        self._hover_timer.stop()
        if self._active_preview_visible() and previous is not None:
            self._show_preview_for(tile)
        else:
            self._hover_timer.start(HOVER_DELAY_MS)

    def _active_preview_visible(self) -> bool:
        return self._video_preview.isVisible() or self._image_preview.isVisible()

    def _show_preview_for(self, tile: MediaTile) -> None:
        if not self._interaction_enabled or self._tile_under_cursor() is not tile:
            return
        self._video_preview.stop()
        self._image_preview.stop()
        if tile.data.is_video:
            self._video_preview.show_for_tile(tile.path, tile.data.video_probe, tile)
        else:
            self._image_preview.show_for_tile(tile.path, tile.data.image_probe, tile)

    def _start_hover_preview(self) -> None:
        tile = self._hover_tile
        if tile and self._interaction_enabled:
            self._show_preview_for(tile)

    def stop_preview(self) -> None:
        self._hover_timer.stop()
        self._hover_tile = None
        self._video_preview.stop()
        self._image_preview.stop()

    def set_interaction_enabled(self, enabled: bool) -> None:
        self._interaction_enabled = enabled
        if enabled:
            self._hover_track_timer.start()
        else:
            self._hover_track_timer.stop()
            self.stop_preview()

    def _on_tile_clicked(self, tile: MediaTile, modifiers: Qt.KeyboardModifier) -> None:
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

    def select_all(self) -> None:
        for tile in self._tiles.values():
            tile.set_selected(True)
        if self._source_order:
            self._anchor_path = self._source_order[0]
        self._update_count_label()
        self.selection_changed.emit()

    def clear_selection(self) -> None:
        for tile in self._tiles.values():
            tile.set_selected(False)
        self._anchor_path = None
        self._update_count_label()
        self.selection_changed.emit()

    def selected_paths(self) -> list[Path]:
        return [
            path
            for path in self._source_order
            if path in self._tiles and self._tiles[path].is_selected()
        ]

    def is_video(self, path: Path) -> bool:
        tile = self._tiles.get(path)
        return tile.data.is_video if tile else is_video_path(path)

    def video_probe_for(self, path: Path) -> VideoProbe | None:
        tile = self._tiles.get(path)
        return tile.data.video_probe if tile else None

    def has_media(self) -> bool:
        return bool(self._tiles)

    def _update_count_label(self) -> None:
        total = len(self._tiles)
        if total == 0:
            self.count_label.setText(tr("censor.no_media"))
            return
        selected = len(self.selected_paths())
        if selected:
            self.count_label.setText(
                tr(
                    "censor.media_count_selected",
                    videos=self._video_count,
                    images=self._image_count,
                    selected=selected,
                )
            )
        else:
            self.count_label.setText(
                tr(
                    "censor.media_count",
                    videos=self._video_count,
                    images=self._image_count,
                )
            )