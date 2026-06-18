# -*- coding: utf-8 -*-

import os
from aqt import mw
from aqt.qt import (
    QApplication,
    QCheckBox,
    QComboBox,
    QCompleter,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    Qt,
    QStackedWidget,
    QTableWidget,
    QHeaderView,
    QProgressBar,
)

class ImportTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dialog = parent
        self.setup_ui()

    def setup_ui(self):
        # Base layout on the ImportTab widget itself
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Scroll Area to hold all settings & editor
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        # Container widget for scroll area
        container = QWidget(scroll)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

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
        file_row_w = QWidget()
        file_row = QHBoxLayout(file_row_w)
        file_row.setContentsMargins(0, 0, 0, 0)

        self.file_edit = QLineEdit()
        self.file_edit.setReadOnly(True)
        self.file_edit.setPlaceholderText("No file selected…")

        self.browse_btn = QPushButton("Browse…")
        self.browse_btn.clicked.connect(self.on_pick_file)

        file_row.addWidget(QLabel("CSV file:"))
        file_row.addWidget(self.file_edit, 1)
        file_row.addWidget(self.browse_btn, 0)
        layout.addWidget(file_row_w)

        # Paste area
        content_header = QWidget()
        content_header_row = QHBoxLayout(content_header)
        content_header_row.setContentsMargins(0, 0, 0, 0)
        self.content_header_label = QLabel("CSV content:")
        content_header_row.addWidget(self.content_header_label)
        content_header_row.addStretch()

        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.on_remove_selected)
        self.remove_btn.setVisible(False)
        content_header_row.addWidget(self.remove_btn, 0)

        self.paste_clipboard_btn = QPushButton("Paste Clipboard")
        self.paste_clipboard_btn.clicked.connect(self.on_paste_clipboard)
        content_header_row.addWidget(self.paste_clipboard_btn, 0)

        self.quick_clipboard_btn = QPushButton("Quick Import Clipboard")
        self.quick_clipboard_btn.clicked.connect(self.on_quick_import_clipboard)
        content_header_row.addWidget(self.quick_clipboard_btn, 0)

        layout.addWidget(content_header)
        
        self.content_stack = QStackedWidget(self)
        
        self.csv_text = QPlainTextEdit()
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
        self.content_stack.addWidget(self.csv_text)
        
        self.bulk_table = QTableWidget()
        self.bulk_table.setColumnCount(5)
        self.bulk_table.setHorizontalHeaderLabels([
            "File Name", "Delimiter", "Note Type (Auto-picked)", "Rows", "Status"
        ])
        self.bulk_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.bulk_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.bulk_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.bulk_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.bulk_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.bulk_table.setAlternatingRowColors(True)
        self.bulk_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.content_stack.addWidget(self.bulk_table)
        
        layout.addWidget(self.content_stack, 1)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #21808D; font-weight: 500;")
        layout.addWidget(self.status_label)

        # Settings
        settings_group = QGroupBox("Import Settings")
        settings_form = QFormLayout(settings_group)

        # Deck combo
        deck_container = QWidget()
        deck_row = QHBoxLayout(deck_container)
        deck_row.setContentsMargins(0, 0, 0, 0)
        self.deck_combo = QComboBox()
        self.deck_combo.setEditable(True)
        self.deck_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        self.completer = QCompleter(self.deck_combo.model(), self.deck_combo)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.deck_combo.setCompleter(self.completer)
        
        deck_row.addWidget(self.deck_combo, 1)

        deck_tooltip = "Imported cards will be placed in this deck."
        deck_label = QLabel("Target Deck:")
        deck_label.setToolTip(deck_tooltip)
        self.deck_combo.setToolTip(deck_tooltip)
        settings_form.addRow(deck_label, deck_container)

        # Subdeck creation
        subdeck_container = QWidget()
        subdeck_row = QHBoxLayout(subdeck_container)
        subdeck_row.setContentsMargins(0, 0, 0, 0)

        self.subdeck_edit = QLineEdit()
        self.subdeck_edit.setPlaceholderText("New subdeck name")

        self.create_subdeck_btn = QPushButton("Create subdeck")
        self.create_subdeck_btn.clicked.connect(self.on_create_subdeck)

        subdeck_row.addWidget(self.subdeck_edit, 1)
        subdeck_row.addWidget(self.create_subdeck_btn, 0)
        
        self.deck_combo.currentIndexChanged.connect(
            lambda _: subdeck_container.setEnabled(self.deck_combo.count() > 0)
        )
        settings_form.addRow("Add Subdeck:", subdeck_container)

        # Note type combo
        self.notetype_combo = QComboBox()
        notetype_tooltip = (
            "Newly-imported notes will have this note type, and only existing notes with this note type will be updated.\n\n"
            "You can choose which fields in the file correspond to which note type fields with the mapping tool."
        )
        notetype_label = QLabel("Note Type:")
        notetype_label.setToolTip(notetype_tooltip)
        self.notetype_combo.setToolTip(notetype_tooltip)
        settings_form.addRow(notetype_label, self.notetype_combo)

        # Delimiter selector
        self.delimiter_combo = QComboBox()
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

        delim_tooltip = (
            "The character separating fields in the text file. "
            "You can use the preview to check if the fields are separated correctly.\n\n"
            "Please note that if this character appears in any field itself, "
            "the field has to be quoted accordingly to the CSV standard. "
            "Spreadsheet programs like LibreOffice will do this automatically.\n\n"
            "It cannot be changed if the text file forces use of a specific separator via a file header. "
            "If a file header is not present, Anki will try to guess what the separator is."
        )
        delim_label = QLabel("Field separator:")
        delim_label.setToolTip(delim_tooltip)
        self.delimiter_combo.setToolTip(delim_tooltip)
        settings_form.addRow(delim_label, self.delimiter_combo)

        # Allow HTML in fields
        self.allow_html_check = QCheckBox("Allow HTML in fields")
        self.allow_html_check.setChecked(True)
        allow_html_tooltip = (
            "Enable this if the file contains HTML formatting. "
            "E.g. if the file contains the string '<br>', it will appear as a line break on your card. "
            "On the other hand, with this option disabled, the literal characters '<br>' will be rendered."
        )
        self.allow_html_check.setToolTip(allow_html_tooltip)
        allow_html_label = QLabel("HTML Options:")
        allow_html_label.setToolTip(allow_html_tooltip)
        settings_form.addRow(allow_html_label, self.allow_html_check)

        # Existing notes
        self.existing_notes_combo = QComboBox()
        self.existing_notes_combo.addItems(
            [
                "Update: Update the existing note",
                "Preserve: Do nothing",
                "Duplicate: Create a new note",
            ]
        )
        self.existing_notes_combo.setCurrentIndex(2)  # Default: Duplicate
        existing_tooltip = (
            "What to do if an imported note matches an existing one.\n\n"
            "Update: Update the existing note.\n"
            "Preserve: Do nothing.\n"
            "Duplicate: Create a new note."
        )
        self.existing_notes_combo.setToolTip(existing_tooltip)
        existing_label = QLabel("Existing notes:")
        existing_label.setToolTip(existing_tooltip)
        settings_form.addRow(existing_label, self.existing_notes_combo)

        # Match scope
        self.match_scope_combo = QComboBox()
        self.match_scope_combo.addItems(
            [
                "Same note type",
                "Same note type and deck",
            ]
        )
        self.match_scope_combo.setCurrentIndex(0)
        match_scope_tooltip = (
            "Only existing notes with the same note type will be checked for duplicates. "
            "This can additionally be restricted to notes with cards in the same deck."
        )
        self.match_scope_combo.setToolTip(match_scope_tooltip)
        match_scope_label = QLabel("Match scope:")
        match_scope_label.setToolTip(match_scope_tooltip)
        settings_form.addRow(match_scope_label, self.match_scope_combo)

        # Tag all notes
        self.tag_all_edit = QLineEdit()
        self.tag_all_edit.setPlaceholderText("space-separated tags")
        tag_all_tooltip = (
            "These tags will be added to both newly-imported and updated notes."
        )
        self.tag_all_edit.setToolTip(tag_all_tooltip)
        tag_all_label = QLabel("Tag all notes:")
        tag_all_label.setToolTip(tag_all_tooltip)
        settings_form.addRow(tag_all_label, self.tag_all_edit)

        # Tag updated notes
        self.tag_updated_edit = QLineEdit()
        self.tag_updated_edit.setPlaceholderText("space-separated tags")
        tag_updated_tooltip = (
            "These tags will be added to any updated notes."
        )
        self.tag_updated_edit.setToolTip(tag_updated_tooltip)
        tag_updated_label = QLabel("Tag updated notes:")
        tag_updated_label.setToolTip(tag_updated_tooltip)
        settings_form.addRow(tag_updated_label, self.tag_updated_edit)

        layout.addWidget(settings_group)

        # Set container to scroll and add scroll to main layout
        scroll.setWidget(container)
        main_layout.addWidget(scroll, 1)

        # Footer buttons (pinned outside of the scroll area!)
        btns = QHBoxLayout()
        self.quick_btn = QPushButton("Quick Import")
        self.quick_btn.clicked.connect(self.on_do_import)
        self.quick_btn.setDefault(True)

        self.anki_btn = QPushButton("Import with Anki Dialog")
        self.anki_btn.setToolTip(
            "Open Anki's import dialog for advanced field mapping and options."
        )
        self.anki_btn.clicked.connect(self.on_open_with_anki)

        self.cancel_btn = QPushButton("Close")
        self.cancel_btn.clicked.connect(self.dialog.reject)

        btns.addStretch()
        btns.addWidget(self.quick_btn)
        btns.addWidget(self.anki_btn)
        btns.addWidget(self.cancel_btn)
        main_layout.addLayout(btns)

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

    def on_remove_selected(self):
        if hasattr(self.dialog, "remove_selected_files"):
            self.dialog.remove_selected_files()
