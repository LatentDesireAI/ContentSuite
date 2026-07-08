from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

from core.app_log import get_logger
from core.config_store import ConfigStore
from ui.folder_picker import FolderPicker
from ui.log_panel import LogPanel


class BaseTab(QWidget):
    """Shared layout: input/output folders + log panel."""

    def __init__(
        self,
        config: ConfigStore,
        parent: QWidget | None = None,
        *,
        input_folder_key: str,
        output_folder_key: str,
        input_label_key: str = "folder.placeholder",
        output_label_key: str = "folder.placeholder",
    ) -> None:
        super().__init__(parent)
        self.config = config
        self._input_folder_key = input_folder_key
        self._output_folder_key = output_folder_key

        self.input_picker = FolderPicker(input_label_key)
        self.output_picker = FolderPicker(output_label_key)
        self.log_panel = LogPanel()

        self.input_picker.set_path(config.folder(input_folder_key))
        self.output_picker.set_path(config.folder(output_folder_key))

        self.input_picker.path_changed.connect(self._on_input_changed)
        self.output_picker.path_changed.connect(self._on_output_changed)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)

        root = QVBoxLayout(self)
        root.addWidget(self.input_picker)
        root.addWidget(self.output_picker)
        root.addWidget(self._content, stretch=1)
        root.addWidget(self.log_panel, stretch=0)

    def content_layout(self) -> QVBoxLayout:
        return self._content_layout

    def log(self, message: str) -> None:
        self.log_panel.append(message)
        get_logger().info("[UI] %s", message)

    def _on_input_changed(self, path: str) -> None:
        self.config.set(self._input_folder_key, path)

    def _on_output_changed(self, path: str) -> None:
        self.config.set(self._output_folder_key, path)