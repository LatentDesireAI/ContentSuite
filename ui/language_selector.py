"""Globe + language label with dropdown menu."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenu, QToolButton, QWidget

from core.config_store import ConfigStore
from core.i18n import I18n, set_language, tr
from core.i18n_catalog import SUPPORTED_LANGUAGES as _LANGS


class LanguageSelector(QWidget):
    def __init__(self, config: ConfigStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = config

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(6)

        self.globe = QLabel("🌐")
        self.globe.setStyleSheet("font-size: 16px;")
        self.globe.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.globe.setCursor(Qt.CursorShape.PointingHandCursor)
        self.globe.setToolTip("")

        self.button = QToolButton()
        self.button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.button.setAutoRaise(True)
        self.button.setCursor(Qt.CursorShape.PointingHandCursor)

        self._menu = QMenu(self)
        self._actions: dict[str, object] = {}
        for code, label_key in _LANGS:
            action = self._menu.addAction("")
            action.setData(code)
            action.triggered.connect(lambda checked=False, c=code: self._pick(c))
            self._actions[code] = action
        self.button.setMenu(self._menu)

        layout.addWidget(self.globe)
        layout.addWidget(self.button)

        I18n.instance().language_changed.connect(self._retranslate)
        self._retranslate(I18n.instance().language)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.button.showMenu()
        super().mousePressEvent(event)

    def _pick(self, code: str) -> None:
        set_language(self.config, code)

    def _retranslate(self, _code: str = "") -> None:
        self.button.setText(tr("lang.label"))
        for code, label_key in _LANGS:
            action = self._actions.get(code)
            if action is not None:
                action.setText(tr(label_key))