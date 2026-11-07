"""Local IBM Plex typography and print-safe, static art QR codes.

Every code keeps a four-module quiet zone. No redirect service, account,
tracking, image generator, or network request is used.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import groupby
from pathlib import Path

import cv2
import numpy as np
import segno
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / 'vendor/fonts'
PX = 300 / 25.4
INK = (29, 48, 54)
PAPER = (240, 233, 216)
QUIET = 4
# 版画のぼかし：上は藍、下は海の色。どちらも紙との明度差を十分に取る
INDIGO_TOP = (11, 33, 60)
INDIGO_BOTTOM = (8, 62, 88)
# 位置検出パターンの角丸（外・中・内、モジュール比）。
# 液状のデータ部は読み取りに影響しないが、ここを丸めすぎると zbar や OpenCV が読めなくなる
EYE_RADII = (0.9, 0.6, 0.45)
LIQUID_SIGMA = 0.24


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


def qr_matrix(url, version=None, error='h'):
    q = segno.make_qr(url, error=error, version=version, boost_error=False)
    return np.array([list(row) for row in q.matrix], dtype=bool)


def _eye_origins(n):
    return (0, 0), (0, n - 7), (n - 7, 0)


def qr_alpha(matrix, mod, knock=None, sigma=LIQUID_SIGMA, eye=EYE_RADII, ss=4):
    """Liquid coverage of the dark modules, quiet zone included, sized (n + 2 * QUIET) * mod.

    Blurring and re-thresholding rounds outer and inner corners alike, while the
    centre of every module stays on its correct side (test_module_centres).
    """
    n = matrix.shape[0]
    big_mod = mod * ss
    data = matrix.copy()
    for r, c in _eye_origins(n):
        data[r:r + 7, c:c + 7] = False
    if knock is not None:
        data &= ~knock
    side = (n + 2 * QUIET) * big_mod
    pad = QUIET * big_mod
    big = np.zeros((side, side), np.float32)
    big[pad:pad + n * big_mod, pad:pad + n * big_mod] = np.kron(data.astype(np.float32), np.ones((big_mod, big_mod), np.float32))
    liquid = (cv2.GaussianBlur(big, (0, 0), sigma * big_mod) > 0.5).astype(np.uint8) * 255
    mask = Image.fromarray(liquid)
    d = ImageDraw.Draw(mask)
    r_out, r_mid, r_in = eye
    for r, c in _eye_origins(n):
        x, y = pad + c * big_mod, pad + r * big_mod
        d.rounded_rectangle((x, y, x + 7 * big_mod - 1, y + 7 * big_mod - 1), radius=int(r_out * big_mod), fill=255)
        d.rounded_rectangle((x + big_mod, y + big_mod, x + 6 * big_mod - 1, y + 6 * big_mod - 1), radius=int(r_mid * big_mod), fill=0)
        d.rounded_rectangle((x + 2 * big_mod, y + 2 * big_mod, x + 5 * big_mod - 1, y + 5 * big_mod - 1), radius=int(r_in * big_mod), fill=255)
    return cv2.resize(np.asarray(mask, np.float32) / 255, (side // ss, side // ss), interpolation=cv2.INTER_AREA)


def emblem_knock(emblem, n, mod, margin=0.5):
    """Modules that a centred RGBA emblem (plus a margin, in modules) would touch."""
    alpha = np.asarray(emblem.split()[-1])
    field = np.zeros((n * mod, n * mod), np.uint8)
    x, y = (n * mod - emblem.width) // 2, (n * mod - emblem.height) // 2
    field[y:y + emblem.height, x:x + emblem.width] = alpha
    grow = int(mod * margin * 2) | 1
    field = cv2.dilate(field, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (grow, grow)))
    return cv2.resize(field, (n, n), interpolation=cv2.INTER_AREA) > 90


def draw_qr(canvas, xy, url, mod, *, version=None, error='h', emblem=None):
    """Draw a liquid, bokashi-coloured code onto `canvas`; its pixels stay as the light modules.

    Returns the module matrix. `xy` is the top-left of the quiet zone.
    """
    matrix = qr_matrix(url, version, error)
    n = matrix.shape[0]
    knock = emblem_knock(emblem, n, mod) if emblem is not None else None
    alpha = qr_alpha(matrix, mod, knock)
    side = alpha.shape[0]
    x, y = xy
    t = np.linspace(0, 1, side, dtype=np.float32)
    t = (t * t * (3 - 2 * t))[:, None, None]
    dark = np.array(INDIGO_TOP, np.float32) * (1 - t) + np.array(INDIGO_BOTTOM, np.float32) * t
    region = np.asarray(canvas.crop((x, y, x + side, y + side)).convert('RGB'), np.float32)
    mixed = region * (1 - alpha[..., None]) + dark * alpha[..., None]
    canvas.paste(Image.fromarray(np.clip(mixed, 0, 255).astype(np.uint8)), (x, y))
    if emblem is not None:
        canvas.paste(emblem, (x + (side - emblem.width) // 2, y + (side - emblem.height) // 2), emblem)
    return matrix


def qr_side(url, mod, version=None, error='h'):
    return (qr_matrix(url, version, error).shape[0] + 2 * QUIET) * mod
