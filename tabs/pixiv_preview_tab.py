from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QColor
from PIL.ImageQt import ImageQt

from core.config_store import ConfigStore
from core.i18n import I18n, tr
from core.pixiv_preview import (
    color_to_hex,
    compose_cover,
    layout_label,
    layout_options_for_count,
    parse_color,
)
from ui.folder_picker import FolderPicker

_PATH_ROLE = Qt.ItemDataRole.UserRole


class PixivPreviewTab(QWidget):
    def __init__(self, config: ConfigStore, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._refresh_preview)

        root = QVBoxLayout(self)

        self._files_group = QGroupBox()
        files_layout = QVBoxLayout(self._files_group)

        self.file_list = QListWidget()
        self.file_list.itemSelectionChanged.connect(self._schedule_preview)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton()
        self.remove_btn = QPushButton()
        self.up_btn = QPushButton("↑")
        self.down_btn = QPushButton("↓")
        self.add_btn.clicked.connect(self._add_images)
        self.remove_btn.clicked.connect(self._remove_selected)
        self.up_btn.clicked.connect(self._move_up)
        self.down_btn.clicked.connect(self._move_down)
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.remove_btn)
        btn_row.addWidget(self.up_btn)
        btn_row.addWidget(self.down_btn)
        btn_row.addStretch()

        files_layout.addWidget(self.file_list)
        files_layout.addLayout(btn_row)

        self._settings_group = QGroupBox()
        form = QFormLayout(self._settings_group)

        self.layout_combo = QComboBox()
        self.layout_combo.currentIndexChanged.connect(self._on_layout_changed)

        self.canvas_spin = QSpinBox()
        self.canvas_spin.setRange(800, 2000)
        self.canvas_spin.setSingleStep(100)
        self.canvas_spin.setValue(int(config.get("pixiv_canvas_size", 1200)))
        self.canvas_spin.valueChanged.connect(self._on_setting_changed)

        self.padding_spin = QSpinBox()
        self.padding_spin.setRange(0, 120)
        self.padding_spin.setValue(int(config.get("pixiv_padding", 24)))
        self.padding_spin.valueChanged.connect(self._on_setting_changed)

        self.gap_spin = QSpinBox()
        self.gap_spin.setRange(0, 80)
        self.gap_spin.setValue(int(config.get("pixiv_gap", 16)))
        self.gap_spin.valueChanged.connect(self._on_setting_changed)

        self._lbl_template = QLabel()
        self._lbl_canvas = QLabel()
        self._lbl_padding = QLabel()
        self._lbl_gap = QLabel()

        form.addRow(self._lbl_template, self.layout_combo)
        form.addRow(self._lbl_canvas, self.canvas_spin)
        form.addRow(self._lbl_padding, self.padding_spin)
        form.addRow(self._lbl_gap, self.gap_spin)

        self.crop_check = QCheckBox()
        self.crop_check.setChecked(bool(config.get("pixiv_crop_fill", True)))
        self.crop_check.toggled.connect(self._on_crop_changed)

        self.frame_width_spin = QSpinBox()
        self.frame_width_spin.setRange(0, 24)
        self.frame_width_spin.setValue(int(config.get("pixiv_frame_width", 4)))
        self.frame_width_spin.valueChanged.connect(self._on_frame_setting_changed)

        self._frame_color = parse_color(config.get("pixiv_frame_color", "#2d2d2d"))
        self.frame_color_btn = QPushButton()
        self.frame_color_btn.clicked.connect(self._pick_frame_color)
        self.frame_color_swatch = QLabel()
        self.frame_color_swatch.setFixedSize(28, 28)
        self._update_frame_swatch()

        self._lbl_frame_px = QLabel()
        self._lbl_frame_color = QLabel()

        frame_row = QHBoxLayout()
        frame_row.addWidget(self.frame_color_swatch)
        frame_row.addWidget(self.frame_color_btn)
        frame_row.addStretch()

        form.addRow("", self.crop_check)
        form.addRow(self._lbl_frame_px, self.frame_width_spin)
        form.addRow(self._lbl_frame_color, frame_row)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(320)
        self.preview_label.setStyleSheet(
            "QLabel { background: #f0f0f0; border: 1px solid #ccc; }"
        )

        self._export_group = QGroupBox()
        export_layout = QFormLayout(self._export_group)

        self.output_picker = FolderPicker("pixiv.output")
        self.output_picker.set_path(config.folder("pixiv_output_folder"))
        self.output_picker.path_changed.connect(
            lambda p: config.set("pixiv_output_folder", p)
        )

        self.name_edit = QLineEdit(config.get("pixiv_cover_name", "pixiv_cover"))
        self.name_edit.textChanged.connect(
            lambda t: config.set("pixiv_cover_name", t)
        )

        self._lbl_filename = QLabel()

        export_layout.addRow(self.output_picker)
        export_layout.addRow(self._lbl_filename, self.name_edit)

        self.export_btn = QPushButton()
        self.export_btn.clicked.connect(self._export_cover)
        self.export_btn.setEnabled(False)

        self._hint_label = QLabel()
        self._hint_label.setWordWrap(True)
        self._hint_label.setStyleSheet("color: #666;")

        root.addWidget(self._files_group)
        root.addWidget(self._settings_group)
        root.addWidget(self.status_label)
        root.addWidget(self.preview_label, stretch=1)
        root.addWidget(self._export_group)
        root.addWidget(self.export_btn)
        root.addWidget(self._hint_label)

        I18n.instance().language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        self._files_group.setTitle(tr("pixiv.files_group"))
        self.add_btn.setText(tr("common.add"))
        self.remove_btn.setText(tr("common.remove"))

        self._settings_group.setTitle(tr("pixiv.layout_group"))
        self._lbl_template.setText(tr("pixiv.template"))
        self._lbl_canvas.setText(tr("pixiv.canvas"))
        self._lbl_padding.setText(tr("pixiv.padding"))
        self._lbl_gap.setText(tr("pixiv.gap"))
        self.crop_check.setText(tr("pixiv.crop_fill"))
        self._lbl_frame_px.setText(tr("pixiv.frame_px"))
        self._lbl_frame_color.setText(tr("pixiv.frame_color"))
        self.frame_color_btn.setText(tr("pixiv.pick_color"))

        self._export_group.setTitle(tr("pixiv.export_group"))
        self._lbl_filename.setText(tr("pixiv.filename"))
        self.export_btn.setText(tr("pixiv.btn_export"))
        self._hint_label.setText(tr("pixiv.hint"))

        self._rebuild_layout_combo()

        paths = self._image_paths()
        if not paths:
            self.status_label.setText(tr("pixiv.status_empty"))
            pixmap = self.preview_label.pixmap()
            if pixmap is None or pixmap.isNull():
                self.preview_label.setText(tr("pixiv.preview_empty"))
        else:
            self._schedule_preview()

    def _image_paths(self) -> list[str]:
        paths: list[str] = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            path = item.data(_PATH_ROLE) if item else None
            if not path:
                path = item.text() if item else ""
            path = str(path).strip()
            if path:
                paths.append(path)
        return paths

    def _add_path_item(self, path: str) -> None:
        path = str(Path(path))
        item = QListWidgetItem(Path(path).name)
        item.setToolTip(path)
        item.setData(_PATH_ROLE, path)
        self.file_list.addItem(item)

    def _schedule_preview(self) -> None:
        self._preview_timer.start(200)

    def _on_setting_changed(self, _value: int = 0) -> None:
        self.config.set("pixiv_canvas_size", self.canvas_spin.value())
        self.config.set("pixiv_padding", self.padding_spin.value())
        self.config.set("pixiv_gap", self.gap_spin.value())
        self._schedule_preview()

    def _on_crop_changed(self, checked: bool) -> None:
        self.config.set("pixiv_crop_fill", checked)
        self._schedule_preview()

    def _on_frame_setting_changed(self, _value: int = 0) -> None:
        self.config.set("pixiv_frame_width", self.frame_width_spin.value())
        self._schedule_preview()

    def _update_frame_swatch(self) -> None:
        hex_color = color_to_hex(self._frame_color)
        self.frame_color_swatch.setStyleSheet(
            f"background: {hex_color}; border: 1px solid #888;"
        )

    def _pick_frame_color(self) -> None:
        initial = QColor(*self._frame_color)
        color = QColorDialog.getColor(initial, self, tr("pixiv.color_dialog"))
        if not color.isValid():
            return
        self._frame_color = (color.red(), color.green(), color.blue())
        self.config.set("pixiv_frame_color", color_to_hex(self._frame_color))
        self._update_frame_swatch()
        self._schedule_preview()

    def _compose_kwargs(self) -> dict:
        return {
            "canvas_size": self.canvas_spin.value(),
            "padding": self.padding_spin.value(),
            "gap": self.gap_spin.value(),
            "crop_fill": self.crop_check.isChecked(),
            "frame_width": self.frame_width_spin.value(),
            "frame_color": color_to_hex(self._frame_color),
        }

    def _on_layout_changed(self) -> None:
        layout = self.layout_combo.currentData()
        if layout:
            self.config.set("pixiv_layout", layout)
        self._schedule_preview()

    def _rebuild_layout_combo(self) -> None:
        count = self.file_list.count()
        options = layout_options_for_count(count)
        allowed = {key for key, _ in options}
        saved = self.config.get("pixiv_layout", "auto")
        if saved not in allowed:
            saved = "auto"

        self.layout_combo.blockSignals(True)
        self.layout_combo.clear()
        for key, label in options:
            self.layout_combo.addItem(label, key)
        idx = self.layout_combo.findData(saved)
        self.layout_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.layout_combo.blockSignals(False)
        self.config.set("pixiv_layout", self.layout_combo.currentData() or "auto")
        self.add_btn.setEnabled(count < 3)
        self.export_btn.setEnabled(count > 0)
        if count == 0:
            self.status_label.setText(tr("pixiv.status_empty"))
        else:
            self.status_label.setText(tr("pixiv.status_count", count=count))

    def _add_images(self) -> None:
        start = ""
        paths = self._image_paths()
        if paths:
            start = str(Path(paths[0]).parent)
        else:
            start = self.config.folder("pixiv_input_folder")

        selected, _ = QFileDialog.getOpenFileNames(
            self,
            tr("pixiv.pick_images"),
            start,
            tr("pixiv.filter_images"),
        )
        if not selected:
            return

        existing = set(self._image_paths())
        added = 0
        for path in selected:
            if self.file_list.count() >= 3:
                break
            normalized = str(Path(path))
            if normalized in existing:
                continue
            self._add_path_item(normalized)
            existing.add(normalized)
            added += 1

        if added == 0:
            QMessageBox.information(
                self,
                tr("common.content_suite"),
                tr("pixiv.no_new_files"),
            )
            return

        self.config.set("pixiv_input_folder", str(Path(selected[0]).parent))
        self._rebuild_layout_combo()
        self._schedule_preview()

    def _remove_selected(self) -> None:
        for item in self.file_list.selectedItems():
            row = self.file_list.row(item)
            self.file_list.takeItem(row)
        self._rebuild_layout_combo()
        self._schedule_preview()

    def _move_up(self) -> None:
        row = self.file_list.currentRow()
        if row > 0:
            item = self.file_list.takeItem(row)
            self.file_list.insertItem(row - 1, item)
            self.file_list.setCurrentRow(row - 1)
            self._schedule_preview()

    def _move_down(self) -> None:
        row = self.file_list.currentRow()
        if 0 <= row < self.file_list.count() - 1:
            item = self.file_list.takeItem(row)
            self.file_list.insertItem(row + 1, item)
            self.file_list.setCurrentRow(row + 1)
            self._schedule_preview()

    def _pil_to_pixmap(self, image) -> QPixmap:
        qimage = QImage(ImageQt(image))
        return QPixmap.fromImage(qimage)

    def _refresh_preview(self) -> None:
        paths = self._image_paths()
        if not paths:
            self.preview_label.setText(tr("pixiv.preview_empty"))
            self.preview_label.setPixmap(QPixmap())
            return

        try:
            layout = self.layout_combo.currentData() or "auto"
            image, resolved = compose_cover(
                paths,
                layout=layout,
                **self._compose_kwargs(),
            )
            self.status_label.setText(
                tr(
                    "pixiv.status_layout",
                    count=len(paths),
                    layout=layout_label(resolved),
                )
            )
            pixmap = self._pil_to_pixmap(image)
            image.close()
            if pixmap.isNull():
                raise RuntimeError("Failed to build preview.")

            scaled = pixmap.scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.preview_label.setPixmap(scaled)
            self.preview_label.setText("")
        except Exception as exc:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText(tr("pixiv.preview_error", error=exc))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._image_paths():
            self._schedule_preview()

    def _export_cover(self) -> None:
        paths = self._image_paths()
        output_dir = self.output_picker.path().strip()
        name = self.name_edit.text().strip() or "pixiv_cover"

        if not paths:
            QMessageBox.warning(
                self, tr("common.content_suite"), tr("pixiv.warn_no_images")
            )
            return
        if not output_dir:
            QMessageBox.warning(
                self, tr("common.content_suite"), tr("pixiv.warn_output")
            )
            return

        missing = [p for p in paths if not Path(p).is_file()]
        if missing:
            QMessageBox.warning(
                self,
                tr("common.content_suite"),
                tr("pixiv.file_missing", path=missing[0]),
            )
            return

        output_path = Path(output_dir) / f"{name}.png"
        try:
            layout = self.layout_combo.currentData() or "auto"
            image, resolved = compose_cover(
                paths,
                layout=layout,
                **self._compose_kwargs(),
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(output_path, "PNG")
            image.close()
            QMessageBox.information(
                self,
                tr("common.content_suite"),
                tr(
                    "pixiv.export_done",
                    layout=layout_label(resolved),
                    count=len(paths),
                    path=output_path,
                ),
            )
        except Exception as exc:
            QMessageBox.critical(self, tr("common.content_suite"), str(exc))