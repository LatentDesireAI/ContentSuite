"""App logo path — works in dev and PyInstaller bundle."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon

LOGO_FILENAME = "contentsuite_icon.png"
ICO_FILENAME = "contentsuite.ico"
LOGO_RELATIVE = f"assets/{LOGO_FILENAME}"
ICO_RELATIVE = f"assets/{ICO_FILENAME}"
WIN_APP_USER_MODEL_ID = "LatentDesireAI.ContentSuite.1"


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parent.parent


def logo_path() -> Path:
    return app_root() / LOGO_RELATIVE


def app_icon_path() -> Path | None:
    """Best icon file for the OS (ICO on Windows for taskbar sizes)."""
    root = app_root()
    if sys.platform == "win32":
        ico = root / ICO_RELATIVE
        if ico.is_file():
            return ico
    png = root / LOGO_RELATIVE
    if png.is_file():
        return png
    ico = root / ICO_RELATIVE
    return ico if ico.is_file() else None


def load_app_icon() -> QIcon | None:
    path = app_icon_path()
    if path is None:
        return None
    icon = QIcon(str(path))
    return None if icon.isNull() else icon


def apply_windows_app_identity() -> None:
    """
    Separate ContentSuite from pythonw.exe in the Windows taskbar.

    Must run before QApplication is created.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            WIN_APP_USER_MODEL_ID
        )
    except Exception:
        pass