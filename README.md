# [CSV Import Plus](https://ankiweb.net/shared/info/196373966) for Anki


CSV Import Plus is an Anki add-on that provides a streamlined and intelligent workflow for importing notes from CSV files or pasted text. It simplifies the import process by auto-detecting formats, suggesting the best note type, and allowing for quick imports with minimal configuration.

It is designed to be a faster alternative to the built-in Anki importer for common import scenarios.

## Features

- **Full Parity with Official Anki Importer Options**: Access advanced options directly in the main layout including `Allow HTML in fields`, Duplicate Resolution mode (`Update`, `Preserve`, or `Duplicate`), Match Scope (`Same note type` or `Same note type and deck`), and custom tagging fields (`Tag all notes` and `Tag updated notes`).
- **Complete Hover Descriptions (Tooltips)**: Hover over any label or input setting in the user interface to read complete and detailed tooltips explaining their functionality.
- **Auto-Detection**: Automatically detects the CSV delimiter (comma, tab, semicolon, etc.) and the most likely note type for your data.
- **Live Delimiter Preview**: The delimiter dropdown updates live to show the currently detected delimiter while you type or paste.
- **Paste or Pick File**: Import data by either picking a `.csv`, `.txt`, or `.tsv` file, or pasting CSV text directly into the dialog.
- **Searchable Deck Selection**: The target deck dropdown is now searchable. Simply type part of a deck name to filter and select your destination quickly.
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
    -   Click **"Pick File..."** to select a `.csv`, `.txt`, or `.tsv` file.
    -   Click **"Paste Clipboard"** to insert the current clipboard text into the editor.
    -   Or, paste your CSV-formatted text directly into the editor.
3.  Use **"Quick Import Clipboard"** beside **"Paste Clipboard"** to import directly from the clipboard. By default, it is enabled only when the clipboard contains valid CSV content.
4.  The status bar updates live to show the detected delimiter, the number of rows, and the suggested note type. The delimiter dropdown also shows a live auto-detect preview.
5.  Choose a target **Deck**. You can type in the deck selector to filter the list and find your deck faster. You can also type a name in the **"Create Subdeck"** field and click the button to create a new deck inside the one selected above.
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


## Support

If you find this add-on useful, please consider supporting its development:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/D1D01W6NQT)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## License

This add-on is licensed under the MIT License. See the LICENSE file for details.
