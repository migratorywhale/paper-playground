"""Five more minutes. Eraser-ghost idea by Ama, variation by Glassgear."""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from paper_playground.carbon import ink_on, smooth_noise
from paper_playground.eraser import graphite, rub_out
from paper_playground.fonts import resolve_font

SIZE = (900, 860)


def lettering(text, xy, font, rng):
    mask = Image.new('L', SIZE)
    draw = ImageDraw.Draw(mask)
    x, y = xy
    for char in text:
        draw.text((x, y + int(rng.integers(-4, 5))), char, font=font, fill=255)
        x += draw.textlength(char, font=font) + 4
    return mask


def render(seed=17, hand_font=None, print_font=None, hand_index=0, print_index=0):
    rng = np.random.default_rng(seed)
    hand = resolve_font(hand_font, handwriting=True)
    printing = resolve_font(print_font)
    h = lambda size: ImageFont.truetype(hand, size, index=hand_index)
    p = lambda size: ImageFont.truetype(printing, size, index=print_index)
    grain = rng.random((SIZE[1], SIZE[0]))
    fibers = smooth_noise(rng, SIZE, (150, 16))
    paper = np.array((249, 251, 248)) + rng.normal(0, 0.65, (*grain.shape, 1))
    sheet = Image.fromarray(np.uint8(np.clip(paper, 0, 255)))
    draw = ImageDraw.Draw(sheet)
    for y in range(150, 771, 100):
        draw.line((70, y, 830, y), fill=(208, 222, 214), width=1)
    draw.line((106, 120, 106, 790), fill=(211, 163, 158), width=1)
    draw.text((70, 54), '17 / SAT', font=p(20), fill=(112, 134, 122))
    draw.text((690, 54), '22 : 30', font=p(20), fill=(112, 134, 122))
    draw.text((130, 170), '\u4eca\u665a', font=h(48), fill=(66, 73, 68))

    old = lettering('\u65e9\u7761', (151, 270), h(125), rng)
    deposit = graphite(old, grain)
    before = ink_on(sheet, deposit, (45, 47, 43))
    rub = Image.new('L', SIZE)
    rubbing = ImageDraw.Draw(rub)
    for row in range(7):
        y = 303 + row * 13
        start, end = int(rng.integers(125, 151)), int(rng.integers(453, 494))
        points = [(x, y + int(rng.integers(-4, 5))) for x in range(start, end, 17)]
        force = 215 + row % 3 * 18
        rubbing.line(points, fill=force, width=25, joint='curve')
        for x, tip_y in (points[0], points[-1]):
            rubbing.ellipse((x - 12, tip_y - 12, x + 12, tip_y + 12), fill=force)
    rub = rub.filter(ImageFilter.GaussianBlur(2.2))
    rub_array = np.asarray(rub, dtype=float) * (0.78 + 0.22 * fibers)
    rub = Image.fromarray(np.uint8(rub_array))
    remaining, dust, wear = rub_out(Image.fromarray(deposit), rub, grain, strength=0.96)
    sheet = ink_on(sheet, np.uint8(wear * 0.08), (118, 125, 118))
    sheet = ink_on(sheet, remaining, (45, 47, 43))
    sheet = ink_on(sheet, dust, (68, 70, 65))
    # Tiny exposed fibers run along the rub, not across the untouched page.
    fiber_layer = Image.new('L', SIZE)
    fdraw = ImageDraw.Draw(fiber_layer)
    for _ in range(1200):
        x, y = int(rng.integers(128, 490)), int(rng.integers(285, 410))
        if wear[y, x] > 80:
            fdraw.line((x, y, x + int(rng.integers(2, 8)), y - 1), fill=75, width=1)
    sheet = ink_on(sheet, np.asarray(fiber_layer), (255, 255, 250))
    erased = sheet.copy()
    new = lettering('\u518d\u73a9\u4e94\u5206\u949f', (160, 326), h(101), rng)
    sheet = ink_on(sheet, graphite(new, grain, Image.fromarray(wear)), (36, 56, 61))
    note = lettering('\u5c31\u4e94\u5206\u949f\u3002', (525, 615), h(42), rng)
    sheet = ink_on(sheet, graphite(note, grain), (67, 72, 64))
    draw = ImageDraw.Draw(sheet)
    for _ in range(39):
        x, y = int(rng.integers(451, 548)), int(rng.integers(380, 462))
        draw.line((x, y, x + int(rng.integers(1, 5)), y + 1), fill=(151, 157, 148), width=2)

    board = Image.new('RGB', (1080, 1050), (224, 233, 230))
    draw = ImageDraw.Draw(board)
    draw.text((90, 28), '\u4e94\u5206\u949f', font=p(28), fill=(43, 67, 57))
    draw.text((727, 38), 'ERASER GHOST / 02', font=p(15), fill=(88, 109, 100))
    draw.rectangle((96, 99, 996, 959), fill=(195, 207, 201))
    board.paste(sheet, (90, 92))
    draw.text((90, 989), 'AMA: IDEA  /  GLASSGEAR: VARIATION', font=p(16), fill=(75, 95, 85))
    return board, before, erased


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('output/eraser-ghost'))
    parser.add_argument('--seed', type=int, default=17)
    parser.add_argument('--hand-font', type=Path)
    parser.add_argument('--print-font', type=Path)
    parser.add_argument('--hand-index', type=int, default=0)
    parser.add_argument('--print-index', type=int, default=0)
    args = parser.parse_args()
    try:
        board, before, erased = render(args.seed, args.hand_font, args.print_font,
                                      args.hand_index, args.print_index)
    except (FileNotFoundError, OSError) as exc:
        parser.error(str(exc))
    args.out.mkdir(parents=True, exist_ok=True)
    board.save(args.out / 'five-more-minutes.png')
    before.save(args.out / 'before.png')
    erased.save(args.out / 'erased.png')
    print(args.out / 'five-more-minutes.png')


if __name__ == '__main__':
    main()
