import os
from aqt.qt import (
    QApplication,
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
    QScrollArea,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
    QPixmap,
    Qt,
    QTreeWidget,
    QTreeWidgetItem,
)


def setup_ui(self):
    self.setWindowTitle("CSV Import +")
    self.setMinimumSize(800, 600)

    # Use a QTabWidget as the root
    self.tabs = QTabWidget(self)
    root_layout = QVBoxLayout(self)
    root_layout.addWidget(self.tabs)
    self.setLayout(root_layout)

    # --- Import Tab ---
    import_tab = QWidget()
    self.tabs.addTab(import_tab, "Import")
    import_layout = QVBoxLayout(import_tab)

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
    import_layout.addWidget(instr)

    # File picker row
    file_row_w = QWidget(import_tab)
    file_row = QHBoxLayout(file_row_w)
    file_row.setContentsMargins(0, 0, 0, 0)

    self.file_edit = QLineEdit(import_tab)
    self.file_edit.setReadOnly(True)
    self.file_edit.setPlaceholderText("No file selected…")

    self.browse_btn = QPushButton("Browse…", import_tab)
    self.browse_btn.clicked.connect(self.pick_file)

    file_row.addWidget(QLabel("CSV file:", import_tab))
    file_row.addWidget(self.file_edit, 1)
    file_row.addWidget(self.browse_btn, 0)

    import_layout.addWidget(file_row_w)

    # Paste area
    content_header = QWidget(import_tab)
    content_header_row = QHBoxLayout(content_header)
    content_header_row.setContentsMargins(0, 0, 0, 0)
    content_header_row.addWidget(QLabel("CSV content:", import_tab))
    content_header_row.addStretch()

    self.paste_clipboard_btn = QPushButton("Paste Clipboard", import_tab)
    self.paste_clipboard_btn.clicked.connect(self.paste_clipboard)
    content_header_row.addWidget(self.paste_clipboard_btn, 0)

    self.quick_clipboard_btn = QPushButton("Quick Import Clipboard", import_tab)
    self.quick_clipboard_btn.clicked.connect(self.quick_import_clipboard)
    content_header_row.addWidget(self.quick_clipboard_btn, 0)

    import_layout.addWidget(content_header)
    self.csv_text = QPlainTextEdit(import_tab)
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
    import_layout.addWidget(self.csv_text, 1)

    # Status
    self.status_label = QLabel("")
    self.status_label.setStyleSheet("color: #21808D; font-weight: 500;")
    import_layout.addWidget(self.status_label)

    # Settings
    settings_group = QGroupBox("Import Settings", import_tab)
    settings_form = QFormLayout(settings_group)

    # Deck combo
    deck_container = QWidget(import_tab)
    deck_row = QHBoxLayout(deck_container)
    deck_row.setContentsMargins(0, 0, 0, 0)
    self.deck_combo = QComboBox(import_tab)
    deck_row.addWidget(self.deck_combo, 1)
    self.refresh_decks()
    settings_form.addRow("Target Deck:", deck_container)

    # Subdeck creation
    subdeck_container = QWidget(import_tab)
    subdeck_row = QHBoxLayout(subdeck_container)
    subdeck_row.setContentsMargins(0, 0, 0, 0)

    self.subdeck_edit = QLineEdit(import_tab)
    self.subdeck_edit.setPlaceholderText("New subdeck name")

    self.create_subdeck_btn = QPushButton("Create subdeck", import_tab)
    self.create_subdeck_btn.clicked.connect(self.create_subdeck)

    subdeck_row.addWidget(self.subdeck_edit, 1)
    subdeck_row.addWidget(self.create_subdeck_btn, 0)

    subdeck_container.setEnabled(self.deck_combo.count() > 0)
    self.deck_combo.currentIndexChanged.connect(
        lambda _: subdeck_container.setEnabled(self.deck_combo.count() > 0)
    )
    settings_form.addRow("Add Subdeck:", subdeck_container)

    # Note type combo
    self.notetype_combo = QComboBox(import_tab)
    self.model_infos = self.get_model_infos()
    self.notetype_combo.addItems([m.name for m in self.model_infos])
    settings_form.addRow("Note Type:", self.notetype_combo)

    # Delimiter selector
    self.delimiter_combo = QComboBox(import_tab)
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

    import_layout.addWidget(settings_group)

    # --- History Tab ---
    history_tab = QWidget()
    self.tabs.addTab(history_tab, "History")
    history_layout = QVBoxLayout(history_tab)
    history_layout.setContentsMargins(10, 10, 10, 10)

    self.history_tree = QTreeWidget(history_tab)
    self.history_tree.setHeaderHidden(True)
    history_layout.addWidget(self.history_tree)

    self.clear_history_btn = QPushButton("Clear Session History", history_tab)
    self.clear_history_btn.clicked.connect(self.clear_history)
    history_layout.addWidget(self.clear_history_btn)

    # --- Advanced Tab ---
    advanced_tab = QWidget()
    self.tabs.addTab(advanced_tab, "Advanced")
    advanced_layout = QVBoxLayout(advanced_tab)
    advanced_layout.setContentsMargins(20, 20, 20, 20)
    advanced_layout.setSpacing(15)

    advanced_hint = QLabel(
        "Advanced options for deck locking, header handling, clipboard behavior, and the built-in Anki importer.",
        advanced_tab,
    )
    advanced_hint.setWordWrap(True)
    advanced_layout.addWidget(advanced_hint)

    advanced_form = QFormLayout()
    advanced_form.setContentsMargins(0, 0, 0, 0)
    advanced_form.setSpacing(10)
    advanced_layout.addLayout(advanced_form)

    self.deck_lock_check = QCheckBox("Lock Target Deck", advanced_tab)
    self.deck_lock_check.toggled.connect(self.on_deck_lock_toggled)
    advanced_form.addRow("", self.deck_lock_check)

    self.header_check = QCheckBox("First row is header", advanced_tab)
    self.header_check.toggled.connect(self.on_content_changed)
    advanced_form.addRow("", self.header_check)

    self.allow_any_clipboard_toggle = QCheckBox(
        "Allow quick import of any clipboard text", advanced_tab
    )
    self.allow_any_clipboard_toggle.setToolTip(
        "Enable Quick Import Clipboard for any non-empty clipboard text, even if it does not look like CSV."
    )
    self.allow_any_clipboard_toggle.toggled.connect(
        self.on_allow_any_clipboard_toggled
    )
    advanced_form.addRow("", self.allow_any_clipboard_toggle)

    self.clipboard_confirm_toggle = QCheckBox(
        "Confirm clipboard quick import", advanced_tab
    )
    self.clipboard_confirm_toggle.setToolTip(
        "Ask for confirmation before importing clipboard content."
    )
    self.clipboard_confirm_toggle.toggled.connect(self.on_clipboard_confirm_toggled)
    advanced_form.addRow("", self.clipboard_confirm_toggle)

    advanced_layout.addStretch()

    # --- Restore buttons to Import tab ---
    btns = QHBoxLayout()
    self.quick_btn = QPushButton("Quick Import", import_tab)
    self.quick_btn.clicked.connect(self.do_import)
    self.quick_btn.setDefault(True)

    self.anki_btn = QPushButton("Import with Anki Dialog", import_tab)
    self.anki_btn.setToolTip(
        "Open Anki's import dialog for advanced field mapping and options."
    )
    self.anki_btn.clicked.connect(self.open_with_default_importer)

    cancel_btn = QPushButton("Close", import_tab)
    cancel_btn.clicked.connect(self.reject)

    btns.addStretch()
    btns.addWidget(self.quick_btn)
    btns.addWidget(self.anki_btn)
    btns.addWidget(cancel_btn)
    import_layout.addLayout(btns)

    # --- Support Tab ---
    support_tab = QWidget()
    self.tabs.addTab(support_tab, "Support")
    support_layout = QVBoxLayout(support_tab)
    support_layout.setContentsMargins(10, 10, 10, 10)

    support_instr = QLabel(
        "If you find this addon useful, consider supporting the development through the following methods:"
    )
    support_instr.setWordWrap(True)
    support_instr.setAlignment(Qt.AlignmentFlag.AlignCenter)
    support_layout.addWidget(support_instr)

    # Scroll area for QR codes
    scroll = QScrollArea(support_tab)
    scroll.setWidgetResizable(True)
    scroll_content = QWidget()
    qr_list = QVBoxLayout(scroll_content)
    qr_list.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    qr_list.setSpacing(30)
    scroll.setWidget(scroll_content)
    support_layout.addWidget(scroll)

    base_path = os.path.dirname(__file__)

    def add_qr(name, address, filename):
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel(f"<b>{name}</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(title)

        qr_label = QLabel()
        qr_path = os.path.join(base_path, "Support", filename)
        pixmap = QPixmap(qr_path)
        if not pixmap.isNull():
            qr_label.setPixmap(pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            qr_label.setText("Image not found")
        qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(qr_label)

        addr_row = QHBoxLayout()
        addr_label = QLineEdit(address)
        addr_label.setReadOnly(True)
        addr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        addr_label.setStyleSheet("background: transparent; border: none;")
        
        copy_btn = QPushButton("Copy")
        copy_btn.setFixedWidth(60)
        copy_btn.clicked.connect(lambda _, a=address: QApplication.clipboard().setText(a))
        
        addr_row.addWidget(addr_label, 1)
        addr_row.addWidget(copy_btn)
        vbox.addLayout(addr_row)

        qr_list.addWidget(container)

    add_qr("UPI", "athulkrishnasv2015-2@okhdfcbank", "UPI.jpg")
    add_qr("BTC", "bc1qrrek3m7sr33qujjrktj949wav6mehdsk057cfx", "BTC.jpg")
    add_qr("ETH", "0xce6899e4903EcB08bE5Be65E44549fadC3F45D27", "ETH.jpg")
