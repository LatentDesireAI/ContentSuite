from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from core.credits import (
    AI_ASSISTED_LABEL,
    AI_COAUTHOR,
    AI_TOOL,
    APP_NAME,
    APP_VERSION,
    PRIMARY_AUTHOR,
    PRIMARY_AUTHOR_URL,
    REPO_URL,
)
from core.i18n import I18n, tr


class AboutDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(420)

        self._body = QLabel()
        self._body.setWordWrap(True)
        self._body.setTextFormat(Qt.TextFormat.RichText)
        self._body.setOpenExternalLinks(True)
        self._body.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self._body)
        layout.addWidget(self.buttons)

        I18n.instance().language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        self.setWindowTitle(tr("about.title"))
        self._body.setText(
            tr(
                "about.body",
                app=APP_NAME,
                version=APP_VERSION,
                author=PRIMARY_AUTHOR,
                author_url=PRIMARY_AUTHOR_URL,
                repo_url=REPO_URL,
                ai_label=AI_ASSISTED_LABEL,
                ai_coauthor=AI_COAUTHOR,
                ai_tool=AI_TOOL,
            )
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(tr("common.ok"))