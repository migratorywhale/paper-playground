"""Font-independent pressure and slip samples; uses Pillow's bundled font."""

from pathlib import Path
import argparse

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from paper_playground.carbon import ink_on, transfer


def render(seed=47):
    rng = np.random.default_rng(seed)
    mask = Image.new('L', (560, 120))
    d = ImageDraw.Draw(mask)
    points = [(x, int(59 + 24 * np.sin(x / 24))) for x in range(16, 544)]
    d.line(points, fill=255, width=4, joint='curve')
    d.ellipse((240, 18, 316, 102), outline=255, width=5)
    grain = rng.random((120, 560))
    image = Image.new('RGB', (760, 850), (249, 251, 250))
    d = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=18)
    d.text((36, 28), 'CARBON PAPER / PRESSURE STUDY', font=font, fill=(35, 56, 68))
    for i, force in enumerate((0.25, 0.45, 0.65, 0.90)):
        d.text((36, 110 + i * 145), f'{force:.2f}', font=font, fill=(114, 88, 76))
        paper = Image.new('RGB', mask.size, (249, 251, 250))
        mark = ink_on(paper, transfer(mask, force, grain), (58, 72, 128))
        image.paste(mark, (160, 74 + i * 145))
    d.text((36, 700), 'SLIP', font=font, fill=(114, 88, 76))
    mark = ink_on(Image.new('RGB', mask.size, (249, 251, 250)),
                  transfer(mask, 0.90, grain, slip=True), (58, 72, 128))
    image.paste(mark, (160, 664))
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('output/sampler.png'))
    parser.add_argument('--seed', type=int, default=47)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    render(args.seed).save(args.out)
    print(args.out)


if __name__ == '__main__':
    main()
