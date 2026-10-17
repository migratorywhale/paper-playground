import unittest

import numpy as np
from PIL import Image

from paper_playground.eraser import graphite, rub_out


class EraserTests(unittest.TestCase):
    def setUp(self):
        self.old = Image.new('L', (80, 30), 180)
        self.rub = Image.new('L', self.old.size, 255)
        self.grain = np.random.default_rng(5).random((30, 80))

    def test_no_pass_leaves_old_marks(self):
        blank = Image.new('L', self.old.size)
        remaining, dust, wear = rub_out(self.old, blank, self.grain)
        np.testing.assert_array_equal(remaining, np.asarray(self.old))
        self.assertFalse(dust.any())
        self.assertFalse(wear.any())

    def test_zero_strength_is_noop(self):
        remaining, dust, wear = rub_out(self.old, self.rub, self.grain, 0)
        np.testing.assert_array_equal(remaining, np.asarray(self.old))
        self.assertFalse(dust.any())
        self.assertFalse(wear.any())

    def test_blank_paper_can_be_worn_but_not_made_into_graphite(self):
        remaining, dust, wear = rub_out(Image.new('L', self.old.size), self.rub, self.grain)
        self.assertFalse(remaining.any())
        self.assertFalse(dust.any())
        self.assertTrue(wear.any())

    def test_removal_varies_with_grain_and_leaves_a_ghost(self):
        result = rub_out(self.old, self.rub, self.grain, 0.9)
        remaining, dust, wear = result
        self.assertGreater(remaining.min(), 0)
        self.assertLess(remaining.max(), 180)
        self.assertGreater(np.ptp(remaining), 0)
        self.assertTrue(dust.any())
        for layer, again in zip(result, rub_out(self.old, self.rub, self.grain, 0.9)):
            self.assertEqual(layer.dtype, np.uint8)
            np.testing.assert_array_equal(layer, again)

    def test_dust_does_not_wrap(self):
        edge = np.zeros((30, 80), dtype=np.uint8)
        edge[:, -1] = 255
        _, dust, _ = rub_out(Image.fromarray(edge), self.rub, self.grain)
        self.assertFalse(dust.any())

    def test_partial_pass_only_removes_marks_it_touches(self):
        mask = np.zeros((30, 80), dtype=np.uint8)
        mask[10:20, 20:40] = 255
        remaining, _, wear = rub_out(self.old, Image.fromarray(mask), self.grain)
        outside = mask == 0
        np.testing.assert_array_equal(remaining[outside], np.asarray(self.old)[outside])
        self.assertFalse(wear[outside].any())

    def test_stronger_pass_leaves_less_graphite(self):
        light = rub_out(self.old, self.rub, self.grain, 0.3)[0]
        firm = rub_out(self.old, self.rub, self.grain, 0.9)[0]
        self.assertTrue(np.all(firm < light))

    def test_later_strokes_react_to_wear(self):
        fresh = graphite(self.rub, self.grain)
        worn = graphite(self.rub, self.grain, self.rub)
        self.assertTrue(np.all(worn <= fresh))
        self.assertTrue(np.any(worn < fresh))

    def test_tiny_page_and_input_unchanged(self):
        before = np.asarray(self.old).copy()
        rub_out(self.old, self.rub, self.grain)
        np.testing.assert_array_equal(np.asarray(self.old), before)
        tiny = Image.new('L', (1, 1), 255)
        self.assertFalse(rub_out(tiny, tiny, np.zeros((1, 1)))[1].any())

    def test_bad_inputs(self):
        for strength in (-1, 2, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                rub_out(self.old, self.rub, self.grain, strength)
        for grain in (np.zeros((1, 1)), self.grain + 2, self.grain * np.nan):
            with self.assertRaises(ValueError):
                rub_out(self.old, self.rub, grain)
        with self.assertRaises(ValueError):
            graphite(self.old.convert('RGB'), self.grain)
        with self.assertRaises(ValueError):
            graphite(self.old, self.grain, Image.new('L', (2, 2)))
        with self.assertRaises(ValueError):
            rub_out(self.old, Image.new('L', (2, 2)), self.grain)
