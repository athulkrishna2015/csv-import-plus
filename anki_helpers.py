# -*- coding: utf-8 -*-

import re
from typing import List, Optional

from aqt import mw
from aqt.utils import showWarning


def refresh_decks(deck_combo, select_name: Optional[str] = None):
    try:
        deck_infos = list(mw.col.decks.all_names_and_ids())
    except Exception:
        deck_infos = []

    deck_combo.clear()
    names = [d.name for d in deck_infos]
    deck_combo.addItems(names)

    # Default: current deck
    try:
        cur = mw.col.decks.current()
        cur_name = cur["name"] if isinstance(cur, dict) else getattr(cur, "name", "")
        if cur_name:
            idx = deck_combo.findText(cur_name)
            if idx >= 0:
                deck_combo.setCurrentIndex(idx)
    except Exception:
        pass

    # Optional selection
    if select_name:
        idx = deck_combo.findText(select_name)
        if idx >= 0:
            deck_combo.setCurrentIndex(idx)
    return deck_infos


def deck_id_from_index(deck_infos, i):
    if not deck_infos or i < 0 or i >= len(deck_infos):
        return None
    d = deck_infos[i]
    return getattr(d, "id", getattr(d, "did", None))


def model_id_from_index(model_infos, i):
    if not model_infos or i < 0 or i >= len(model_infos):
        return None
    m = model_infos[i]
    return getattr(m, "id", None)


def create_subdeck(deck_combo, subdeck_edit, status_label):
    parent_name = deck_combo.currentText().strip()
    child = subdeck_edit.text().strip()
    if not child:
        showWarning("Enter a subdeck name first.")
        return None

    child = re.sub(r"\s{2,}", " ", child)
    full_name = f"{parent_name}::{child}"
    try:
        did = mw.col.decks.id(full_name)
        mw.col.decks.select(did)
        subdeck_edit.clear()
        status_label.setText(f"✓ Created subdeck: {full_name}")
        return full_name
    except Exception as e:
        showWarning(f"Could not create subdeck: {e}")
        return None


def get_model_infos():
    try:
        return list(mw.col.models.all_names_and_ids())
    except Exception:
        return []
