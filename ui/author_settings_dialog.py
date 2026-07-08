from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from core.config_store import ConfigStore
from core.i18n import I18n, tr


class AuthorSettingsDialog(QDialog):
    def __init__(self, config: ConfigStore, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self.setMinimumWidth(480)

        self.intro = QLabel()
        self.intro.setWordWrap(True)

        self.enabled_check = QCheckBox()
        self.enabled_check.setChecked(bool(config.get("embed_author_metadata", False)))

        self.author_edit = QLineEdit(config.get("author_name", ""))
        self.website_edit = QLineEdit(config.get("author_website", ""))
        self.copyright_edit = QLineEdit(config.get("author_copyright", ""))
        self.description_edit = QLineEdit(config.get("author_description", ""))

        self._lbl_author = QLabel()
        self._lbl_website = QLabel()
        self._lbl_copyright = QLabel()
        self._lbl_description = QLabel()

        form = QFormLayout()
        form.addRow(self._lbl_author, self.author_edit)
        form.addRow(self._lbl_website, self.website_edit)
        form.addRow(self._lbl_copyright, self.copyright_edit)
        form.addRow(self._lbl_description, self.description_edit)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self._save)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.intro)
        layout.addWidget(self.enabled_check)
        layout.addLayout(form)
        layout.addWidget(self.buttons)

        I18n.instance().language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        self.setWindowTitle(tr("author.title"))
        self.intro.setText(tr("author.intro"))
        self.enabled_check.setText(tr("author.enabled"))
        self._lbl_author.setText(tr("author.name"))
        self._lbl_website.setText(tr("author.website"))
        self._lbl_copyright.setText(tr("author.copyright"))
        self._lbl_description.setText(tr("author.description"))
        self.author_edit.setPlaceholderText(tr("author.name_ph"))
        self.website_edit.setPlaceholderText(tr("author.website_ph"))
        self.copyright_edit.setPlaceholderText(tr("author.copyright_ph"))
        self.description_edit.setPlaceholderText(tr("author.description_ph"))
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setText(tr("common.save"))
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("common.cancel"))

    def _save(self) -> None:
        self.config.update({
            "embed_author_metadata": self.enabled_check.isChecked(),
            "author_name": self.author_edit.text().strip(),
            "author_website": self.website_edit.text().strip(),
            "author_copyright": self.copyright_edit.text().strip(),
            "author_description": self.description_edit.text().strip(),
        })
        self.accept()