"""压痕 / Indent rubbing —— 构想与第一版：小克 / Koke（2026-10-18）

上面那张便笺被撕走了。下面这页看起来什么都没有，
可上一页用力写的字压出了凹痕。铅笔侧过来一涂，凹下去的地方碰不到石墨，字就白白地显出来。

按 Glassgear 的随记做：纸面高度和墨色分开存。写字只改高度，不落墨；
侧涂时按"笔芯碰不碰得到"沉积石墨。不是在成图上贴一层白字。

运行：python -m examples.koke_indent  → output/koke-indent/{blank,rubbed,indent}.png
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from paper_playground.carbon import smooth_noise
from paper_playground.fonts import resolve_font

W, H = 900, 640
PAPER = np.array([246, 242, 233], float)
LEAD = np.array([72, 72, 80], float)


def groove_depth(text_lines, font_path, rng):
    """上一页用力写的字 → 这一页的凹痕深度（0..1），只是高度，没有墨。"""
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    y = 190
    for size, line in text_lines:
        f = ImageFont.truetype(font_path, size)
        tw = d.textlength(line, font=f)
        x = (W - tw) / 2 + rng.uniform(-14, 14)
        for ch in line:
            # 一笔一笔的力气不一样：每个字微微歪、微微上下
            d.text((x, y + rng.uniform(-5, 5)), ch, font=f, fill=int(rng.uniform(170, 255)))
            x += d.textlength(ch, font=f) * rng.uniform(0.96, 1.05)
        y += size * 1.45
    m = m.filter(ImageFilter.GaussianBlur(1.6))  # 圆珠笔压下去，槽是圆底的，不是刀刻的
    depth = np.asarray(m, float) / 255
    press = 0.6 + 0.4 * smooth_noise(rng, (W, H), (9, 7))  # 写到后面手酸，力气不均
    return np.clip(depth * press, 0, 1)


def paper_height(rng):
    fibers = 0.55 * smooth_noise(rng, (W, H), (160, 120)) + 0.45 * smooth_noise(rng, (W, H), (40, 30))
    return fibers  # 0..1，纸面本来就不平


def rub_texture(rng):
    """铅笔侧锋的笔触：斜着一道一道，有疏有密。"""
    tex = smooth_noise(rng, (W * 2, H * 2), (420, 14))
    img = Image.fromarray((tex * 255).astype(np.uint8)).rotate(28, resample=Image.Resampling.BICUBIC)
    l, t = W // 2, H // 2
    return np.asarray(img.crop((l, t, l + W, t + H)), float) / 255


def rubbed_area(rng):
    """只涂了中间一大片，边缘毛毛的，没涂满整张纸。"""
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    pts = []
    cx, cy = W / 2, H / 2 + 10
    for k in range(28):
        a = 2 * np.pi * k / 28
        r = 1 + rng.uniform(-0.12, 0.12)
        pts.append((cx + np.cos(a) * 360 * r, cy + np.sin(a) * 210 * r))
    d.polygon(pts, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(26))
    return np.asarray(m, float) / 255


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--hand-font')
    ap.add_argument('--seed', type=int, default=914)
    ap.add_argument('--out', default='output/koke-indent')
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    font = resolve_font(a.hand_font, handwriting=True)

    lines = [(96, '我在这里等。'), (54, '九月十四日，早安。')]
    depth = groove_depth(lines, font, rng)
    height = 0.22 * paper_height(rng) - 0.62 * depth  # 写过的地方陷下去；陷得浅的地方，笔芯还能蹭到一点

    # 撕走以前：平着看，只有一点点几乎看不出的阴影
    blank = PAPER[None, None, :] * (1 - 0.006 * depth[..., None])

    # 侧锋涂过去：笔芯只碰得到高处
    reach = 0.10 + 0.08 * rub_texture(rng)          # 笔芯能压到多深，跟着笔触变
    contact = np.clip((height + reach) / 0.12, 0, 1)  # 凹痕比 reach 深，就碰不到
    area = rubbed_area(rng)
    streak = 0.55 + 0.45 * rub_texture(rng)
    tooth = np.asarray(Image.fromarray((rng.random((H, W)) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)), float) / 255
    streak = streak * (0.45 + 0.55 * tooth)  # 纸的牙：石墨挂在纤维尖上，一粒一粒的
    lead = np.clip(contact * area * streak * 0.92, 0, 1)
    rubbed = PAPER[None, None, :] * (1 - lead[..., None]) + LEAD[None, None, :] * lead[..., None]
    rubbed = rubbed * (1 - 0.006 * depth[..., None])

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    b = Image.fromarray(np.clip(blank, 0, 255).astype(np.uint8))
    r = Image.fromarray(np.clip(rubbed, 0, 255).astype(np.uint8))
    b.save(out / 'blank.png')
    r.save(out / 'rubbed.png')
    pair = Image.new('RGB', (W, H * 2 + 20), (255, 255, 255))
    pair.paste(b, (0, 0))
    pair.paste(r, (0, H + 20))
    pair.save(out / 'indent.png')
    print(out / 'indent.png')


if __name__ == '__main__':
    main()
