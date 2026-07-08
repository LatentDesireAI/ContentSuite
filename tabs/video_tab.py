from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QFrame,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.app_log import get_logger
from core.config_store import ConfigStore
from core.i18n import I18n, tr
from core.ffmpeg_wrapper import (
    UgoiraExportResult,
    VideoBatchSummary,
    calc_pixiv_ugoira_fps,
    check_ffmpeg,
    collect_videos,
    default_video_worker_count,
    export_ugoira,
    filter_ugoira_options,
    job_output_dir,
    process_video_batch,
    resolve_ugoira_fps,
)
from core.watermark import WatermarkSettings
from tabs.base_tab import BaseTab
from ui.clip_grid import ClipGrid


class VideoBatchWorker(QThread):
    log_line = Signal(str)
    progress = Signal(int, int)
    finished_ok = Signal(object)
    finished_error = Signal(str)

    def __init__(
        self,
        sources: list[Path],
        output_dir: str,
        job: str,
        workers: int,
        base_name: str,
        job_kwargs: dict,
    ) -> None:
        super().__init__()
        self.sources = sources
        self.output_dir = output_dir
        self.job = job
        self.workers = workers
        self.base_name = base_name
        self.job_kwargs = job_kwargs

    def run(self) -> None:
        try:
            get_logger().info(
                "VideoBatchWorker start: job=%s, files=%d, workers=%d",
                self.job,
                len(self.sources),
                self.workers,
            )
            def on_progress(current: int, total: int, result) -> None:
                self.progress.emit(current, total)
                if result.probe:
                    prefix = result.probe.summary
                else:
                    prefix = result.source.name
                if result.success:
                    out_name = result.output.name if result.output else "?"
                    self.log_line.emit(f"[{current}/{total}] {prefix} → {out_name}")
                else:
                    self.log_line.emit(
                        f"[{current}/{total}] {result.source.name} — ошибка: {result.message}"
                    )

            summary = process_video_batch(
                self.sources,
                Path(self.output_dir),
                self.job,
                workers=self.workers,
                base_name=self.base_name,
                on_progress=on_progress,
                **self.job_kwargs,
            )
            get_logger().info(
                "VideoBatchWorker done: job=%s, ok=%d, failed=%d",
                self.job,
                summary.processed,
                summary.failed,
            )
            self.finished_ok.emit(summary)
        except Exception as exc:
            get_logger().exception("VideoBatchWorker crashed: job=%s", self.job)
            self.finished_error.emit(str(exc))


class UgoiraBatchWorker(QThread):
    log_line = Signal(str)
    progress = Signal(int, int)
    finished_ok = Signal(object)
    finished_error = Signal(str)

    def __init__(
        self,
        sources: list[Path],
        output_root: str,
        base_name: str,
        options: dict,
    ) -> None:
        super().__init__()
        self.sources = sources
        self.output_root = output_root
        self.base_name = base_name
        self.options = options

    def run(self) -> None:
        results: list[UgoiraExportResult] = []
        try:
            total = len(self.sources)
            for index, source in enumerate(self.sources, start=1):
                folder_name = f"{self.base_name}_{index}"
                out_dir = Path(self.output_root) / "ugoira" / folder_name
                fps = resolve_ugoira_fps(
                    self.options["chunk_sec"],
                    max_frames=self.options["max_frames"],
                    auto_fps=self.options.get("auto_fps", True),
                    manual_fps=self.options["fps"],
                )
                get_logger().info("UgoiraWorker start: %s → %s", source.name, out_dir)
                self.log_line.emit(
                    f"Ugoira [{index}/{total}]: {source.name} → {folder_name}/ ({fps} fps)"
                )
                result = export_ugoira(
                    source, out_dir, **filter_ugoira_options(self.options)
                )
                for chunk in result.chunks:
                    size_mb = chunk.size_bytes / 1024 / 1024
                    max_mb = float(self.options.get("max_chunk_mb", 30))
                    over = (
                        self.options.get("auto_fit_size", True)
                        and size_mb > max_mb + 0.05
                    )
                    self.log_line.emit(
                        f"  {folder_name}/{chunk.frames_dir.name}: "
                        f"{chunk.frame_count} кадров, {size_mb:.1f} МБ"
                        + (
                            f", JPEG q={chunk.jpeg_quality}"
                            if chunk.jpeg_quality
                            else ""
                        )
                        + (" ⚠ выше лимита" if over else "")
                    )
                results.append(result)
                self.progress.emit(index, total)
            get_logger().info("UgoiraBatchWorker done: %d files", len(results))
            self.finished_ok.emit(results)
        except Exception as exc:
            get_logger().exception("UgoiraBatchWorker crashed")
            self.finished_error.emit(str(exc))


class VideoTab(BaseTab):
    def __init__(self, config: ConfigStore, parent=None) -> None:
        super().__init__(
            config,
            parent,
            input_folder_key="video_input_folder",
            output_folder_key="video_output_folder",
            input_label_key="video.input",
            output_label_key="video.output",
        )
        self._batch_worker: VideoBatchWorker | None = None
        self._ugoira_worker: UgoiraBatchWorker | None = None

        ok, msg = check_ffmpeg()
        get_logger().info("VideoTab init, ffmpeg ok=%s", ok)
        if not ok:
            get_logger().error("ffmpeg check failed: %s", msg)
            warn = QLabel(f"⚠ {msg}")
            warn.setStyleSheet("color: #c00;")
            warn.setWordWrap(True)
            self.content_layout().addWidget(warn)

        self._pack_group = QGroupBox()
        pack_form = QFormLayout(self._pack_group)
        default_name = config.get("video_base_name", "") or config.get("image_base_name", "")
        self.base_name_edit = QLineEdit()
        self.base_name_edit.setText(default_name)
        self.base_name_edit.textChanged.connect(
            lambda text: config.set("video_base_name", text)
        )
        self._lbl_pack_prefix = QLabel()
        self._lbl_pack_hint = QLabel()
        self._lbl_pack_hint.setWordWrap(True)
        self._lbl_pack_hint.setStyleSheet("color: #666; font-size: 10px;")
        pack_form.addRow(self._lbl_pack_prefix, self.base_name_edit)

        # --- Watermark ---
        self._wm_group = QGroupBox()
        wm_form = QFormLayout(self._wm_group)

        wm_row = QHBoxLayout()
        self.watermark_combo = QComboBox()
        self.watermark_combo.setMinimumWidth(200)
        self._reload_watermark_combo()
        self._add_wm_btn = QPushButton()
        self._add_wm_btn.clicked.connect(self._add_watermark_file)
        wm_row.addWidget(self.watermark_combo, stretch=1)
        wm_row.addWidget(self._add_wm_btn)

        self.wm_height_spin = QDoubleSpinBox()
        self.wm_height_spin.setRange(1.0, 50.0)
        self.wm_height_spin.setSingleStep(0.5)
        self.wm_height_spin.setDecimals(1)
        self.wm_height_spin.setSuffix(" %")
        self.wm_height_spin.setValue(config.watermark_height_pct())
        self.wm_height_spin.valueChanged.connect(
            lambda v: config.set("watermark_height_pct", v)
        )

        self.wm_alpha_spin = QSpinBox()
        self.wm_alpha_spin.setRange(0, 100)
        self.wm_alpha_spin.setValue(int(config.get("watermark_alpha", 50)))
        self.wm_alpha_spin.setSuffix(" %")
        self.wm_alpha_spin.valueChanged.connect(
            lambda v: config.set("watermark_alpha", v)
        )

        self.wm_x_spin = QDoubleSpinBox()
        self.wm_x_spin.setRange(0.0, 1.0)
        self.wm_x_spin.setSingleStep(0.05)
        self.wm_x_spin.setDecimals(2)
        self.wm_x_spin.setValue(float(config.get("watermark_x", 0.85)))
        self.wm_x_spin.valueChanged.connect(
            lambda v: config.set("watermark_x", v)
        )

        self.wm_y_spin = QDoubleSpinBox()
        self.wm_y_spin.setRange(0.0, 1.0)
        self.wm_y_spin.setSingleStep(0.05)
        self.wm_y_spin.setDecimals(2)
        self.wm_y_spin.setValue(float(config.get("watermark_y", 0.85)))
        self.wm_y_spin.valueChanged.connect(
            lambda v: config.set("watermark_y", v)
        )

        self._lbl_wm_file = QLabel()
        self._lbl_wm_height = QLabel()
        self._lbl_wm_alpha = QLabel()
        self._lbl_wm_pos_x = QLabel()
        self._lbl_wm_pos_y = QLabel()
        wm_form.addRow(self._lbl_wm_file, wm_row)
        wm_form.addRow(self._lbl_wm_height, self.wm_height_spin)
        wm_form.addRow(self._lbl_wm_alpha, self.wm_alpha_spin)
        wm_form.addRow(self._lbl_wm_pos_x, self.wm_x_spin)
        wm_form.addRow(self._lbl_wm_pos_y, self.wm_y_spin)

        self.watermark_btn = QPushButton()
        self.watermark_btn.clicked.connect(self._start_watermark)

        # --- GIF ---
        self._gif_group = QGroupBox()
        gif_form = QFormLayout(self._gif_group)

        self.gif_fps_spin = QSpinBox()
        self.gif_fps_spin.setRange(1, 60)
        self.gif_fps_spin.setValue(int(config.get("gif_fps", 24)))
        self.gif_fps_spin.valueChanged.connect(lambda v: config.set("gif_fps", v))

        self.gif_width_spin = QSpinBox()
        self.gif_width_spin.setRange(160, 1920)
        self.gif_width_spin.setSingleStep(80)
        self.gif_width_spin.setValue(int(config.get("gif_width", 720)))
        self.gif_width_spin.valueChanged.connect(lambda v: config.set("gif_width", v))

        self._lbl_gif_fps = QLabel()
        self._lbl_gif_width = QLabel()
        gif_form.addRow(self._lbl_gif_fps, self.gif_fps_spin)
        gif_form.addRow(self._lbl_gif_width, self.gif_width_spin)

        self.gif_btn = QPushButton()
        self.gif_btn.clicked.connect(self._start_gif)

        # --- Convert ---
        self._conv_group = QGroupBox()
        conv_form = QFormLayout(self._conv_group)

        self.format_combo = QComboBox()
        for fmt in ("webm", "mp4", "mov"):
            self.format_combo.addItem(fmt.upper(), fmt)
        saved_fmt = config.get("video_output_format", "webm")
        idx = self.format_combo.findData(saved_fmt)
        self.format_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)

        self.keep_audio_cb = QCheckBox()
        self.keep_audio_cb.setChecked(bool(config.get("video_keep_audio", True)))
        self.keep_audio_cb.toggled.connect(
            lambda v: config.set("video_keep_audio", v)
        )

        self.remove_meta_cb = QCheckBox()
        self.remove_meta_cb.setChecked(bool(config.get("video_remove_metadata", True)))
        self.remove_meta_cb.toggled.connect(
            lambda v: config.set("video_remove_metadata", v)
        )

        self.reencode_cb = QCheckBox()
        self.reencode_cb.setChecked(bool(config.get("video_reencode", False)))
        self.reencode_cb.toggled.connect(
            lambda v: config.set("video_reencode", v)
        )

        cpus = os.cpu_count() or 4
        recommended = default_video_worker_count()
        self._cpus = cpus
        self._recommended_workers = recommended
        self._lbl_cpu_hint = QLabel()
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, max(8, min(cpus // 2, 16)))
        saved_workers = int(config.get("video_workers", 0))
        self.workers_spin.setValue(saved_workers if saved_workers > 0 else recommended)
        self.workers_spin.valueChanged.connect(
            lambda v: config.set("video_workers", v)
        )

        self.patch_in_place_cb = QCheckBox()
        self.patch_in_place_cb.setChecked(bool(config.get("video_patch_in_place", True)))
        self.patch_in_place_cb.toggled.connect(
            lambda v: config.set("video_patch_in_place", v)
        )

        self.convert_btn = QPushButton()
        self.convert_btn.clicked.connect(self._start_convert)

        self.metadata_btn = QPushButton()
        self.metadata_btn.clicked.connect(self._start_metadata)

        self._lbl_format = QLabel()
        conv_form.addRow(self._lbl_format, self.format_combo)
        conv_form.addRow("", self.keep_audio_cb)
        conv_form.addRow("", self.remove_meta_cb)
        conv_form.addRow("", self.reencode_cb)
        conv_form.addRow(self._lbl_cpu_hint, self.workers_spin)
        conv_form.addRow("", self.patch_in_place_cb)

        # --- Ugoira ---
        self._ugoira_group = QGroupBox()
        ugoira_form = QFormLayout(self._ugoira_group)

        self.ugoira_chunk_spin = QSpinBox()
        self.ugoira_chunk_spin.setRange(3, 60)
        self.ugoira_chunk_spin.setValue(int(config.get("ugoira_chunk_sec", 10)))
        self.ugoira_chunk_spin.setSuffix(" сек")
        self.ugoira_chunk_spin.valueChanged.connect(
            lambda v: config.set("ugoira_chunk_sec", v)
        )
        self.ugoira_chunk_spin.valueChanged.connect(self._update_ugoira_fps_hint)

        self.ugoira_auto_fps_cb = QCheckBox()
        self.ugoira_auto_fps_cb.setChecked(bool(config.get("ugoira_auto_fps", True)))
        self.ugoira_auto_fps_cb.toggled.connect(self._on_ugoira_auto_fps_changed)

        self.ugoira_fps_spin = QSpinBox()
        self.ugoira_fps_spin.setRange(1, 60)
        self.ugoira_fps_spin.setValue(int(config.get("ugoira_fps", 20)))
        self.ugoira_fps_spin.valueChanged.connect(
            lambda v: config.set("ugoira_fps", v)
        )
        self.ugoira_fps_spin.valueChanged.connect(self._update_ugoira_fps_hint)

        self.ugoira_fps_hint = QLabel()
        self.ugoira_fps_hint.setStyleSheet("color: #666; font-size: 10px;")

        self.ugoira_max_frames_spin = QSpinBox()
        self.ugoira_max_frames_spin.setRange(10, 200)
        self.ugoira_max_frames_spin.setValue(int(config.get("ugoira_max_frames", 150)))
        self.ugoira_max_frames_spin.valueChanged.connect(
            lambda v: config.set("ugoira_max_frames", v)
        )
        self.ugoira_max_frames_spin.valueChanged.connect(self._update_ugoira_fps_hint)

        self.ugoira_quality_spin = QSpinBox()
        self.ugoira_quality_spin.setRange(30, 100)
        self.ugoira_quality_spin.setValue(int(config.get("ugoira_quality", 80)))
        self.ugoira_quality_spin.valueChanged.connect(
            lambda v: config.set("ugoira_quality", v)
        )
        self.ugoira_quality_spin.valueChanged.connect(self._update_ugoira_fps_hint)

        self.ugoira_auto_size_cb = QCheckBox()
        self.ugoira_auto_size_cb.setChecked(bool(config.get("ugoira_auto_fit_size", True)))
        self.ugoira_auto_size_cb.toggled.connect(
            lambda v: config.set("ugoira_auto_fit_size", v)
        )
        self.ugoira_auto_size_cb.toggled.connect(self._update_ugoira_size_controls)
        self.ugoira_auto_size_cb.toggled.connect(self._update_ugoira_fps_hint)

        self.ugoira_max_mb_spin = QSpinBox()
        self.ugoira_max_mb_spin.setRange(10, 50)
        self.ugoira_max_mb_spin.setValue(int(config.get("ugoira_max_chunk_mb", 30)))
        self.ugoira_max_mb_spin.setSuffix(" МБ")
        self.ugoira_max_mb_spin.valueChanged.connect(
            lambda v: config.set("ugoira_max_chunk_mb", v)
        )
        self.ugoira_max_mb_spin.valueChanged.connect(self._update_ugoira_fps_hint)

        self.ugoira_max_width_spin = QSpinBox()
        self.ugoira_max_width_spin.setRange(640, 1920)
        self.ugoira_max_width_spin.setSingleStep(80)
        self.ugoira_max_width_spin.setValue(int(config.get("ugoira_max_width", 1200)))
        self.ugoira_max_width_spin.valueChanged.connect(
            lambda v: config.set("ugoira_max_width", v)
        )

        self.ugoira_size_hint = QLabel()
        self.ugoira_size_hint.setStyleSheet("color: #666; font-size: 10px;")

        self.ugoira_wm_cb = QCheckBox()
        self.ugoira_wm_cb.setChecked(bool(config.get("ugoira_watermark", True)))
        self.ugoira_wm_cb.toggled.connect(
            lambda v: config.set("ugoira_watermark", v)
        )

        self._lbl_ugoira_chunk = QLabel()
        self._lbl_ugoira_fps = QLabel()
        self._lbl_ugoira_max_frames = QLabel()
        self._lbl_ugoira_jpeg_quality = QLabel()
        self._lbl_ugoira_limit = QLabel()
        self._lbl_ugoira_max_width = QLabel()
        ugoira_form.addRow(self._lbl_ugoira_chunk, self.ugoira_chunk_spin)
        ugoira_form.addRow("", self.ugoira_auto_fps_cb)
        ugoira_form.addRow(self._lbl_ugoira_fps, self.ugoira_fps_spin)
        ugoira_form.addRow("", self.ugoira_fps_hint)
        ugoira_form.addRow(self._lbl_ugoira_max_frames, self.ugoira_max_frames_spin)
        ugoira_form.addRow(self._lbl_ugoira_jpeg_quality, self.ugoira_quality_spin)
        ugoira_form.addRow("", self.ugoira_auto_size_cb)
        ugoira_form.addRow(self._lbl_ugoira_limit, self.ugoira_max_mb_spin)
        ugoira_form.addRow(self._lbl_ugoira_max_width, self.ugoira_max_width_spin)
        ugoira_form.addRow("", self.ugoira_size_hint)
        ugoira_form.addRow("", self.ugoira_wm_cb)

        self._lbl_ugoira_hint = QLabel()
        self._lbl_ugoira_hint.setWordWrap(True)
        self._lbl_ugoira_hint.setStyleSheet("color: #666;")

        self.ugoira_btn = QPushButton()
        self.ugoira_btn.clicked.connect(self._start_ugoira)

        # --- Clip grid ---
        self.clip_grid = ClipGrid()
        self.clip_grid.selection_changed.connect(self._update_buttons)
        self.patch_in_place_cb.toggled.connect(self._update_buttons)
        self.clip_grid.load_finished.connect(self._on_clips_loaded)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setVisible(False)

        self._lbl_hint = QLabel()
        self._lbl_hint.setWordWrap(True)
        self._lbl_hint.setStyleSheet("color: #666;")

        row_gif_conv = QHBoxLayout()
        row_gif_conv.addWidget(self.gif_btn)
        row_gif_conv.addWidget(self.convert_btn)
        row_gif_conv.addWidget(self.metadata_btn)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.addWidget(self.input_picker)
        left_layout.addWidget(self.output_picker)
        left_layout.addWidget(self._pack_group)
        left_layout.addWidget(self._lbl_pack_hint)
        left_layout.addWidget(self._wm_group)
        left_layout.addWidget(self.watermark_btn)
        left_layout.addWidget(self._gif_group)
        left_layout.addWidget(self._conv_group)
        left_layout.addWidget(self._ugoira_group)
        left_layout.addWidget(self._lbl_ugoira_hint)
        left_layout.addWidget(self.ugoira_btn)
        left_layout.addLayout(row_gif_conv)
        left_layout.addWidget(self.progress)
        left_layout.addWidget(self._lbl_hint)
        left_layout.addStretch()

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setWidget(left_panel)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.clip_grid.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        split = QHBoxLayout()
        split.setContentsMargins(0, 0, 0, 0)
        split.setSpacing(10)
        split.addWidget(left_scroll, stretch=1)
        split.addWidget(self.clip_grid, stretch=2)

        split_host = QWidget()
        split_host.setLayout(split)

        root = self.layout()
        root.removeWidget(self.input_picker)
        root.removeWidget(self.output_picker)
        self.content_layout().addWidget(split_host, stretch=1)

        self.input_picker.path_changed.connect(self._refresh_file_list)
        self.output_picker.path_changed.connect(self._update_buttons)
        self._on_ugoira_auto_fps_changed(self.ugoira_auto_fps_cb.isChecked())
        self._refresh_file_list()

        I18n.instance().language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        self._pack_group.setTitle(tr("video.pack_group"))
        self._lbl_pack_prefix.setText(tr("video.pack_prefix"))
        self.base_name_edit.setPlaceholderText(tr("video.pack_placeholder"))
        self._lbl_pack_hint.setText(tr("video.pack_hint"))

        self._wm_group.setTitle(tr("video.wm_group"))
        self._lbl_wm_file.setText(tr("video.wm_file"))
        self._lbl_wm_height.setText(tr("video.wm_height"))
        self._lbl_wm_alpha.setText(tr("video.wm_alpha"))
        self._lbl_wm_pos_x.setText(tr("video.wm_pos_x"))
        self._lbl_wm_pos_y.setText(tr("video.wm_pos_y"))
        self._add_wm_btn.setText(tr("common.add"))
        self.wm_height_spin.setToolTip(tr("video.wm_height_tip"))
        self.watermark_btn.setText(tr("video.btn_watermark"))

        self._gif_group.setTitle(tr("video.gif_group"))
        self._lbl_gif_fps.setText(tr("common.fps"))
        self._lbl_gif_width.setText(tr("video.gif_width"))
        self.gif_btn.setText(tr("video.btn_gif"))

        self._conv_group.setTitle(tr("video.conv_group"))
        self._lbl_format.setText(tr("video.format"))
        self.keep_audio_cb.setText(tr("video.keep_audio"))
        self.remove_meta_cb.setText(tr("video.remove_meta"))
        self.reencode_cb.setText(tr("video.reencode"))
        self._lbl_cpu_hint.setText(tr("video.parallel_tasks"))
        self.workers_spin.setToolTip(
            tr(
                "video.workers_tip",
                cpus=self._cpus,
                rec=self._recommended_workers,
            )
        )
        self.patch_in_place_cb.setText(tr("video.patch_in_place"))
        self.patch_in_place_cb.setToolTip(tr("video.patch_in_place_tip"))
        self.convert_btn.setText(tr("video.btn_convert"))
        self.metadata_btn.setText(tr("video.btn_metadata"))

        self._ugoira_group.setTitle(tr("video.ugoira_group"))
        self._lbl_ugoira_chunk.setText(tr("video.ugoira_chunk"))
        self.ugoira_auto_fps_cb.setText(tr("video.ugoira_auto_fps"))
        self._lbl_ugoira_fps.setText(tr("video.ugoira_fps"))
        self._lbl_ugoira_max_frames.setText(tr("video.ugoira_max_frames"))
        self._lbl_ugoira_jpeg_quality.setText(tr("video.ugoira_jpeg_quality"))
        self.ugoira_auto_size_cb.setText(tr("video.ugoira_auto_size"))
        self._lbl_ugoira_limit.setText(tr("video.ugoira_limit"))
        self.ugoira_max_mb_spin.setToolTip(tr("video.ugoira_limit_tip"))
        self._lbl_ugoira_max_width.setText(tr("video.ugoira_max_width"))
        self.ugoira_max_width_spin.setToolTip(tr("video.ugoira_max_width_tip"))
        self.ugoira_wm_cb.setText(tr("video.ugoira_wm"))
        self.ugoira_wm_cb.setToolTip(tr("video.ugoira_wm_tip"))
        self._lbl_ugoira_hint.setText(tr("video.ugoira_hint"))
        self.ugoira_btn.setText(tr("video.btn_ugoira"))
        self._lbl_hint.setText(tr("video.hint"))

        current_wm = self.watermark_combo.currentData()
        self._reload_watermark_combo()
        if current_wm:
            idx = self.watermark_combo.findData(current_wm)
            if idx >= 0:
                self.watermark_combo.setCurrentIndex(idx)

        self._update_ugoira_fps_hint()

    def _on_ugoira_auto_fps_changed(self, enabled: bool) -> None:
        self.config.set("ugoira_auto_fps", enabled)
        self.ugoira_fps_spin.setEnabled(not enabled)
        self._update_ugoira_fps_hint()

    def _update_ugoira_size_controls(self) -> None:
        auto = self.ugoira_auto_size_cb.isChecked()
        self.ugoira_max_mb_spin.setEnabled(auto)

    def _update_ugoira_fps_hint(self, *_args) -> None:
        chunk = self.ugoira_chunk_spin.value()
        max_frames = self.ugoira_max_frames_spin.value()
        auto = self.ugoira_auto_fps_cb.isChecked()
        fps = resolve_ugoira_fps(
            chunk,
            max_frames=max_frames,
            auto_fps=auto,
            manual_fps=self.ugoira_fps_spin.value(),
        )
        cap = calc_pixiv_ugoira_fps(chunk, max_frames)
        est_frames = min(max_frames, fps * chunk)
        if auto:
            self.ugoira_fps_hint.setText(
                tr(
                    "video.ugoira_fps_auto",
                    fps=fps,
                    frames=est_frames,
                    chunk=chunk,
                    max_frames=max_frames,
                )
            )
        else:
            self.ugoira_fps_hint.setText(
                tr(
                    "video.ugoira_fps_manual",
                    fps=fps,
                    cap=cap,
                    max_frames=max_frames,
                    est=est_frames,
                )
            )

        self._update_ugoira_size_controls()
        if self.ugoira_auto_size_cb.isChecked():
            max_mb = self.ugoira_max_mb_spin.value()
            per_frame_kb = max_mb * 1024 / max(1, max_frames)
            self.ugoira_size_hint.setText(
                tr(
                    "video.ugoira_size_auto",
                    max_mb=max_mb,
                    kb=int(per_frame_kb),
                    max_frames=max_frames,
                )
            )
        else:
            self.ugoira_size_hint.setText(tr("video.ugoira_size_off"))

    def _validate_base_name(self) -> str | None:
        base_name = self.base_name_edit.text().strip()
        if not base_name:
            QMessageBox.warning(
                self, tr("common.content_suite"), tr("video.warn_pack_name")
            )
            return None
        return base_name

    def _on_format_changed(self) -> None:
        self.config.set("video_output_format", self.format_combo.currentData())

    def _reload_watermark_combo(self) -> None:
        self.watermark_combo.clear()
        files: list[str] = self.config.get("watermark_files", []) or []
        for path in files:
            if Path(path).is_file():
                self.watermark_combo.addItem(Path(path).name, path)
        if self.watermark_combo.count() == 0:
            self.watermark_combo.addItem(tr("common.not_selected"), "")

    def _add_watermark_file(self) -> None:
        start = str(Path(self.watermark_combo.currentData() or "").parent)
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("video.wm_dialog"),
            start,
            tr("video.wm_filter"),
        )
        if not path:
            return
        files: list[str] = list(self.config.get("watermark_files", []) or [])
        if path not in files:
            files.append(path)
            self.config.set("watermark_files", files)
        self._reload_watermark_combo()
        idx = self.watermark_combo.findData(path)
        if idx >= 0:
            self.watermark_combo.setCurrentIndex(idx)

    def _watermark_settings(self) -> WatermarkSettings:
        return WatermarkSettings(
            x=self.wm_x_spin.value(),
            y=self.wm_y_spin.value(),
            alpha=self.wm_alpha_spin.value(),
            height_pct=self.wm_height_spin.value(),
            margin_px=int(self.config.get("watermark_margin", 10)),
        )

    def _selected_watermark_path(self) -> Path | None:
        data = self.watermark_combo.currentData()
        if not data:
            return None
        path = Path(data)
        return path if path.is_file() else None

    def _sources(self) -> list[Path]:
        input_path = Path(self.input_picker.path())
        return collect_videos(input_path)

    def _selected_sources(self) -> list[Path]:
        selected = self.clip_grid.selected_paths()
        if selected:
            return selected
        return self._sources()

    def _is_busy(self) -> bool:
        workers = (self._batch_worker, self._ugoira_worker)
        return any(w is not None and w.isRunning() for w in workers)

    def _set_busy(self, busy: bool) -> None:
        for btn in (
            self.watermark_btn,
            self.gif_btn,
            self.convert_btn,
            self.metadata_btn,
            self.ugoira_btn,
        ):
            btn.setEnabled(not busy)
        self.progress.setVisible(busy)
        self.clip_grid.set_interaction_enabled(not busy)
        if not busy:
            self._update_buttons()

    def _refresh_file_list(self, _path: str = "") -> None:
        if self._is_busy():
            return
        self.clip_grid.set_sources(self._sources())
        self._update_buttons()

    def _on_clips_loaded(self, _count: int) -> None:
        self._update_buttons()

    def _update_buttons(self) -> None:
        if self._is_busy():
            return
        has_videos = self.clip_grid.has_videos()
        has_wm = self._selected_watermark_path() is not None
        has_output = bool(self.output_picker.path())

        self.watermark_btn.setEnabled(has_videos and has_wm and has_output)
        self.gif_btn.setEnabled(has_videos and has_output)
        self.convert_btn.setEnabled(has_videos and has_output)
        author_on = bool(self.config.get_author_metadata().get("enabled"))
        in_place = self.patch_in_place_cb.isChecked()
        self.metadata_btn.setEnabled(
            has_videos and author_on and (in_place or has_output)
        )
        self.ugoira_btn.setEnabled(has_videos and has_output)

    def _validate_output(self) -> str | None:
        output = self.output_picker.path()
        if not output:
            QMessageBox.warning(
                self, tr("common.content_suite"), tr("video.warn_output")
            )
            return None
        return output

    def _export_kwargs(self) -> dict:
        return {
            "remove_metadata": self.remove_meta_cb.isChecked(),
            "author_meta": self.config.get_author_metadata(),
        }

    def _author_log_note(self) -> str:
        meta = self.config.get_author_metadata()
        if meta.get("enabled") and meta.get("author"):
            return f", автор={meta['author']}"
        return ""

    def _start_batch(
        self,
        job: str,
        job_kwargs: dict,
        log_header: str,
        *,
        require_base_name: bool = True,
    ) -> None:
        sources = self._selected_sources()
        in_place = bool(job_kwargs.get("in_place"))
        output = self.input_picker.path() if in_place else self._validate_output()
        base_name = self._validate_base_name() if require_base_name else (
            self.base_name_edit.text().strip()
        )
        if not sources or self._is_busy():
            if not sources:
                QMessageBox.warning(
                    self, tr("common.content_suite"), tr("video.warn_no_video")
                )
            return
        if not output:
            return
        if require_base_name and not base_name:
            return

        job_kwargs = {**self._export_kwargs(), **job_kwargs}
        self.log_panel.clear()
        if in_place:
            self.log(f"{log_header}{self._author_log_note()}")
        else:
            out_sub = job_output_dir(Path(output), job)
            pack_note = f" | пак «{base_name}»" if base_name else ""
            self.log(
                f"{log_header}{pack_note} → {out_sub.name}/{self._author_log_note()}"
            )
        self._set_busy(True)
        self.progress.setValue(0)

        self._batch_worker = VideoBatchWorker(
            sources,
            output,
            job,
            self.workers_spin.value(),
            base_name,
            job_kwargs,
        )
        self._batch_worker.log_line.connect(self.log)
        self._batch_worker.progress.connect(self._on_progress)
        self._batch_worker.finished_ok.connect(
            lambda s: self._on_batch_finished(s, job)
        )
        self._batch_worker.finished_error.connect(self._on_error)
        self._batch_worker.start()

    def _start_watermark(self) -> None:
        wm_path = self._selected_watermark_path()
        if not wm_path:
            QMessageBox.warning(
                self, tr("common.content_suite"), tr("video.warn_wm_png")
            )
            return
        self._start_batch(
            "watermark",
            {
                "watermark_path": wm_path,
                "watermark_settings": self._watermark_settings(),
            },
            f"Watermark: {wm_path.name} | высота={self.wm_height_spin.value()}%, "
            f"alpha={self.wm_alpha_spin.value()}%",
        )

    def _start_gif(self) -> None:
        self._start_batch(
            "gif",
            {
                "fps": self.gif_fps_spin.value(),
                "width": self.gif_width_spin.value(),
            },
            f"GIF: fps={self.gif_fps_spin.value()}, ширина={self.gif_width_spin.value()}px",
        )

    def _start_metadata(self) -> None:
        author_meta = self.config.get_author_metadata()
        if not author_meta.get("enabled"):
            QMessageBox.warning(
                self,
                tr("common.content_suite"),
                tr("video.warn_author"),
            )
            return

        sources = self._selected_sources()
        in_place = self.patch_in_place_cb.isChecked()
        output = self.input_picker.path() if in_place else self._validate_output()
        if not sources or self._is_busy():
            if not sources:
                QMessageBox.warning(
                    self, tr("common.content_suite"), tr("video.warn_no_video")
                )
            return
        if not in_place and not output:
            return

        base_name = self.base_name_edit.text().strip()
        mode = "на месте" if in_place else f"→ {job_output_dir(Path(output), 'metadata')}"
        self._start_batch(
            "metadata",
            {"in_place": in_place},
            f"Авторство (copy): {len(sources)} файл(ов) {mode}"
            + (f" | пак «{base_name}»" if base_name and not in_place else ""),
            require_base_name=not in_place,
        )

    def _start_convert(self) -> None:
        fmt = self.format_combo.currentData()
        self._start_batch(
            "convert",
            {
                "output_format": fmt,
                "remove_metadata": self.remove_meta_cb.isChecked(),
                "keep_audio": self.keep_audio_cb.isChecked(),
                "reencode": self.reencode_cb.isChecked(),
            },
            f"Конвертация → {fmt} | звук={'да' if self.keep_audio_cb.isChecked() else 'нет'}, "
            f"метаданные={'удалить' if self.remove_meta_cb.isChecked() else 'оставить'}",
        )

    def _start_ugoira(self) -> None:
        sources = self._selected_sources()
        output = self._validate_output()
        base_name = self._validate_base_name()
        if not sources or not output or not base_name or self._is_busy():
            if not sources:
                QMessageBox.warning(
                    self, tr("common.content_suite"), tr("video.warn_no_video")
                )
            return

        chunk = self.ugoira_chunk_spin.value()
        max_frames = self.ugoira_max_frames_spin.value()
        effective_fps = resolve_ugoira_fps(
            chunk,
            max_frames=max_frames,
            auto_fps=self.ugoira_auto_fps_cb.isChecked(),
            manual_fps=self.ugoira_fps_spin.value(),
        )
        options = {
            "chunk_sec": chunk,
            "fps": self.ugoira_fps_spin.value(),
            "max_frames": max_frames,
            "auto_fps": self.ugoira_auto_fps_cb.isChecked(),
            "quality": self.ugoira_quality_spin.value(),
            "auto_fit_size": self.ugoira_auto_size_cb.isChecked(),
            "max_chunk_mb": float(self.ugoira_max_mb_spin.value()),
            "max_width": self.ugoira_max_width_spin.value(),
            "author_meta": self.config.get_author_metadata(),
        }
        wm_note = ""
        if self.ugoira_wm_cb.isChecked():
            wm_path = self._selected_watermark_path()
            if not wm_path:
                QMessageBox.warning(
                    self,
                    tr("common.content_suite"),
                    tr("video.warn_ugoira_wm"),
                )
                return
            options["watermark_path"] = wm_path
            options["watermark_settings"] = self._watermark_settings()
            wm_note = f", watermark={wm_path.name}"

        self.log_panel.clear()
        self.log(
            f"Ugoira: {len(sources)} ролик(ов) | пак «{base_name}» → ugoira/ | "
            f"chunk={chunk}s, fps={effective_fps}, max={max_frames}"
            + (
                f", лимит={self.ugoira_max_mb_spin.value()}МБ"
                if self.ugoira_auto_size_cb.isChecked()
                else ""
            )
            + wm_note
            + f"{self._author_log_note()}"
        )
        self._set_busy(True)
        self.progress.setMaximum(len(sources))
        self.progress.setValue(0)
        self.progress.setVisible(True)

        self._ugoira_worker = UgoiraBatchWorker(sources, output, base_name, options)
        self._ugoira_worker.log_line.connect(self.log)
        self._ugoira_worker.progress.connect(self._on_progress)
        self._ugoira_worker.finished_ok.connect(self._on_ugoira_finished)
        self._ugoira_worker.finished_error.connect(self._on_error)
        self._ugoira_worker.start()

    def _on_progress(self, current: int, total: int) -> None:
        self.progress.setMaximum(total)
        self.progress.setValue(current)

    def _on_batch_finished(self, summary: VideoBatchSummary, job: str) -> None:
        self._set_busy(False)
        self.log("—" * 40)
        self.log(f"Готово: {summary.processed} из {summary.total}")
        if summary.failed:
            self.log(f"Ошибок: {summary.failed}")

        labels = {
            "watermark": tr("video.done_watermark"),
            "gif": tr("video.done_gif"),
            "convert": tr("video.done_convert"),
            "metadata": tr("video.done_metadata"),
        }
        if job == "metadata" and self.patch_in_place_cb.isChecked():
            out_path = self.input_picker.path()
        else:
            out_path = job_output_dir(Path(self.output_picker.path()), job)
        QMessageBox.information(
            self,
            tr("common.content_suite"),
            tr(
                "video.done_batch",
                job=labels.get(job, job),
                done=summary.processed,
                total=summary.total,
                folder=out_path,
            ),
        )

    def _on_ugoira_finished(self, results: list[UgoiraExportResult]) -> None:
        self._set_busy(False)
        total_frames = sum(r.total_frames for r in results)
        total_chunks = sum(len(r.chunks) for r in results)
        out_root = Path(self.output_picker.path()) / "ugoira"
        self.log("—" * 40)
        self.log(
            f"Ugoira готов: {len(results)} ролик(ов), {total_chunks} ugoira-частей, "
            f"{total_frames} кадров → {out_root}"
        )
        QMessageBox.information(
            self,
            tr("common.content_suite"),
            tr(
                "video.done_ugoira",
                clips=len(results),
                chunks=total_chunks,
                frames=total_frames,
                path=out_root,
            ),
        )

    def _on_error(self, message: str) -> None:
        self._set_busy(False)
        self.log(f"Ошибка: {message}")
        QMessageBox.critical(self, tr("common.content_suite"), message)