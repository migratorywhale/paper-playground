"""Granular carbon-paper transfer, originally sketched by Glassgear."""

import numpy as np
from PIL import Image


def smooth_noise(rng, size, cells):
    tiny = Image.fromarray(rng.integers(0, 256, (cells[1], cells[0]), dtype=np.uint8))
    return np.asarray(tiny.resize(size, Image.Resampling.BICUBIC), dtype=float) / 255


def transfer(mask, pressure, grain, slip=False):
    """Return an 8-bit transfer mask from pressure and fixed paper grain.

    mask: Pillow L image. pressure: finite nonnegative scalar or matching array
    (roughly 0..1). grain: same-size array in [0, 1]. slip: a small local
    displacement, centered at 527/930 of the page height. No whole-image blur.
    """
    if mask.mode != 'L':
        raise ValueError('mask must be a grayscale Pillow L image')
    a = np.asarray(mask, dtype=float) / 255
    pressure = np.asarray(pressure, dtype=float)
    grain = np.asarray(grain, dtype=float)
    if pressure.shape not in ((), a.shape) or grain.shape != a.shape:
        raise ValueError('pressure and grain must match the mask; pressure may be scalar')
    if not np.all(np.isfinite(pressure)) or np.any(pressure < 0):
        raise ValueError('pressure must be finite and nonnegative')
    if not np.all(np.isfinite(grain)) or np.any((grain < 0) | (grain > 1)):
        raise ValueError('grain must be finite and in [0, 1]')
    contact = np.clip((pressure - 0.16) / 0.70, 0, 1)
    deposited = a * contact * np.where(grain < contact, 0.76 + grain * 0.24, 0.035)
    if slip:
        y, x = np.indices(a.shape)
        band = np.exp(-((y - a.shape[0] * (527 / 930)) / (a.shape[0] * (54 / 930))) ** 2)
        dx = np.rint((3.2 * a.shape[1] / 660) * band).astype(int)
        source = x - dx
        shifted = np.take_along_axis(deposited, np.clip(source, 0, a.shape[1] - 1), axis=1)
        shifted[source < 0] = 0
        deposited = shifted * 0.88 + deposited * band * 0.12
    return np.uint8(np.clip(deposited * 255, 0, 255))


def ink_on(paper, alpha, rgb):
    layer = Image.new('RGBA', paper.size, rgb + (0,))
    layer.putalpha(Image.fromarray(np.uint8(alpha)))
    return Image.alpha_composite(paper.convert('RGBA'), layer).convert('RGB')
