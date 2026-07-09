"""Art checker tile grid — same UX as ImageGrid with OK/MISS status."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QEvent, QPoint, QRect, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QCursor, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
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
from core.art_checker import ArtRow
from core.compress import (
    ImageProbe,
    extract_image_thumbnail,
    format_file_size,
    image_thumbnail_cache_path,
    probe_image,
)
from core.i18n import I18n, tr
from ui.tile_style import apply_tile_selection_style
from ui.image_grid import (
    HOVER_DELAY_MS,
    HOVER_TRACK_MS,
    ImageHoverPreviewPopup,
    RELAYOUT_DEBOUNCE_MS,
    TILE_MAX_WIDTH,
    TILE_MIN_WIDTH,
    _calc_grid_metrics,
    _elide,
)


@dataclass(frozen=True)
class ArtGridItem:
    row: ArtRow
    image_paths: tuple[Path, ...] = ()


class ArtThumbLoadWorker(QThread):
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
                get_logger().warning("Art thumb failed for %s: %s", path.name, exc)
            self.image_ready.emit(path, probe, thumb_path)
        self.finished_all.emit()


class VariantStackBadge(QFrame):
    """Small stacked-pages indicator for multi-file arts."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setFixedSize(46, 40)
        self.setStyleSheet("background: transparent;")

        self._back = QFrame(self)
        self._back.setGeometry(10, 2, 24, 18)
        self._back.setStyleSheet(
            "background: #e2e8f0; border: 1px solid #94a3b8; border-radius: 3px;"
        )
        self._mid = QFrame(self)
        self._mid.setGeometry(6, 6, 24, 18)
        self._mid.setStyleSheet(
            "background: #f8fafc; border: 1px solid #64748b; border-radius: 3px;"
        )
        self._front = QFrame(self)
        self._front.setGeometry(2, 10, 24, 18)
        self._front.setStyleSheet(
            "background: white; border: 1px solid #334155; border-radius: 3px;"
        )
        self._count = QLabel(self)
        self._count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._count.setStyleSheet(
            "color: white; background: rgba(15, 23, 42, 0.88); "
            "font-size: 9px; font-weight: bold; border-radius: 6px; padding: 1px 4px;"
        )
        self._count.setGeometry(0, 24, 46, 14)

    def set_variant(self, current: int, total: int) -> None:
        self._count.setText(f"{current}/{total}")


class ArtTile(QFrame):
    clicked = Signal(object, object)
    double_clicked = Signal(object)
    hover_enter = Signal(object)
    hover_leave = Signal(object)
    variant_changed = Signal(object)

    def __init__(
        self,
        item: ArtGridItem,
        *,
        tile_width: int = TILE_MIN_WIDTH,
        thumb_height: int = 148,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.item = item
        self._file_paths: list[Path] = list(item.image_paths)
        self._file_index = 0
        self._variant_cache: dict[Path, tuple[ImageProbe | None, str]] = {}
        self.probe: ImageProbe | None = None
        self._selected = False
        self._thumb_path = ""
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
        thumb_layout.addWidget(self.thumb_label)

        self.status_badge = QLabel(self.thumb_wrap)
        self.status_badge.adjustSize()

        self.check_badge = QLabel("✓", self.thumb_wrap)
        self.check_badge.setStyleSheet(
            "background: #2563eb; color: white; font-weight: bold; "
            "padding: 2px 8px; border-radius: 10px; font-size: 11px;"
        )
        self.check_badge.hide()
        self.check_badge.adjustSize()

        self.stack_badge = VariantStackBadge(self.thumb_wrap)
        self.stack_badge.hide()

        self.name_label = QLabel()
        self.name_label.setStyleSheet("font-size: 11px;")

        self.meta_label = QLabel()
        self.meta_label.setStyleSheet("font-size: 10px;")

        root.addWidget(self.thumb_wrap)
        root.addWidget(self.name_label)
        root.addWidget(self.meta_label)

        self._apply_status_badge()
        self._update_stack_badge()
        if not self._file_paths:
            self._show_missing_placeholder()
        else:
            self.thumb_label.setText("…")
            self._set_meta_loading()
        self._refresh_name_label()
        self._apply_style()

    def _display_filename(self) -> str:
        if self.path is not None:
            return self.path.name
        expected = self.item.row.expected_path
        if expected:
            return Path(expected).name
        return self.item.row.name

    def _refresh_name_label(self) -> None:
        filename = self._display_filename()
        self.name_label.setText(_elide(filename, self._tile_width - 8))
        self.name_label.setToolTip(filename)

    @property
    def path(self) -> Path | None:
        if not self._file_paths:
            return None
        return self._file_paths[self._file_index]

    def variant_count(self) -> int:
        return len(self._file_paths)

    def _apply_status_badge(self) -> None:
        if self.item.row.status == "present":
            self.status_badge.setText(tr("art_checker.status_present"))
            self.status_badge.setStyleSheet(
                "background: #15803d; color: white; font-weight: bold; "
                "padding: 2px 8px; border-radius: 10px; font-size: 11px;"
            )
        else:
            self.status_badge.setText(tr("art_checker.status_missing"))
            self.status_badge.setStyleSheet(
                "background: #b91c1c; color: white; font-weight: bold; "
                "padding: 2px 8px; border-radius: 10px; font-size: 11px;"
            )
        self.status_badge.adjustSize()
        self.status_badge.move(
            self.thumb_wrap.width() - self.status_badge.width() - 6,
            6,
        )

    def _update_stack_badge(self) -> None:
        count = len(self._file_paths)
        if count <= 1:
            self.stack_badge.hide()
            return
        self.stack_badge.show()
        self.stack_badge.set_variant(self._file_index + 1, count)
        self.stack_badge.move(6, self.thumb_wrap.height() - self.stack_badge.height() - 6)
        tip = tr(
            "art_checker.variants_wheel",
            count=count,
            current=self._file_index + 1,
        )
        self.stack_badge.setToolTip(tip)
        self.thumb_wrap.setToolTip(tip)

    def _show_missing_placeholder(self) -> None:
        self._meta_state = "missing"
        self.thumb_label.setPixmap(QPixmap())
        self.thumb_label.setText(tr("art_checker.tile_missing"))
        self.thumb_label.setStyleSheet(
            "color: #fca5a5; font-size: 13px; font-weight: bold; border-radius: 8px;"
        )
        section = self.item.row.section or "—"
        self.meta_label.setText(f"{section} · {tr('art_checker.status_missing')}")
        self.setToolTip(
            tr(
                "art_checker.preview_missing",
                name=self.item.row.name,
                path=self.item.row.expected_path,
            )
        )

    def _set_meta_loading(self) -> None:
        self._meta_state = "loading"
        section = self.item.row.section or "—"
        self.meta_label.setText(f"{section} · {tr('grid.loading')}")

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.check_badge.setVisible(selected)
        self._apply_style()

    def is_selected(self) -> bool:
        return self._selected

    def set_probe(self, probe: ImageProbe | None) -> None:
        self.probe = probe
        section = self.item.row.section or "—"
        if probe:
            self._meta_state = "ok"
            variant_note = ""
            if len(self._file_paths) > 1:
                variant_note = f" · {self._file_index + 1}/{len(self._file_paths)}"
            self.meta_label.setText(
                f"{section}{variant_note} · {probe.width}×{probe.height} · "
                f"{format_file_size(probe.size_bytes)}"
            )
            tip = probe.summary
            if len(self._file_paths) > 1:
                tip = (
                    f"{tip}\n"
                    + tr(
                        "art_checker.variants_wheel",
                        count=len(self._file_paths),
                        current=self._file_index + 1,
                    )
                )
            self.setToolTip(tip)
        else:
            self._meta_state = "failed"
            self.meta_label.setText(f"{section} · {tr('grid.read_failed')}")
            self.setToolTip(self.item.row.name)

    def apply_variant_cache(
        self,
        path: Path,
        probe: ImageProbe | None,
        thumb_path: str,
    ) -> None:
        self._variant_cache[path] = (probe, thumb_path)
        if self.path == path:
            self.set_probe(probe)
            self.set_thumbnail(thumb_path)

    def _apply_current_variant(self) -> None:
        path = self.path
        if path is None:
            return
        if path in self._variant_cache:
            probe, thumb = self._variant_cache[path]
            self.set_probe(probe)
            self.set_thumbnail(thumb)
        else:
            self.probe = None
            self._thumb_path = ""
            self.thumb_label.setPixmap(QPixmap())
            self.thumb_label.setText("…")
            self._set_meta_loading()
        self._update_stack_badge()
        self._refresh_name_label()

    def cycle_variant(self, step: int) -> bool:
        count = len(self._file_paths)
        if count <= 1:
            return False
        self._file_index = (self._file_index + step) % count
        self._apply_current_variant()
        self.variant_changed.emit(self)
        return True

    def retranslate_meta(self) -> None:
        if not self._file_paths:
            self._show_missing_placeholder()
            return
        if self._meta_state == "loading":
            self._set_meta_loading()
        elif self._meta_state == "failed":
            section = self.item.row.section or "—"
            self.meta_label.setText(f"{section} · {tr('grid.read_failed')}")
        elif self.probe:
            self.set_probe(self.probe)
        self._apply_status_badge()
        self._update_stack_badge()

    def set_thumbnail(self, thumb_path: str) -> None:
        self._thumb_path = thumb_path
        if not thumb_path:
            self.thumb_label.setText("🖼")
            return
        pixmap = QPixmap(thumb_path)
        if pixmap.isNull():
            self.thumb_label.setText("🖼")
            return
        scaled = pixmap.scaled(
            self._tile_width,
            self._thumb_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.thumb_label.setPixmap(scaled)
        self.thumb_label.setText("")
        self.thumb_label.setStyleSheet("color: #666; border-radius: 8px;")

    def resize_tile(self, tile_width: int, thumb_height: int) -> None:
        self._tile_width = tile_width
        self._thumb_height = thumb_height
        self.setFixedWidth(tile_width)
        self.thumb_wrap.setFixedSize(tile_width, thumb_height)
        self.thumb_label.setFixedSize(tile_width, thumb_height)
        self._refresh_name_label()
        if self._thumb_path:
            self.set_thumbnail(self._thumb_path)
        self._apply_status_badge()
        self._update_stack_badge()
        self._apply_style()

    def _apply_style(self) -> None:
        apply_tile_selection_style(
            self,
            selected=self._selected,
            name_label=self.name_label,
            meta_label=self.meta_label,
            class_name="ArtTile",
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

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self)
        super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event) -> None:
        if len(self._file_paths) <= 1:
            event.ignore()
            return
        delta = event.angleDelta().y()
        if delta == 0:
            event.ignore()
            return
        step = 1 if delta < 0 else -1
        if self.cycle_variant(step):
            event.accept()
            return
        event.ignore()


class ArtCheckerGrid(QWidget):
    selection_changed = Signal()
    copy_requested = Signal(object)
    load_finished = Signal(int)
    filter_changed = Signal()
    sort_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tiles: dict[int, ArtTile] = {}
        self._order: list[int] = []
        self._items: dict[int, ArtGridItem] = {}
        self._anchor_index: int | None = None
        self._load_worker: ArtThumbLoadWorker | None = None
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
        self._hover_tile: ArtTile | None = None

        self._hover_track_timer = QTimer(self)
        self._hover_track_timer.setInterval(HOVER_TRACK_MS)
        self._hover_track_timer.timeout.connect(self._update_hover_from_cursor)

        self._preview = ImageHoverPreviewPopup()

        toolbar = QHBoxLayout()
        self.select_all_btn = QPushButton()
        self.select_all_btn.clicked.connect(self.select_all)
        self.clear_sel_btn = QPushButton()
        self.clear_sel_btn.clicked.connect(self.clear_selection)

        self._lbl_filter = QLabel()
        self.filter_combo = QComboBox()
        self.filter_combo.setMinimumWidth(120)
        for key in ("all", "missing", "present", "sfw", "nsfw", "sex"):
            self.filter_combo.addItem("", key)
        self.filter_combo.currentIndexChanged.connect(self._emit_filter_changed)

        self._lbl_sort = QLabel()
        self.sort_combo = QComboBox()
        self.sort_combo.setMinimumWidth(130)
        for key in ("name", "date", "missing_first"):
            self.sort_combo.addItem("", key)
        self.sort_combo.currentIndexChanged.connect(self._emit_sort_changed)

        self.count_label = QLabel()
        self.count_label.setStyleSheet("color: #666;")
        toolbar.addWidget(self.select_all_btn)
        toolbar.addWidget(self.clear_sel_btn)
        toolbar.addStretch()
        toolbar.addWidget(self._lbl_filter)
        toolbar.addWidget(self.filter_combo)
        toolbar.addWidget(self._lbl_sort)
        toolbar.addWidget(self.sort_combo)
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
        self._scroll.setMinimumHeight(240)
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

    def _emit_filter_changed(self) -> None:
        self.filter_changed.emit()

    def _emit_sort_changed(self) -> None:
        self.sort_changed.emit()

    def filter_mode(self) -> str:
        return self.filter_combo.currentData() or "all"

    def sort_mode(self) -> str:
        return self.sort_combo.currentData() or "name"

    def set_filter_mode(self, mode: str) -> None:
        idx = self.filter_combo.findData(mode)
        if idx >= 0:
            self.filter_combo.setCurrentIndex(idx)

    def set_sort_mode(self, mode: str) -> None:
        idx = self.sort_combo.findData(mode)
        if idx >= 0:
            self.sort_combo.setCurrentIndex(idx)

    def retranslate_ui(self) -> None:
        self.select_all_btn.setText(tr("grid.select_all"))
        self.clear_sel_btn.setText(tr("grid.clear_selection"))
        self._lbl_filter.setText(tr("art_checker.filter"))
        self._lbl_sort.setText(tr("art_checker.sort"))
        for index, key in enumerate(("all", "missing", "present", "sfw", "nsfw", "sex")):
            self.filter_combo.setItemText(index, tr(f"art_checker.filter_{key}"))
        for index, key in enumerate(("name", "date", "missing_first")):
            self.sort_combo.setItemText(index, tr(f"art_checker.sort_{key}"))
        self._hint_label.setText(tr("art_checker.grid_hint"))
        self._preview.retranslate_ui()
        for tile in self._tiles.values():
            tile.retranslate_meta()
        self._update_count_label()

    def _is_host_window_active(self) -> bool:
        host = self.window()
        return host is not None and host.isActiveWindow()

    def _on_app_focus_changed(self, _old: QWidget | None, _new: QWidget | None) -> None:
        if not self._is_host_window_active():
            self.stop_preview()

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
        for idx, key in enumerate(self._order):
            tile = self._tiles.get(key)
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

    def _tile_under_cursor(self) -> ArtTile | None:
        pos = QCursor.pos()
        for key in self._order:
            tile = self._tiles.get(key)
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
        if tile is None or tile.path is None:
            if self._hover_tile is not None or self._preview.isVisible():
                self._hover_tile = None
                self._hover_timer.stop()
                self._preview.stop()
            return

        if tile is self._hover_tile:
            if not self._preview.isVisible() and not self._hover_timer.isActive():
                self._hover_timer.start(HOVER_DELAY_MS)
            return

        previous = self._hover_tile
        self._hover_tile = tile
        self._hover_timer.stop()
        if self._preview.isVisible() and previous is not None:
            self._show_preview_for(tile)
        else:
            self._hover_timer.start(HOVER_DELAY_MS)

    def _show_preview_for(self, tile: ArtTile) -> None:
        if not self._interaction_enabled or tile.path is None:
            return
        if self._tile_under_cursor() is not tile:
            return
        self._preview.show_for_tile(tile.path, tile.probe, tile)

    def set_items(self, items: list[ArtGridItem]) -> None:
        self.stop_preview()
        if self._load_worker and self._load_worker.isRunning():
            self._load_worker.requestInterruption()
            self._load_worker.wait(2000)

        self._clear_tiles()
        self._order = [item.row.index for item in items]
        self._items = {item.row.index: item for item in items}
        self._anchor_index = None

        if not items:
            self._update_count_label()
            self.load_finished.emit(0)
            return

        cols, tile_w, thumb_h = self._current_metrics()
        self._grid_cols = cols
        self._tile_width = tile_w
        self._thumb_height = thumb_h

        load_paths: list[Path] = []
        for idx, item in enumerate(items):
            tile = ArtTile(item, tile_width=tile_w, thumb_height=thumb_h)
            tile.clicked.connect(self._on_tile_clicked)
            tile.double_clicked.connect(self._on_tile_double_clicked)
            tile.variant_changed.connect(self._on_tile_variant_changed)
            row, col = divmod(idx, cols)
            self._grid_layout.addWidget(tile, row, col, Qt.AlignmentFlag.AlignTop)
            self._tiles[item.row.index] = tile
            for image_path in item.image_paths:
                if image_path not in load_paths:
                    load_paths.append(image_path)

        if load_paths:
            self._load_worker = ArtThumbLoadWorker(load_paths)
            self._load_worker.image_ready.connect(self._on_image_ready)
            self._load_worker.finished_all.connect(self._on_load_finished)
            self._load_worker.start()
        else:
            self._on_load_finished()

        self._schedule_relayout()
        self._update_count_label()

    def _path_to_index(self, path: Path) -> int | None:
        for index, item in self._items.items():
            if path in item.image_paths:
                return index
        return None

    def _on_image_ready(self, path: Path, probe: ImageProbe | None, thumb_path: str) -> None:
        index = self._path_to_index(path)
        if index is None:
            return
        tile = self._tiles.get(index)
        if tile is None:
            return
        tile.apply_variant_cache(path, probe, thumb_path)

    def _on_tile_variant_changed(self, tile: ArtTile) -> None:
        if self._hover_tile is tile and tile.path is not None:
            self._preview.show_for_tile(tile.path, tile.probe, tile)

    def _on_load_finished(self) -> None:
        self._update_count_label()
        self.load_finished.emit(len(self._tiles))

    def _clear_tiles(self) -> None:
        for tile in self._tiles.values():
            self._grid_layout.removeWidget(tile)
            tile.deleteLater()
        self._tiles.clear()
        self._items.clear()
        self._order.clear()

    def _on_tile_clicked(self, tile: ArtTile, modifiers: Qt.KeyboardModifier) -> None:
        if not self._interaction_enabled:
            return
        mods = Qt.KeyboardModifiers(modifiers)
        key = tile.item.row.index
        if mods & Qt.KeyboardModifier.ShiftModifier and self._anchor_index is not None:
            self._select_range(self._anchor_index, key)
        elif mods & Qt.KeyboardModifier.ControlModifier:
            tile.set_selected(not tile.is_selected())
            self._anchor_index = key
        else:
            for other in self._tiles.values():
                other.set_selected(other is tile)
            self._anchor_index = key
        self._update_count_label()
        self.selection_changed.emit()

    def _on_tile_double_clicked(self, tile: ArtTile) -> None:
        self.copy_requested.emit(tile.item.row)

    def _select_range(self, anchor: int, target: int) -> None:
        try:
            start = self._order.index(anchor)
            end = self._order.index(target)
        except ValueError:
            self._tiles[target].set_selected(True)
            return
        lo, hi = sorted((start, end))
        for key in self._order[lo : hi + 1]:
            self._tiles[key].set_selected(True)

    def _start_hover_preview(self) -> None:
        tile = self._hover_tile
        if tile is None or tile.path is None:
            return
        self._show_preview_for(tile)

    def stop_preview(self) -> None:
        self._hover_timer.stop()
        self._hover_tile = None
        self._preview.stop()

    def select_all(self) -> None:
        for tile in self._tiles.values():
            tile.set_selected(True)
        if self._order:
            self._anchor_index = self._order[0]
        self._update_count_label()
        self.selection_changed.emit()

    def clear_selection(self) -> None:
        for tile in self._tiles.values():
            tile.set_selected(False)
        self._anchor_index = None
        self._update_count_label()
        self.selection_changed.emit()

    def selected_rows(self) -> list[ArtRow]:
        return [
            self._items[key].row
            for key in self._order
            if key in self._tiles and self._tiles[key].is_selected()
        ]

    def selected_row(self) -> ArtRow | None:
        rows = self.selected_rows()
        return rows[0] if rows else None

    def has_items(self) -> bool:
        return bool(self._tiles)

    def _update_count_label(self) -> None:
        count = len(self._tiles)
        if count == 0:
            self.count_label.setText(tr("art_checker.grid_empty"))
            return
        present = sum(1 for item in self._items.values() if item.row.status == "present")
        missing = count - present
        selected = len(self.selected_rows())
        if selected:
            self.count_label.setText(
                tr(
                    "art_checker.grid_count_selected",
                    count=count,
                    present=present,
                    missing=missing,
                    selected=selected,
                )
            )
        else:
            self.count_label.setText(
                tr(
                    "art_checker.grid_count",
                    count=count,
                    present=present,
                    missing=missing,
                )
            )