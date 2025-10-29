# -*- coding: utf-8 -*-

from aqt.qt import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
)


def setup_ui(self):
    self.setWindowTitle("CSV Import +")
    self.setMinimumSize(760, 560)

    root = QVBoxLayout(self)

    instr = QLabel(
        "Paste CSV or choose a CSV file, adjust options, pick deck and note type, then import.\n"
        "Supported delimiters: comma, tab, semicolon, pipe. Directives: #notetype:Basic or #notetype:Cloze\n"
        "Quick Import adds notes directly; Import with Anki dialog opens the standard importer."
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
    root.addWidget(QLabel("CSV content:", self))
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
    self.csv_text.textChanged.connect(self.on_content_changed)
    root.addWidget(self.csv_text, 1)

    # Status
    self.status_label = QLabel("")
    self.status_label.setStyleSheet("color: #21808D; font-weight: 500;")
    root.addWidget(self.status_label)

    # Settings
    settings_group = QGroupBox("Import Settings", self)
    settings_form = QFormLayout(settings_group)

    # Deck combo
    self.deck_combo = QComboBox(self)
    self.refresh_decks()
    settings_form.addRow("Target Deck:", self.deck_combo)

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

    # Header checkbox
    self.header_check = QCheckBox("First row is header", self)
    self.header_check.toggled.connect(self.on_content_changed)
    settings_form.addRow("", self.header_check)

    root.addWidget(settings_group)

    # Buttons
    btns = QHBoxLayout()
    self.quick_btn = QPushButton("Quick Import", self)
    self.quick_btn.clicked.connect(self.do_import)
    self.quick_btn.setDefault(True)

    self.anki_btn = QPushButton("Import with Anki dialog", self)
    self.anki_btn.clicked.connect(self.open_with_default_importer)

    cancel_btn = QPushButton("Close", self)
    cancel_btn.clicked.connect(self.reject)

    btns.addStretch()
    btns.addWidget(self.quick_btn)
    btns.addWidget(self.anki_btn)
    btns.addWidget(cancel_btn)

    root.addLayout(btns)
    self.setLayout(root)
