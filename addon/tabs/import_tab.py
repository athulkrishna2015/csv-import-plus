# -*- coding: utf-8 -*-

import os
from aqt import mw
from aqt.qt import (
    QApplication,
    QComboBox,
    QCompleter,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
    Qt,
)

class ImportTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dialog = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        instr = QLabel(
            "Paste CSV or choose a CSV file, adjust options, pick deck and note type, then import.<br>"
            "Supported delimiters: comma, tab, semicolon, pipe. Directives: #notetype:Basic or #notetype:Cloze<br>"
            "Quick Import adds notes directly; use Advanced for options.<br><br>"
            "<b>Tips:</b> Generate CSV using <a href='https://gemini.google.com/gem/1k_mMJwsDi040LcxEdTsReGiZnomCv5VQ?usp=sharing'>Gemini CSV Creator</a> "
            "or <a href='https://chatgpt.com/g/g-6970ad9011508191a896ddf804f3eb2b-anki-flsh-card-gen-v46'>Custom GPT</a>."
        )
        instr.setWordWrap(True)
        instr.setOpenExternalLinks(True)
        instr.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(instr)

        # File picker row
        file_row_w = QWidget(self)
        file_row = QHBoxLayout(file_row_w)
        file_row.setContentsMargins(0, 0, 0, 0)

        self.file_edit = QLineEdit(self)
        self.file_edit.setReadOnly(True)
        self.file_edit.setPlaceholderText("No file selected…")

        self.browse_btn = QPushButton("Browse…", self)
        self.browse_btn.clicked.connect(self.on_pick_file)

        file_row.addWidget(QLabel("CSV file:", self))
        file_row.addWidget(self.file_edit, 1)
        file_row.addWidget(self.browse_btn, 0)
        layout.addWidget(file_row_w)

        # Paste area
        content_header = QWidget(self)
        content_header_row = QHBoxLayout(content_header)
        content_header_row.setContentsMargins(0, 0, 0, 0)
        content_header_row.addWidget(QLabel("CSV content:", self))
        content_header_row.addStretch()

        self.paste_clipboard_btn = QPushButton("Paste Clipboard", self)
        self.paste_clipboard_btn.clicked.connect(self.on_paste_clipboard)
        content_header_row.addWidget(self.paste_clipboard_btn, 0)

        self.quick_clipboard_btn = QPushButton("Quick Import Clipboard", self)
        self.quick_clipboard_btn.clicked.connect(self.on_quick_import_clipboard)
        content_header_row.addWidget(self.quick_clipboard_btn, 0)

        layout.addWidget(content_header)
        self.csv_text = QPlainTextEdit(self)
        self.csv_text.setPlaceholderText(
            "Paste CSV here...\n\n"
            "#notetype:Basic\n"
            "Front,Back,Tags\n"
            "What is 2+2?,4,math\n\n"
            "Or:\n"
            "#notetype:Cloze\n"
            "Text,Extra,Tags\n"
            "{{c1::Humans}} landed on the moon in {{c1::1969}}.,,space"
        )
        self.csv_text.textChanged.connect(self.on_csv_text_changed)
        layout.addWidget(self.csv_text, 1)

        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #21808D; font-weight: 500;")
        layout.addWidget(self.status_label)

        # Settings
        settings_group = QGroupBox("Import Settings", self)
        settings_form = QFormLayout(settings_group)

        # Deck combo
        deck_container = QWidget(self)
        deck_row = QHBoxLayout(deck_container)
        deck_row.setContentsMargins(0, 0, 0, 0)
        self.deck_combo = QComboBox(self)
        self.deck_combo.setEditable(True)
        self.deck_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        self.completer = QCompleter(self.deck_combo.model(), self.deck_combo)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.deck_combo.setCompleter(self.completer)
        
        deck_row.addWidget(self.deck_combo, 1)
        settings_form.addRow("Target Deck:", deck_container)

        # Subdeck creation
        subdeck_container = QWidget(self)
        subdeck_row = QHBoxLayout(subdeck_container)
        subdeck_row.setContentsMargins(0, 0, 0, 0)

        self.subdeck_edit = QLineEdit(self)
        self.subdeck_edit.setPlaceholderText("New subdeck name")

        self.create_subdeck_btn = QPushButton("Create subdeck", self)
        self.create_subdeck_btn.clicked.connect(self.on_create_subdeck)

        subdeck_row.addWidget(self.subdeck_edit, 1)
        subdeck_row.addWidget(self.create_subdeck_btn, 0)
        
        self.deck_combo.currentIndexChanged.connect(
            lambda _: subdeck_container.setEnabled(self.deck_combo.count() > 0)
        )
        settings_form.addRow("Add Subdeck:", subdeck_container)

        # Note type combo
        self.notetype_combo = QComboBox(self)
        settings_form.addRow("Note Type:", self.notetype_combo)

        # Delimiter selector
        self.delimiter_combo = QComboBox(self)
        self.delimiter_combo.addItems(
            [
                "Auto-detect",
                "Comma (,)",
                "Tab",
                "Semicolon (;)",
                "Pipe (|)",
            ]
        )
        self.delimiter_combo.setCurrentIndex(0)
        self.delimiter_combo.currentIndexChanged.connect(self.on_delimiter_changed)
        settings_form.addRow("Delimiter:", self.delimiter_combo)

        layout.addWidget(settings_group)

        # Footer buttons
        btns = QHBoxLayout()
        self.quick_btn = QPushButton("Quick Import", self)
        self.quick_btn.clicked.connect(self.on_do_import)
        self.quick_btn.setDefault(True)

        self.anki_btn = QPushButton("Import with Anki Dialog", self)
        self.anki_btn.setToolTip(
            "Open Anki's import dialog for advanced field mapping and options."
        )
        self.anki_btn.clicked.connect(self.on_open_with_anki)

        self.cancel_btn = QPushButton("Close", self)
        self.cancel_btn.clicked.connect(self.dialog.reject)

        btns.addStretch()
        btns.addWidget(self.quick_btn)
        btns.addWidget(self.anki_btn)
        btns.addWidget(self.cancel_btn)
        layout.addLayout(btns)

    def on_pick_file(self):
        if hasattr(self.dialog, "pick_file"):
            self.dialog.pick_file()

    def on_paste_clipboard(self):
        if hasattr(self.dialog, "paste_clipboard"):
            self.dialog.paste_clipboard()

    def on_quick_import_clipboard(self):
        if hasattr(self.dialog, "quick_import_clipboard"):
            self.dialog.quick_import_clipboard()

    def on_csv_text_changed(self):
        if hasattr(self.dialog, "schedule_content_changed"):
            self.dialog.schedule_content_changed()

    def on_create_subdeck(self):
        if hasattr(self.dialog, "create_subdeck"):
            self.dialog.create_subdeck()

    def on_delimiter_changed(self, index):
        if hasattr(self.dialog, "on_content_changed"):
            self.dialog.on_content_changed()

    def on_do_import(self):
        if hasattr(self.dialog, "do_import"):
            self.dialog.do_import()

    def on_open_with_anki(self):
        if hasattr(self.dialog, "open_with_default_importer"):
            self.dialog.open_with_default_importer()
