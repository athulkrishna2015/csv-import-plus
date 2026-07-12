# -*- coding: utf-8 -*-

from aqt import mw
from aqt.qt import (
    Qt,
    QVBoxLayout,
    QWidget,
    QLabel,
    QFormLayout,
    QCheckBox,
)

CONFIG_KEY_CONFIRM_CLIPBOARD_QUICK_IMPORT = "confirm_clipboard_quick_import"
CONFIG_KEY_ALLOW_ANY_CLIPBOARD_QUICK_IMPORT = "allow_any_clipboard_quick_import"

class AdvancedTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dialog = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        hint = QLabel(
            "Advanced options for deck locking, header handling, clipboard behavior, and the built-in Anki importer.",
            self,
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(10)
        layout.addLayout(form)

        self.deck_lock_check = QCheckBox("Lock Target Deck", self)
        self.deck_lock_check.toggled.connect(self.on_deck_lock_toggled)
        form.addRow("", self.deck_lock_check)

        self.header_check = QCheckBox("First row is header", self)
        self.header_check.toggled.connect(self.on_header_check_toggled)
        form.addRow("", self.header_check)

        self.remember_history_check = QCheckBox("Remember history until manually cleared", self)
        self.remember_history_check.toggled.connect(self.on_remember_history_toggled)
        form.addRow("", self.remember_history_check)

        self.allow_any_clipboard_toggle = QCheckBox(
            "Allow quick import of any clipboard text", self
        )
        self.allow_any_clipboard_toggle.setToolTip(
            "Enable Quick Import Clipboard for any non-empty clipboard text, even if it does not look like CSV."
        )
        self.allow_any_clipboard_toggle.toggled.connect(
            self.on_allow_any_clipboard_toggled
        )
        form.addRow("", self.allow_any_clipboard_toggle)

        self.clipboard_confirm_toggle = QCheckBox(
            "Confirm clipboard quick import", self
        )
        self.clipboard_confirm_toggle.setToolTip(
            "Ask for confirmation before importing clipboard content."
        )
        self.clipboard_confirm_toggle.toggled.connect(self.on_clipboard_confirm_toggled)
        form.addRow("", self.clipboard_confirm_toggle)

        self.disable_notetype_auto_detect_check = QCheckBox(
            "Disable Note Type Auto-Detection", self
        )
        self.disable_notetype_auto_detect_check.setToolTip(
            "Prevent the addon from automatically changing the Note Type dropdown when CSV content is loaded."
        )
        self.disable_notetype_auto_detect_check.toggled.connect(
            lambda _: self.dialog.save_config() if hasattr(self.dialog, "save_config") else None
        )
        form.addRow("", self.disable_notetype_auto_detect_check)

        self.disable_delimiter_auto_detect_check = QCheckBox(
            "Disable Delimiter Auto-Detection", self
        )
        self.disable_delimiter_auto_detect_check.setToolTip(
            "Prevent the addon from automatically guessing the CSV column separator when content is loaded."
        )
        self.disable_delimiter_auto_detect_check.toggled.connect(
            lambda _: self.dialog.save_config() if hasattr(self.dialog, "save_config") else None
        )
        form.addRow("", self.disable_delimiter_auto_detect_check)

        layout.addStretch()

    def load_config(self, config):
        self.deck_lock_check.blockSignals(True)
        self.deck_lock_check.setChecked(config.get("deck_lock", False))
        self.deck_lock_check.blockSignals(False)

        self.header_check.blockSignals(True)
        self.header_check.setChecked(config.get("first_row_header", False))
        self.header_check.blockSignals(False)

        self.remember_history_check.blockSignals(True)
        self.remember_history_check.setChecked(config.get("remember_history", False))
        self.remember_history_check.blockSignals(False)

        self.allow_any_clipboard_toggle.blockSignals(True)
        self.allow_any_clipboard_toggle.setChecked(
            config.get(CONFIG_KEY_ALLOW_ANY_CLIPBOARD_QUICK_IMPORT, False)
        )
        self.allow_any_clipboard_toggle.blockSignals(False)

        self.clipboard_confirm_toggle.blockSignals(True)
        self.clipboard_confirm_toggle.setChecked(
            config.get(CONFIG_KEY_CONFIRM_CLIPBOARD_QUICK_IMPORT, False)
        )
        self.clipboard_confirm_toggle.blockSignals(False)

        self.disable_notetype_auto_detect_check.blockSignals(True)
        self.disable_notetype_auto_detect_check.setChecked(
            config.get("disable_notetype_auto_detect", False)
        )
        self.disable_notetype_auto_detect_check.blockSignals(False)

        self.disable_delimiter_auto_detect_check.blockSignals(True)
        self.disable_delimiter_auto_detect_check.setChecked(
            config.get("disable_delimiter_auto_detect", False)
        )
        self.disable_delimiter_auto_detect_check.blockSignals(False)

    def save_config(self, config):
        config["deck_lock"] = self.deck_lock_check.isChecked()
        config["first_row_header"] = self.header_check.isChecked()
        config["remember_history"] = self.remember_history_check.isChecked()
        config[CONFIG_KEY_ALLOW_ANY_CLIPBOARD_QUICK_IMPORT] = self.allow_any_clipboard_toggle.isChecked()
        config[CONFIG_KEY_CONFIRM_CLIPBOARD_QUICK_IMPORT] = self.clipboard_confirm_toggle.isChecked()
        config["disable_notetype_auto_detect"] = self.disable_notetype_auto_detect_check.isChecked()
        config["disable_delimiter_auto_detect"] = self.disable_delimiter_auto_detect_check.isChecked()

    def on_deck_lock_toggled(self, checked):
        if hasattr(self.dialog, "on_deck_lock_toggled"):
            self.dialog.on_deck_lock_toggled(checked)

    def on_clipboard_confirm_toggled(self, checked):
        if hasattr(self.dialog, "on_clipboard_confirm_toggled"):
            self.dialog.on_clipboard_confirm_toggled(checked)

    def on_allow_any_clipboard_toggled(self, checked):
        if hasattr(self.dialog, "on_allow_any_clipboard_toggled"):
            self.dialog.on_allow_any_clipboard_toggled(checked)

    def on_header_check_toggled(self, checked):
        if hasattr(self.dialog, "on_header_check_toggled"):
            self.dialog.on_header_check_toggled(checked)

    def on_remember_history_toggled(self, checked):
        if hasattr(self.dialog, "on_remember_history_toggled"):
            self.dialog.on_remember_history_toggled(checked)
