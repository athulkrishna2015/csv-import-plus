# -*- coding: utf-8 -*-

import os
import csv
import io

from aqt import mw
from aqt.qt import QDialog, QFileDialog

from . import anki_helpers
from . import detector
from . import importer
from . import ui

PROFILE_KEY_LAST_DIR = "csv_import_plus_last_dir"


class CSVImportPlusDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.deck_infos = []
        self.model_infos = []
        # State
        self.file_path = ""
        self.locked_deck_name = None
        self.setup_ui()
        self.load_config()

    def closeEvent(self, event):
        self.deleteLater()
        event.accept()

    # -------------------- UI --------------------
    setup_ui = ui.setup_ui

    # -------------------- Config --------------------
    def load_config(self):
        config = mw.addonManager.getConfig(__name__)
        if not config:
            return
        
        self.deck_lock_check.setChecked(config.get("deck_lock", False))
        self.locked_deck_name = config.get("locked_deck_name")

        if self.deck_lock_check.isChecked() and self.locked_deck_name:
            self.deck_combo.setCurrentText(self.locked_deck_name)

    def save_config(self):
        config = {
            "deck_lock": self.deck_lock_check.isChecked(),
            "locked_deck_name": self.locked_deck_name,
        }
        mw.addonManager.writeConfig(__name__, config)

    def on_deck_lock_toggled(self, checked):
        if checked:
            self.locked_deck_name = self.deck_combo.currentText()
        else:
            self.locked_deck_name = None
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

    # -------------------- Status updates --------------------
    def on_content_changed(self):
        raw = self.get_active_raw()
        if not raw:
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

        # Determine delimiter & rows
        if self.delimiter_combo.currentText() == "Auto-detect":
            try:
                delimiter, rows = detector.detect_csv_format(content)
            except Exception as e:
                self.status_label.setText(f"⚠ Detection failed: {str(e)}")
                return
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
                f"Note type: {model_name} ({field_count} field(s), via directive))"
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
        importer.do_import(
            raw,
            self.deck_combo,
            self.deck_infos,
            self.notetype_combo,
            self.model_infos,
            self.header_check,
            self.delimiter_combo,
        )

        if self.deck_lock_check.isChecked() and self.locked_deck_name:
            self.deck_combo.setCurrentText(self.locked_deck_name)
