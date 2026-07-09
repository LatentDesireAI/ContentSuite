from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.compress import PackSummary, collect_images, default_worker_count, process_pack
from core.media_scan import sort_media_paths
from core.config_store import ConfigStore
from core.i18n import I18n, tr
from core.pdf_export import PdfExportResult, export_folder_to_pdf
from tabs.base_tab import BaseTab
from ui.image_grid import ImageGrid


class CompressWorker(QThread):
    log_line = Signal(str)
    progress = Signal(int, int)
    finished_ok = Signal(object)
    finished_error = Signal(str)

    def __init__(
        self,
        input_folder: str,
        output_folder: str,
        base_name: str,
        quality: int,
        max_res: int,
        workers: int,
        author_meta: dict,
        sources: list[Path] | None = None,
        keep_original_name: bool = False,
    ) -> None:
        super().__init__()
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.base_name = base_name
        self.quality = quality
        self.max_res = max_res
        self.workers = workers
        self.author_meta = author_meta
        self.sources = sources
        self.keep_original_name = keep_original_name

    def run(self) -> None:
        try:
            def on_progress(current: int, total: int, result) -> None:
                self.progress.emit(current, total)
                if result.success:
                    orig_mb = result.original_size / 1024 / 1024
                    new_mb = result.new_size / 1024 / 1024
                    resize_note = tr("log.resized") if result.resized else ""
                    self.log_line.emit(
                        f"[{current}/{total}] {result.source_name} → {result.output_name}"
                        f" ({orig_mb:.1f} MB → {new_mb:.1f} MB{resize_note})"
                    )
                else:
                    self.log_line.emit(
                        tr(
                            "log.compress_error",
                            cur=current,
                            total=total,
                            name=result.source_name,
                            error=result.error,
                        )
                    )

            summary = process_pack(
                self.input_folder,
                self.output_folder,
                self.base_name,
                quality=self.quality,
                max_res=self.max_res,
                workers=self.workers,
                author_meta=self.author_meta,
                sources=self.sources,
                keep_original_name=self.keep_original_name,
                on_progress=on_progress,
            )
            self.finished_ok.emit(summary)
        except Exception as exc:
            self.finished_error.emit(str(exc))


class PdfWorker(QThread):
    log_line = Signal(str)
    progress = Signal(int, int)
    finished_ok = Signal(object)
    finished_error = Signal(str)

    def __init__(
        self,
        source_folder: str,
        output_pdf: str,
        title: str,
        dpi: float,
        author_meta: dict,
    ) -> None:
        super().__init__()
        self.source_folder = source_folder
        self.output_pdf = output_pdf
        self.title = title
        self.dpi = dpi
        self.author_meta = author_meta

    def run(self) -> None:
        try:
            def on_progress(current: int, total: int, name: str) -> None:
                self.progress.emit(current, total)
                self.log_line.emit(tr("log.page", cur=current, total=total, name=name))

            result = export_folder_to_pdf(
                self.source_folder,
                self.output_pdf,
                self.title,
                dpi=self.dpi,
                author_meta=self.author_meta,
                on_progress=on_progress,
            )
            self.finished_ok.emit(result)
        except Exception as exc:
            self.finished_error.emit(str(exc))


class ImagesTab(BaseTab):
    def __init__(self, config: ConfigStore, parent=None) -> None:
        super().__init__(
            config,
            parent,
            input_folder_key="images_input_folder",
            output_folder_key="images_output_folder",
            input_label_key="images.input",
            output_label_key="images.output",
        )
        self._compress_worker: CompressWorker | None = None
        self._pdf_worker: PdfWorker | None = None

        self.settings_group = QGroupBox()
        form = QFormLayout(self.settings_group)

        self.base_name_edit = QLineEdit()
        self.base_name_edit.setText(config.get("image_base_name", ""))
        self.base_name_edit.textChanged.connect(
            lambda text: config.set("image_base_name", text)
        )

        self.keep_original_name_cb = QCheckBox()
        self.keep_original_name_cb.setChecked(
            bool(config.get("image_keep_original_name", False))
        )
        self.keep_original_name_cb.toggled.connect(self._on_keep_original_name_toggled)
        self._on_keep_original_name_toggled(self.keep_original_name_cb.isChecked())

        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(int(config.get("image_quality", 98)))
        self.quality_spin.valueChanged.connect(
            lambda v: config.set("image_quality", v)
        )

        self.max_res_spin = QSpinBox()
        self.max_res_spin.setRange(512, 8192)
        self.max_res_spin.setSingleStep(256)
        self.max_res_spin.setValue(int(config.get("image_max_res", 2560)))
        self.max_res_spin.valueChanged.connect(
            lambda v: config.set("image_max_res", v)
        )

        self._cpu_count = default_worker_count()
        saved_workers = int(config.get("image_workers", 0))
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, max(self._cpu_count * 2, 16))
        self.workers_spin.setValue(saved_workers if saved_workers > 0 else self._cpu_count)
        self.workers_spin.valueChanged.connect(
            lambda v: config.set("image_workers", v)
        )

        self._lbl_pack_name = QLabel()
        self._lbl_jpeg_quality = QLabel()
        self._lbl_max_side = QLabel()
        self._lbl_workers = QLabel()

        form.addRow(self._lbl_pack_name, self.base_name_edit)
        form.addRow("", self.keep_original_name_cb)
        form.addRow(self._lbl_jpeg_quality, self.quality_spin)
        form.addRow(self._lbl_max_side, self.max_res_spin)
        form.addRow(self._lbl_workers, self.workers_spin)

        self.pdf_group = QGroupBox()
        pdf_form = QFormLayout(self.pdf_group)

        self.pdf_source_combo = QComboBox()
        self.pdf_source_combo.currentIndexChanged.connect(self._on_pdf_source_changed)

        self.pdf_dpi_spin = QSpinBox()
        self.pdf_dpi_spin.setRange(72, 600)
        self.pdf_dpi_spin.setValue(int(config.get("pdf_dpi", 150)))
        self.pdf_dpi_spin.valueChanged.connect(
            lambda v: config.set("pdf_dpi", v)
        )

        self._lbl_pdf_source = QLabel()
        self._lbl_dpi = QLabel()

        pdf_form.addRow(self._lbl_pdf_source, self.pdf_source_combo)
        pdf_form.addRow(self._lbl_dpi, self.pdf_dpi_spin)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setVisible(False)

        self.process_btn = QPushButton()
        self.process_btn.clicked.connect(self._start_processing)

        self.pdf_btn = QPushButton()
        self.pdf_btn.clicked.connect(self._start_pdf_export)

        self.hint_label = QLabel()
        self.hint_label.setWordWrap(True)
        self.hint_label.setStyleSheet("color: #666;")

        # --- Image grid ---
        self.image_grid = ImageGrid()
        self.image_grid.set_sort_mode(
            str(config.get("image_sort", "name") or "name")
        )
        self.image_grid.selection_changed.connect(self._update_buttons)
        self.image_grid.load_finished.connect(self._on_images_loaded)
        self.image_grid.sort_changed.connect(self._on_image_sort_changed)

        row_actions = QHBoxLayout()
        row_actions.addWidget(self.process_btn)
        row_actions.addWidget(self.pdf_btn)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.addWidget(self.input_picker)
        left_layout.addWidget(self.output_picker)
        left_layout.addWidget(self.settings_group)
        left_layout.addWidget(self.pdf_group)
        left_layout.addLayout(row_actions)
        left_layout.addWidget(self.progress)
        left_layout.addWidget(self.hint_label)
        left_layout.addStretch()

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setWidget(left_panel)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.image_grid.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        split = QHBoxLayout()
        split.setContentsMargins(0, 0, 0, 0)
        split.setSpacing(10)
        split.addWidget(left_scroll, stretch=1)
        split.addWidget(self.image_grid, stretch=2)

        split_host = QWidget()
        split_host.setLayout(split)

        root = self.layout()
        root.removeWidget(self.input_picker)
        root.removeWidget(self.output_picker)
        self.content_layout().addWidget(split_host, stretch=1)

        self.input_picker.path_changed.connect(self._refresh_image_list)
        self.output_picker.path_changed.connect(self._update_buttons)

        I18n.instance().language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

        self._refresh_image_list()

    def retranslate_ui(self) -> None:
        self.input_picker.retranslate_ui()
        self.output_picker.retranslate_ui()

        self.settings_group.setTitle(tr("images.group_compress"))
        self.pdf_group.setTitle(tr("images.group_pdf"))

        self._lbl_pack_name.setText(tr("images.pack_name"))
        self._lbl_jpeg_quality.setText(tr("images.jpeg_quality"))
        self._lbl_max_side.setText(tr("images.max_side"))
        self._lbl_workers.setText(tr("images.workers"))
        self._lbl_pdf_source.setText(tr("images.pdf_source"))
        self._lbl_dpi.setText(tr("common.dpi"))

        self.base_name_edit.setPlaceholderText(tr("images.pack_placeholder"))
        self.keep_original_name_cb.setText(tr("images.keep_original_name"))
        self.keep_original_name_cb.setToolTip(tr("images.keep_original_name_tip"))
        self.workers_spin.setToolTip(tr("images.workers_tip", cpus=self._cpu_count))
        self.pdf_dpi_spin.setToolTip(tr("images.pdf_dpi_tip"))

        self.process_btn.setText(tr("images.btn_compress"))
        self.pdf_btn.setText(tr("images.btn_pdf"))
        self.hint_label.setText(tr("images.hint"))

        current_source = self.pdf_source_combo.currentData()
        if current_source is None:
            current_source = self.config.get("pdf_source", "input")
        self.pdf_source_combo.blockSignals(True)
        self.pdf_source_combo.clear()
        self.pdf_source_combo.addItem(tr("images.pdf_source_input"), "input")
        self.pdf_source_combo.addItem(tr("images.pdf_source_output"), "output")
        idx = self.pdf_source_combo.findData(current_source)
        self.pdf_source_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.pdf_source_combo.blockSignals(False)

    def _on_keep_original_name_toggled(self, enabled: bool) -> None:
        self.config.set("image_keep_original_name", enabled)
        self.base_name_edit.setEnabled(not enabled)

    def _on_pdf_source_changed(self) -> None:
        self.config.set("pdf_source", self.pdf_source_combo.currentData())
        self._update_buttons()

    def _pdf_source_folder(self) -> str:
        if self.pdf_source_combo.currentData() == "output":
            return self.output_picker.path()
        return self.input_picker.path()

    def _sources(self) -> list[Path]:
        input_path = Path(self.input_picker.path())
        return collect_images(input_path)

    def _selected_sources(self) -> list[Path]:
        selected = self.image_grid.selected_paths()
        if selected:
            return selected
        return self._sources()

    def _is_busy(self) -> bool:
        workers = (self._compress_worker, self._pdf_worker)
        return any(w is not None and w.isRunning() for w in workers)

    def _set_busy(self, busy: bool) -> None:
        self.process_btn.setEnabled(not busy)
        self.pdf_btn.setEnabled(not busy)
        self.progress.setVisible(busy)
        self.image_grid.set_interaction_enabled(not busy)
        if not busy:
            self._update_buttons()

    def _on_image_sort_changed(self) -> None:
        self.config.set("image_sort", self.image_grid.sort_mode())
        self._refresh_image_list()

    def _sorted_sources(self) -> list[Path]:
        return sort_media_paths(self._sources(), self.image_grid.sort_mode())

    def _refresh_image_list(self, _path: str = "") -> None:
        if self._is_busy():
            return
        self.image_grid.set_sources(self._sorted_sources())
        self._update_buttons()

    def _on_images_loaded(self, _count: int) -> None:
        self._update_buttons()

    def _update_buttons(self) -> None:
        if self._is_busy():
            return

        has_images = self.image_grid.has_images()
        has_output = bool(self.output_picker.path())
        pdf_folder = self._pdf_source_folder()
        pdf_count = (
            len(collect_images(Path(pdf_folder)))
            if pdf_folder and Path(pdf_folder).is_dir()
            else 0
        )

        self.process_btn.setEnabled(has_images and has_output)
        self.pdf_btn.setEnabled(pdf_count > 0 and has_output)

    def _validate_base_name(self, *, required: bool = True) -> str | None:
        base_name = self.base_name_edit.text().strip()
        if required and not base_name:
            QMessageBox.warning(
                self, tr("common.content_suite"), tr("images.warn_pack_name")
            )
            return None
        return base_name

    def _start_processing(self) -> None:
        input_folder = self.input_picker.path()
        output_folder = self.output_picker.path()
        keep_original_name = self.keep_original_name_cb.isChecked()
        base_name = self._validate_base_name(required=not keep_original_name)
        sources = self._selected_sources()

        if not input_folder:
            QMessageBox.warning(
                self, tr("common.content_suite"), tr("images.warn_input")
            )
            return
        if not output_folder:
            QMessageBox.warning(
                self, tr("common.content_suite"), tr("images.warn_output")
            )
            return
        if base_name is None:
            return
        if not sources:
            QMessageBox.warning(
                self, tr("common.content_suite"), tr("images.warn_no_images")
            )
            return
        if self._is_busy():
            return

        self.log_panel.clear()
        workers = self.workers_spin.value()
        author_meta = self.config.get_author_metadata()
        meta_note = ""
        if author_meta.get("enabled") and author_meta.get("author"):
            meta_note = tr("log.author_suffix", author=author_meta["author"])
        selected_note = ""
        if len(sources) < self.image_grid.count():
            selected_note = tr(
                "log.images.selected",
                count=len(sources),
                total=self.image_grid.count(),
            )
        name_note = (
            tr("log.images.name_original")
            if keep_original_name
            else tr("log.images.name_pack", pack=base_name)
        )
        self.log(
            tr(
                "log.images.compress_start",
                input=input_folder,
                output=output_folder,
                name_note=name_note,
                quality=self.quality_spin.value(),
                max=self.max_res_spin.value(),
                workers=workers,
                selected=selected_note,
                author=meta_note,
            )
        )

        self._set_busy(True)
        self.progress.setValue(0)

        self._compress_worker = CompressWorker(
            input_folder,
            output_folder,
            base_name,
            self.quality_spin.value(),
            self.max_res_spin.value(),
            workers,
            author_meta,
            sources=sources,
            keep_original_name=keep_original_name,
        )
        self._compress_worker.log_line.connect(self.log)
        self._compress_worker.progress.connect(self._on_progress)
        self._compress_worker.finished_ok.connect(self._on_compress_finished)
        self._compress_worker.finished_error.connect(self._on_error)
        self._compress_worker.start()

    def _start_pdf_export(self) -> None:
        output_folder = self.output_picker.path()
        source_folder = self._pdf_source_folder()
        base_name = self._validate_base_name()

        if not source_folder:
            QMessageBox.warning(
                self, tr("common.content_suite"), tr("images.warn_pdf_source")
            )
            return
        if not output_folder:
            QMessageBox.warning(
                self, tr("common.content_suite"), tr("images.warn_pdf_output")
            )
            return
        if not base_name:
            return
        if self._is_busy():
            return

        output_pdf = str(Path(output_folder) / f"{base_name}.pdf")
        author_meta = self.config.get_author_metadata()

        self.log_panel.clear()
        self.log(
            tr(
                "log.images.pdf_start",
                input=source_folder,
                output=output_pdf,
                pages=len(collect_images(Path(source_folder))),
                dpi=self.pdf_dpi_spin.value(),
            )
        )

        self._set_busy(True)
        self.progress.setValue(0)

        self._pdf_worker = PdfWorker(
            source_folder,
            output_pdf,
            base_name,
            float(self.pdf_dpi_spin.value()),
            author_meta,
        )
        self._pdf_worker.log_line.connect(self.log)
        self._pdf_worker.progress.connect(self._on_progress)
        self._pdf_worker.finished_ok.connect(self._on_pdf_finished)
        self._pdf_worker.finished_error.connect(self._on_error)
        self._pdf_worker.start()

    def _on_progress(self, current: int, total: int) -> None:
        self.progress.setMaximum(total)
        self.progress.setValue(current)

    def _on_compress_finished(self, summary: PackSummary) -> None:
        self._set_busy(False)

        if summary.total_files == 0:
            self.log(tr("images.not_found"))
            QMessageBox.information(
                self, tr("common.content_suite"), tr("images.not_found")
            )
            return

        saved_mb = (summary.original_bytes - summary.output_bytes) / 1024 / 1024
        pct = 0
        if summary.original_bytes > 0:
            pct = (1 - summary.output_bytes / summary.original_bytes) * 100

        self.log("—" * 40)
        self.log(
            tr("log.done", done=summary.processed, total=summary.total_files)
        )
        if summary.failed:
            self.log(tr("log.errors_count", failed=summary.failed))
        self.log(
            tr(
                "log.images.size_summary",
                before=summary.original_bytes / 1024 / 1024,
                after=summary.output_bytes / 1024 / 1024,
                saved=saved_mb,
                pct=pct,
            )
        )

        QMessageBox.information(
            self,
            tr("common.content_suite"),
            tr(
                "images.done",
                done=summary.processed,
                total=summary.total_files,
                folder=self.output_picker.path(),
            ),
        )

    def _on_pdf_finished(self, result: PdfExportResult) -> None:
        self._set_busy(False)

        self.log("—" * 40)
        self.log(
            tr(
                "log.images.pdf_done_log",
                name=result.output_path.name,
                pages=result.page_count,
                size=result.file_size / 1024 / 1024,
            )
        )

        QMessageBox.information(
            self,
            tr("common.content_suite"),
            tr("images.pdf_done", pages=result.page_count, path=result.output_path),
        )

    def _on_error(self, message: str) -> None:
        self._set_busy(False)
        self.log(tr("log.error", msg=message))
        QMessageBox.critical(self, tr("common.content_suite"), message)