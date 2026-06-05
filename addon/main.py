import os
import json
import csv
import io
from aqt import mw, gui_hooks
from aqt.utils import openLink
from aqt.qt import (
    QAction,
    QObject,
    QEvent,
    QApplication,
    Qt,
)

from .dialog import CSVImportPlusDialog


def is_valid_csv_text(text: str) -> bool:
    text = text.strip()
    if not text:
        return False
    if text.startswith("#notetype:"):
        return True
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return False
    
    # Try delimiters
    for delim in (',', '\t', ';', '|'):
        try:
            reader = csv.reader(io.StringIO(text), delimiter=delim)
            rows = [r for r in reader if r]
            if rows and any(len(r) > 1 for r in rows):
                return True
        except Exception:
            continue
    return False


class OverviewDragDropFilter(QObject):
    def eventFilter(self, obj, event):
        if getattr(mw, "state", None) != "overview":
            return super().eventFilter(obj, event)

        if event.type() == QEvent.Type.DragEnter:
            if event.mimeData().hasUrls():
                for url in event.mimeData().urls():
                    path = url.toLocalFile()
                    if path.lower().endswith(('.csv', '.txt', '.tsv')):
                        event.acceptProposedAction()
                        return True
        elif event.type() == QEvent.Type.Drop:
            if event.mimeData().hasUrls():
                urls = event.mimeData().urls()
                if urls:
                    file_path = urls[0].toLocalFile()
                    if file_path.lower().endswith(('.csv', '.txt', '.tsv')):
                        show_csv_import_plus_dialog(file_path=file_path)
                        event.acceptProposedAction()
                        return True
        return super().eventFilter(obj, event)


def show_csv_import_plus_dialog(tab_index=None, file_path=None, pasted_text=None):
    dialog = getattr(mw, "csv_import_plus_dialog", None)
    if dialog and dialog.isVisible():
        if tab_index is not None:
            dialog.tabs.setCurrentIndex(tab_index)
        if file_path:
            dialog.load_file_from_path(file_path)
        elif pasted_text:
            dialog.load_text_content(pasted_text)
        dialog.activateWindow()
        dialog.raise_()
        return

    d = CSVImportPlusDialog(mw)
    if tab_index is not None:
        d.tabs.setCurrentIndex(tab_index)
    if file_path:
        d.load_file_from_path(file_path)
    elif pasted_text:
        d.load_text_content(pasted_text)

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
        
        # If the user has opted out because they are a supporter, skip the welcome
        if meta.get("supporter_opt_out", False):
            return

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


_drag_drop_filter = None


def setup_drag_drop_filter():
    global _drag_drop_filter
    if getattr(mw, "web", None) is not None:
        _drag_drop_filter = OverviewDragDropFilter(mw.web)
        mw.web.installEventFilter(_drag_drop_filter)


def init():
    gui_hooks.main_window_did_init.append(setup_menu)
    gui_hooks.main_window_did_init.append(check_for_update_welcome)
    gui_hooks.main_window_did_init.append(setup_drag_drop_filter)
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
