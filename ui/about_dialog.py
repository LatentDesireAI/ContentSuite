from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from core.branding import logo_path
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

        self._logo = QLabel()
        self._logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo.setStyleSheet("background: transparent;")

        self._title = QLabel()
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet(
            "font-size: 18px; font-weight: 600; color: #ececec; margin-top: 4px;"
        )

        self._version = QLabel()
        self._version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._version.setStyleSheet("color: #888; font-size: 12px; margin-bottom: 8px;")

        self._body = QLabel()
        self._body.setWordWrap(True)
        self._body.setTextFormat(Qt.TextFormat.RichText)
        self._body.setOpenExternalLinks(True)
        self._body.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self._logo)
        layout.addWidget(self._title)
        layout.addWidget(self._version)
        layout.addWidget(self._body)
        layout.addWidget(self.buttons)

        self._load_logo()

        I18n.instance().language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        self.setWindowTitle(tr("about.title"))
        self._title.setText(APP_NAME)
        self._version.setText(tr("about.version", version=APP_VERSION))
        self._body.setText(
            tr(
                "about.body",
                author=PRIMARY_AUTHOR,
                author_url=PRIMARY_AUTHOR_URL,
                repo_url=REPO_URL,
                ai_label=AI_ASSISTED_LABEL,
                ai_coauthor=AI_COAUTHOR,
                ai_tool=AI_TOOL,
            )
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(tr("common.ok"))

    def _load_logo(self) -> None:
        path = logo_path()
        if not path.is_file():
            self._logo.hide()
            return
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self._logo.hide()
            return
        self._logo.setPixmap(
            pixmap.scaled(
                96,
                96,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self._logo.show()