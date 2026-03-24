# [CSV Import Plus](https://ankiweb.net/shared/info/196373966) for Anki

CSV Import Plus is an Anki add-on that provides a streamlined and intelligent workflow for importing notes from CSV files or pasted text. It simplifies the import process by auto-detecting formats, suggesting the best note type, and allowing for quick imports with minimal configuration.

It is designed to be a faster alternative to the built-in Anki importer for common import scenarios.

## Features

- **Auto-Detection**: Automatically detects the CSV delimiter (comma, tab, semicolon, etc.) and the most likely note type for your data.
- **Live Delimiter Preview**: The delimiter dropdown updates live to show the currently detected delimiter while you type or paste.
- **Paste or Pick File**: Import data by either picking a `.csv` file or pasting CSV text directly into the dialog.
- **Paste Clipboard Button**: Use the dedicated `Paste Clipboard` button to pull clipboard text into the editor without manual paste.
- **Quick Import Clipboard**: Import clipboard content directly from the editor toolbar when the clipboard contains valid CSV content.
- **Quick Import**: A one-click import that uses the auto-detected settings to add notes instantly.
- **Lock Target Deck**: A checkbox to lock the selected target deck. The addon will remember your locked deck even after restarting Anki.
- **Smarter Imports with Locked Deck**: When a deck is locked, you can still create a new subdeck and import into it. After the import, the target deck selection will automatically revert to your locked deck.
- **Note Type Suggestion**: Analyzes the number of columns in your CSV to find and select the best matching note type.
- **On-the-fly Subdeck Creation**: Quickly create a new subdeck to import your cards into, with the name conveniently pre-filled from your filename.
- **Advanced Clipboard Options**: From **Advanced**, you can allow quick import of any non-empty clipboard text or re-enable clipboard confirmation.
- **`#notetype` Directive**: Force a specific note type by adding a special comment to your CSV data.
- **Tag Importing**: Automatically add tags to new notes by placing them in an extra column at the end of your data.
- **Anki Import Dialog**: Open Anki's current import screen from the main tab for advanced field mapping and options.
- **Session History Tab**: Keep track of imported card batches, review cards visually, and utilize the robust multi-selection feature (Ctrl/Shift + Click) to natively locate cards in the browser ("Browse Selected") or eradicate them altogether ("Delete Selected" / "Delete Batch").
- **Persistent Memory**: Opt-in to remember your session history across dialog checks via Advanced options, safely paired alongside overarching configuration memory across Anki restarts.

## AI Assistants for CSV Generation

To help you create CSV data from your documents, you can use our custom AI tools:

-   **[Gemini CSV Creator](https://gemini.google.com/gem/1k_mMJwsDi040LcxEdTsReGiZnomCv5VQ?usp=sharing)**: Simply upload or paste your document, and it will generate the CSV content ready for "CSV Import Plus".
-   **[Anki Flash Card Gen v4.6 (GPT)](https://chatgpt.com/g/g-6970ad9011508191a896ddf804f3eb2b-anki-flsh-card-gen-v46)**: A specialized custom GPT for generating high-quality Anki cards in CSV format.

<img width="1163" height="948" alt="Screenshot_20260318_141307" src="https://github.com/user-attachments/assets/f73984c1-2231-4e03-8ecf-6eba141a016d" />

## How to Use

1.  Go to **Tools → CSV Import +...** in Anki's main menu.
2.  In the dialog, you can either:
    -   Click **"Pick File..."** to select a `.csv` file.
    -   Click **"Paste Clipboard"** to insert the current clipboard text into the editor.
    -   Or, paste your CSV-formatted text directly into the editor.
3.  Use **"Quick Import Clipboard"** beside **"Paste Clipboard"** to import directly from the clipboard. By default, it is enabled only when the clipboard contains valid CSV content.
4.  The status bar updates live to show the detected delimiter, the number of rows, and the suggested note type. The delimiter dropdown also shows a live auto-detect preview.
5.  Choose a target **Deck**. You can also type a name in the **"Create Subdeck"** field and click the button to create a new deck inside the one selected above.
6.  If the suggested **Note Type** is not correct, you can manually select another one from the dropdown.
7.  Adjust the **Delimiter** if needed.
8.  Open **"Advanced"** for header-row handling, deck lock, clipboard override or confirmation. You can also toggle History retention here.
9.  Click **"Import with Anki Dialog"** at the bottom if you need Anki's full import options.
10. Click **"Quick Import"** to import the notes immediately using the current settings.
11. Navigate flexibly to the **"History"** tab anytime to review, browse, or batch-delete imported cards from your session.

Import status is shown inline in the main addon window.

## Special Features

### `#notetype` Directive

To ensure your CSV file is always imported with a specific note type, add a line at the top of your file or pasted text like this:

```csv
#notetype: My Custom Note Type
...your,csv,data,here...
```

The add-on will read this directive and automatically select "My Custom Note Type", overriding the auto-detection.

### Tag Importing

If your CSV data has one more column than your note type has fields, the content of that last column will be treated as tags. You can include multiple tags separated by spaces.

**Example:** For a note type with `Front` and `Back` fields:

```csv
What is the capital of France?,Paris,geography europe
What is 2+2?,4,math basics
```

The first note will be tagged `geography` and `europe`, and the second will be tagged `math` and `basics`.


## Changelog

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

## License

This add-on is licensed under the MIT License. See the LICENSE file for details.
