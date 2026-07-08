"""Interactive censorship zone editor on a video frame."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
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

from core.censor import CensorStore, CensorZone, extract_preview_frame
from core.ffmpeg_wrapper import VideoProbe
from core.i18n import I18n, tr


class CensorCanvas(QWidget):
    """Draw video frame and censorship zones; drag to add a new zone."""

    zones_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(640, 360)
        self.setMouseTracking(True)
        self.setStyleSheet("background: #111;")

        self._pixmap = QPixmap()
        self._video_w = 1
        self._video_h = 1
        self._zones: list[CensorZone] = []
        self._block_size = 16
        self._image_rect = QRect()
        self._drag_start: QPoint | None = None
        self._drag_end: QPoint | None = None

    def set_block_size(self, value: int) -> None:
        self._block_size = max(4, min(64, value))

    def set_frame(self, pixmap: QPixmap, video_w: int, video_h: int) -> None:
        self._pixmap = pixmap
        self._video_w = max(1, video_w)
        self._video_h = max(1, video_h)
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
            avail.width() / self._video_w,
            avail.height() / self._video_h,
        )
        w = max(1, int(self._video_w * scale))
        h = max(1, int(self._video_h * scale))
        x = avail.x() + (avail.width() - w) // 2
        y = avail.y() + (avail.height() - h) // 2
        self._image_rect = QRect(x, y, w, h)

    def _widget_to_video(self, point: QPoint) -> tuple[int, int]:
        if self._image_rect.isEmpty():
            return 0, 0
        rel_x = (point.x() - self._image_rect.x()) / max(1, self._image_rect.width())
        rel_y = (point.y() - self._image_rect.y()) / max(1, self._image_rect.height())
        rel_x = max(0.0, min(1.0, rel_x))
        rel_y = max(0.0, min(1.0, rel_y))
        return int(rel_x * self._video_w), int(rel_y * self._video_h)

    def _video_rect_to_widget(self, zone: CensorZone) -> QRect:
        if self._image_rect.isEmpty():
            return QRect()
        x = self._image_rect.x() + int(
            zone.x / self._video_w * self._image_rect.width()
        )
        y = self._image_rect.y() + int(
            zone.y / self._video_h * self._image_rect.height()
        )
        w = max(2, int(zone.width / self._video_w * self._image_rect.width()))
        h = max(2, int(zone.height / self._video_h * self._image_rect.height()))
        return QRect(x, y, w, h)

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

        pen = QPen(QColor(37, 99, 235), 2, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        for zone in self._zones:
            rect = self._video_rect_to_widget(zone)
            painter.fillRect(rect, QColor(37, 99, 235, 60))
            painter.drawRect(rect)

        if self._drag_start and self._drag_end:
            rect = QRect(self._drag_start, self._drag_end).normalized()
            painter.setPen(QPen(QColor(250, 204, 21), 2, Qt.PenStyle.DashLine))
            painter.fillRect(rect, QColor(250, 204, 21, 50))
            painter.drawRect(rect)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._image_rect.contains(
            event.pos()
        ):
            self._drag_start = event.pos()
            self._drag_end = event.pos()
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_start is not None:
            self._drag_end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._drag_start is not None
            and self._drag_end is not None
        ):
            x1, y1 = self._widget_to_video(self._drag_start)
            x2, y2 = self._widget_to_video(self._drag_end)
            left, right = sorted((x1, x2))
            top, bottom = sorted((y1, y2))
            zone = CensorZone(
                left,
                top,
                max(8, right - left),
                max(8, bottom - top),
                self._block_size,
            ).clamp(self._video_w, self._video_h)
            if zone.width >= 8 and zone.height >= 8:
                self._zones.append(zone)
                self.zones_changed.emit()
        self._drag_start = None
        self._drag_end = None
        self.update()


class CensorEditorDialog(QDialog):
    def __init__(
        self,
        video_path: Path,
        probe: VideoProbe | None,
        store: CensorStore,
        default_block_size: int = 16,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.video_path = video_path
        self.probe = probe
        self.store = store
        self._time_sec = 1.0

        self.resize(960, 720)

        video_w = probe.width if probe else 1920
        video_h = probe.height if probe else 1080
        duration = probe.duration if probe else 10.0

        self._hint = QLabel()
        self._hint.setWordWrap(True)
        self._hint.setStyleSheet("color: #555;")

        self.canvas = CensorCanvas()
        self.canvas.set_block_size(default_block_size)
        self.canvas.set_zones(store.get_zones(video_path))
        self.canvas.zones_changed.connect(self._sync_zone_list)

        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setRange(0, max(1, int(duration * 10)))
        self.time_slider.setValue(min(int(self._time_sec * 10), self.time_slider.maximum()))
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
        self.zone_list.currentRowChanged.connect(self._on_zone_selected)

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

        layout = QVBoxLayout(self)
        layout.addWidget(self._hint)
        layout.addWidget(self.canvas, stretch=1)
        time_row = QHBoxLayout()
        time_row.addWidget(self._lbl_frame)
        time_row.addWidget(self.time_slider, stretch=1)
        time_row.addWidget(self.time_label)
        layout.addLayout(time_row)
        layout.addLayout(block_row)
        layout.addWidget(self._lbl_zones)
        layout.addWidget(self.zone_list)
        layout.addLayout(zone_btns)
        layout.addWidget(self.buttons)

        self._video_w = video_w
        self._video_h = video_h

        I18n.instance().language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()
        self._load_frame()

    def retranslate_ui(self) -> None:
        self.setWindowTitle(tr("censor.editor_title", name=self.video_path.name))
        self._hint.setText(tr("censor.editor_hint"))
        self._lbl_frame.setText(tr("censor.editor_frame"))
        self._lbl_block.setText(tr("censor.editor_block"))
        self.block_spin.setToolTip(tr("censor.editor_block_tip"))
        self._lbl_zones.setText(tr("censor.editor_zones"))
        self.remove_btn.setText(tr("censor.editor_remove"))
        self.clear_btn.setText(tr("censor.editor_clear"))
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setText(tr("common.save"))
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("common.cancel"))
        self._sync_zone_list()
        self.time_label.setText(f"{self._time_sec:.1f} с")

    def _on_block_changed(self, value: int) -> None:
        self.canvas.set_block_size(value)

    def _on_time_changed(self, value: int) -> None:
        self._time_sec = value / 10.0
        self._load_frame()

    def _load_frame(self) -> None:
        try:
            frame_path = extract_preview_frame(self.video_path, self._time_sec)
            pix = QPixmap(str(frame_path))
            self.canvas.set_frame(pix, self._video_w, self._video_h)
            self.time_label.setText(f"{self._time_sec:.1f} с")
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
            item = QListWidgetItem(
                tr(
                    "censor.zone_item",
                    n=i,
                    w=zone.width,
                    h=zone.height,
                    x=zone.x,
                    y=zone.y,
                    block=zone.block_size,
                )
            )
            self.zone_list.addItem(item)
        self.zone_list.blockSignals(False)

    def _on_zone_selected(self, row: int) -> None:
        pass

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
        zones = self.canvas.zones()
        if not zones:
            QMessageBox.warning(
                self,
                tr("common.content_suite"),
                tr("censor.editor_need_zone"),
            )
            return
        self.store.set_zones(self.video_path, zones)
        self.accept()