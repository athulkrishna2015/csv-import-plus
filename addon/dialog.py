# -*- coding: utf-8 -*-

import os
import csv
import io

from aqt import mw
from aqt.qt import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QKeySequence,
    QShortcut,
    QPlainTextEdit,
    QTimer,
    Qt,
    QVBoxLayout,
    QTreeWidgetItem,
    QPushButton,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QLineEdit,
    QFormLayout,
    QGroupBox,
    QProgressBar,
    QCompleter,
    QWidget,
)

from . import anki_helpers
from . import detector
from . import importer
from . import ui

PROFILE_KEY_LAST_DIR = "csv_import_plus_last_dir"
CONFIG_KEY_CONFIRM_CLIPBOARD_QUICK_IMPORT = "confirm_clipboard_quick_import"
CONFIG_KEY_ALLOW_ANY_CLIPBOARD_QUICK_IMPORT = "allow_any_clipboard_quick_import"


class CSVImportPlusDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.deck_infos = []
        self.model_infos = []
        # State
        self.file_path = ""
        self.file_paths = []
        self.locked_deck_name = None
        self.confirm_clipboard_quick_import = False
        self.allow_any_clipboard_quick_import = False
        self._analysis_timer = QTimer(self)
        self._analysis_timer.setSingleShot(True)
        self._analysis_timer.timeout.connect(self.on_content_changed)
        self.setup_ui()
        self.refresh_decks()
        self.model_infos = self.get_model_infos()
        self.notetype_combo.clear()
        self.notetype_combo.addItems([m.name for m in self.model_infos])
        self._clipboard = QApplication.clipboard()
        if self._clipboard is not None:
            self._clipboard.dataChanged.connect(
                self.update_quick_clipboard_button_state
            )
        self.update_quick_clipboard_button_state()
        self.load_config()
        self.history_tab_widget.refresh_history()

        self.undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.undo_shortcut.activated.connect(self.on_anki_undo)
        
        self.redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self)
        self.redo_shortcut.activated.connect(self.on_anki_redo)
        
        self.redo_shortcut_shift = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
        self.redo_shortcut_shift.activated.connect(self.on_anki_redo)
        self.setAcceptDrops(True)

    def closeEvent(self, event):
        self.deleteLater()
        event.accept()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path.lower().endswith(('.csv', '.txt', '.tsv')):
                    event.acceptProposedAction()
                    return
        super().dragEnterEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            valid_paths = []
            for url in urls:
                path = url.toLocalFile()
                if path.lower().endswith(('.csv', '.txt', '.tsv')):
                    valid_paths.append(path)
            if valid_paths:
                if self.file_paths:
                    self.add_file_paths(valid_paths)
                elif self.file_path:
                    all_paths = [self.file_path]
                    for p in valid_paths:
                        if p not in all_paths:
                            all_paths.append(p)
                    self.load_files(all_paths)
                else:
                    self.load_files(valid_paths)
                event.acceptProposedAction()
                return
        super().dropEvent(event)

    # -------------------- UI --------------------
    setup_ui = ui.setup_ui

    def on_anki_undo(self):
        if getattr(self, "raw_csv_edit", None) and self.raw_csv_edit.hasFocus():
            self.raw_csv_edit.undo()
        else:
            if hasattr(mw, "onUndo"):
                mw.onUndo()
                self.history_tab_widget.refresh_history()

    def on_anki_redo(self):
        if getattr(self, "raw_csv_edit", None) and self.raw_csv_edit.hasFocus():
            self.raw_csv_edit.redo()
        else:
            if hasattr(mw, "onRedo"):
                mw.onRedo()
                self.history_tab_widget.refresh_history()

    # -------------------- Config --------------------
    def _get_config_name(self):
        return mw.addonManager.addonFromModule(__name__)

    def load_config(self):
        config = mw.addonManager.getConfig(self._get_config_name()) or {}

        if not getattr(mw, 'csv_import_plus_history_loaded', False):
            if config.get("remember_history", False):
                mw.csv_import_plus_history = config.get("saved_history", [])
            else:
                mw.csv_import_plus_history = []
            mw.csv_import_plus_history_loaded = True

        self.confirm_clipboard_quick_import = config.get(
            CONFIG_KEY_CONFIRM_CLIPBOARD_QUICK_IMPORT, False
        )
        self.allow_any_clipboard_quick_import = config.get(
            CONFIG_KEY_ALLOW_ANY_CLIPBOARD_QUICK_IMPORT, False
        )
        
        self.advanced_tab_widget.load_config(config)
        self.locked_deck_name = config.get("locked_deck_name")

        # Load new importer settings
        self.allow_html_check.blockSignals(True)
        self.allow_html_check.setChecked(config.get("allow_html", True))
        self.allow_html_check.blockSignals(False)

        self.existing_notes_combo.blockSignals(True)
        self.existing_notes_combo.setCurrentIndex(config.get("existing_notes_index", 2))
        self.existing_notes_combo.blockSignals(False)

        self.match_scope_combo.blockSignals(True)
        self.match_scope_combo.setCurrentIndex(config.get("match_scope_index", 0))
        self.match_scope_combo.blockSignals(False)

        self.tag_all_edit.blockSignals(True)
        self.tag_all_edit.setText(config.get("tag_all", ""))
        self.tag_all_edit.blockSignals(False)

        self.tag_updated_edit.blockSignals(True)
        self.tag_updated_edit.setText(config.get("tag_updated", ""))
        self.tag_updated_edit.blockSignals(False)

        # Connect signals for auto-save
        self.allow_html_check.stateChanged.connect(lambda _: self.save_config())
        self.existing_notes_combo.currentIndexChanged.connect(lambda _: self.save_config())
        self.match_scope_combo.currentIndexChanged.connect(lambda _: self.save_config())
        self.tag_all_edit.textChanged.connect(lambda _: self.save_config())
        self.tag_updated_edit.textChanged.connect(lambda _: self.save_config())

        self.update_quick_clipboard_button_state()

    def save_config(self):
        config = mw.addonManager.getConfig(self._get_config_name()) or {}
        self.advanced_tab_widget.save_config(config)
        
        config["locked_deck_name"] = self.locked_deck_name
        config[CONFIG_KEY_CONFIRM_CLIPBOARD_QUICK_IMPORT] = self.confirm_clipboard_quick_import
        config[CONFIG_KEY_ALLOW_ANY_CLIPBOARD_QUICK_IMPORT] = self.allow_any_clipboard_quick_import
        
        # Save new importer settings
        config["allow_html"] = self.allow_html_check.isChecked()
        config["existing_notes_index"] = self.existing_notes_combo.currentIndex()
        config["match_scope_index"] = self.match_scope_combo.currentIndex()
        config["tag_all"] = self.tag_all_edit.text()
        config["tag_updated"] = self.tag_updated_edit.text()

        if self.remember_history_check.isChecked():
            config["saved_history"] = getattr(mw, "csv_import_plus_history", [])
        else:
            config.pop("saved_history", None)

        mw.addonManager.writeConfig(self._get_config_name(), config)

    def save_history_if_needed(self):
        if hasattr(self, "remember_history_check") and self.remember_history_check.isChecked():
            self.save_config()

    def on_deck_lock_toggled(self, checked):
        if checked:
            self.locked_deck_name = self.deck_combo.currentText()
        else:
            self.locked_deck_name = None
        self.save_config()

    def on_clipboard_confirm_toggled(self, checked):
        self.confirm_clipboard_quick_import = checked
        self.save_config()

    def on_allow_any_clipboard_toggled(self, checked):
        self.allow_any_clipboard_quick_import = checked
        self.save_config()
        self.update_quick_clipboard_button_state()

    def on_header_check_toggled(self, checked):
        self.save_config()
        self.on_content_changed()

    def on_remember_history_toggled(self, checked):
        self.save_config()

    # -------------------- Deck/model helpers --------------------
    def refresh_decks(self, select_name: str | None = None):
        self.deck_infos = anki_helpers.refresh_decks(self.deck_combo, select_name)

    def create_subdeck(self):
        full_name = anki_helpers.create_subdeck(
            self.deck_combo, self.subdeck_edit, self.status_label
        )
        if full_name:
            self.refresh_decks(select_name=full_name)

    def get_model_infos(self):
        return anki_helpers.get_model_infos()

    # -------------------- Source content --------------------
    def select_active_deck(self):
        # Determine current active deck (if any) and select it in the deck combo.
        # Check if we are in deck overview state and select that deck.
        if getattr(mw, "state", None) == "overview":
            try:
                current_deck = mw.col.decks.current()
                if current_deck:
                    deck_name = current_deck.get("name")
                    if deck_name:
                        idx = self.deck_combo.findText(deck_name)
                        if idx >= 0:
                            self.deck_combo.setCurrentIndex(idx)
            except Exception:
                pass

    def load_file_from_path(self, path: str):
        self.file_path = path
        self.file_paths = []
        self.file_edit.setText(path)
        try:
            mw.pm.profile[PROFILE_KEY_LAST_DIR] = os.path.dirname(path)
        except Exception:
            pass

        # Ensure UI shows single-file/editor view
        self.import_tab_widget.content_stack.setCurrentIndex(0)
        self.import_tab_widget.paste_clipboard_btn.setEnabled(True)
        self.import_tab_widget.quick_clipboard_btn.setEnabled(self.clipboard_can_quick_import())
        self.import_tab_widget.content_header_label.setText("CSV content:")
        self.import_tab_widget.remove_btn.setVisible(False)
        self.import_tab_widget.paste_clipboard_btn.setVisible(True)
        self.import_tab_widget.quick_clipboard_btn.setVisible(True)
        self.import_tab_widget.quick_btn.setText("Quick Import")
        self.import_tab_widget.anki_btn.setVisible(True)

        # Clear any pasted CSV text to use the file instead
        self.csv_text.clear()

        # Prefill subdeck name from filename
        base = os.path.splitext(os.path.basename(path))[0]
        self.subdeck_edit.setText(base)

        self.select_active_deck()
        self.on_content_changed()

    def load_files(self, paths):
        if not paths:
            return
        
        if len(paths) == 1:
            self.load_file_from_path(paths[0])
        else:
            self.file_path = ""
            self.file_paths = list(paths)
            self.file_edit.setText(f"{len(paths)} files selected")
            self.import_tab_widget.content_stack.setCurrentIndex(1)
            self.import_tab_widget.paste_clipboard_btn.setEnabled(False)
            self.import_tab_widget.quick_clipboard_btn.setEnabled(False)
            self.import_tab_widget.content_header_label.setText("Files to import:")
            self.import_tab_widget.remove_btn.setVisible(True)
            self.import_tab_widget.paste_clipboard_btn.setVisible(False)
            self.import_tab_widget.quick_clipboard_btn.setVisible(False)
            self.import_tab_widget.quick_btn.setText("Quick Import All")
            self.import_tab_widget.anki_btn.setVisible(False)
            
            # Clear pasted text in editor
            self.csv_text.clear()
            
            # Populate bulk table
            self.populate_bulk_table()

    def populate_bulk_table(self):
        self.import_tab_widget.bulk_table.setRowCount(0)
        self.import_tab_widget.bulk_table.setRowCount(len(self.file_paths))
        
        self.bulk_file_details = []
        
        for row_idx, path in enumerate(self.file_paths):
            filename = os.path.basename(path)
            
            # Read file content
            content = ""
            for enc in ("utf-8", "utf-8-sig"):
                try:
                    with open(path, "r", encoding=enc, newline="") as f:
                        content = f.read()
                        break
                except Exception:
                    continue
            if not content:
                try:
                    with open(path, "r", errors="ignore") as f:
                        content = f.read()
                except Exception:
                    pass
            
            # Detect formatting
            delimiter = ","
            rows_count = 0
            if content:
                try:
                    delimiter, rows_count = detector.detect_csv_format(content)
                except Exception:
                    pass
            
            delim_name = detector.get_delimiter_name(delimiter)
            
            # Auto-pick model/note type
            model_name = "None"
            model_idx = None
            
            # Check for directive
            directives = detector.extract_directives(content)
            directive_nt_name = directives.get("notetype")
            if directive_nt_name:
                idx = detector.find_model_index_by_name(self.model_infos, directive_nt_name)
                if idx is not None:
                    model_idx = idx
                    model_name = f"{self.model_infos[idx].name} (via directive)"
            
            if model_idx is None and content:
                best_name, best_fields, best_idx = detector.auto_pick_note_type(
                    content, delimiter, self.model_infos, self.header_check
                )
                if best_idx is not None:
                    model_name = best_name
                    model_idx = best_idx
            
            self.bulk_file_details.append({
                "path": path,
                "content": content,
                "delimiter": delimiter,
                "model_idx": model_idx,
                "rows_count": rows_count
            })
            
            # Create Table Items
            item_name = QTableWidgetItem(filename)
            item_name.setToolTip(path)
            item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            item_delim = QTableWidgetItem(delim_name)
            item_delim.setFlags(item_delim.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            item_model = QTableWidgetItem(model_name)
            item_model.setFlags(item_model.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            item_rows = QTableWidgetItem(str(rows_count))
            item_rows.setFlags(item_rows.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            item_status = QTableWidgetItem("Ready")
            item_status.setFlags(item_status.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            self.import_tab_widget.bulk_table.setItem(row_idx, 0, item_name)
            self.import_tab_widget.bulk_table.setItem(row_idx, 1, item_delim)
            self.import_tab_widget.bulk_table.setItem(row_idx, 2, item_model)
            self.import_tab_widget.bulk_table.setItem(row_idx, 3, item_rows)
            self.import_tab_widget.bulk_table.setItem(row_idx, 4, item_status)

    def load_text_content(self, text: str):
        # Clear selected file
        self.file_path = ""
        self.file_paths = []
        self.file_edit.clear()
        self.import_tab_widget.content_stack.setCurrentIndex(0)
        self.import_tab_widget.paste_clipboard_btn.setEnabled(True)
        self.import_tab_widget.quick_clipboard_btn.setEnabled(self.clipboard_can_quick_import())
        self.import_tab_widget.content_header_label.setText("CSV content:")
        self.import_tab_widget.remove_btn.setVisible(False)
        self.import_tab_widget.paste_clipboard_btn.setVisible(True)
        self.import_tab_widget.quick_clipboard_btn.setVisible(True)
        self.import_tab_widget.quick_btn.setText("Quick Import")
        self.import_tab_widget.anki_btn.setVisible(True)

        self.csv_text.setPlainText(text)
        self.select_active_deck()
        self.on_content_changed()

    def pick_file(self):
        start_dir = mw.pm.profile.get(PROFILE_KEY_LAST_DIR, "")
        paths, _ = QFileDialog.getOpenFileNames(
            mw, "Select CSV Files to Import", start_dir, "Text/CSV Files (*.csv *.txt *.tsv);;All Files (*)"
        )
        if not paths:
            return
            
        try:
            mw.pm.profile[PROFILE_KEY_LAST_DIR] = os.path.dirname(paths[0])
        except Exception:
            pass

        self.load_files(paths)

    def read_file_text(self) -> str:
        if not self.file_path:
            return ""
        # Try utf-8 and utf-8-sig
        for enc in ("utf-8", "utf-8-sig"):
            try:
                with open(self.file_path, "r", encoding=enc, newline="") as f:
                    return f.read()
            except Exception:
                continue
        # Fallback
        try:
            with open(self.file_path, "r", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""

    def get_active_raw(self) -> str:
        # Prefer Paste if it has content; otherwise use selected file (if any)
        paste = self.csv_text.toPlainText().strip()
        if paste:
            return paste
        if self.file_path:
            return self.read_file_text().strip()
        return ""

    def schedule_content_changed(self):
        # Debounce text edits to avoid expensive re-parsing on every keystroke.
        self._analysis_timer.start(180)

    def paste_clipboard(self):
        clipboard = QApplication.clipboard()
        if clipboard is None:
            self.status_label.setText("⚠ Clipboard is unavailable.")
            return

        text = clipboard.text()
        if not text.strip():
            self.status_label.setText("⚠ Clipboard is empty.")
            return

        self.csv_text.setPlainText(text)
        self.csv_text.setFocus()
        self.on_content_changed()

    def raw_content_is_valid_csv(self, raw: str) -> bool:
        csv_content = detector.strip_directive_lines(raw).strip()
        if not csv_content:
            return False

        try:
            delimiter = importer.get_delimiter(self.delimiter_combo, csv_content)
            reader = csv.reader(io.StringIO(csv_content), delimiter=delimiter)
            rows = [row for row in reader if any(cell.strip() for cell in row)]
        except Exception:
            return False

        if not rows:
            return False

        # Treat clipboard quick import as CSV-only unless the Advanced override is enabled.
        return any(len(row) > 1 for row in rows)

    def raw_content_allows_quick_clipboard_import(self, raw: str) -> bool:
        if not raw.strip():
            return False
        if self.allow_any_clipboard_quick_import:
            return True
        return self.raw_content_is_valid_csv(raw)

    def clipboard_can_quick_import(self) -> bool:
        clipboard = QApplication.clipboard()
        if clipboard is None:
            return False
        return self.raw_content_allows_quick_clipboard_import(clipboard.text())

    def update_quick_clipboard_button_state(self):
        can_import = self.clipboard_can_quick_import()
        self.quick_clipboard_btn.setEnabled(can_import)
        if can_import:
            if self.allow_any_clipboard_quick_import:
                self.quick_clipboard_btn.setToolTip(
                    "Import any non-empty clipboard text directly using current settings."
                )
            else:
                self.quick_clipboard_btn.setToolTip(
                    "Import clipboard content directly using current settings."
                )
        else:
            if self.allow_any_clipboard_quick_import:
                self.quick_clipboard_btn.setToolTip("Clipboard is empty.")
            else:
                self.quick_clipboard_btn.setToolTip(
                    "Clipboard does not contain valid CSV content. Enable the Advanced option to allow any text."
                )

    def quick_import_clipboard(self):
        clipboard = QApplication.clipboard()
        if clipboard is None:
            self.status_label.setText("⚠ Clipboard is unavailable.")
            return

        raw = clipboard.text()
        if not raw.strip():
            self.status_label.setText("⚠ Clipboard is empty.")
            return
        if not self.raw_content_allows_quick_clipboard_import(raw):
            self.status_label.setText(
                "⚠ Clipboard does not contain valid CSV content."
            )
            self.update_quick_clipboard_button_state()
            return

        if self.confirm_clipboard_quick_import:
            summary = self._build_clipboard_import_summary(raw)
            if not self._confirm_clipboard_quick_import(summary, raw):
                return

        self._run_import(raw, clear_pasted_input=False)
        self.update_quick_clipboard_button_state()

    def _build_clipboard_import_summary(self, raw: str) -> str:
        csv_content = detector.strip_directive_lines(raw)
        delimiter = importer.get_delimiter(self.delimiter_combo, csv_content)
        delimiter_name = detector.get_delimiter_name(delimiter)

        try:
            reader = csv.reader(io.StringIO(csv_content), delimiter=delimiter)
            row_count = sum(1 for _ in reader)
        except Exception:
            row_count = 0

        rows_to_import = row_count
        if self.header_check.isChecked() and row_count > 0:
            rows_to_import -= 1

        note_type_name = self.notetype_combo.currentText()
        directives = detector.extract_directives(raw)
        directive_notetype = directives.get("notetype")
        if directive_notetype:
            idx = detector.find_model_index_by_name(self.model_infos, directive_notetype)
            if idx is not None:
                note_type_name = f"{self.model_infos[idx].name} (via #notetype)"
            else:
                note_type_name = (
                    f"{note_type_name} (#notetype '{directive_notetype}' not found)"
                )

        return "\n".join(
            [
                f"Deck: {self.deck_combo.currentText()}",
                f"Note type: {note_type_name}",
                f"Delimiter: {delimiter_name}",
                f"Rows detected: {row_count}",
                f"Rows to import: {max(0, rows_to_import)}",
            ]
        )

    def _confirm_clipboard_quick_import(self, summary: str, raw: str) -> bool:
        dialog = QDialog(self)
        dialog.setWindowTitle("Quick Import Clipboard")
        dialog.setModal(True)
        dialog.resize(620, 420)

        layout = QVBoxLayout(dialog)

        title_label = QLabel("Import clipboard content directly?", dialog)
        title_label.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(title_label)

        summary_label = QLabel(summary, dialog)
        summary_label.setTextFormat(Qt.TextFormat.PlainText)
        summary_label.setWordWrap(True)
        layout.addWidget(summary_label)

        preview_label = QLabel("Preview:", dialog)
        preview_label.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(preview_label)

        full_content = detector.strip_directive_lines(raw).strip()
        preview_edit = QPlainTextEdit(dialog)
        preview_edit.setReadOnly(True)
        preview_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        preview_edit.setPlainText(
            full_content or "(No importable content after directives)"
        )
        preview_edit.setFixedHeight(180)
        layout.addWidget(preview_edit)

        dont_ask = QCheckBox("Don't ask again for clipboard quick import", dialog)
        layout.addWidget(dont_ask)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.Cancel,
            dialog,
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        yes_button = buttons.button(QDialogButtonBox.StandardButton.Yes)
        if yes_button is not None:
            yes_button.setDefault(True)
        layout.addWidget(buttons)

        confirmed = dialog.exec() == QDialog.DialogCode.Accepted
        if confirmed and dont_ask.isChecked():
            self.confirm_clipboard_quick_import = False
            self.clipboard_confirm_toggle.blockSignals(True)
            self.clipboard_confirm_toggle.setChecked(False)
            self.clipboard_confirm_toggle.blockSignals(False)
            self.save_config()

        return confirmed

    def _run_import(self, raw: str, clear_pasted_input: bool):
        self.save_config()
        result = importer.do_import(
            raw,
            self.deck_combo,
            self.deck_infos,
            self.notetype_combo,
            self.model_infos,
            self.header_check,
            self.delimiter_combo,
            allow_html=self.allow_html_check.isChecked(),
            existing_notes_index=self.existing_notes_combo.currentIndex(),
            match_scope_index=self.match_scope_combo.currentIndex(),
            tag_all=self.tag_all_edit.text(),
            tag_updated=self.tag_updated_edit.text(),
        )
        if result:
            self.history_tab_widget.refresh_history()
            if clear_pasted_input:
                # Clear only pasted input after successful import from editor/file.
                self.csv_text.blockSignals(True)
                self.csv_text.clear()
                self.csv_text.blockSignals(False)

            parts = [
                f"✓ Import complete: Added {result['added']} note(s) to deck '{result['deck_name']}'"
            ]
            if result["skipped_empty"]:
                parts.append(f"Skipped empty rows: {result['skipped_empty']}")
            if result["used_auto_delimiter"]:
                parts.append(f"Used delimiter: {result['delimiter_name']}")
            self.status_label.setText(" • ".join(parts))

        if self.deck_lock_check.isChecked() and self.locked_deck_name:
            self.deck_combo.setCurrentText(self.locked_deck_name)

    # -------------------- Status updates --------------------
    def on_content_changed(self):
        self.update_quick_clipboard_button_state()
        if self.file_paths:
            self.populate_bulk_table()
            return
        raw = self.get_active_raw()
        if not raw:
            try:
                self.delimiter_combo.setItemText(0, "Auto-detect")
            except Exception:
                pass
            self.status_label.setText("")
            return

        directives = detector.extract_directives(raw)
        content = detector.strip_directive_lines(raw)

        # Apply #notetype directive if present
        forced_model_info = None
        nt_name = directives.get("notetype")
        if nt_name:
            idx = detector.find_model_index_by_name(self.model_infos, nt_name)
            if idx is not None:
                try:
                    self.notetype_combo.setCurrentIndex(idx)
                    forced_model_info = (
                        self.model_infos[idx].name,
                        len(mw.col.models.get(self.model_infos[idx].id)["flds"]),
                    )
                except Exception:
                    pass

        # Live delimiter detection preview (updates even in manual mode).
        detected_delimiter = None
        detected_rows = 0
        try:
            detected_delimiter, detected_rows = detector.detect_csv_format(content)
            detected_name = detector.get_delimiter_name(detected_delimiter)
            self.delimiter_combo.setItemText(0, f"Auto-detect ({detected_name})")
        except Exception as e:
            try:
                self.delimiter_combo.setItemText(0, "Auto-detect")
            except Exception:
                pass
            if self.delimiter_combo.currentIndex() == 0:
                self.status_label.setText(f"⚠ Detection failed: {str(e)}")
                return

        # Determine delimiter & rows used for preview/status and import settings.
        if self.delimiter_combo.currentIndex() == 0:
            delimiter = detected_delimiter if detected_delimiter is not None else ","
            rows = detected_rows
        else:
            delimiter = importer.get_delimiter(self.delimiter_combo, content)
            try:
                reader = csv.reader(io.StringIO(content), delimiter=delimiter)
                rows = sum(1 for _ in reader)
            except Exception:
                rows = 0

        delim_name = detector.get_delimiter_name(delimiter)

        # Auto-pick note type if not forced
        detected_model = None
        if not forced_model_info:
            (best_name, best_fields, best_idx) = detector.auto_pick_note_type(
                content, delimiter, self.model_infos, self.header_check
            )
            if best_idx is not None:
                self.notetype_combo.setCurrentIndex(best_idx)
                detected_model = (best_name, best_fields)

        parts = []
        parts.append(f"✓ Detected: {delim_name} delimiter")
        parts.append(f"{rows} row(s)")
        if forced_model_info:
            model_name, field_count = forced_model_info
            parts.append(
                f"Note type: {model_name} ({field_count} field(s), via directive)"
            )
        elif detected_model:
            model_name, field_count = detected_model
            parts.append(f"Note type: {model_name} ({field_count} field(s))")

        self.status_label.setText(" • ".join(parts))

    def open_with_default_importer(self):
        raw = self.get_active_raw()
        importer.open_with_default_importer(raw, self.deck_combo, self.deck_infos)

    def do_import(self):
        if self.file_paths:
            self.run_bulk_import()
        else:
            raw = self.get_active_raw()
            self._run_import(raw, clear_pasted_input=True)

    def remove_selected_files(self):
        selected_ranges = self.import_tab_widget.bulk_table.selectedRanges()
        if not selected_ranges:
            return
        
        indices_to_remove = set()
        for r in selected_ranges:
            for i in range(r.topRow(), r.bottomRow() + 1):
                indices_to_remove.add(i)
                
        for i in sorted(indices_to_remove, reverse=True):
            if 0 <= i < len(self.file_paths):
                self.file_paths.pop(i)
                
        if not self.file_paths:
            # Revert to single file/editor mode
            self.load_text_content("")
        else:
            self.load_files(self.file_paths)

    def add_file_paths(self, paths):
        for p in paths:
            if p not in self.file_paths:
                self.file_paths.append(p)
        self.load_files(self.file_paths)

    def run_bulk_import(self):
        if not self.file_paths:
            return

        deck_idx = self.deck_combo.currentIndex()
        if deck_idx < 0:
            deck_idx = self.deck_combo.findText(self.deck_combo.currentText())
        
        existing_notes_index = self.existing_notes_combo.currentIndex()
        match_scope_index = self.match_scope_combo.currentIndex()
        allow_html = self.allow_html_check.isChecked()
        header_checked = self.header_check.isChecked()
        tag_all = self.tag_all_edit.text()
        tag_updated = self.tag_updated_edit.text()
        
        self.save_config()

        # Disable main UI buttons during import
        self.import_tab_widget.quick_btn.setEnabled(False)
        self.import_tab_widget.remove_btn.setEnabled(False)
        self.import_tab_widget.cancel_btn.setEnabled(False)
        self.import_tab_widget.browse_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(self.file_paths))
        self.progress_bar.setValue(0)

        total_added = 0
        total_updated = 0
        total_skipped = 0
        success_count = 0
        
        for idx, details in enumerate(self.bulk_file_details):
            path = details["path"]
            content = details["content"]
            delimiter = details["delimiter"]
            model_idx = details["model_idx"]
            
            if model_idx is None:
                self.import_tab_widget.bulk_table.setItem(idx, 4, QTableWidgetItem("Failed: No note type selected/picked"))
                continue
                
            self.import_tab_widget.bulk_table.setItem(idx, 4, QTableWidgetItem("Importing..."))
            QApplication.processEvents()
            
            dummy_deck_combo = DummyWidget(_index=deck_idx, _text=self.deck_combo.currentText())
            dummy_notetype_combo = DummyWidget(_index=model_idx)
            dummy_delimiter_combo = DummyWidget(_index=0, _text="Auto-detect")
            dummy_header_check = DummyWidget(_checked=header_checked)
            
            try:
                res = importer.do_import(
                    content,
                    dummy_deck_combo,
                    self.deck_infos,
                    dummy_notetype_combo,
                    self.model_infos,
                    dummy_header_check,
                    dummy_delimiter_combo,
                    allow_html=allow_html,
                    existing_notes_index=existing_notes_index,
                    match_scope_index=match_scope_index,
                    tag_all=tag_all,
                    tag_updated=tag_updated,
                )
                if res:
                    total_added += res["added"]
                    total_updated += res["updated"]
                    total_skipped += res["skipped_empty"]
                    success_count += 1
                    status_text = f"✓ Added: {res['added']}, Updated: {res['updated']}"
                    self.import_tab_widget.bulk_table.setItem(idx, 4, QTableWidgetItem(status_text))
                else:
                    self.import_tab_widget.bulk_table.setItem(idx, 4, QTableWidgetItem("⚠ Failed"))
            except Exception as e:
                self.import_tab_widget.bulk_table.setItem(idx, 4, QTableWidgetItem(f"⚠ Error: {str(e)}"))
            
            self.progress_bar.setValue(idx + 1)
            QApplication.processEvents()

        summary = f"Imported {success_count}/{len(self.file_paths)} files. Added {total_added} notes, updated {total_updated}."
        self.status_label.setText(summary)
        
        # Re-enable main UI buttons
        self.import_tab_widget.quick_btn.setEnabled(True)
        self.import_tab_widget.remove_btn.setEnabled(True)
        self.import_tab_widget.cancel_btn.setEnabled(True)
        self.import_tab_widget.browse_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # Refresh history tab if it exists
        try:
            self.history_tab_widget.refresh_history()
        except Exception:
            pass


class DummyWidget:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    
    def currentIndex(self):
        return getattr(self, "_index", 0)
    
    def currentText(self):
        return getattr(self, "_text", "")
    
    def findText(self, text):
        return getattr(self, "_index", 0)
        
    def setCurrentIndex(self, index):
        self._index = index
        
    def isChecked(self):
        return getattr(self, "_checked", False)
