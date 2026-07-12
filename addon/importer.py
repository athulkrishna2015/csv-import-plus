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
    if deck_idx < 0:
        deck_idx = deck_combo.findText(deck_combo.currentText())
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
    allow_html=True,
    existing_notes_index=2,
    match_scope_index=0,
    tag_all="",
    tag_updated="",
    field_mapping=None,
):
    if not raw_content:
        showWarning("Provide CSV via Paste or choose a CSV file first.")
        return

    csv_content = detector.strip_directive_lines(raw_content)

    deck_idx = deck_combo.currentIndex()
    if deck_idx < 0:
        deck_idx = deck_combo.findText(deck_combo.currentText())
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

        # Retrieve existing notes for duplicate checking if mode is Update or Preserve
        existing_notes = {}
        if existing_notes_index in (0, 1) and mw is not None:
            if match_scope_index == 1:
                # Same note type and deck
                db_rows = mw.col.db.all(
                    "select distinct n.id, n.flds from notes n "
                    "join cards c on n.id = c.nid "
                    "where n.mid = ? and c.did = ?",
                    model_id, deck_id
                )
            else:
                # Same note type
                db_rows = mw.col.db.all(
                    "select id, flds from notes where mid = ?", model_id
                )
            
            for nid, flds in db_rows:
                first_fld = flds.split("\x1f")[0]
                existing_notes[first_fld.strip()] = nid

        added = 0
        updated = 0
        skipped_empty = 0
        notes_to_add = []
        notes_to_update = []

        tags_all_list = [t for t in tag_all.strip().split() if t]
        tags_updated_list = [t for t in tag_updated.strip().split() if t]

        for row in rows:
            if not row or all(not c.strip() for c in row):
                skipped_empty += 1
                continue

            # Determine key (first field processed)
            first_field_col_idx = 0
            if field_mapping and len(field_names) > 0:
                mapped_idx = field_mapping.get(field_names[0])
                if mapped_idx is not None:
                    first_field_col_idx = mapped_idx

            first_val = row[first_field_col_idx].strip() if len(row) > first_field_col_idx else ""
            if not allow_html:
                import html
                first_val_processed = html.escape(first_val).replace("\r\n", "<br>").replace("\n", "<br>")
            else:
                first_val_processed = first_val.replace("\r\n", "<br>").replace("\n", "<br>")

            existing_note_id = existing_notes.get(first_val_processed)

            if existing_note_id is not None:
                if existing_notes_index == 1:
                    # Preserve: do nothing, skip this row
                    continue
                elif existing_notes_index == 0:
                    # Update: update existing note
                    try:
                        note = mw.col.get_note(existing_note_id)
                        if field_mapping:
                            for f_idx, f_name in enumerate(field_names):
                                col_idx = field_mapping.get(f_name)
                                if col_idx is not None and col_idx < len(row):
                                    val_str = row[col_idx].strip()
                                    if not allow_html:
                                        import html
                                        val_str = html.escape(val_str)
                                    val_str = val_str.replace("\r\n", "<br>").replace("\n", "<br>")
                                    note.fields[f_idx] = val_str
                        else:
                            for i, val in enumerate(row[: len(field_names)]):
                                val_str = val.strip()
                                if not allow_html:
                                    import html
                                    val_str = html.escape(val_str)
                                val_str = val_str.replace("\r\n", "<br>").replace("\n", "<br>")
                                note.fields[i] = val_str

                        # Add tags
                        for tag in tags_all_list + tags_updated_list:
                            if tag not in note.tags:
                                note.tags.append(tag)

                        notes_to_update.append(note)
                        continue
                    except Exception:
                        pass

            # Duplicate/Create New Note
            note = mw.col.new_note(notetype)
            if field_mapping:
                for f_idx, f_name in enumerate(field_names):
                    col_idx = field_mapping.get(f_name)
                    if col_idx is not None and col_idx < len(row):
                        val_str = row[col_idx].strip()
                        if not allow_html:
                            import html
                            val_str = html.escape(val_str)
                        val_str = val_str.replace("\r\n", "<br>").replace("\n", "<br>")
                        note.fields[f_idx] = val_str
            else:
                for i, val in enumerate(row[: len(field_names)]):
                    val_str = val.strip()
                    if not allow_html:
                        import html
                        val_str = html.escape(val_str)
                    val_str = val_str.replace("\r\n", "<br>").replace("\n", "<br>")
                    note.fields[i] = val_str

            if field_mapping:
                tags_col_idx = field_mapping.get("Tags")
                if tags_col_idx is not None and tags_col_idx < len(row):
                    tags_val = row[tags_col_idx].strip()
                    if tags_val:
                        for t in tags_val.split():
                            if t not in note.tags:
                                note.tags.append(t)
            else:
                if len(row) > len(field_names):
                    tags = row[-1].strip()
                    if tags:
                        for t in tags.split():
                            if t not in note.tags:
                                note.tags.append(t)

            for tag in tags_all_list:
                if tag not in note.tags:
                    note.tags.append(tag)

            notes_to_add.append(note)

        mw.progress.start()
        
        # Merge operations in modern Anki for native batch Ctrl+Z
        use_bulk_undo = hasattr(mw.col, "add_custom_undo_entry") and hasattr(mw.col, "merge_undo_entries")
        undo_entry = None
        if use_bulk_undo:
            try:
                undo_entry = mw.col.add_custom_undo_entry("CSV Import")
            except Exception:
                pass
        else:
            mw.checkpoint("CSV Import Plus")

        added_cards_previews = []

        # Save updated notes
        for note in notes_to_update:
            try:
                if hasattr(mw.col, "update_note"):
                    mw.col.update_note(note)
                else:
                    note.flush()
                updated += 1
                if len(note.fields) > 0:
                    added_cards_previews.append({"id": note.id, "preview": note.fields[0]})
                else:
                    added_cards_previews.append({"id": note.id, "preview": "Updated Note"})
            except Exception:
                pass

        # Save new notes
        for note in notes_to_add:
            try:
                mw.col.add_note(note, deck_id)
                added += 1
                if len(note.fields) > 0:
                    added_cards_previews.append({"id": note.id, "preview": note.fields[0]})
                else:
                    added_cards_previews.append({"id": note.id, "preview": "Empty Note"})
            except Exception as e:
                pass

        if use_bulk_undo and undo_entry is not None:
            try:
                mw.col.merge_undo_entries(undo_entry)
            except Exception:
                pass

        mw.progress.finish()
        mw.reset()

        deck_name = deck_combo.currentText()
        if (added + updated) > 0:
            if not hasattr(mw, "csv_import_plus_history"):
                mw.csv_import_plus_history = []
            now_str = datetime.datetime.now().strftime("%I:%M %p")
            mw.csv_import_plus_history.append({
                "time": now_str,
                "deck_name": deck_name,
                "notetype_name": notetype.get("name", "Unknown"),
                "expanded": False,
                "added": added,
                "updated": updated,
                "cards": added_cards_previews
            })
        return {
            "added": added,
            "updated": updated,
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
