# -*- coding: utf-8 -*-

from aqt.qt import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QPlainTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)


def setup_ui(self):
    self.setWindowTitle("CSV Import +")
    self.setMinimumSize(760, 560)

    root = QVBoxLayout(self)

    instr = QLabel(
        "Paste CSV or choose a CSV file, adjust options, pick deck and note type, then import.\n"
        "Supported delimiters: comma, tab, semicolon, pipe. Directives: #notetype:Basic or #notetype:Cloze\n"
        "Quick Import adds notes directly; use Advanced for delimiter, header, clipboard, and fallback import options."
    )
    instr.setWordWrap(True)
    root.addWidget(instr)

    # File picker row (visible on main screen)
    file_row_w = QWidget(self)
    file_row = QHBoxLayout(file_row_w)
    file_row.setContentsMargins(0, 0, 0, 0)

    self.file_edit = QLineEdit(self)
    self.file_edit.setReadOnly(True)
    self.file_edit.setPlaceholderText("No file selected…")

    self.browse_btn = QPushButton("Browse…", self)
    self.browse_btn.clicked.connect(self.pick_file)

    file_row.addWidget(QLabel("CSV file:", self))
    file_row.addWidget(self.file_edit, 1)
    file_row.addWidget(self.browse_btn, 0)

    root.addWidget(file_row_w)

    # Paste area
    content_header = QWidget(self)
    content_header_row = QHBoxLayout(content_header)
    content_header_row.setContentsMargins(0, 0, 0, 0)
    content_header_row.addWidget(QLabel("CSV content:", self))
    content_header_row.addStretch()

    self.paste_clipboard_btn = QPushButton("Paste Clipboard", self)
    self.paste_clipboard_btn.clicked.connect(self.paste_clipboard)
    content_header_row.addWidget(self.paste_clipboard_btn, 0)

    self.quick_clipboard_btn = QPushButton("Quick Import Clipboard", self)
    self.quick_clipboard_btn.clicked.connect(self.quick_import_clipboard)
    content_header_row.addWidget(self.quick_clipboard_btn, 0)

    root.addWidget(content_header)
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
    self.csv_text.textChanged.connect(self.schedule_content_changed)
    root.addWidget(self.csv_text, 1)

    # Status
    self.status_label = QLabel("")
    self.status_label.setStyleSheet("color: #21808D; font-weight: 500;")
    root.addWidget(self.status_label)

    # Settings
    settings_group = QGroupBox("Import Settings", self)
    settings_form = QFormLayout(settings_group)

    # Deck combo
    deck_container = QWidget(self)
    deck_row = QHBoxLayout(deck_container)
    deck_row.setContentsMargins(0, 0, 0, 0)
    self.deck_combo = QComboBox(self)
    deck_row.addWidget(self.deck_combo, 1)
    self.refresh_decks()
    settings_form.addRow("Target Deck:", deck_container)

    # Subdeck creation
    subdeck_container = QWidget(self)
    subdeck_row = QHBoxLayout(subdeck_container)
    subdeck_row.setContentsMargins(0, 0, 0, 0)

    self.subdeck_edit = QLineEdit(self)
    self.subdeck_edit.setPlaceholderText("New subdeck name")

    self.create_subdeck_btn = QPushButton("Create subdeck", self)
    self.create_subdeck_btn.clicked.connect(self.create_subdeck)

    subdeck_row.addWidget(self.subdeck_edit, 1)
    subdeck_row.addWidget(self.create_subdeck_btn, 0)

    subdeck_container.setEnabled(self.deck_combo.count() > 0)
    self.deck_combo.currentIndexChanged.connect(
        lambda _: subdeck_container.setEnabled(self.deck_combo.count() > 0)
    )
    settings_form.addRow("Add Subdeck:", subdeck_container)

    # Note type combo
    self.notetype_combo = QComboBox(self)
    self.model_infos = self.get_model_infos()
    self.notetype_combo.addItems([m.name for m in self.model_infos])
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
    self.delimiter_combo.currentIndexChanged.connect(self.on_content_changed)
    settings_form.addRow("Delimiter:", self.delimiter_combo)

    root.addWidget(settings_group)

    # Advanced menu
    self.advanced_menu = QMenu(self)
    advanced_panel = QWidget(self.advanced_menu)
    advanced_panel.setMinimumWidth(360)

    advanced_layout = QVBoxLayout(advanced_panel)
    advanced_layout.setContentsMargins(12, 12, 12, 12)
    advanced_layout.setSpacing(10)

    advanced_hint = QLabel(
        "Advanced options for deck locking, header handling, clipboard behavior, and the built-in Anki importer.",
        advanced_panel,
    )
    advanced_hint.setWordWrap(True)
    advanced_layout.addWidget(advanced_hint)

    advanced_form = QFormLayout()
    advanced_form.setContentsMargins(0, 0, 0, 0)
    advanced_layout.addLayout(advanced_form)

    self.deck_lock_check = QCheckBox("Lock Target Deck", advanced_panel)
    self.deck_lock_check.toggled.connect(self.on_deck_lock_toggled)
    advanced_form.addRow("", self.deck_lock_check)

    self.header_check = QCheckBox("First row is header", advanced_panel)
    self.header_check.toggled.connect(self.on_content_changed)
    advanced_form.addRow("", self.header_check)

    self.allow_any_clipboard_toggle = QCheckBox(
        "Allow quick import of any clipboard text", advanced_panel
    )
    self.allow_any_clipboard_toggle.setToolTip(
        "Enable Quick Import Clipboard for any non-empty clipboard text, even if it does not look like CSV."
    )
    self.allow_any_clipboard_toggle.toggled.connect(
        self.on_allow_any_clipboard_toggled
    )
    advanced_form.addRow("", self.allow_any_clipboard_toggle)

    self.clipboard_confirm_toggle = QCheckBox(
        "Confirm clipboard quick import", advanced_panel
    )
    self.clipboard_confirm_toggle.setToolTip(
        "Ask for confirmation before importing clipboard content."
    )
    self.clipboard_confirm_toggle.toggled.connect(self.on_clipboard_confirm_toggled)
    advanced_form.addRow("", self.clipboard_confirm_toggle)

    self.anki_btn = QPushButton("Import with Anki dialog", advanced_panel)
    self.anki_btn.clicked.connect(self.open_with_default_importer)
    advanced_layout.addWidget(self.anki_btn)

    advanced_action = QWidgetAction(self.advanced_menu)
    advanced_action.setDefaultWidget(advanced_panel)
    self.advanced_menu.addAction(advanced_action)

    # Buttons
    btns = QHBoxLayout()
    self.quick_btn = QPushButton("Quick Import", self)
    self.quick_btn.clicked.connect(self.do_import)
    self.quick_btn.setDefault(True)

    self.advanced_btn = QToolButton(self)
    self.advanced_btn.setText("Advanced")
    self.advanced_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
    self.advanced_btn.setMenu(self.advanced_menu)

    cancel_btn = QPushButton("Close", self)
    cancel_btn.clicked.connect(self.reject)

    btns.addStretch()
    btns.addWidget(self.advanced_btn)
    btns.addWidget(self.quick_btn)
    btns.addWidget(cancel_btn)

    root.addLayout(btns)
    self.setLayout(root)
