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
        self.locked_deck_name = None
        self.confirm_clipboard_quick_import = False
        self.allow_any_clipboard_quick_import = False
        self._analysis_timer = QTimer(self)
        self._analysis_timer.setSingleShot(True)
        self._analysis_timer.timeout.connect(self.on_content_changed)
        self.setup_ui()
        self._clipboard = QApplication.clipboard()
        if self._clipboard is not None:
            self._clipboard.dataChanged.connect(
                self.update_quick_clipboard_button_state
            )
        self.update_quick_clipboard_button_state()
        self.load_config()
        self.refresh_decks()
        self.refresh_notetypes()
        self.refresh_history()

        self.undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.undo_shortcut.activated.connect(self.on_anki_undo)
        
        self.redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self)
        self.redo_shortcut.activated.connect(self.on_anki_redo)
        
        self.redo_shortcut_shift = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
        self.redo_shortcut_shift.activated.connect(self.on_anki_redo)

    def closeEvent(self, event):
        self.deleteLater()
        event.accept()

    # -------------------- UI --------------------
    setup_ui = ui.setup_ui

    def on_anki_undo(self):
        if getattr(self, "raw_csv_edit", None) and self.raw_csv_edit.hasFocus():
            self.raw_csv_edit.undo()
        else:
            if hasattr(mw, "onUndo"):
                mw.onUndo()
                self.refresh_history()

    def on_anki_redo(self):
        if getattr(self, "raw_csv_edit", None) and self.raw_csv_edit.hasFocus():
            self.raw_csv_edit.redo()
        else:
            if hasattr(mw, "onRedo"):
                mw.onRedo()
                self.refresh_history()

    # -------------------- Config --------------------
    def load_config(self):
        config = mw.addonManager.getConfig(__name__) or {}

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
        self.clipboard_confirm_toggle.blockSignals(True)
        self.clipboard_confirm_toggle.setChecked(self.confirm_clipboard_quick_import)
        self.clipboard_confirm_toggle.blockSignals(False)
        self.allow_any_clipboard_toggle.blockSignals(True)
        self.allow_any_clipboard_toggle.setChecked(
            self.allow_any_clipboard_quick_import
        )
        self.allow_any_clipboard_toggle.blockSignals(False)
        self.deck_lock_check.blockSignals(True)
        self.deck_lock_check.setChecked(config.get("deck_lock", False))
        self.deck_lock_check.blockSignals(False)
        self.locked_deck_name = config.get("locked_deck_name")

        if hasattr(self, "header_check"):
            self.header_check.blockSignals(True)
            self.header_check.setChecked(config.get("first_row_header", False))
            self.header_check.blockSignals(False)

        if hasattr(self, "remember_history_check"):
            self.remember_history_check.blockSignals(True)
            self.remember_history_check.setChecked(config.get("remember_history", False))
            self.remember_history_check.blockSignals(False)

        self.update_quick_clipboard_button_state()

    def save_config(self):
        config = mw.addonManager.getConfig(__name__) or {}
        config["deck_lock"] = self.deck_lock_check.isChecked()
        config["locked_deck_name"] = self.locked_deck_name
        config[CONFIG_KEY_CONFIRM_CLIPBOARD_QUICK_IMPORT] = self.confirm_clipboard_quick_import
        config[CONFIG_KEY_ALLOW_ANY_CLIPBOARD_QUICK_IMPORT] = self.allow_any_clipboard_quick_import
        
        if hasattr(self, "header_check"):
            config["first_row_header"] = self.header_check.isChecked()
            
        if hasattr(self, "remember_history_check"):
            config["remember_history"] = self.remember_history_check.isChecked()
            if self.remember_history_check.isChecked():
                config["saved_history"] = getattr(mw, "csv_import_plus_history", [])
            else:
                config.pop("saved_history", None)

        mw.addonManager.writeConfig(__name__, config)

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
    def pick_file(self):
        start_dir = mw.pm.profile.get(PROFILE_KEY_LAST_DIR, "")
        path, _ = QFileDialog.getOpenFileName(
            mw, "Select CSV to Import", start_dir, "CSV Files (*.csv)"
        )
        if not path:
            return
        self.file_path = path
        self.file_edit.setText(path)
        try:
            mw.pm.profile[PROFILE_KEY_LAST_DIR] = os.path.dirname(path)
        except Exception:
            pass

        # Prefill subdeck name from filename
        base = os.path.splitext(os.path.basename(path))[0]
        self.subdeck_edit.setText(base)

        self.on_content_changed()

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
        result = importer.do_import(
            raw,
            self.deck_combo,
            self.deck_infos,
            self.notetype_combo,
            self.model_infos,
            self.header_check,
            self.delimiter_combo,
        )
        if result:
            self.refresh_history()
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

    # -------------------- Import paths --------------------
    def open_with_default_importer(self):
        raw = self.get_active_raw()
        importer.open_with_default_importer(raw, self.deck_combo, self.deck_infos)

    def do_import(self):
        raw = self.get_active_raw()
        self._run_import(raw, clear_pasted_input=True)

    # -------------------- History --------------------
    def refresh_history(self):
        self.history_tree.blockSignals(True)
        self.history_tree.clear()
        history = getattr(mw, "csv_import_plus_history", [])
        for i, batch in enumerate(reversed(history)):
            real_idx = len(history) - 1 - i
            batch_item = QTreeWidgetItem(self.history_tree)
            batch_item.setData(0, Qt.ItemDataRole.UserRole, real_idx)
            
            notetype_name = batch.get("notetype_name", "Unknown")
            batch_item.setText(0, f"[{batch['time']}] Added {batch['added']} cards to '{batch['deck_name']}' ({notetype_name})")
            
            batch_del_btn = QPushButton("Delete Batch")
            batch_del_btn.setStyleSheet("color: #d32f2f; font-weight: bold; padding: 2px 8px; margin: 2px;")
            batch_del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            batch_del_btn.clicked.connect(lambda _, bidx=real_idx: self.delete_history_batch(bidx))
            self.history_tree.setItemWidget(batch_item, 1, batch_del_btn)
            
            for c_idx, card in enumerate(batch["cards"]):
                card_item = QTreeWidgetItem(batch_item)
                
                if isinstance(card, dict):
                    preview_text = card.get("preview", "")
                    nid = card.get("id")
                else:
                    preview_text = str(card)
                    nid = None

                preview = (preview_text[:150] + '...') if len(preview_text) > 150 else preview_text
                card_item.setText(0, preview)
                if nid is not None:
                    card_item.setData(0, Qt.ItemDataRole.UserRole + 1, nid)
                    
                card_del_btn = QPushButton("Delete")
                card_del_btn.setStyleSheet("color: #d32f2f; padding: 0px 8px;")
                card_del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                card_del_btn.clicked.connect(lambda _, bidx=real_idx, cid=c_idx: self.delete_history_card(bidx, cid))
                self.history_tree.setItemWidget(card_item, 1, card_del_btn)
            
            batch_item.setExpanded(batch.get("expanded", True))
            
        self.history_tree.blockSignals(False)
        self.save_history_if_needed()

    def on_history_item_expanded(self, item):
        real_idx = item.data(0, Qt.ItemDataRole.UserRole)
        if real_idx is not None and isinstance(real_idx, int):
            history = getattr(mw, "csv_import_plus_history", [])
            if 0 <= real_idx < len(history):
                history[real_idx]["expanded"] = True
                self.save_history_if_needed()

    def on_history_item_collapsed(self, item):
        real_idx = item.data(0, Qt.ItemDataRole.UserRole)
        if real_idx is not None and isinstance(real_idx, int):
            history = getattr(mw, "csv_import_plus_history", [])
            if 0 <= real_idx < len(history):
                history[real_idx]["expanded"] = False
                self.save_history_if_needed()

    def on_history_selection_changed(self):
        selected = self.history_tree.selectedItems()
        has_selection = len(selected) > 0
        self.browse_history_btn.setEnabled(has_selection)
        if hasattr(self, "delete_selected_history_btn"):
            self.delete_selected_history_btn.setEnabled(has_selection)

    def browse_selected_history(self):
        selected = self.history_tree.selectedItems()
        if not selected:
            return

        nids = []
        for item in selected:
            if item.childCount() > 0:
                for i in range(item.childCount()):
                    child = item.child(i)
                    nid = child.data(0, Qt.ItemDataRole.UserRole + 1)
                    if nid is not None:
                        nids.append(nid)
            else:
                nid = item.data(0, Qt.ItemDataRole.UserRole + 1)
                if nid is not None:
                    nids.append(nid)

        if not nids:
            return

        query = f"nid:{','.join(map(str, set(nids)))}"
        import aqt
        browser = aqt.dialogs.open("Browser", mw)
        browser.form.searchEdit.lineEdit().setText(query)
        browser.onSearchActivated()

    def delete_selected_history(self):
        selected = self.history_tree.selectedItems()
        if not selected:
            return

        nids_to_del = set()
        
        for item in selected:
            if item.childCount() > 0:
                for i in range(item.childCount()):
                    child = item.child(i)
                    nid = child.data(0, Qt.ItemDataRole.UserRole + 1)
                    if nid is not None:
                        nids_to_del.add(nid)
            else:
                nid = item.data(0, Qt.ItemDataRole.UserRole + 1)
                if nid is not None:
                    nids_to_del.add(nid)

        if not nids_to_del:
            return

        try:
            mw.col.remove_notes(list(nids_to_del))
        except Exception:
            try:
                mw.col.remNotes(list(nids_to_del))
            except Exception:
                pass

        history = getattr(mw, "csv_import_plus_history", [])
        for batch in history:
            batch["cards"] = [
                c for c in batch["cards"] 
                if (isinstance(c, dict) and c.get("id") not in nids_to_del) or not isinstance(c, dict)
            ]
            batch["added"] = len(batch["cards"])
            
        history[:] = [b for b in history if b["added"] > 0]
        
        self.refresh_history()

    def delete_history_batch(self, real_idx):
        history = getattr(mw, "csv_import_plus_history", [])
        if 0 <= real_idx < len(history):
            batch = history[real_idx]
            nids = []
            for c in batch["cards"]:
                if isinstance(c, dict) and c.get("id"):
                    nids.append(c["id"])
            if nids:
                try:
                    mw.col.remove_notes(nids)
                except Exception:
                    try:
                        mw.col.remNotes(nids)
                    except Exception:
                        pass
            del history[real_idx]
            self.refresh_history()

    def delete_history_card(self, real_idx, card_idx):
        history = getattr(mw, "csv_import_plus_history", [])
        if 0 <= real_idx < len(history):
            batch = history[real_idx]
            cards = batch["cards"]
            if 0 <= card_idx < len(cards):
                c = cards[card_idx]
                if isinstance(c, dict) and c.get("id"):
                    try:
                        mw.col.remove_notes([c["id"]])
                    except Exception:
                        try:
                            mw.col.remNotes([c["id"]])
                        except Exception:
                            pass
                del cards[card_idx]
                batch["added"] = len(cards)
                if not cards:
                    del history[real_idx]
                self.refresh_history()

    def clear_history(self):
        mw.csv_import_plus_history = []
        self.refresh_history()
