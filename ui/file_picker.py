from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from core.i18n import I18n, tr


class FilePicker(QWidget):
    path_changed = Signal(str)

    def __init__(
        self,
        label_key: str,
        *,
        file_filter_key: str = "file.filter_json",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._label_key = label_key
        self._file_filter_key = file_filter_key

        self.label = QLabel()
        self.path_edit = QLineEdit()
        self.browse_btn = QPushButton()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        layout.addWidget(self.path_edit, stretch=1)
        layout.addWidget(self.browse_btn)

        self.browse_btn.clicked.connect(self._browse)
        self.path_edit.textChanged.connect(self.path_changed.emit)

        I18n.instance().language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        self.label.setText(tr(self._label_key))
        self.path_edit.setPlaceholderText(tr("file.placeholder"))
        self.browse_btn.setText(tr("common.browse"))

    def path(self) -> str:
        return self.path_edit.text().strip()

    def set_path(self, path: str) -> None:
        self.path_edit.setText(path)

    def _browse(self) -> None:
        start = self.path() or ""
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("file.dialog", label=self.label.text()),
            start,
            tr(self._file_filter_key),
        )
        if path:
            self.set_path(path)