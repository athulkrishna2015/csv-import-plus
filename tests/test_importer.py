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


class TestImporter(unittest.TestCase):
    def test_get_delimiter_auto(self):
        combo = _DummyCombo("Auto-detect", 0)
        delim = importer.get_delimiter(combo, "A\tB\n1\t2")
        self.assertEqual(delim, "\t")

    def test_get_delimiter_manual(self):
        combo = _DummyCombo("Pipe (|)", 4)
        delim = importer.get_delimiter(combo, "A|B\n1|2")
        self.assertEqual(delim, "|")


if __name__ == "__main__":
    unittest.main()
