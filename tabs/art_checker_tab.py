from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QFileSystemWatcher
from PySide6.QtGui import QClipboard
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.app_log import get_logger
from core.art_checker import ArtRow, ArtScanResult, scan_arts, sort_art_rows
from core.config_store import ConfigStore
from core.i18n import I18n, tr
from ui.art_checker_grid import ArtCheckerGrid, ArtGridItem
from ui.file_picker import FilePicker
from ui.folder_picker import FolderPicker
from ui.log_panel import LogPanel

_RESCAN_DEBOUNCE_MS = 900


class ArtCheckerTab(QWidget):
    def __init__(self, config: ConfigStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self._result: ArtScanResult | None = None
        self._scan_root = Path()

        self._rescan_timer = QTimer(self)
        self._rescan_timer.setSingleShot(True)
        self._rescan_timer.setInterval(_RESCAN_DEBOUNCE_MS)
        self._rescan_timer.timeout.connect(self._run_scan)

        self._watcher = QFileSystemWatcher(self)
        self._watcher.directoryChanged.connect(self._on_folder_activity)

        root = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter, stretch=1)

        controls = QWidget()
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        self.json_picker = FilePicker("art_checker.json")
        self.json_picker.set_path(str(config.get("art_checker_json_path", "") or ""))
        self.json_picker.path_changed.connect(self._on_json_changed)

        self.folder_picker = FolderPicker("art_checker.scan_folder")
        self.folder_picker.set_path(config.folder("art_checker_scan_folder"))
        self.folder_picker.path_changed.connect(self._on_folder_changed)

        action_row = QHBoxLayout()
        self.refresh_btn = QPushButton()
        self.refresh_btn.clicked.connect(self._run_scan)
        self.auto_watch_cb = QCheckBox()
        self.auto_watch_cb.setChecked(bool(config.get("art_checker_auto_watch", True)))
        self.auto_watch_cb.toggled.connect(self._on_auto_watch_changed)
        action_row.addWidget(self.refresh_btn)
        action_row.addWidget(self.auto_watch_cb)
        action_row.addStretch()

        search_row = QHBoxLayout()
        self._lbl_search = QLabel()
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self._refresh_grid)
        search_row.addWidget(self._lbl_search)
        search_row.addWidget(self.search_edit, stretch=1)

        copy_row = QHBoxLayout()
        self.copy_name_btn = QPushButton()
        self.copy_name_btn.clicked.connect(self._copy_selected_name)
        self.copy_missing_btn = QPushButton()
        self.copy_missing_btn.clicked.connect(self._copy_all_missing)
        copy_row.addWidget(self.copy_name_btn)
        copy_row.addWidget(self.copy_missing_btn)
        copy_row.addStretch()

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)

        self._extra_group = QGroupBox()
        extra_layout = QVBoxLayout(self._extra_group)
        self.extra_label = QLabel()
        self.extra_label.setWordWrap(True)
        self.extra_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        extra_layout.addWidget(self.extra_label)

        controls_layout.addWidget(self.json_picker)
        controls_layout.addWidget(self.folder_picker)
        controls_layout.addLayout(action_row)
        controls_layout.addLayout(search_row)
        controls_layout.addLayout(copy_row)
        controls_layout.addWidget(self.summary_label)
        controls_layout.addWidget(self._extra_group, stretch=1)

        arts_panel = QWidget()
        arts_layout = QVBoxLayout(arts_panel)
        arts_layout.setContentsMargins(0, 0, 0, 0)

        self._arts_group = QGroupBox()
        arts_group_layout = QVBoxLayout(self._arts_group)
        self.art_grid = ArtCheckerGrid()
        self.art_grid.set_filter_mode(
            str(config.get("art_checker_filter", "all") or "all")
        )
        self.art_grid.set_sort_mode(
            str(config.get("art_checker_sort", "name") or "name")
        )
        self.art_grid.selection_changed.connect(self._update_copy_buttons)
        self.art_grid.copy_requested.connect(self._copy_row_name)
        self.art_grid.filter_changed.connect(self._on_filter_changed)
        self.art_grid.sort_changed.connect(self._on_sort_changed)
        arts_group_layout.addWidget(self.art_grid)
        arts_layout.addWidget(self._arts_group)

        splitter.addWidget(controls)
        splitter.addWidget(arts_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 760])

        self.log_panel = LogPanel()
        root.addWidget(self.log_panel, stretch=0)

        I18n.instance().language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()
        self._update_watch_paths()
        if self.json_picker.path() and self.folder_picker.path():
            self._run_scan()

    def retranslate_ui(self) -> None:
        self.refresh_btn.setText(tr("art_checker.refresh"))
        self.auto_watch_cb.setText(tr("art_checker.auto_watch"))
        self.auto_watch_cb.setToolTip(tr("art_checker.auto_watch_tip"))
        self._lbl_search.setText(tr("art_checker.search"))
        self.copy_name_btn.setText(tr("art_checker.copy_name"))
        self.copy_missing_btn.setText(tr("art_checker.copy_missing"))
        self._extra_group.setTitle(tr("art_checker.extra_group"))
        self._arts_group.setTitle(tr("art_checker.arts_group"))
        self.art_grid.retranslate_ui()
        self._refresh_summary()
        self._refresh_extra()
        self._update_copy_buttons()

    def log(self, message: str) -> None:
        self.log_panel.append(message)
        get_logger().info("[ArtChecker] %s", message)

    def _on_json_changed(self, path: str) -> None:
        self.config.set("art_checker_json_path", path)
        self._schedule_rescan()

    def _on_folder_changed(self, path: str) -> None:
        self.config.set("art_checker_scan_folder", path)
        self._update_watch_paths()
        self._schedule_rescan()

    def _on_auto_watch_changed(self, enabled: bool) -> None:
        self.config.set("art_checker_auto_watch", enabled)
        self._update_watch_paths()

    def _on_filter_changed(self) -> None:
        self.config.set("art_checker_filter", self.art_grid.filter_mode())
        self._refresh_grid()

    def _on_sort_changed(self) -> None:
        self.config.set("art_checker_sort", self.art_grid.sort_mode())
        self._refresh_grid()

    def _update_watch_paths(self) -> None:
        self._sync_watch_paths()

    def _sync_watch_paths(self) -> None:
        for path in self._watcher.directories():
            self._watcher.removePath(path)

        if not self.auto_watch_cb.isChecked():
            return

        folder = self.folder_picker.path().strip()
        root = Path(folder)
        if not root.is_dir():
            return

        paths = [str(root)]
        for sub in root.rglob("*"):
            if sub.is_dir():
                paths.append(str(sub))
        for path in paths[:256]:
            if path not in self._watcher.directories():
                self._watcher.addPath(path)

    def _on_folder_activity(self, _path: str) -> None:
        if self.auto_watch_cb.isChecked():
            self._schedule_rescan()

    def _schedule_rescan(self) -> None:
        if not self.json_picker.path().strip() or not self.folder_picker.path().strip():
            return
        self._rescan_timer.start()

    def _run_scan(self) -> None:
        json_path = Path(self.json_picker.path().strip())
        scan_root = Path(self.folder_picker.path().strip())

        if not json_path.is_file():
            if self.json_picker.path().strip():
                QMessageBox.warning(
                    self, tr("common.content_suite"), tr("art_checker.warn_json")
                )
            return

        try:
            self._result = scan_arts(json_path, scan_root)
            self._scan_root = scan_root
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, tr("common.content_suite"), str(exc))
            get_logger().exception("Art checker scan failed")
            return

        self._refresh_summary()
        self._refresh_extra()
        self._refresh_grid()
        self._sync_watch_paths()
        self.log(tr("art_checker.scan_done", **self._summary_kwargs()))

    def _summary_kwargs(self) -> dict:
        if not self._result:
            return {
                "total": 0,
                "files": 0,
                "present": 0,
                "missing": 0,
                "extra": 0,
            }
        r = self._result
        return {
            "total": r.total_in_json,
            "files": r.total_files_unique,
            "present": r.present_count,
            "missing": r.missing_count,
            "extra": len(r.extra_files_not_in_json),
        }

    def _refresh_summary(self) -> None:
        if not self._result:
            self.summary_label.setText(tr("art_checker.summary_idle"))
            return
        self.summary_label.setText(tr("art_checker.summary", **self._summary_kwargs()))

    def _refresh_extra(self) -> None:
        if not self._result or not self._result.extra_files_not_in_json:
            self.extra_label.setText(tr("art_checker.extra_none"))
            return
        lines = self._result.extra_files_not_in_json[:40]
        text = "\n".join(lines)
        if len(self._result.extra_files_not_in_json) > 40:
            text += tr(
                "art_checker.extra_more",
                count=len(self._result.extra_files_not_in_json) - 40,
            )
        self.extra_label.setText(text)

    def _filtered_rows(self) -> list[ArtRow]:
        if not self._result:
            return []
        mode = self.art_grid.filter_mode()
        query = self.search_edit.text().strip().lower()
        rows = self._result.all_arts
        if mode == "missing":
            rows = [row for row in rows if row.status == "missing"]
        elif mode == "present":
            rows = [row for row in rows if row.status == "present"]
        elif mode in {"sfw", "nsfw", "sex"}:
            rows = [row for row in rows if row.section == mode]
        if query:
            rows = [
                row
                for row in rows
                if query in row.name.lower() or query in row.section.lower()
            ]
        return rows

    def _refresh_grid(self) -> None:
        rows = sort_art_rows(
            self._filtered_rows(),
            self.art_grid.sort_mode(),
            self._scan_root,
        )
        items: list[ArtGridItem] = []
        for row in rows:
            image_paths: list[Path] = []
            if row.files and self._scan_root.is_dir():
                for rel in row.files:
                    candidate = self._scan_root / rel
                    if candidate.is_file():
                        image_paths.append(candidate)
            items.append(ArtGridItem(row=row, image_paths=tuple(image_paths)))
        self.art_grid.set_items(items)
        self._update_copy_buttons()

    def _update_copy_buttons(self) -> None:
        has_selection = self.art_grid.selected_row() is not None
        self.copy_name_btn.setEnabled(has_selection)
        self.copy_missing_btn.setEnabled(
            bool(self._result and self._result.missing)
        )

    def _clipboard(self) -> QClipboard | None:
        app = QApplication.instance()
        return app.clipboard() if app is not None else None

    def _copy_text(self, text: str, hint_key: str, **kwargs) -> None:
        clip = self._clipboard()
        if clip is None or not text:
            return
        clip.setText(text)
        self.log(tr(hint_key, **kwargs))

    def _copy_row_name(self, row: ArtRow) -> None:
        if row.name:
            self._copy_text(row.name, "art_checker.copied_one", name=row.name)

    def _copy_selected_name(self) -> None:
        row = self.art_grid.selected_row()
        if row and row.name:
            self._copy_row_name(row)

    def _copy_all_missing(self) -> None:
        if not self._result or not self._result.missing:
            return
        text = "\n".join(row.name for row in self._result.missing if row.name)
        self._copy_text(text, "art_checker.copied_missing", count=len(self._result.missing))