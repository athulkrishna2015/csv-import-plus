# -*- coding: utf-8 -*-

import csv
import io
import os
import tempfile

from aqt import mw
from aqt.utils import showInfo, showWarning
from aqt.importing import importFile

from . import detector
from . import anki_helpers


def open_with_default_importer(raw_content, deck_combo, deck_infos):
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

    try:
        importFile(mw, path)
        # Dialog intentionally stays open for further imports
    except Exception as e:
        showWarning(f"Could not open import dialog: {e}")
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


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

        if header_check.isChecked() and len(rows) > 1:
            rows = rows[1:]

        field_names = [f["name"] for f in notetype["flds"]]

        mw.col.decks.select(deck_id)

        added = 0
        skipped_empty = 0
        for row in rows:
            if not row or all(not c.strip() for c in row):
                skipped_empty += 1
                continue

            note = mw.col.new_note(notetype)
            for i, val in enumerate(row[: len(field_names)]):
                note.fields[i] = val.strip()

            # Tags from last column if extra
            if len(row) > len(field_names):
                tags = row[-1].strip()
                if tags:
                    note.tags = tags.split()

            mw.col.add_note(note, deck_id)
            added += 1

        mw.reset()

        deck_name = deck_combo.currentText()
        msg = f"Import complete!\n\nAdded: {added} note(s) to deck '{deck_name}'"
        if skipped_empty:
            msg += f"\nSkipped empty rows: {skipped_empty}"
        if delimiter_combo.currentText() == "Auto-detect":
            msg += f"\n\nUsed delimiter: {detector.get_delimiter_name(delimiter)}"

        showInfo(msg)
        # Dialog intentionally stays open for further imports
    except Exception as e:
        showWarning(f"Import failed: {str(e)}")


def get_delimiter(delimiter_combo, content):
    selection = delimiter_combo.currentText()
    if selection == "Auto-detect":
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
