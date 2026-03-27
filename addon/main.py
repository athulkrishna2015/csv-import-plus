# -*- coding: utf-8 -*-

from aqt import mw, gui_hooks
from aqt.utils import openLink
from aqt.qt import QAction

from .dialog import CSVImportPlusDialog


def show_csv_import_plus_dialog():
    dialog = getattr(mw, "csv_import_plus_dialog", None)
    if dialog and dialog.isVisible():
        dialog.activateWindow()
        dialog.raise_()
        return

    # Use a top-level window (no Qt parent) so it does not stay on top of,
    # minimize with, or force-focus the Anki main window.
    d = CSVImportPlusDialog()

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
    gui_hooks.webview_will_set_content.append(on_webview_will_set_content)


KOFI_SCRIPT = """
<script type='text/javascript' src='https://storage.ko-fi.com/cdn/widget/Widget_2.js'></script>
<script type='text/javascript'>
  kofiwidget2.init('Support me on Ko-fi', '#72a4f2', 'D1D01W6NQT');
  kofiwidget2.draw();
</script>
"""

def on_webview_will_set_content(web_content, webview):
    # Only inject into the main window and reviewer for a clean experience
    from aqt import mw
    if webview in [mw.web, getattr(mw.reviewer, "web", None)]:
        if KOFI_SCRIPT not in web_content.head:
            web_content.head += KOFI_SCRIPT
