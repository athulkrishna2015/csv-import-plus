# -*- coding: utf-8 -*-

from aqt.qt import (
    QTabWidget,
    QVBoxLayout,
)

from .tabs.import_tab import ImportTab
from .tabs.history_tab import HistoryTab
from .tabs.advanced_tab import AdvancedTab
from .tabs.support_tab import SupportTab

def setup_ui(self):
    self.setWindowTitle("CSV Import +")
    self.setMinimumSize(800, 600)

    # Use a QTabWidget as the root
    self.tabs = QTabWidget(self)
    root_layout = QVBoxLayout(self)
    root_layout.addWidget(self.tabs)
    self.setLayout(root_layout)

    # Instantiate tabs
    self.import_tab_widget = ImportTab(self)
    self.history_tab_widget = HistoryTab(self)
    self.advanced_tab_widget = AdvancedTab(self)
    self.support_tab_widget = SupportTab(self)

    # Add tabs
    self.tabs.addTab(self.import_tab_widget, "Import")
    self.tabs.addTab(self.history_tab_widget, "History")
    self.tabs.addTab(self.advanced_tab_widget, "Advanced")
    self.tabs.addTab(self.support_tab_widget, "Support")

    # Map internal references for backward compatibility if needed, 
    # but it's better to update dialog.py to use tab_widget references.
    self.file_edit = self.import_tab_widget.file_edit
    self.csv_text = self.import_tab_widget.csv_text
    self.status_label = self.import_tab_widget.status_label
    self.deck_combo = self.import_tab_widget.deck_combo
    self.subdeck_edit = self.import_tab_widget.subdeck_edit
    self.notetype_combo = self.import_tab_widget.notetype_combo
    self.delimiter_combo = self.import_tab_widget.delimiter_combo
    self.quick_clipboard_btn = self.import_tab_widget.quick_clipboard_btn
    self.remove_btn = self.import_tab_widget.remove_btn
    self.progress_bar = self.import_tab_widget.progress_bar
    
    self.allow_html_check = self.import_tab_widget.allow_html_check
    self.existing_notes_combo = self.import_tab_widget.existing_notes_combo
    self.match_scope_combo = self.import_tab_widget.match_scope_combo
    self.tag_all_edit = self.import_tab_widget.tag_all_edit
    self.tag_updated_edit = self.import_tab_widget.tag_updated_edit
    
    self.history_tree = self.history_tab_widget.history_tree
    self.browse_history_btn = self.history_tab_widget.browse_history_btn
    self.delete_selected_history_btn = self.history_tab_widget.delete_selected_history_btn
    
    self.deck_lock_check = self.advanced_tab_widget.deck_lock_check
    self.header_check = self.advanced_tab_widget.header_check
    self.remember_history_check = self.advanced_tab_widget.remember_history_check
    self.allow_any_clipboard_toggle = self.advanced_tab_widget.allow_any_clipboard_toggle
    self.clipboard_confirm_toggle = self.advanced_tab_widget.clipboard_confirm_toggle

    self.supporter_check = self.support_tab_widget.supporter_check
