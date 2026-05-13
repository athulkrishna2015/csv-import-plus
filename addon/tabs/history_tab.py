# -*- coding: utf-8 -*-

from aqt import mw
from aqt.qt import (
    Qt,
    QVBoxLayout,
    QWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
    QHBoxLayout,
    QAbstractItemView,
)

class HistoryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dialog = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.history_tree = QTreeWidget(self)
        self.history_tree.setColumnCount(2)
        self.history_tree.setHeaderLabels(["History", "Action"])
        self.history_tree.header().resizeSection(0, 550)
        self.history_tree.setIndentation(15)
        self.history_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(self.history_tree)
        
        self.history_tree.itemExpanded.connect(self.on_history_item_expanded)
        self.history_tree.itemCollapsed.connect(self.on_history_item_collapsed)
        self.history_tree.itemSelectionChanged.connect(self.on_history_selection_changed)

        history_btns = QHBoxLayout()

        self.browse_history_btn = QPushButton("Browse Selected", self)
        self.browse_history_btn.setEnabled(False)
        self.browse_history_btn.clicked.connect(self.browse_selected_history)
        history_btns.addWidget(self.browse_history_btn)

        self.delete_selected_history_btn = QPushButton("Delete Selected", self)
        self.delete_selected_history_btn.setEnabled(False)
        self.delete_selected_history_btn.clicked.connect(self.delete_selected_history)
        history_btns.addWidget(self.delete_selected_history_btn)

        history_btns.addStretch()

        self.clear_history_btn = QPushButton("Clear Session History", self)
        self.clear_history_btn.clicked.connect(self.clear_history)
        history_btns.addWidget(self.clear_history_btn)
        
        layout.addLayout(history_btns)

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
            
            batch_item.setExpanded(batch.get("expanded", False))
            
        self.history_tree.blockSignals(False)
        if hasattr(self.dialog, "save_history_if_needed"):
            self.dialog.save_history_if_needed()

    def on_history_item_expanded(self, item):
        real_idx = item.data(0, Qt.ItemDataRole.UserRole)
        if real_idx is not None and isinstance(real_idx, int):
            history = getattr(mw, "csv_import_plus_history", [])
            if 0 <= real_idx < len(history):
                history[real_idx]["expanded"] = True
                if hasattr(self.dialog, "save_history_if_needed"):
                    self.dialog.save_history_if_needed()

    def on_history_item_collapsed(self, item):
        real_idx = item.data(0, Qt.ItemDataRole.UserRole)
        if real_idx is not None and isinstance(real_idx, int):
            history = getattr(mw, "csv_import_plus_history", [])
            if 0 <= real_idx < len(history):
                history[real_idx]["expanded"] = False
                if hasattr(self.dialog, "save_history_if_needed"):
                    self.dialog.save_history_if_needed()

    def on_history_selection_changed(self):
        selected = self.history_tree.selectedItems()
        has_selection = len(selected) > 0
        self.browse_history_btn.setEnabled(has_selection)
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
