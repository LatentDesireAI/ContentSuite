"""ContentSuite — desktop tool for Patreon / Pixiv / X content preparation.

AI-Assisted · co-developed with Grok (xAI) via Cursor.
"""

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMainWindow, QSizePolicy, QTabWidget, QToolBar, QWidget

from core.app_log import get_logger, install_qt_message_handler, log_file_path, setup_app_logging
from core.config_store import ConfigStore
from core.branding import apply_windows_app_identity, load_app_icon
from core.credits import AI_ASSISTED_LABEL
from core.i18n import I18n, init_language, tr
from core.thumb_cache import prune_all_thumbnail_caches
from tabs.images_tab import ImagesTab
from tabs.pixiv_censor_tab import PixivCensorTab
from tabs.pixiv_preview_tab import PixivPreviewTab
from tabs.video_tab import VideoTab
from ui.about_dialog import AboutDialog
from ui.author_settings_dialog import AuthorSettingsDialog
from ui.language_selector import LanguageSelector

_TAB_KEYS = (
    "tab.images",
    "tab.pixiv_preview",
    "tab.video",
    "tab.pixiv_censor",
)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        log = get_logger()
        log.info("Initializing MainWindow")
        self.config = ConfigStore()
        init_language(self.config)

        self.resize(1200, 820)

        self.tabs = QTabWidget()
        self._tab_widgets = (
            ImagesTab(self.config),
            PixivPreviewTab(self.config),
            VideoTab(self.config),
            PixivCensorTab(self.config),
        )
        for widget in self._tab_widgets:
            self.tabs.addTab(widget, "")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.setCentralWidget(self.tabs)

        toolbar = QToolBar()
        toolbar.setMovable(False)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        toolbar.addWidget(LanguageSelector(self.config))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        self._settings_menu = self.menuBar().addMenu("")
        self._author_action = QAction("", self)
        self._author_action.triggered.connect(self._open_author_settings)
        self._settings_menu.addAction(self._author_action)
        self._log_action = QAction("", self)
        self._log_action.triggered.connect(self._open_session_log)
        self._settings_menu.addAction(self._log_action)
        self._settings_menu.addSeparator()
        self._about_action = QAction("", self)
        self._about_action.triggered.connect(self._open_about)
        self._settings_menu.addAction(self._about_action)

        I18n.instance().language_changed.connect(self._retranslate_ui)
        self._retranslate_ui()
        log.info("MainWindow ready")

    def _retranslate_ui(self, _code: str = "") -> None:
        self.setWindowTitle(f"{tr('common.content_suite')} · {AI_ASSISTED_LABEL}")
        self._settings_menu.setTitle(tr("menu.settings"))
        self._author_action.setText(tr("menu.author_metadata"))
        self._log_action.setText(tr("menu.open_log"))
        self._about_action.setText(tr("menu.about"))
        for index, key in enumerate(_TAB_KEYS):
            self.tabs.setTabText(index, tr(key))
        for widget in self._tab_widgets:
            if hasattr(widget, "retranslate_ui"):
                widget.retranslate_ui()

    def _open_about(self) -> None:
        AboutDialog(self).exec()

    def _open_author_settings(self) -> None:
        get_logger().info("Opening author settings dialog")
        dialog = AuthorSettingsDialog(self.config, self)
        dialog.exec()

    def _open_session_log(self) -> None:
        import os

        path = log_file_path()
        get_logger().info("Opening session log: %s", path)
        if path.is_file():
            os.startfile(path)
        elif path.parent.is_dir():
            os.startfile(path.parent)

    def _on_tab_changed(self, index: int) -> None:
        tab = self.tabs.widget(index)
        title = self.tabs.tabText(index)
        get_logger().info("Tab switched: %s (%s)", title, type(tab).__name__)


def main() -> int:
    log = setup_app_logging()
    install_qt_message_handler()
    prune_summary = prune_all_thumbnail_caches()
    if prune_summary.deleted_files:
        log.info(
            "Thumbnail cache pruned: %d file(s), %.1f MB freed",
            prune_summary.deleted_files,
            prune_summary.freed_bytes / 1024 / 1024,
        )
    try:
        apply_windows_app_identity()
        log.info("Creating QApplication")
        app = QApplication(sys.argv)
        app.setApplicationName("ContentSuite")
        app_icon = load_app_icon()
        if app_icon is not None:
            app.setWindowIcon(app_icon)
        window = MainWindow()
        if app_icon is not None:
            window.setWindowIcon(app_icon)
        window.show()
        log.info("Event loop started (log: %s)", log_file_path())
        code = app.exec()
        log.info("Event loop finished, code=%s", code)
        return code
    except Exception:
        log.exception("Fatal error in main()")
        raise


if __name__ == "__main__":
    raise SystemExit(main())