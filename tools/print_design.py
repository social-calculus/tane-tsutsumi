"""Local IBM Plex typography and print-safe, static styled QR codes.

The four-module quiet zone is part of each returned image. No redirect service,
account, tracking, image generator, or network request is used.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import groupby
from pathlib import Path

import segno
from segno.consts import TYPE_DATA_DARK
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / 'vendor/fonts'
PX = 300 / 25.4
INK = (29, 48, 54)
PAPER = (240, 233, 216)
QUIET = 4


@lru_cache(maxsize=96)
def font(mm, latin=False, medium=False, scale=PX):
    family = 'IBMPlexSans' if latin else 'IBMPlexSansJP'
    weight = 'Medium' if medium else 'Regular'
    return ImageFont.truetype(str(FONTS / f'{family}-{weight}.ttf'), max(1, round(mm * scale)))


def draw_text(draw, xy, text, mm, fill=INK, anchor='lm', medium=False, scale=PX):
    """JP glyphs use Plex Sans JP, ASCII uses Plex Sans, on a common baseline."""
    runs = []
    for latin, chars in groupby(text, lambda c: ord(c) < 128):
        s = ''.join(chars)
        f = font(mm, latin=latin, medium=medium, scale=scale)
        runs.append((s, f, draw.textlength(s, font=f), draw.textbbox((0, 0), s, font=f, anchor='ls')))
    if not runs:
        return
    width = sum(r[2] for r in runs)
    top, bottom = min(r[3][1] for r in runs), max(r[3][3] for r in runs)
    x, y = xy
    if anchor[0] == 'm':
        x -= width / 2
    elif anchor[0] == 'r':
        x -= width
    if anchor[1] == 'm':
        y -= (top + bottom) / 2
    elif anchor[1] == 't':
        y -= top
    elif anchor[1] == 'b':
        y -= bottom
    for s, f, length, _ in runs:
        draw.text((x, y), s, font=f, fill=fill, anchor='ls')
        x += length


def qr_image(url, mm, scale=PX, *, rounded=False, logo=False):
    """Size includes quiet zone; finder/timing structures remain recognisable.

    The X badge uses H correction and covers only the central five modules.
    Small utility codes have no logo and use M correction.
    """
    q = segno.make_qr(url, error='h' if logo else 'm', boost_error=False)
    n = len(q.matrix)
    mod = max(1, int(mm * scale) // (n + QUIET * 2))
    side = (n + QUIET * 2) * mod
    im = Image.new('RGB', (side, side), PAPER)
    d = ImageDraw.Draw(im)
    types = list(q.matrix_iter(scale=1, border=0, verbose=True))
    for y, row in enumerate(q.matrix):
        for x, dark in enumerate(row):
            if not dark:
                continue
            left, top = (x + QUIET) * mod, (y + QUIET) * mod
            box = (left, top, left + mod - 1, top + mod - 1)
            if rounded and types[y][x] == TYPE_DATA_DARK:
                d.rounded_rectangle(box, radius=mod * 0.28, fill=INK)
                # Join neighbouring dark modules. Only exposed data corners are
                # rounded; finder, timing and alignment structures stay square.
                if x and q.matrix[y][x - 1]:
                    d.rectangle((left, top, left + mod // 2, top + mod - 1), fill=INK)
                if x + 1 < n and q.matrix[y][x + 1]:
                    d.rectangle((left + mod // 2, top, left + mod - 1, top + mod - 1), fill=INK)
                if y and q.matrix[y - 1][x]:
                    d.rectangle((left, top, left + mod - 1, top + mod // 2), fill=INK)
                if y + 1 < n and q.matrix[y + 1][x]:
                    d.rectangle((left, top + mod // 2, left + mod - 1, top + mod - 1), fill=INK)
            else:
                d.rectangle(box, fill=INK)
    if logo:
        c = side / 2
        d.rectangle((c - 2.5 * mod, c - 2.5 * mod, c + 2.5 * mod, c + 2.5 * mod), fill=PAPER)
        d.rounded_rectangle((c - 1.9 * mod, c - 1.9 * mod, c + 1.9 * mod, c + 1.9 * mod),
                            radius=mod * 0.45, fill=INK)
        draw_text(d, (c, c), 'X', mod * 3 / scale, fill=PAPER, medium=True, anchor='mm', scale=scale)
    return im
