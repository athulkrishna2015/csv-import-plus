# -*- coding: utf-8 -*-

import os
import json
from aqt import mw, gui_hooks
from aqt.utils import openLink
from aqt.qt import QAction

from .dialog import CSVImportPlusDialog


def show_csv_import_plus_dialog(tab_index=None):
    dialog = getattr(mw, "csv_import_plus_dialog", None)
    if dialog and dialog.isVisible():
        if tab_index is not None:
            dialog.tabs.setCurrentIndex(tab_index)
        dialog.activateWindow()
        dialog.raise_()
        return

    # Use mw as parent so it closes with Anki.
    # We still keep it non-modal by using .show()
    d = CSVImportPlusDialog(mw)
    if tab_index is not None:
        d.tabs.setCurrentIndex(tab_index)

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
    action.triggered.connect(lambda: show_csv_import_plus_dialog())
    mw.form.menuTools.addAction(action)


def check_for_update_welcome():
    addon_id = mw.addonManager.addonFromModule(__name__)
    if not addon_id:
        return
    
    # Use meta.json for internal state tracking
    meta = mw.addonManager.addonMeta(addon_id)
    
    # Get current version from manifest.json
    addon_path = os.path.dirname(__file__)
    manifest_path = os.path.join(addon_path, "manifest.json")
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            current_version = manifest.get("version", "0.0.0")
    except Exception:
        current_version = "0.0.0"

    last_version = meta.get("last_version_seen", "0.0.0")
    
    if current_version != last_version:
        meta["last_version_seen"] = current_version
        mw.addonManager.writeAddonMeta(addon_id, meta)
        
        # Also clean up from config.json if it was there
        config = mw.addonManager.getConfig(addon_id)
        if config and ("last_version" in config or "last_version_seen" in config):
            config.pop("last_version", None)
            config.pop("last_version_seen", None)
            mw.addonManager.writeConfig(addon_id, config)

        # 3 is the index of the "Support" tab
        # Use a small delay to ensure the main window is ready
        from aqt.qt import QTimer
        QTimer.singleShot(1000, lambda: show_csv_import_plus_dialog(tab_index=3))


def init():
    gui_hooks.main_window_did_init.append(setup_menu)
    gui_hooks.main_window_did_init.append(check_for_update_welcome)
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
