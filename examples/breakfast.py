"""One cup upstairs, two cups downstairs. A fictional duplicate order slip."""

from pathlib import Path
import argparse

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from paper_playground.carbon import ink_on, smooth_noise, transfer
from paper_playground.fonts import resolve_font

SIZE = (660, 930)


class CarbonDesk:
    def __init__(self, seed=47, hand_font=None, print_font=None, hand_index=0, print_index=0):
        self.rng = np.random.default_rng(seed)
        self.hand = resolve_font(hand_font, handwriting=True)
        self.print = resolve_font(print_font)
        self.hand_index, self.print_index = hand_index, print_index
        self.top = self.paper(False)
        self.copy = self.paper(True)
        self.pressure = 0.68 + 0.45 * (smooth_noise(self.rng, SIZE, (17, 23)) - 0.5)
        self.grain = self.rng.random((SIZE[1], SIZE[0]))

    def print_font(self, size):
        return ImageFont.truetype(self.print, size, index=self.print_index)

    def paper(self, duplicate):
        noise = self.rng.normal(0, 0.6, (SIZE[1], SIZE[0], 1))
        base = np.array((250, 252, 249) if not duplicate else (246, 250, 252))
        image = Image.fromarray(np.uint8(np.clip(base + noise, 0, 255)))
        d = ImageDraw.Draw(image)
        f = self.print_font
        line = (187, 122, 116) if not duplicate else (126, 163, 168)
        pale = tuple(round(c * 0.40 + 250 * 0.60) for c in line)
        d.text((52, 48), '\u65e9\u70b9', font=f(39), fill=line)
        label = '\u53a8\u623f\u8054' if duplicate else '\u67dc\u53f0\u8054'
        d.text((494, 65), label, font=f(21), fill=line)
        d.text((54, 110), 'No. 0047', font=f(19), fill=line)
        d.text((470, 110), '07 : 12', font=f(19), fill=line)
        d.line((46, 151, 614, 151), fill=line, width=2)
        d.text((61, 180), '\u54c1\u540d', font=f(20), fill=line)
        d.text((463, 180), '\u6570\u91cf', font=f(20), fill=line)
        for y in (227, 348, 469, 590, 711):
            d.line((46, y, 614, y), fill=pale, width=1)
        d.line((423, 168, 423, 711), fill=pale, width=1)
        d.text((52, 750), '\u5907\u6ce8', font=f(18), fill=line)
        d.line((46, 849, 614, 849), fill=pale, width=1)
        d.text((52, 869), '02 / CARBON' if duplicate else '01 / ORIGINAL', font=f(13), fill=line)
        for x in range(24, 642, 15):
            d.line((x, 21, x + 4, 21), fill=(207, 210, 209), width=1)
        return image

    def mark(self, mask, force=1.0, slip=False):
        a = np.asarray(mask, dtype=float)
        self.top = ink_on(self.top, np.uint8(a * (0.82 + self.grain * 0.18)), (36, 59, 104))
        self.copy = ink_on(self.copy, transfer(mask, self.pressure * force, self.grain, slip), (58, 72, 128))

    def write(self, text, x, y, size=63, force=1.0, slip=False):
        mask = Image.new('L', SIZE)
        d = ImageDraw.Draw(mask)
        font = ImageFont.truetype(self.hand, size, index=self.hand_index)
        for char in text:
            jitter = int(self.rng.integers(-3, 4))
            d.text((x, y + jitter), char, font=font, fill=255)
            x += d.textlength(char, font=font) + 3
        self.mark(mask, force, slip)

    def stroke(self, points, width=3, force=1.0, slip=False):
        mask = Image.new('L', SIZE)
        ImageDraw.Draw(mask).line(points, fill=255, width=width, joint='curve')
        self.mark(mask, force, slip)


def render(desk):
    desk.write('\u8c46\u6d46', 77, 256, force=1.18)
    desk.write('2', 472, 252, size=68, force=1.17)
    desk.write('\u5305\u5b50', 83, 378, force=1.08)
    desk.write('3', 476, 372, size=67)
    desk.write('\u6cb9\u6761', 77, 497, force=0.98, slip=True)
    desk.write('1', 480, 499, size=67, slip=True)
    desk.write('\u5e26\u8d70', 79, 623, size=59, force=0.95)
    desk.write('\u7cd6\u5c11\u4e00\u70b9', 129, 774, size=49, force=0.60)
    # The correction has clear ink above but barely any pressure below.
    desk.stroke([(462, 303), (502, 279), (474, 313), (509, 294)], width=3, force=0.30)
    desk.write('1', 538, 250, size=66, force=0.30)
    desk.stroke([(80, 687), (126, 690), (180, 687), (211, 681)], width=3, force=0.63)
    board = Image.new('RGB', (1500, 1130), (234, 237, 239))
    d = ImageDraw.Draw(board)
    f = desk.print_font
    d.text((62, 27), '\u590d\u5199\u7eb8', font=f(32), fill=(39, 53, 61))
    d.text((1130, 38), 'GLASSGEAR / STUDY 01', font=f(16), fill=(83, 99, 107))
    for x, sheet in ((62, desk.top), (778, desk.copy)):
        d.rectangle((x + 4, 93, x + 664, 1023), fill=(215, 222, 225))
        board.paste(sheet, (x, 88))
    d.text((62, 1051), '\u4e00\u676f\u3002', font=f(25), fill=(39, 53, 61))
    d.text((778, 1051), '\u4e24\u676f\u3002', font=f(25), fill=(39, 53, 61))
    return board


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('output/breakfast'))
    parser.add_argument('--seed', type=int, default=47)
    parser.add_argument('--hand-font', type=Path)
    parser.add_argument('--print-font', type=Path)
    parser.add_argument('--hand-index', type=int, default=0, help='Font face index for a TTC collection')
    parser.add_argument('--print-index', type=int, default=0)
    args = parser.parse_args()
    try:
        desk = CarbonDesk(args.seed, args.hand_font, args.print_font, args.hand_index, args.print_index)
        board = render(desk)
    except (FileNotFoundError, OSError) as exc:
        parser.error(str(exc))
    args.out.mkdir(parents=True, exist_ok=True)
    desk.top.save(args.out / 'counter.png')
    desk.copy.save(args.out / 'kitchen.png')
    board.save(args.out / 'breakfast.png')
    print(args.out / 'breakfast.png')


if __name__ == '__main__':
    main()
