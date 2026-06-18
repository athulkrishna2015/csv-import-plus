import os
import sys
import unittest
import tempfile
import shutil
import types
from pathlib import Path

# Add parent directory and addon directory to path
sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parents[1] / "addon"))

from anki.collection import Collection
import addon.importer as importer
import addon.detector as detector
import addon.anki_helpers as anki_helpers

class _DummyCombo:
    def __init__(self, text: str, index: int = 0):
        self._text = text
        self._index = index

    def currentText(self):
        return self._text

    def currentIndex(self):
        return self._index

    def findText(self, text):
        return self._index

    def setCurrentIndex(self, index):
        self._index = index

class TestImporterFunctional(unittest.TestCase):
    def setUp(self):
        # Create a temp directory for the collection
        self.temp_dir = tempfile.mkdtemp()
        self.col_path = os.path.join(self.temp_dir, "collection.anki2")
        self.col = Collection(self.col_path)

        # Mock mw
        import aqt
        from aqt.qt import QApplication
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        aqt.mw = types.SimpleNamespace()
        aqt.mw.col = self.col
        aqt.mw.progress = types.SimpleNamespace(start=lambda: None, finish=lambda: None)
        aqt.mw.reset = lambda: None
        aqt.mw.checkpoint = lambda *args, **kwargs: None
        aqt.mw.app = app
        aqt.mw.mediaServer = types.SimpleNamespace(set_page_html=lambda *args, **kwargs: None)
        aqt.mw.serverURL = lambda: "http://localhost/"

        # Import modules and bind their mw references to our mock mw
        import addon.dialog as dialog_mod
        import addon.detector as detector_mod
        import addon.anki_helpers as anki_helpers_mod
        import addon.importer as importer_mod
        import addon.tabs.import_tab as import_tab_mod
        import addon.tabs.history_tab as history_tab_mod
        import addon.tabs.advanced_tab as advanced_tab_mod
        import addon.tabs.support_tab as support_tab_mod
        import addon.main as main_mod

        dialog_mod.mw = aqt.mw
        detector_mod.mw = aqt.mw
        anki_helpers_mod.mw = aqt.mw
        importer_mod.mw = aqt.mw
        import_tab_mod.mw = aqt.mw
        history_tab_mod.mw = aqt.mw
        advanced_tab_mod.mw = aqt.mw
        support_tab_mod.mw = aqt.mw
        main_mod.mw = aqt.mw

        # Get default deck and model
        self.deck_id = self.col.decks.id("Default")
        self.model = self.col.models.by_name("Basic")
        self.model_id = self.model["id"]

    def tearDown(self):
        self.col.close()
        shutil.rmtree(self.temp_dir)

    def test_functional_import_duplicate_mode(self):
        # Initial import (Duplicate Mode)
        deck_combo = _DummyCombo("Default", 0)
        notetype_combo = _DummyCombo("Basic", 0)
        delimiter_combo = _DummyCombo("Comma (,)", 1)
        header_check = types.SimpleNamespace(isChecked=lambda: False)

        deck_infos = [types.SimpleNamespace(name="Default", id=self.deck_id)]
        model_infos = [types.SimpleNamespace(name="Basic", id=self.model_id)]

        raw_csv = "Front1,Back1\nFront2,Back2"

        res = importer.do_import(
            raw_csv,
            deck_combo,
            deck_infos,
            notetype_combo,
            model_infos,
            header_check,
            delimiter_combo,
            allow_html=True,
            existing_notes_index=2, # Duplicate
            tag_all="tagA",
        )
        self.assertEqual(res["added"], 2)
        self.assertEqual(res["updated"], 0)

        # Verify notes in database
        notes = [self.col.get_note(nid) for nid in self.col.find_notes("")]
        self.assertEqual(len(notes), 2)
        self.assertEqual(notes[0].fields[0], "Front1")
        self.assertEqual(notes[0].tags, ["tagA"])

    def test_functional_import_html_escaping(self):
        deck_combo = _DummyCombo("Default", 0)
        notetype_combo = _DummyCombo("Basic", 0)
        delimiter_combo = _DummyCombo("Comma (,)", 1)
        header_check = types.SimpleNamespace(isChecked=lambda: False)
        deck_infos = [types.SimpleNamespace(name="Default", id=self.deck_id)]
        model_infos = [types.SimpleNamespace(name="Basic", id=self.model_id)]

        # Allow HTML = False
        raw_csv = "<b>Bold</b>,<i>Italic</i>\n\"Line1\nLine2\",Back"
        res = importer.do_import(
            raw_csv,
            deck_combo,
            deck_infos,
            notetype_combo,
            model_infos,
            header_check,
            delimiter_combo,
            allow_html=False,
            existing_notes_index=2,
        )
        # Get first note
        nids = self.col.find_notes("")
        notes = [self.col.get_note(nid) for nid in nids]
        self.assertEqual(notes[0].fields[0], "&lt;b&gt;Bold&lt;/b&gt;")
        self.assertEqual(notes[0].fields[1], "&lt;i&gt;Italic&lt;/i&gt;")
        self.assertEqual(notes[1].fields[0], "Line1<br>Line2")

    def test_functional_import_update_and_preserve_modes(self):
        deck_combo = _DummyCombo("Default", 0)
        notetype_combo = _DummyCombo("Basic", 0)
        delimiter_combo = _DummyCombo("Comma (,)", 1)
        header_check = types.SimpleNamespace(isChecked=lambda: False)
        deck_infos = [types.SimpleNamespace(name="Default", id=self.deck_id)]
        model_infos = [types.SimpleNamespace(name="Basic", id=self.model_id)]

        # 1. Add initial note
        importer.do_import(
            "MatchFront,OldBack",
            deck_combo,
            deck_infos,
            notetype_combo,
            model_infos,
            header_check,
            delimiter_combo,
            existing_notes_index=2, # Duplicate
        )

        # 2. Import with PRESERVE (Existing notes mode = 1)
        res = importer.do_import(
            "MatchFront,NewBack",
            deck_combo,
            deck_infos,
            notetype_combo,
            model_infos,
            header_check,
            delimiter_combo,
            existing_notes_index=1, # Preserve
        )
        self.assertEqual(res["added"], 0)
        self.assertEqual(res["updated"], 0)
        
        # Verify it wasn't modified
        nids = self.col.find_notes("")
        notes = [self.col.get_note(nid) for nid in nids]
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].fields[1], "OldBack")

        # 3. Import with UPDATE (Existing notes mode = 0)
        res = importer.do_import(
            "MatchFront,NewBack",
            deck_combo,
            deck_infos,
            notetype_combo,
            model_infos,
            header_check,
            delimiter_combo,
            existing_notes_index=0, # Update
            tag_all="tagAll",
            tag_updated="tagUpdate",
        )
        self.assertEqual(res["added"], 0)
        self.assertEqual(res["updated"], 1)

        # Verify it was updated and tagged
        notes = [self.col.get_note(nid) for nid in self.col.find_notes("")]
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].fields[1], "NewBack")
        self.assertTrue("tagAll" in notes[0].tags)
        self.assertTrue("tagUpdate" in notes[0].tags)

    def test_drag_drop_filter_and_dialog_load(self):
        from addon.main import is_valid_csv_text

        # Test is_valid_csv_text helper
        self.assertTrue(is_valid_csv_text("a,b\nc,d"))
        self.assertTrue(is_valid_csv_text("#notetype:Basic\na,b"))
        self.assertFalse(is_valid_csv_text(""))
        self.assertFalse(is_valid_csv_text("single_column_no_delimiters"))

    def test_bulk_import_dialog(self):
        # Create some temp CSV files
        file1 = os.path.join(self.temp_dir, "test1.csv")
        with open(file1, "w", encoding="utf-8") as f:
            f.write("Front,Back\nFront1,Back1\nFront2,Back2")

        file2 = os.path.join(self.temp_dir, "test2.csv")
        with open(file2, "w", encoding="utf-8") as f:
            f.write("#notetype:Basic\nFront,Back\nFront3,Back3\nFront4,Back4")

        # Mock mw configuration and properties
        import aqt
        aqt.mw.addonManager = types.SimpleNamespace(
            getConfig=lambda *args: {},
            writeConfig=lambda *args: None,
            addonFromModule=lambda *args: "csv_import_plus_dev",
            addonMeta=lambda *args: {},
        )
        import addon.dialog as dialog_mod
        import addon.detector as detector_mod
        import addon.anki_helpers as anki_helpers_mod
        import addon.importer as importer_mod
        dialog_mod.mw = aqt.mw
        detector_mod.mw = aqt.mw
        anki_helpers_mod.mw = aqt.mw
        importer_mod.mw = aqt.mw

        from addon.dialog import CSVImportPlusDialog
        
        # Instantiate Main Dialog
        dialog = CSVImportPlusDialog(None)
        dialog.header_check.setChecked(True)
        
        # Load multiple files to enter bulk mode
        dialog.load_files([file1, file2])
        self.assertEqual(len(dialog.file_paths), 2)
        
        # Verify bulk table row count and items
        self.assertEqual(dialog.import_tab_widget.bulk_table.rowCount(), 2)
        self.assertEqual(dialog.import_tab_widget.bulk_table.item(0, 0).text(), "test1.csv")
        self.assertEqual(dialog.import_tab_widget.bulk_table.item(1, 0).text(), "test2.csv")

        # Run bulk import
        dialog.do_import()

        # Verify notes in database
        notes = [self.col.get_note(nid) for nid in self.col.find_notes("")]
        self.assertEqual(len(notes), 4)
        
        # Test add/remove paths
        dialog.add_file_paths([file1])  # Duplicate, should not add
        self.assertEqual(len(dialog.file_paths), 2)
        
        file3 = os.path.join(self.temp_dir, "test3.csv")
        dialog.add_file_paths([file3])
        self.assertEqual(len(dialog.file_paths), 3)

        # Cleanup dialog
        dialog.accept()

if __name__ == "__main__":
    unittest.main()
