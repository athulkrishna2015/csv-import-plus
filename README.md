# [CSV Import Plus](https://ankiweb.net/shared/info/196373966) for Anki

CSV Import Plus is an Anki add-on that provides a streamlined and intelligent workflow for importing notes from CSV files or pasted text. It simplifies the import process by auto-detecting formats, suggesting the best note type, and allowing for quick imports with minimal configuration.

It is designed to be a faster alternative to the built-in Anki importer for common import scenarios.

## Features

- **Auto-Detection**: Automatically detects the CSV delimiter (comma, tab, semicolon, etc.) and the most likely note type for your data.
- **Paste or Pick File**: Import data by either picking a `.csv` file or pasting CSV text directly into the dialog.
- **Quick Import**: A one-click import that uses the auto-detected settings to add notes instantly.
- **Note Type Suggestion**: Analyzes the number of columns in your CSV to find and select the best matching note type.
- **On-the-fly Subdeck Creation**: Quickly create a new subdeck to import your cards into, with the name conveniently pre-filled from your filename.
- **`#notetype` Directive**: Force a specific note type by adding a special comment to your CSV data.
- **Tag Importing**: Automatically add tags to new notes by placing them in an extra column at the end of your data.
- **Fallback to Anki Importer**: For complex cases, you can easily send the data to Anki's standard import dialog to handle advanced field mapping.
<img width="1444" height="919" alt="Screenshot_20251029_190259" src="https://github.com/user-attachments/assets/0683a882-b846-492a-a48c-c489a69c3a73" />

## How to Use

1.  Go to **Tools → CSV Import +...** in Anki's main menu.
2.  In the dialog, you can either:
    -   Click **"Pick File..."** to select a `.csv` file.
    -   Or, paste your CSV-formatted text directly into the "Paste CSV Text" area.
3.  The status bar will update to show you the detected delimiter, the number of rows, and the suggested note type.
4.  Choose a target **Deck**. You can also type a name in the **"Create Subdeck"** field and click the button to create a new deck inside the one selected above.
5.  If the suggested **Note Type** is not correct, you can manually select another one from the dropdown.
6.  Click **"Quick Import"** to import the notes immediately using the current settings.

A confirmation message will appear summarizing how many notes were added.

## Special Features

### Auto detect subdeck nam

auto detect subdeck name from csv file name 

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

## License

This add-on is licensed under the MIT License. See the LICENSE file for details.
