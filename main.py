# -*- coding: utf-8 -*-

from aqt import mw, gui_hooks
from aqt.qt import QAction

from .dialog import CSVImportPlusDialog


def show_csv_import_plus_dialog():
    dlg = CSVImportPlusDialog(mw)
    dlg.exec()


def setup_menu():
    action = QAction("CSV Import +...", mw)
    action.triggered.connect(show_csv_import_plus_dialog)
    mw.form.menuTools.addAction(action)


def init():
    gui_hooks.main_window_did_init.append(setup_menu)

