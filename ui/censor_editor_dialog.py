"""Interactive censorship zone editor — lasso on video frame or image."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRect, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.censor import CensorStore, CensorZone, extract_preview_frame, is_image_path
from core.compress import probe_image
from core.ffmpeg_wrapper import VideoProbe
from core.i18n import I18n, tr

LASSO_MIN_POINTS = 3
LASSO_POINT_SPACING = 5


class CensorCanvas(QWidget):
    """Draw frame and lasso censorship zones; hold LMB to outline an area."""

    zones_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(640, 360)
        self.setMouseTracking(True)
        self.setStyleSheet("background: #111;")

        self._pixmap = QPixmap()
        self._media_w = 1
        self._media_h = 1
        self._zones: list[CensorZone] = []
        self._block_size = 16
        self._image_rect = QRect()
        self._lasso_active = False
        self._lasso_points: list[QPoint] = []

    def set_block_size(self, value: int) -> None:
        self._block_size = max(4, min(64, value))

    def set_frame(self, pixmap: QPixmap, media_w: int, media_h: int) -> None:
        self._pixmap = pixmap
        self._media_w = max(1, media_w)
        self._media_h = max(1, media_h)
        self._recalc_image_rect()
        self.update()

    def set_zones(self, zones: list[CensorZone]) -> None:
        self._zones = list(zones)
        self.update()
        self.zones_changed.emit()

    def zones(self) -> list[CensorZone]:
        return list(self._zones)

    def clear_zones(self) -> None:
        self._zones.clear()
        self.update()
        self.zones_changed.emit()

    def remove_zone(self, index: int) -> None:
        if 0 <= index < len(self._zones):
            del self._zones[index]
            self.update()
            self.zones_changed.emit()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._recalc_image_rect()

    def _recalc_image_rect(self) -> None:
        if self._pixmap.isNull():
            self._image_rect = QRect()
            return
        avail = self.rect().adjusted(8, 8, -8, -8)
        scale = min(
            avail.width() / self._media_w,
            avail.height() / self._media_h,
        )
        w = max(1, int(self._media_w * scale))
        h = max(1, int(self._media_h * scale))
        x = avail.x() + (avail.width() - w) // 2
        y = avail.y() + (avail.height() - h) // 2
        self._image_rect = QRect(x, y, w, h)

    def _widget_to_media(self, point: QPoint) -> tuple[int, int]:
        if self._image_rect.isEmpty():
            return 0, 0
        rel_x = (point.x() - self._image_rect.x()) / max(1, self._image_rect.width())
        rel_y = (point.y() - self._image_rect.y()) / max(1, self._image_rect.height())
        rel_x = max(0.0, min(1.0, rel_x))
        rel_y = max(0.0, min(1.0, rel_y))
        return int(rel_x * self._media_w), int(rel_y * self._media_h)

    def _media_point_to_widget(self, x: int, y: int) -> QPointF:
        if self._image_rect.isEmpty():
            return QPointF()
        wx = self._image_rect.x() + x / self._media_w * self._image_rect.width()
        wy = self._image_rect.y() + y / self._media_h * self._image_rect.height()
        return QPointF(wx, wy)

    def _zone_to_widget_polygon(self, zone: CensorZone) -> QPolygonF:
        if zone.is_lasso:
            return QPolygonF(
                [self._media_point_to_widget(p[0], p[1]) for p in zone.polygon]
            )
        return QPolygonF([
            self._media_point_to_widget(zone.x, zone.y),
            self._media_point_to_widget(zone.x + zone.width, zone.y),
            self._media_point_to_widget(zone.x + zone.width, zone.y + zone.height),
            self._media_point_to_widget(zone.x, zone.y + zone.height),
        ])

    def _append_lasso_point(self, point: QPoint) -> None:
        if not self._image_rect.contains(point):
            return
        if self._lasso_points:
            last = self._lasso_points[-1]
            dx = point.x() - last.x()
            dy = point.y() - last.y()
            if (dx * dx + dy * dy) < LASSO_POINT_SPACING * LASSO_POINT_SPACING:
                return
        self._lasso_points.append(point)

    def _finish_lasso(self) -> None:
        if len(self._lasso_points) < LASSO_MIN_POINTS:
            self._lasso_points.clear()
            return

        media_points = [self._widget_to_media(p) for p in self._lasso_points]
        xs = [p[0] for p in media_points]
        ys = [p[1] for p in media_points]
        left, right = min(xs), max(xs)
        top, bottom = min(ys), max(ys)
        polygon = [[p[0], p[1]] for p in media_points]
        zone = CensorZone(
            left,
            top,
            max(8, right - left + 1),
            max(8, bottom - top + 1),
            self._block_size,
            polygon,
        ).clamp(self._media_w, self._media_h)
        if zone.is_lasso:
            self._zones.append(zone)
            self.zones_changed.emit()
        self._lasso_points.clear()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#111"))

        if not self._pixmap.isNull() and not self._image_rect.isEmpty():
            scaled = self._pixmap.scaled(
                self._image_rect.size(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.drawPixmap(self._image_rect.topLeft(), scaled)

        for zone in self._zones:
            poly = self._zone_to_widget_polygon(zone)
            path = QPainterPath()
            path.addPolygon(poly)
            painter.fillPath(path, QColor(37, 99, 235, 60))
            painter.setPen(QPen(QColor(37, 99, 235), 2, Qt.PenStyle.SolidLine))
            painter.drawPath(path)

        if self._lasso_points:
            path = QPainterPath()
            path.moveTo(self._lasso_points[0])
            for point in self._lasso_points[1:]:
                path.lineTo(point)
            if len(self._lasso_points) >= LASSO_MIN_POINTS:
                path.lineTo(self._lasso_points[0])
            painter.setPen(QPen(QColor(250, 204, 21), 2, Qt.PenStyle.DashLine))
            painter.fillPath(path, QColor(250, 204, 21, 50))
            painter.drawPath(path)

    def mousePressEvent(self, event) -> None:
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._image_rect.contains(event.pos())
        ):
            self._lasso_active = True
            self._lasso_points = [event.pos()]
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if self._lasso_active:
            self._append_lasso_point(event.pos())
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._lasso_active:
            self._append_lasso_point(event.pos())
            self._finish_lasso()
            self._lasso_active = False
            self.update()


class CensorEditorDialog(QDialog):
    def __init__(
        self,
        paths: list[Path],
        *,
        video_probe_for: Callable[[Path], VideoProbe | None] | None = None,
        store: CensorStore,
        default_block_size: int = 16,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        if not paths:
            raise ValueError("CensorEditorDialog requires at least one path")
        self._all_paths = list(paths)
        self._index = 0
        self._video_probe_for = video_probe_for or (lambda _path: None)
        self.store = store
        self._time_sec = 1.0
        self.media_path = self._all_paths[0]
        self.is_image = is_image_path(self.media_path)
        self.video_probe: VideoProbe | None = None
        self._media_w = 1920
        self._media_h = 1080

        self.resize(960, 720)

        self._hint = QLabel()
        self._hint.setWordWrap(True)
        self._hint.setStyleSheet("color: #555;")

        self.canvas = CensorCanvas()
        self.canvas.set_block_size(default_block_size)
        self.canvas.zones_changed.connect(self._sync_zone_list)

        self.prev_btn = QPushButton()
        self.prev_btn.clicked.connect(self._go_prev)
        self.next_btn = QPushButton()
        self.next_btn.clicked.connect(self._go_next)
        self._nav_label = QLabel()
        self._nav_label.setStyleSheet("color: #555;")
        self._nav_row = QWidget()
        nav_layout = QHBoxLayout(self._nav_row)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self._nav_label, stretch=1, alignment=Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(self.next_btn)

        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.valueChanged.connect(self._on_time_changed)
        self.time_label = QLabel()

        self._lbl_block = QLabel()
        block_row = QHBoxLayout()
        block_row.addWidget(self._lbl_block)
        self.block_spin = QSpinBox()
        self.block_spin.setRange(4, 64)
        self.block_spin.setValue(default_block_size)
        self.block_spin.valueChanged.connect(self._on_block_changed)
        block_row.addWidget(self.block_spin)
        block_row.addStretch()

        self.zone_list = QListWidget()
        self.zone_list.setMaximumHeight(100)

        self.remove_btn = QPushButton()
        self.remove_btn.clicked.connect(self._remove_selected_zone)
        self.clear_btn = QPushButton()
        self.clear_btn.clicked.connect(self._clear_zones)
        zone_btns = QHBoxLayout()
        zone_btns.addWidget(self.remove_btn)
        zone_btns.addWidget(self.clear_btn)
        zone_btns.addStretch()

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self._save)
        self.buttons.rejected.connect(self.reject)

        self._lbl_frame = QLabel()
        self._lbl_zones = QLabel()
        self._time_row_widget = QWidget()
        time_row = QHBoxLayout(self._time_row_widget)
        time_row.setContentsMargins(0, 0, 0, 0)
        time_row.addWidget(self._lbl_frame)
        time_row.addWidget(self.time_slider, stretch=1)
        time_row.addWidget(self.time_label)

        layout = QVBoxLayout(self)
        layout.addWidget(self._hint)
        layout.addWidget(self._nav_row)
        layout.addWidget(self.canvas, stretch=1)
        layout.addWidget(self._time_row_widget)
        layout.addLayout(block_row)
        layout.addWidget(self._lbl_zones)
        layout.addWidget(self.zone_list)
        layout.addLayout(zone_btns)
        layout.addWidget(self.buttons)

        I18n.instance().language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()
        self._load_media(self._index)

    def retranslate_ui(self) -> None:
        total = len(self._all_paths)
        if total > 1:
            self.setWindowTitle(
                tr(
                    "censor.editor_title_batch",
                    name=self.media_path.name,
                    cur=self._index + 1,
                    total=total,
                )
            )
        else:
            self.setWindowTitle(tr("censor.editor_title", name=self.media_path.name))
        self._hint.setText(tr("censor.editor_hint"))
        self.prev_btn.setText(tr("censor.editor_prev"))
        self.next_btn.setText(tr("censor.editor_next"))
        self._nav_label.setText(
            tr("censor.editor_nav", cur=self._index + 1, total=total)
        )
        self._nav_row.setVisible(total > 1)
        self.prev_btn.setEnabled(self._index > 0)
        self.next_btn.setEnabled(self._index < total - 1)
        self._lbl_frame.setText(tr("censor.editor_frame"))
        self._lbl_block.setText(tr("censor.editor_block"))
        self.block_spin.setToolTip(tr("censor.editor_block_tip"))
        self._lbl_zones.setText(tr("censor.editor_zones"))
        self.remove_btn.setText(tr("censor.editor_remove"))
        self.clear_btn.setText(tr("censor.editor_clear"))
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setText(tr("common.save"))
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("common.cancel"))
        self._sync_zone_list()
        if self.is_image:
            self.time_label.setText("")
        else:
            self.time_label.setText(tr("unit.time_sec", value=self._time_sec))

    def _on_block_changed(self, value: int) -> None:
        self.canvas.set_block_size(value)

    def _on_time_changed(self, value: int) -> None:
        self._time_sec = value / 10.0
        self._load_frame()

    def _go_prev(self) -> None:
        if self._index > 0:
            self._switch_media(self._index - 1)

    def _go_next(self) -> None:
        if self._index < len(self._all_paths) - 1:
            self._switch_media(self._index + 1)

    def _switch_media(self, index: int) -> None:
        if index == self._index:
            return
        self._persist_current(require_zones=False)
        self._load_media(index)

    def _persist_current(self, *, require_zones: bool) -> bool:
        zones = self.canvas.zones()
        if not zones:
            if require_zones:
                QMessageBox.warning(
                    self,
                    tr("common.content_suite"),
                    tr("censor.editor_need_zone"),
                )
                return False
            return True
        self.store.set_zones(self.media_path, zones)
        return True

    def _load_media(self, index: int) -> None:
        self._index = index
        self.media_path = self._all_paths[index]
        self.is_image = is_image_path(self.media_path)
        self.video_probe = (
            None if self.is_image else self._video_probe_for(self.media_path)
        )

        if self.is_image:
            try:
                image_probe = probe_image(self.media_path)
                self._media_w, self._media_h = image_probe.width, image_probe.height
            except OSError:
                self._media_w, self._media_h = 1920, 1080
            duration = 0.0
        else:
            probe = self.video_probe
            self._media_w = probe.width if probe else 1920
            self._media_h = probe.height if probe else 1080
            duration = probe.duration if probe else 10.0

        self.time_slider.blockSignals(True)
        self.time_slider.setRange(0, max(1, int(duration * 10)))
        self.time_slider.setValue(min(int(self._time_sec * 10), self.time_slider.maximum()))
        self.time_slider.blockSignals(False)
        self._time_row_widget.setVisible(not self.is_image)

        self.canvas.set_zones(self.store.get_zones(self.media_path))
        self._sync_zone_list()
        self.retranslate_ui()
        self._load_frame()

    def _load_frame(self) -> None:
        try:
            if self.is_image:
                pix = QPixmap(str(self.media_path))
            else:
                frame_path = extract_preview_frame(self.media_path, self._time_sec)
                pix = QPixmap(str(frame_path))
            self.canvas.set_frame(pix, self._media_w, self._media_h)
            if not self.is_image:
                self.time_label.setText(tr("unit.time_sec", value=self._time_sec))
        except Exception as exc:
            QMessageBox.warning(
                self,
                tr("common.content_suite"),
                tr("censor.editor_frame_fail", error=exc),
            )

    def _sync_zone_list(self) -> None:
        self.zone_list.blockSignals(True)
        self.zone_list.clear()
        for i, zone in enumerate(self.canvas.zones(), start=1):
            if zone.is_lasso:
                text = tr(
                    "censor.zone_item_lasso",
                    n=i,
                    points=len(zone.polygon),
                    block=zone.block_size,
                )
            else:
                text = tr(
                    "censor.zone_item",
                    n=i,
                    w=zone.width,
                    h=zone.height,
                    x=zone.x,
                    y=zone.y,
                    block=zone.block_size,
                )
            self.zone_list.addItem(QListWidgetItem(text))
        self.zone_list.blockSignals(False)

    def _remove_selected_zone(self) -> None:
        row = self.zone_list.currentRow()
        if row >= 0:
            self.canvas.remove_zone(row)
            self._sync_zone_list()

    def _clear_zones(self) -> None:
        if not self.canvas.zones():
            return
        if QMessageBox.question(
            self,
            tr("common.content_suite"),
            tr("censor.editor_clear_confirm"),
        ) != QMessageBox.StandardButton.Yes:
            return
        self.canvas.clear_zones()
        self._sync_zone_list()

    def _save(self) -> None:
        if not self._persist_current(require_zones=True):
            return
        self.accept()