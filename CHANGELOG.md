# Changelog

All notable changes to this project will be documented in this file.

### [3.3.1] - 2026-07-13

- **Fixed**: Clipboard quick import now uses sequential column mapping, preventing empty card imports when the GUI editor is empty.
- **Fixed**: Clipboard quick import now dynamically auto-detects Note Type (e.g. Cloze) and field delimiters directly from the clipboard content.

### [3.3.0] - 2026-07-12

- **Added**: Full parity with default Anki importer's Column and Field mapping, allowing customized column assignment for target note fields and Tags.
- **Added**: Options in the Advanced settings tab to disable Note Type and Delimiter auto-detections, remembering settings across Anki restarts.
- **Improved**: GUI selections for Note Type and Delimiter are now explicitly respected on import even if the CSV contains directive header lines.

### [3.2.0] - 2026-06-18

- **Added**: Full integration of bulk file importing directly into the main GUI. Multiple files can be chosen via file browser or dragged and dropped to enter an inline bulk table showing status and parsing metadata.
- **Added**: Ability to append files dynamically and remove selected files from the bulk import queue directly in the GUI.

### [3.1.0] - 2026-06-05

- **Added**: Drag and drop support on Anki's Deck Overview screen. Dragging a `.csv`, `.txt`, or `.tsv` file onto the deck overview page automatically opens the importer with that file loaded and the active deck selected.
- **Improved**: Updated `make_ankiaddon.py` to respect `.gitignore` rules dynamically when packaging the addon.

### [3.0.0] - 2026-05-28

- **Added**: Full parity with official Anki importer settings (`Allow HTML in fields`, Duplicate Resolution mode (`Update`, `Preserve`, or `Duplicate`), Match Scope, and custom tagging options (`Tag all notes`, `Tag updated notes`)).
- **Added**: Complete and rich hover tooltips detailing all import configuration options in the GUI.
- **Added**: New functional test suite with real Anki collection database coverage.

### [2.9.0] - 2026-05-13

- **Fixed**: Configuration settings in the "Advanced" tab now persist correctly across Anki restarts.
- **Fixed**: The addon window now closes automatically when Anki is closed.
- **Added**: History groups are now collapsed by default for a cleaner interface.
- **Added**: A "Changelog" link has been added to the Support tab.
- **Improved**: The Support tab now opens automatically exactly once per addon update (tracked via `meta.json`).

### [2026-05-06]

- **Added**: Support for importing `.txt` and `.tsv` files in the file picker.
- **Added**: Searchable Target Deck selection dropdown using an integrated auto-completer.

### [2026-03-24]

- **Added**: History tab to browse imported cards by batch per session.
- **Added**: Inline "Delete", "Delete Batch", and "Delete Selected" buttons directly inside the History tab context.
- **Added**: Multi-select (ExtendedSelection) configuration for tracking history items.
- **Added**: "Browse Selected" button to quickly show batch cards or specific imported cards in the Anki Browser.
- **Added**: Advanced toggle to remember History payload persistently across window checks, while all Advanced parameters properly persist across Anki restarts.
- **Changed**: Note insertions are now wrapped natively to support grouped Ctrl+Z undo operations effortlessly.
- **Changed**: Documentation split effectively between setup docs (`README.md`) and dev docs (`DEVELOPMENT.md`).

### [2026-03-18]

- **Changed**: Moved the Anki import dialog button to the main Import tab footer.
- **Changed**: The Anki dialog now uses the current Anki importer flow and keeps temp CSV files until the dialog closes.
- **Added**: Basic unit tests for delimiter detection and CSV helpers.
- **Changed**: Updated build/version scripts to support `major.minor[.patch]` versions.

### [2026-03-09]

- **Added**: Direct links to **Gemini CSV Creator** and **Anki Flash Card Gen (GPT)** in the UI and README to help users generate CSV data from documents.
- **Changed**: Improved UI layout with a tabbed interface for better organization of Import and Advanced settings.

### [2026-03-07]

- **Added**: Dedicated **Paste Clipboard** and **Quick Import Clipboard** actions beside the editor header for faster clipboard workflows.
- **Changed**: **Quick Import Clipboard** is now disabled by default unless the clipboard contains valid CSV content.
- **Changed**: **Add Subdeck** and **Delimiter** remain in the main window, while header, deck lock, clipboard behavior, and the built-in importer stay under **Advanced**.
- **Added**: New **Advanced** option to allow **Quick Import Clipboard** for any non-empty clipboard text.
- **Changed**: Clipboard quick-import confirmation is now off by default; when enabled, it shows import details plus an embedded scrollable preview.

### [2026-02-23]

- **Changed**: Removed the Quick Import completion pop-up dialog.
- **Changed**: Quick Import completion details are now shown in the main window status line.
- **Changed**: Pasted CSV text is cleared automatically after a successful Quick Import.
- **Changed**: Delimiter auto-detection preview in the dropdown now updates live as content changes.
- **Fixed**: Resolved an intermittent issue where the addon window could close unexpectedly.
- **Fixed**: Header-only CSV input now correctly stops import when "First row is header" is enabled.
- **Improved**: Live delimiter/note-type preview is now debounced to reduce UI lag on large pasted CSV content.

### [2025-11-01]

- **Added**: "Lock Target Deck" option to persist the selected deck across imports and sessions.
- **Added**: The success message now shows the name of the deck cards were imported into.
- **Improved**: The addon window is now non-modal, allowing interaction with the main Anki window.
- **Fixed**: The addon window no longer always stays on top of the main Anki window.
- **Fixed**: Resolved a crash on startup with newer Anki versions related to window handling.
