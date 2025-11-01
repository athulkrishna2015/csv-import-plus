# -*- coding: utf-8 -*-

from aqt import mw, gui_hooks
from aqt.qt import QAction

from .dialog import CSVImportPlusDialog


def show_csv_import_plus_dialog():
    if hasattr(mw, "csv_import_plus_dialog") and mw.csv_import_plus_dialog.isVisible():
        mw.csv_import_plus_dialog.activateWindow()
        return
    mw.csv_import_plus_dialog = CSVImportPlusDialog(None)
    mw.csv_import_plus_dialog.show()


def setup_menu():
    action = QAction("CSV Import +...", mw)
    action.triggered.connect(show_csv_import_plus_dialog)
    mw.form.menuTools.addAction(action)


def init():
    gui_hooks.main_window_did_init.append(setup_menu)

