from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from paper_playground.fonts import resolve_font


class FontTests(unittest.TestCase):
    def test_explicit_font_path(self):
        with TemporaryDirectory() as directory:
            font = Path(directory) / 'local.ttf'
            font.touch()
            self.assertEqual(resolve_font(font), str(font))

    def test_missing_explicit_font_is_not_silently_replaced(self):
        with TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                resolve_font(Path(directory) / 'missing.ttf')

    def test_absent_fonts_explain_both_options(self):
        with patch.object(Path, 'is_dir', return_value=False):
            with self.assertRaisesRegex(FileNotFoundError, '--hand-font'):
                resolve_font(handwriting=True)
            with self.assertRaisesRegex(FileNotFoundError, '--print-font'):
                resolve_font()


if __name__ == '__main__':
    unittest.main()
