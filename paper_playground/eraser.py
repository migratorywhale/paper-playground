"""A stylized eraser: lift graphite, drag some dust, roughen the paper."""

import numpy as np
from PIL import Image


def _mask(image, name):
    if not isinstance(image, Image.Image) or image.mode != 'L':
        raise ValueError(f'{name} must be a grayscale Pillow L image')
    return np.asarray(image, dtype=float) / 255


def _grain(value, shape):
    value = np.asarray(value, dtype=float)
    if value.shape != shape or not np.all(np.isfinite(value)):
        raise ValueError('grain must be finite and match the mask')
    if np.any((value < 0) | (value > 1)):
        raise ValueError('grain must be in [0, 1]')
    return value


def graphite(mask, grain, wear=None):
    """Deposit pencil on fixed grain; optional wear breaks up later strokes."""
    ink = _mask(mask, 'mask')
    grain = _grain(grain, ink.shape)
    damage = np.zeros_like(ink) if wear is None else _mask(wear, 'wear')
    if damage.shape != ink.shape:
        raise ValueError('wear must match the mask')
    contact = np.where(grain < 0.78, 0.42 + 0.42 * grain, 0.13)
    raised_fibers = 1 - damage * np.where(grain > 0.57, 0.74, 0.16)
    return np.uint8(255 * ink * contact * raised_fibers)


def rub_out(deposit, rub_mask, grain, strength=0.9):
    """Return (remaining graphite, dragged dust, paper wear) as uint8 masks.

    The rub mask describes a left-to-right pass. Dust shifts only rightward,
    without wrapping at the edge. Wear exists even on originally blank paper.
    These are compositing layers, not a conservation-of-mass simulation.
    """
    old = _mask(deposit, 'deposit')
    rub = _mask(rub_mask, 'rub_mask')
    grain = _grain(grain, old.shape)
    if rub.shape != old.shape:
        raise ValueError('rub_mask must match deposit')
    if not np.isscalar(strength) or not np.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    abrasion = rub * strength
    lifted = old * abrasion * (0.72 + 0.28 * grain)
    dust = np.zeros_like(old)
    # A directional trail instead of a blurred copy of the entire page.
    for shift in range(1, 25):
        if shift >= old.shape[1]:
            break
        dust[:, shift:] += lifted[:, :-shift] * (25 - shift) / 300
    dust *= 0.30 * (0.35 + 0.65 * grain)
    wear = abrasion * (0.25 + 0.75 * grain)
    return tuple(np.uint8(np.clip(layer * 255, 0, 255))
                 for layer in (old - lifted, dust, wear))
