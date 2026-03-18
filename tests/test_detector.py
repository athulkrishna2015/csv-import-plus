import os
import sys
import unittest

sys.path.append(os.path.dirname(__file__))

from _helpers import install_anki_stubs, load_addon_module

install_anki_stubs()

detector = load_addon_module("detector")


class TestDetector(unittest.TestCase):
    def test_extract_directives(self):
        content = """#notetype: Basic\n#foo: bar\n\nFront,Back\n1,2"""
        directives = detector.extract_directives(content)
        self.assertEqual(directives.get("notetype"), "Basic")
        self.assertEqual(directives.get("foo"), "bar")

    def test_strip_directive_lines(self):
        content = """#notetype: Cloze\n#tags: demo\n\nA,B\n1,2"""
        stripped = detector.strip_directive_lines(content)
        self.assertEqual(stripped.splitlines()[0], "A,B")

    def test_normalize_name(self):
        self.assertEqual(detector.normalize_name("  Front-Text!! "), "front text")

    def test_detect_cloze_in_text(self):
        self.assertTrue(detector.detect_cloze_in_text("{{c1::Answer}}"))
        self.assertFalse(detector.detect_cloze_in_text("No cloze here"))

    def test_detect_csv_format(self):
        delim, rows = detector.detect_csv_format("A,B\n1,2\n3,4")
        self.assertEqual(delim, ",")
        self.assertEqual(rows, 3)

    def test_fallback_delimiter_detection(self):
        sample = "A;B\n1;2\n3;4"
        self.assertEqual(detector.fallback_delimiter_detection(sample), ";")

    def test_get_delimiter_name(self):
        self.assertEqual(detector.get_delimiter_name("|"), "Pipe (|)")


if __name__ == "__main__":
    unittest.main()
