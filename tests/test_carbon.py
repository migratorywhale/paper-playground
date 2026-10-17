import unittest

import numpy as np
from PIL import Image, ImageDraw

from examples.sampler import render
from paper_playground.carbon import ink_on, smooth_noise, transfer


class CarbonTests(unittest.TestCase):
    def setUp(self):
        self.mask = Image.new('L', (660, 930))
        ImageDraw.Draw(self.mask).line((80, 527, 570, 527), fill=255, width=9)
        self.grain = np.random.default_rng(12).random((930, 660))

    def test_pressure_is_not_just_uniform_fading(self):
        light = transfer(self.mask, 0.26, self.grain)
        heavy = transfer(self.mask, 0.85, self.grain)
        self.assertLess(light.sum(), heavy.sum() * 0.25)
        self.assertGreater(np.unique(light[np.asarray(self.mask) > 0]).size, 2)

    def test_low_pressure_leaves_nothing(self):
        self.assertFalse(transfer(self.mask, 0.16, self.grain).any())

    def test_saturation(self):
        np.testing.assert_array_equal(transfer(self.mask, 1, self.grain),
                                      transfer(self.mask, 8, self.grain))

    def test_no_ink_outside_unslipped_mark(self):
        out = transfer(self.mask, 0.9, self.grain)
        self.assertFalse(out[np.asarray(self.mask) == 0].any())
        self.assertEqual(out.dtype, np.uint8)

    def test_scalar_matches_array(self):
        np.testing.assert_array_equal(transfer(self.mask, 0.6, self.grain),
                                      transfer(self.mask, np.full(self.grain.shape, 0.6), self.grain))

    def test_transfer_repeatable(self):
        np.testing.assert_array_equal(transfer(self.mask, 0.6, self.grain, True),
                                      transfer(self.mask, 0.6, self.grain, True))

    def test_slip_is_local_and_does_not_wrap(self):
        mask = Image.new('L', self.mask.size)
        d = ImageDraw.Draw(mask)
        d.line((659, 0, 659, 929), fill=255, width=1)
        out = transfer(mask, 1, self.grain, slip=True)
        self.assertFalse(out[:, :10].any())
        self.assertLess(out[527, -1], out[0, -1])

    def test_blank_stays_blank(self):
        self.assertFalse(transfer(Image.new('L', self.mask.size), 1, self.grain, True).any())

    def test_invalid_shape(self):
        with self.assertRaises(ValueError):
            transfer(self.mask, [0.4, 0.6], self.grain)
        with self.assertRaises(ValueError):
            transfer(self.mask, 0.6, np.zeros((3, 4)))

    def test_invalid_values(self):
        for pressure in (-1, np.nan, np.inf):
            with self.subTest(pressure=pressure), self.assertRaises(ValueError):
                transfer(self.mask, pressure, self.grain)
        for value in (-0.1, 1.1, np.nan):
            with self.subTest(grain=value), self.assertRaises(ValueError):
                transfer(self.mask, 0.6, np.full(self.grain.shape, value))

    def test_color_mask_rejected(self):
        with self.assertRaises(ValueError):
            transfer(self.mask.convert('RGB'), 0.6, self.grain)

    def test_composite_retains_white_paper(self):
        paper = Image.new('RGB', self.mask.size, 'white')
        out = ink_on(paper, transfer(self.mask, 0.6, self.grain), (58, 72, 128))
        self.assertEqual(out.getpixel((0, 0)), (255, 255, 255))
        self.assertNotEqual(out.getpixel((300, 527)), (255, 255, 255))
        self.assertEqual(paper.getpixel((300, 527)), (255, 255, 255))

    def test_noise_is_repeatable_and_shaped(self):
        a = smooth_noise(np.random.default_rng(47), (20, 30), (4, 6))
        b = smooth_noise(np.random.default_rng(47), (20, 30), (4, 6))
        np.testing.assert_array_equal(a, b)
        self.assertEqual(a.shape, (30, 20))
        self.assertTrue(np.all((a >= 0) & (a <= 1)))

    def test_sampler_is_visible_repeatable_and_seeded(self):
        a = np.asarray(render(47))
        np.testing.assert_array_equal(a, np.asarray(render(47)))
        self.assertFalse(np.array_equal(a, np.asarray(render(48))))
        self.assertGreater(np.count_nonzero(a[:, :, 0] < 200), 2000)


if __name__ == '__main__':
    unittest.main()
