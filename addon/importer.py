# -*- coding: utf-8 -*-

import csv
import io
import os
import tempfile
import datetime

try:
    from aqt import mw
    from aqt.utils import showWarning
except Exception:  # pragma: no cover - fallback for tests
    mw = None

    def showWarning(_msg):
        pass

from . import detector
from . import anki_helpers

_PENDING_IMPORT_CLEANUP = set()
_IMPORT_DIALOG_HOOKED = False


def _safe_unlink(path: str) -> None:
    try:
        os.unlink(path)
    except Exception:
        pass


def _ensure_import_dialog_cleanup_hook() -> None:
    global _IMPORT_DIALOG_HOOKED
    if _IMPORT_DIALOG_HOOKED:
        return
    try:
        from anki.hooks import wrap
        from aqt.import_export import import_dialog
    except Exception:
        return

    def _after_init(self, *args, **kwargs) -> None:
        path = getattr(getattr(self, "args", None), "path", None)
        if not path:
            return
        if path in _PENDING_IMPORT_CLEANUP:
            _PENDING_IMPORT_CLEANUP.discard(path)
            try:
                self.finished.connect(lambda _=None, p=path: _safe_unlink(p))
            except Exception:
                pass

    import_dialog.ImportDialog.__init__ = wrap(
        import_dialog.ImportDialog.__init__, _after_init, "after"
    )
    _IMPORT_DIALOG_HOOKED = True


def _open_with_latest_importer(path: str) -> bool:
    if mw is None:
        return False
    try:
        from aqt.import_export.importing import import_file
    except Exception:
        return False

    _ensure_import_dialog_cleanup_hook()
    _PENDING_IMPORT_CLEANUP.add(path)
    import_file(mw, path)
    return True


def open_with_default_importer(raw_content, deck_combo, deck_infos):
    if mw is None:
        showWarning("Anki is not available.")
        return
    if not raw_content:
        showWarning("Provide CSV via Paste or choose a CSV file first.")
        return

    # Select deck for sane defaults
    deck_idx = deck_combo.currentIndex()
    deck_id = anki_helpers.deck_id_from_index(deck_infos, deck_idx)
    if deck_id is not None:
        try:
            mw.col.decks.select(deck_id)
        except Exception:
            pass

    # Write a temp CSV and let Anki's importer handle it
    csv_content = detector.strip_directive_lines(raw_content)
    try:
        fd, path = tempfile.mkstemp(
            prefix="anki_csv_import_plus_", suffix=".csv", text=True
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                f.write(csv_content)
        except Exception as e:
            try:
                os.close(fd)
            except Exception:
                pass
            showWarning(f"Could not write temp CSV: {e}")
            return
    except Exception as e:
        showWarning(f"Could not create temp file: {e}")
        return

    used_latest = False
    try:
        used_latest = _open_with_latest_importer(path)
        if not used_latest:
            from aqt.importing import importFile

            importFile(mw, path)
            # Dialog intentionally stays open for further imports
    except Exception as e:
        showWarning(f"Could not open import dialog: {e}")
        if used_latest:
            _PENDING_IMPORT_CLEANUP.discard(path)
            _safe_unlink(path)
    finally:
        if not used_latest:
            _safe_unlink(path)


def do_import(
    raw_content,
    deck_combo,
    deck_infos,
    notetype_combo,
    model_infos,
    header_check,
    delimiter_combo,
):
    if not raw_content:
        showWarning("Provide CSV via Paste or choose a CSV file first.")
        return

    # Re-apply #notetype directive at import time
    directives = detector.extract_directives(raw_content)
    nt_name = directives.get("notetype")
    if nt_name:
        idx = detector.find_model_index_by_name(model_infos, nt_name)
        if idx is not None:
            notetype_combo.setCurrentIndex(idx)

    csv_content = detector.strip_directive_lines(raw_content)

    deck_idx = deck_combo.currentIndex()
    model_idx = notetype_combo.currentIndex()
    deck_id = anki_helpers.deck_id_from_index(deck_infos, deck_idx)
    model_id = anki_helpers.model_id_from_index(model_infos, model_idx)

    if deck_id is None:
        showWarning("Could not resolve target deck.")
        return
    if model_id is None:
        showWarning("Could not resolve note type.")
        return

    try:
        notetype = mw.col.models.get(model_id)
        if not notetype:
            showWarning("Selected note type not found.")
            return

        delimiter = get_delimiter(delimiter_combo, csv_content)
        reader = csv.reader(io.StringIO(csv_content), delimiter=delimiter)
        rows = [r for r in reader]
        if not rows:
            showWarning("No data rows found.")
            return

        if header_check.isChecked():
            rows = rows[1:]
            if not rows:
                showWarning("No data rows found after skipping header row.")
                return

        field_names = [f["name"] for f in notetype["flds"]]

        mw.col.decks.select(deck_id)

        added = 0
        skipped_empty = 0
        notes_to_add = []
        for row in rows:
            if not row or all(not c.strip() for c in row):
                skipped_empty += 1
                continue

            note = mw.col.new_note(notetype)
            for i, val in enumerate(row[: len(field_names)]):
                note.fields[i] = val.strip()

            if len(row) > len(field_names):
                tags = row[-1].strip()
                if tags:
                    note.tags = tags.split()
                    
            notes_to_add.append(note)

        mw.progress.start()
        mw.checkpoint("CSV Import Plus")
        
        # Merge operations in highly modern Anki:
        try:
            if hasattr(mw.col, "merge_undo_entries"):
                pass  # Alternatively, just use checkpoint and Anki groups it automatically or leaves it per note.
        except Exception:
            pass

        added_cards_previews = []
        for note in notes_to_add:
            mw.col.add_note(note, deck_id)
            added += 1
            if len(note.fields) > 0:
                added_cards_previews.append({"id": note.id, "preview": note.fields[0]})
            else:
                added_cards_previews.append({"id": note.id, "preview": "Empty Note"})

        mw.progress.finish()
        mw.reset()

        deck_name = deck_combo.currentText()
        if added > 0:
            if not hasattr(mw, "csv_import_plus_history"):
                mw.csv_import_plus_history = []
            now_str = datetime.datetime.now().strftime("%I:%M %p")
            mw.csv_import_plus_history.append({
                "time": now_str,
                "deck_name": deck_name,
                "notetype_name": notetype.get("name", "Unknown"),
                "expanded": True,
                "added": added,
                "cards": added_cards_previews
            })
        return {
            "added": added,
            "skipped_empty": skipped_empty,
            "deck_name": deck_name,
            "used_auto_delimiter": delimiter_combo.currentIndex() == 0,
            "delimiter_name": detector.get_delimiter_name(delimiter),
        }
    except Exception as e:
        showWarning(f"Import failed: {str(e)}")
        return None


def get_delimiter(delimiter_combo, content):
    selection = delimiter_combo.currentText()
    if delimiter_combo.currentIndex() == 0 or selection.startswith("Auto-detect"):
        if content:
            try:
                delimiter, _ = detector.detect_csv_format(content)
                return delimiter
            except Exception:
                return ","
        return ","
    mapping = {
        "Comma (,)": ",",
        "Tab": "\t",
        "Semicolon (;)": ";",
        "Pipe (|)": "|",
    }
    return mapping.get(selection, ",")
