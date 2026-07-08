"""Session log file — truncated on every application start."""

from __future__ import annotations

import atexit
import faulthandler
import logging
import platform
import sys
import threading
import traceback
from pathlib import Path
from typing import TextIO

from core.config_store import APP_NAME, config_path

_logger: logging.Logger | None = None
_log_fp: TextIO | None = None


def log_file_path() -> Path:
    return config_path().parent / "contentsuite.log"


def get_logger() -> logging.Logger:
    if _logger is None:
        return setup_app_logging()
    return _logger


def setup_app_logging() -> logging.Logger:
    global _logger, _log_fp

    if _logger is not None:
        return _logger

    path = log_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(APP_NAME)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.handlers.clear()

    handler = logging.FileHandler(path, mode="w", encoding="utf-8")
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)

    _log_fp = open(path, "a", encoding="utf-8")  # noqa: SIM115
    faulthandler.enable(file=_log_fp, all_threads=True)

    _install_excepthook(logger)
    _install_thread_excepthook(logger)
    atexit.register(_on_exit)

    logger.info("=== ContentSuite session start ===")
    logger.info("Python: %s", sys.version.replace("\n", " "))
    logger.info("Platform: %s", platform.platform())
    logger.info("Executable: %s", sys.executable)
    logger.info("CWD: %s", Path.cwd())
    logger.info("Args: %s", sys.argv)
    logger.info("Log file: %s", path.resolve())

    _logger = logger
    return logger


def install_qt_message_handler() -> None:
    """Call once after PySide6 is importable (before or after QApplication)."""
    try:
        from PySide6.QtCore import QtMsgType, qInstallMessageHandler
    except ImportError:
        get_logger().warning("PySide6 unavailable — Qt log hook skipped")
        return

    level_map = {
        QtMsgType.QtDebugMsg: logging.DEBUG,
        QtMsgType.QtInfoMsg: logging.INFO,
        QtMsgType.QtWarningMsg: logging.WARNING,
        QtMsgType.QtCriticalMsg: logging.ERROR,
        QtMsgType.QtFatalMsg: logging.CRITICAL,
    }

    logger = get_logger()

    def _handler(mode, context, message) -> None:  # noqa: ANN001
        level = level_map.get(mode, logging.INFO)
        where = ""
        if context.file:
            where = f" ({context.file}:{context.line})"
        logger.log(level, "Qt%s: %s", where, message)

    qInstallMessageHandler(_handler)
    logger.debug("Qt message handler installed")


def _install_excepthook(logger: logging.Logger) -> None:
    def _hook(exc_type, exc_value, exc_tb) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            logger.info("KeyboardInterrupt")
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        logger.critical(
            "Uncaught exception:\n%s",
            "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
        )
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _hook


def _install_thread_excepthook(logger: logging.Logger) -> None:
    if not hasattr(threading, "excepthook"):
        return

    def _hook(args: threading.ExceptHookArgs) -> None:
        logger.critical(
            "Thread exception in %s:\n%s",
            args.thread.name,
            "".join(
                traceback.format_exception(
                    args.exc_type, args.exc_value, args.exc_traceback
                )
            ),
        )
        threading.__excepthook__(args)

    threading.excepthook = _hook


def _on_exit() -> None:
    logger = get_logger()
    logger.info("=== ContentSuite exit ===")
    for handler in logger.handlers:
        handler.flush()
    global _log_fp
    if _log_fp is not None:
        faulthandler.disable()
        _log_fp.flush()
        _log_fp.close()
        _log_fp = None