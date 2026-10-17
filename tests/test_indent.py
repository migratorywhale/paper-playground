import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageFont

from examples import koke_indent


class IndentTests(unittest.TestCase):
    def test_paper_and_rubbing_fields_are_bounded_and_repeatable(self):
        for make_field in (koke_indent.paper_height, koke_indent.rub_texture,
                           koke_indent.rubbed_area):
            with self.subTest(field=make_field.__name__):
                first = make_field(np.random.default_rng(914))
                again = make_field(np.random.default_rng(914))
                self.assertEqual(first.shape, (koke_indent.H, koke_indent.W))
                self.assertTrue(np.isfinite(first).all())
                self.assertGreaterEqual(first.min(), 0)
                self.assertLessEqual(first.max(), 1)
                np.testing.assert_array_equal(first, again)

    def test_rubbing_leaves_a_margin(self):
        area = koke_indent.rubbed_area(np.random.default_rng(914))
        self.assertGreater(area[koke_indent.H // 2, koke_indent.W // 2], 0.9)
        self.assertLess(area[0, 0], 0.01)
        self.assertLess(area[-1, -1], 0.01)

    def test_no_writing_leaves_no_groove(self):
        depth = koke_indent.groove_depth([], 'unused', np.random.default_rng(914))
        self.assertFalse(depth.any())

    def test_writing_leaves_local_repeatable_depth(self):
        font = ImageFont.load_default(size=70)
        with patch.object(koke_indent.ImageFont, 'truetype', return_value=font):
            first = koke_indent.groove_depth([(70, 'WAIT HERE')], 'test-font',
                                             np.random.default_rng(914))
            again = koke_indent.groove_depth([(70, 'WAIT HERE')], 'test-font',
                                             np.random.default_rng(914))
        self.assertGreater(first.max(), 0.1)
        self.assertLessEqual(first.max(), 1)
        self.assertFalse(first[:100].any())
        self.assertFalse(first[-100:].any())
        np.testing.assert_array_equal(first, again)

    def test_example_outputs_and_fixed_seed_without_external_fonts(self):
        # Exercise the composition without making CI depend on macOS CJK fonts.
        # The real-font default composition is rendered and inspected separately.
        font = ImageFont.load_default(size=70)
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            args = ['koke_indent', '--out', str(out), '--seed', '914']
            with patch('sys.argv', args), \
                    patch.object(koke_indent, 'resolve_font', return_value='test-font'), \
                    patch.object(koke_indent.ImageFont, 'truetype', return_value=font), \
                    contextlib.redirect_stdout(io.StringIO()):
                koke_indent.main()
                first = {path.name: path.read_bytes() for path in out.iterdir()}
                koke_indent.main()
            self.assertEqual(set(first), {'blank.png', 'rubbed.png', 'indent.png'})
            self.assertEqual(first, {path.name: path.read_bytes() for path in out.iterdir()})
            with Image.open(out / 'blank.png') as blank, \
                    Image.open(out / 'rubbed.png') as rubbed, \
                    Image.open(out / 'indent.png') as pair:
                self.assertEqual(blank.mode, 'RGB')
                self.assertEqual(blank.size, (koke_indent.W, koke_indent.H))
                self.assertEqual(pair.size, (koke_indent.W, koke_indent.H * 2 + 20))
                blank_pixels = np.asarray(blank)
                rubbed_pixels = np.asarray(rubbed)
                self.assertTrue(np.all(blank_pixels >= koke_indent.PAPER - 3))
                self.assertGreater(float(blank_pixels.mean() - rubbed_pixels.mean()), 20)
                np.testing.assert_array_equal(np.asarray(pair)[:koke_indent.H], blank_pixels)
                np.testing.assert_array_equal(np.asarray(pair)[koke_indent.H + 20:], rubbed_pixels)
