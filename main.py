# -*- coding: utf-8 -*-

from aqt import mw, gui_hooks
from aqt.qt import QAction

from .dialog import CSVImportPlusDialog


def show_csv_import_plus_dialog():
    dialog = getattr(mw, "csv_import_plus_dialog", None)
    if dialog and dialog.isVisible():
        dialog.activateWindow()
        dialog.raise_()
        return

    d = CSVImportPlusDialog(mw)

    def _clear_dialog_ref(*_):
        if getattr(mw, "csv_import_plus_dialog", None) is d:
            setattr(mw, "csv_import_plus_dialog", None)

    d.destroyed.connect(_clear_dialog_ref)
    d.show()
    d.raise_()
    d.activateWindow()
    mw.csv_import_plus_dialog = d


def setup_menu():
    action = QAction("CSV Import +...", mw)
    action.triggered.connect(show_csv_import_plus_dialog)
    mw.form.menuTools.addAction(action)


def init():
    gui_hooks.main_window_did_init.append(setup_menu)
