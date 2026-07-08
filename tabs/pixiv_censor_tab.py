from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
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

from core.app_log import get_logger
from core.censor import (
    CensorStore,
    apply_image_censor,
    apply_video_censor,
    collect_censor_media,
    is_image_path,
    is_video_path,
)
from core.config_store import ConfigStore
from core.ffmpeg_wrapper import VideoBatchSummary, VideoJobResult, check_ffmpeg
from core.i18n import I18n, tr
from tabs.base_tab import BaseTab
from ui.censor_editor_dialog import CensorEditorDialog
from ui.censor_media_grid import CensorMediaGrid


class CensorBatchWorker(QThread):
    log_line = Signal(str)
    progress = Signal(int, int)
    finished_ok = Signal(object)
    finished_error = Signal(str)

    def __init__(
        self,
        sources: list[Path],
        output_dir: str,
        base_name: str,
        store: CensorStore,
        options: dict,
    ) -> None:
        super().__init__()
        self.sources = sources
        self.output_dir = output_dir
        self.base_name = base_name
        self.store = store
        self.options = options

    def run(self) -> None:
        try:
            results: list[VideoJobResult] = []
            total = len(self.sources)
            for index, source in enumerate(self.sources, start=1):
                zones = self.store.get_zones(source)
                if not zones:
                    results.append(
                        VideoJobResult(
                            source,
                            None,
                            False,
                            tr("log.censor.no_zones"),
                        )
                    )
                    self.log_line.emit(
                        tr(
                            "log.censor.skip",
                            cur=index,
                            total=total,
                            name=source.name,
                        )
                    )
                    self.progress.emit(index, total)
                    continue

                if is_image_path(source):
                    out_name = f"{self.base_name}_{index}.jpg"
                else:
                    out_name = f"{self.base_name}_{index}.mp4"
                out_path = Path(self.output_dir) / "pixiv" / out_name
                kind = (
                    tr("log.censor.kind_img")
                    if is_image_path(source)
                    else tr("log.censor.kind_vid")
                )
                self.log_line.emit(
                    tr(
                        "log.censor.item",
                        cur=index,
                        total=total,
                        name=source.name,
                        kind=kind,
                        out=out_name,
                        zones=len(zones),
                    )
                )

                if is_image_path(source):
                    apply_image_censor(
                        source,
                        out_path,
                        zones,
                        remove_metadata=self.options.get("remove_metadata", True),
                        author_meta=self.options.get("author_meta"),
                    )
                else:
                    apply_video_censor(
                        source,
                        out_path,
                        zones,
                        output_format="mp4",
                        compression_level=self.options.get("compression_level", "medium"),
                        remove_metadata=self.options.get("remove_metadata", True),
                        author_meta=self.options.get("author_meta"),
                        title=f"{self.base_name}_{index}",
                    )
                results.append(VideoJobResult(source, out_path, True))
                self.progress.emit(index, total)

            processed = sum(1 for r in results if r.success)
            failed = len(results) - processed
            summary = VideoBatchSummary(
                total=total,
                processed=processed,
                failed=failed,
                results=results,
            )
            self.finished_ok.emit(summary)
        except Exception as exc:
            get_logger().exception("CensorBatchWorker crashed")
            self.finished_error.emit(str(exc))


class PixivCensorTab(BaseTab):
    def __init__(self, config: ConfigStore, parent=None) -> None:
        super().__init__(
            config,
            parent,
            input_folder_key="pixiv_censor_input_folder",
            output_folder_key="pixiv_censor_output_folder",
            input_label_key="censor.input",
            output_label_key="censor.output",
        )
        self._worker: CensorBatchWorker | None = None
        self._store = CensorStore()

        ok, msg = check_ffmpeg()
        self._ffmpeg_warn: QLabel | None = None
        if not ok:
            self._ffmpeg_warn = QLabel()
            self._ffmpeg_warn.setStyleSheet("color: #c00;")
            self._ffmpeg_warn.setWordWrap(True)
            self._ffmpeg_msg = msg
            self.content_layout().addWidget(self._ffmpeg_warn)

        self.pack_group = QGroupBox()
        pack_form = QFormLayout(self.pack_group)
        self.base_name_edit = QLineEdit()
        default = config.get("pixiv_censor_base_name", "") or config.get(
            "video_base_name", ""
        )
        self.base_name_edit.setText(default)
        self.base_name_edit.textChanged.connect(
            lambda text: config.set("pixiv_censor_base_name", text)
        )
        self._lbl_pack_prefix = QLabel()
        pack_form.addRow(self._lbl_pack_prefix, self.base_name_edit)

        self.settings_group = QGroupBox()
        settings_form = QFormLayout(self.settings_group)

        self.block_spin = QSpinBox()
        self.block_spin.setRange(4, 64)
        self.block_spin.setValue(int(config.get("pixiv_censor_block_size", 18)))
        self.block_spin.valueChanged.connect(
            lambda v: config.set("pixiv_censor_block_size", v)
        )
        self._lbl_block_default = QLabel()
        settings_form.addRow(self._lbl_block_default, self.block_spin)

        self.editor_btn = QPushButton()
        self.editor_btn.clicked.connect(self._open_editor)

        self.export_btn = QPushButton()
        self.export_btn.clicked.connect(self._start_export)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setVisible(False)

        self._hint = QLabel()
        self._hint.setWordWrap(True)
        self._hint.setStyleSheet("color: #666;")

        self.media_grid = CensorMediaGrid()
        self.media_grid.selection_changed.connect(self._update_buttons)
        self.media_grid.load_finished.connect(self._on_media_loaded)

        row_actions = QHBoxLayout()
        row_actions.addWidget(self.editor_btn)
        row_actions.addWidget(self.export_btn)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.addWidget(self.input_picker)
        left_layout.addWidget(self.output_picker)
        left_layout.addWidget(self.pack_group)
        left_layout.addWidget(self.settings_group)
        left_layout.addLayout(row_actions)
        left_layout.addWidget(self.progress)
        left_layout.addWidget(self._hint)
        left_layout.addStretch()

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setWidget(left_panel)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.media_grid.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        split = QHBoxLayout()
        split.setContentsMargins(0, 0, 0, 0)
        split.setSpacing(10)
        split.addWidget(left_scroll, stretch=1)
        split.addWidget(self.media_grid, stretch=2)

        split_host = QWidget()
        split_host.setLayout(split)

        root = self.layout()
        root.removeWidget(self.input_picker)
        root.removeWidget(self.output_picker)
        self.content_layout().addWidget(split_host, stretch=1)

        self.input_picker.path_changed.connect(self._refresh_file_list)
        self.output_picker.path_changed.connect(self._update_buttons)
        self._refresh_file_list()

        I18n.instance().language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        if self._ffmpeg_warn is not None:
            self._ffmpeg_warn.setText(f"⚠ {self._ffmpeg_msg}")
        self.pack_group.setTitle(tr("censor.pack_group"))
        self.base_name_edit.setPlaceholderText(tr("censor.pack_placeholder"))
        self._lbl_pack_prefix.setText(tr("censor.pack_prefix"))
        self.settings_group.setTitle(tr("censor.group"))
        self._lbl_block_default.setText(tr("censor.block_default"))
        self.block_spin.setToolTip(tr("censor.block_tip"))
        self.editor_btn.setText(tr("censor.btn_editor"))
        self.export_btn.setText(tr("censor.btn_export"))
        self._hint.setText(tr("censor.hint"))

    def _sources(self) -> list[Path]:
        return collect_censor_media(Path(self.input_picker.path()))

    def _selected_sources(self) -> list[Path]:
        selected = self.media_grid.selected_paths()
        if selected:
            return selected
        return self._sources()

    def _is_busy(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    def _set_busy(self, busy: bool) -> None:
        self.editor_btn.setEnabled(not busy)
        self.export_btn.setEnabled(not busy)
        self.progress.setVisible(busy)
        self.media_grid.set_interaction_enabled(not busy)
        if not busy:
            self._update_buttons()

    def _refresh_file_list(self, _path: str = "") -> None:
        if self._is_busy():
            return
        self.media_grid.set_sources(self._sources())
        self._update_buttons()

    def _on_media_loaded(self, _count: int) -> None:
        self._update_buttons()

    def _update_buttons(self) -> None:
        if self._is_busy():
            return
        has_media = self.media_grid.has_media()
        has_output = bool(self.output_picker.path())
        has_selection = bool(self.media_grid.selected_paths())
        self.editor_btn.setEnabled(has_media and has_selection)
        self.export_btn.setEnabled(has_media and has_output)

    def _validate_base_name(self) -> str | None:
        base_name = self.base_name_edit.text().strip()
        if not base_name:
            QMessageBox.warning(self, tr("common.content_suite"), tr("censor.warn_pack_name"))
            return None
        return base_name

    def _open_editor(self) -> None:
        selected = self.media_grid.selected_paths()
        if not selected:
            QMessageBox.warning(
                self,
                tr("common.content_suite"),
                tr("censor.warn_select_item"),
            )
            return
        dialog = CensorEditorDialog(
            selected,
            video_probe_for=self.media_grid.video_probe_for,
            store=self._store,
            default_block_size=self.block_spin.value(),
            parent=self,
        )
        if dialog.exec():
            for path in selected:
                zones = self._store.get_zones(path)
                if zones:
                    self.log(
                        tr(
                            "log.censor.saved",
                            name=path.name,
                            zones=len(zones),
                        )
                    )

    def _start_export(self) -> None:
        sources = self._selected_sources()
        output = self.output_picker.path()
        base_name = self._validate_base_name()
        if not sources:
            QMessageBox.warning(self, tr("common.content_suite"), tr("censor.warn_no_media"))
            return
        if not output:
            QMessageBox.warning(self, tr("common.content_suite"), tr("censor.warn_output"))
            return
        if not base_name:
            return
        if self._is_busy():
            return

        missing = [p for p in sources if not self._store.has_zones(p)]
        if missing:
            names = ", ".join(p.name for p in missing[:3])
            extra = (
                tr("censor.and_more", n=len(missing) - 3)
                if len(missing) > 3
                else ""
            )
            if (
                QMessageBox.question(
                    self,
                    tr("common.content_suite"),
                    tr(
                        "censor.missing_zones",
                        count=len(missing),
                        names=names,
                        extra=extra,
                    ),
                )
                != QMessageBox.StandardButton.Yes
            ):
                return

        video_count = sum(1 for p in sources if is_video_path(p))
        image_count = sum(1 for p in sources if is_image_path(p))
        author_meta = self.config.get_author_metadata()
        self.log_panel.clear()
        self.log(
            tr(
                "log.censor.start",
                videos=video_count,
                images=image_count,
                pack=base_name,
            )
        )
        self._set_busy(True)
        self.progress.setMaximum(len(sources))
        self.progress.setValue(0)

        self._worker = CensorBatchWorker(
            sources,
            output,
            base_name,
            self._store,
            {
                "compression_level": self.config.get(
                    "video_compression_level", "medium"
                ),
                "remove_metadata": self.config.get("video_remove_metadata", True),
                "author_meta": author_meta,
            },
        )
        self._worker.log_line.connect(self.log)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.finished_error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, current: int, total: int) -> None:
        self.progress.setMaximum(total)
        self.progress.setValue(current)

    def _on_finished(self, summary: VideoBatchSummary) -> None:
        self._set_busy(False)
        self.log("—" * 40)
        self.log(
            tr("log.done", done=summary.processed, total=summary.total)
        )
        if summary.failed:
            self.log(tr("log.skipped_failed", failed=summary.failed))
        out_root = Path(self.output_picker.path()) / "pixiv"
        QMessageBox.information(
            self,
            tr("common.content_suite"),
            tr(
                "censor.done",
                done=summary.processed,
                total=summary.total,
                path=out_root,
            ),
        )

    def _on_error(self, message: str) -> None:
        self._set_busy(False)
        self.log(tr("log.error", msg=message))
        QMessageBox.critical(self, tr("common.content_suite"), message)