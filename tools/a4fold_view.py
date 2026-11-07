"""a4fold の各状態を描く。テクスチャは紙の座標で持つ（P 面・Q 面とも x,y でそのまま引く）。"""
from __future__ import annotations
import math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
from a4fold import *

SCALE = 8.0   # テクスチャ px/mm
TW, TH = int(W * SCALE), int(L * SCALE)


def blank(color):
    return Image.new('RGB', (TW, TH), color)


def px(x, y):
    return (x * SCALE, (L - y) * SCALE)


def view_matrix(kind='xy', back=False, rot=0.0, scale=3.0):
    """紙の世界座標 → 画面（スケール前、y 下向き）の 2x3 行列。kind='uv' は長条を立てた向き"""
    if kind == 'uv':
        # U 右、V 下：sx = U, sy = V
        m = np.array([[1 / RT2, 1 / RT2, -105 / RT2], [1 / RT2, -1 / RT2, 192 / RT2], [0, 0, 1]])
    else:
        m = np.array([[1, 0, 0], [0, -1, L], [0, 0, 1.0]])
    if back:
        m = np.array([[-1, 0, 0], [0, 1, 0], [0, 0, 1.0]]) @ m
    if rot:
        c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        m = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]]) @ m
    return np.array([[scale, 0, 0], [0, scale, 0], [0, 0, 1.0]]) @ m


def render(sheet, tex_p, tex_q, kind='xy', back=False, rot=0.0, scale=3.0, pad=10, bg=(244, 242, 236), shadow=True):
    """Layer を下から順に描く。back=True なら裏から見る（順を逆に、見える面も逆に）"""
    vm = view_matrix(kind, back, rot, scale)
    pts = []
    for l in sheet.layers:
        for p in l.world():
            q = vm @ np.array([p[0], p[1], 1.0])
            pts.append(q[:2])
    pts = np.array(pts)
    mn, mx = pts.min(axis=0) - pad, pts.max(axis=0) + pad
    T = np.array([[1, 0, -mn[0]], [0, 1, -mn[1]], [0, 0, 1.0]])
    size = (int(mx[0] - mn[0] + 1), int(mx[1] - mn[1] + 1))
    canvas = Image.new('RGB', size, bg)
    texP = np.asarray(tex_p); texQ = np.asarray(tex_q)
    # テクスチャ px → 紙 mm
    tex2paper = np.array([[1 / SCALE, 0, 0], [0, -1 / SCALE, L], [0, 0, 1.0]])
    layers = list(sheet.layers)
    if back:
        layers = layers[::-1]
    for l in layers:
        M = T @ vm @ l.m @ tex2paper
        showing_p = (l.flips % 2 == 0) != back
        src = texP if showing_p else texQ
        col = cv2.warpAffine(src, M[:2], size, flags=cv2.INTER_AREA if scale < SCALE else cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        q = [(T @ vm @ np.array([a, b, 1.0]))[:2] for a, b in l.world()]
        mask = Image.new('L', size, 0)
        ImageDraw.Draw(mask).polygon([tuple(v) for v in q], fill=255)
        if shadow:
            sh = mask.filter(ImageFilter.GaussianBlur(scale * 0.7)).point(lambda v: int(v * 0.28))
            canvas.paste((0, 0, 0), (0, 0), sh)
        canvas.paste(Image.fromarray(col), (0, 0), mask)
        if shadow:
            ImageDraw.Draw(canvas).line([tuple(v) for v in q] + [tuple(q[0])], fill=(150, 145, 135), width=1)
    return canvas


def state_step1():
    return Sheet().fold(1, 0, 105, True)


def state_flap_open():
    """閉じた形から正面のふたを持ち上げた形。舌は折り上げたまま、Q 面を見せている"""
    a, b, c = uv_line(0, 1, V6)
    return state_strip().fold(a, b, c, True)


def state_top_mountain():
    """3 を開き 4 だけ折った形で、V<V5 を裏側へ（写真 0818 は裏から見ている）"""
    s = state_after4_only()
    a, b, c = uv_line(0, 1, V5)
    stay, move = [], []
    R = reflect_matrix(a, b, c)
    for l in s.layers:
        na = a * l.m[0, 0] + b * l.m[1, 0]
        nb = a * l.m[0, 1] + b * l.m[1, 1]
        nc = c - a * l.m[0, 2] - b * l.m[1, 2]
        f = clip(l.poly, na, nb, nc, keep_ge=False)
        bk = clip(l.poly, na, nb, nc, keep_ge=True)
        if len(bk) >= 3 and area(bk) > 1e-6:
            stay.append(Layer(bk, l.m.copy(), l.flips, l.tag))
        if len(f) >= 3 and area(f) > 1e-6:
            move.append(Layer(f, R @ l.m, l.flips + 1, l.tag))
    s.layers = list(reversed(move)) + stay
    return s
