"""Lightweight UI translation manager."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from core.i18n_catalog import SUPPORTED_LANGUAGES, TRANSLATIONS

DEFAULT_LANGUAGE = "en"


class I18n(QObject):
    language_changed = Signal(str)

    _instance: I18n | None = None

    def __init__(self) -> None:
        super().__init__()
        self._language = DEFAULT_LANGUAGE

    @classmethod
    def instance(cls) -> I18n:
        if cls._instance is None:
            cls._instance = I18n()
        return cls._instance

    @property
    def language(self) -> str:
        return self._language

    def set_language(self, code: str) -> None:
        if code not in TRANSLATIONS:
            code = DEFAULT_LANGUAGE
        if code == self._language:
            return
        self._language = code
        self.language_changed.emit(code)

    def tr(self, key: str, **kwargs: object) -> str:
        table = TRANSLATIONS.get(self._language) or TRANSLATIONS[DEFAULT_LANGUAGE]
        text = table.get(key) or TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
        if kwargs:
            return text.format(**kwargs)
        return text


def tr(key: str, **kwargs: object) -> str:
    return I18n.instance().tr(key, **kwargs)


def init_language(config) -> None:
    saved = str(config.get("ui_language", DEFAULT_LANGUAGE) or DEFAULT_LANGUAGE)
    if saved not in TRANSLATIONS:
        saved = DEFAULT_LANGUAGE
    I18n.instance()._language = saved


def set_language(config, code: str) -> None:
    I18n.instance().set_language(code)
    config.set("ui_language", I18n.instance().language)