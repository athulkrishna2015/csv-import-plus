import os
import sys
import unittest

sys.path.append(os.path.dirname(__file__))

from _helpers import install_anki_stubs, load_addon_module

install_anki_stubs()

importer = load_addon_module("importer")


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


class TestImporter(unittest.TestCase):
    def test_get_delimiter_auto(self):
        combo = _DummyCombo("Auto-detect", 0)
        delim = importer.get_delimiter(combo, "A\tB\n1\t2")
        self.assertEqual(delim, "\t")

    def test_get_delimiter_manual(self):
        combo = _DummyCombo("Pipe (|)", 4)
        delim = importer.get_delimiter(combo, "A|B\n1|2")
        self.assertEqual(delim, "|")

    def test_do_import_html_handling(self):
        from aqt import mw
        import types

        # Setup mock note and collection
        class MockNote:
            def __init__(self, notetype):
                self.fields = [""] * len(notetype["flds"])
                self.tags = []
                self.id = 1
                self.mid = 1

        class MockDecks:
            def select(self, did):
                pass
            def current(self):
                return {"name": "Default"}

        class MockModels:
            def get(self, mid):
                return {"id": 1, "name": "Basic", "flds": [{"name": "Front"}, {"name": "Back"}]}

        mock_col = types.SimpleNamespace()
        mock_col.models = MockModels()
        mock_col.decks = MockDecks()
        
        added_notes = []
        def add_note(note, deck_id):
            added_notes.append(note)
            return 1
        mock_col.add_note = add_note

        def new_note(notetype):
            return MockNote(notetype)
        mock_col.new_note = new_note
        mock_col.db = types.SimpleNamespace(all=lambda *args, **kwargs: [])

        # Mock mw attributes
        mw.col = mock_col
        mw.checkpoint = lambda *args, **kwargs: None
        mw.progress = types.SimpleNamespace(start=lambda: None, finish=lambda: None)
        mw.reset = lambda: None

        # Test Import with Allow HTML = False
        deck_combo = _DummyCombo("Default", 0)
        notetype_combo = _DummyCombo("Basic", 0)
        delimiter_combo = _DummyCombo("Comma (,)", 1)
        header_check = types.SimpleNamespace(isChecked=lambda: False)

        raw_csv = "<b>Front</b>,Back <with> HTML\nLine 2 Front,Line 2 Back"
        
        # 1. HTML Disabled
        added_notes.clear()
        res = importer.do_import(
            raw_csv,
            deck_combo,
            [types.SimpleNamespace(name="Default", id=1)],
            notetype_combo,
            [types.SimpleNamespace(name="Basic", id=1)],
            header_check,
            delimiter_combo,
            allow_html=False,
            existing_notes_index=2, # Duplicate mode
            tag_all="tag1 tag2",
        )
        self.assertEqual(res["added"], 2)
        self.assertEqual(added_notes[0].fields[0], "&lt;b&gt;Front&lt;/b&gt;")
        self.assertEqual(added_notes[0].fields[1], "Back &lt;with&gt; HTML")
        self.assertEqual(added_notes[0].tags, ["tag1", "tag2"])

        # 2. HTML Enabled
        added_notes.clear()
        res = importer.do_import(
            raw_csv,
            deck_combo,
            [types.SimpleNamespace(name="Default", id=1)],
            notetype_combo,
            [types.SimpleNamespace(name="Basic", id=1)],
            header_check,
            delimiter_combo,
            allow_html=True,
            existing_notes_index=2, # Duplicate mode
            tag_all="tag1 tag2",
        )
        self.assertEqual(res["added"], 2)
        self.assertEqual(added_notes[0].fields[0], "<b>Front</b>")
        self.assertEqual(added_notes[0].fields[1], "Back <with> HTML")
        self.assertEqual(added_notes[0].tags, ["tag1", "tag2"])


if __name__ == "__main__":
    unittest.main()
