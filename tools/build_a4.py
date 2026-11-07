"""完成図（画面ごとの絵）を切り分けて A4 両面の PDF にする。
  uv run ... python tools/build_a4.py <デザイン名> [--margin 4.5]

入力 designs/a4/<デザイン名>/
  front.png    合上の正面         1:1
  scroll.png   開いて最初の長い絵   74.25:210（約 1:2.83）
  hexagon.png  六角形に開いた絵    210:297（四隅は使わない）
  flat.png     全部開いた内側      210:297（真ん中の帯は hexagon で上書きする）
  back.png     任意。なければ表示欄を自動で作る
  tongue.png   任意。なければ舌の案内を自動で作る

出力 dist/a4/<デザイン名>/：print.pdf（1 ページ目が内側 P、2 ページ目が外側 Q）と各画面の予想図。
PDF は紙の端まで絵を入れる。--margin は複合機が刷れない幅を予想図に白く出すだけで、PDF は変えない。
"""
from __future__ import annotations
import argparse, hashlib, json, math, pathlib, re, sys
import numpy as np, cv2, zxingcpp
from PIL import Image, ImageDraw
from print_design import QUIET, draw_qr, draw_text, qr_side

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from a4fold import *
from a4fold_view import render, TW, TH, SCALE, state_flap_open, state_top_mountain

DPI = 300
PX = DPI / 25.4
# 札・背面・舌は 45 度回して刷るので、倍の解像度で作って文字と QR の輪郭を保つ
CARD_RES = 2
CPX = PX * CARD_RES
INK = (29, 48, 54)
RULE = (160, 150, 130)
CAPTION = (84, 79, 68)
WASHI = (240, 233, 216)
RED = (176, 58, 42)
CONF = {
    'qr_inside': 'https://x.com/iwami_kankou',
    'qr_source': 'https://github.com/social-calculus/tane-tsutsumi',
    'qr_grow': 'https://social-calculus.github.io/tane-tsutsumi/grow.html',
    'qr_label': '岩美町の中の人',
    'qr_note': 'X  @iwami_kankou',
    'label': [('名称', 'かぼちゃの種（栽培用）'), ('内容量', '3粒'), ('採種地', '鳥取県岩美町 岩美駅前'),
              ('採種', '2026年11月'), ('注意', '食べられません'), ('ひとこと', '何が育つかはお楽しみ')],
    'credit': '絵・型紙 CC BY 4.0 · SOCIAL CALCULUS',
    'tongue_note': '種は春まで、涼しく乾いたところに。',
    'tongue': [('育て方', '畑で、大きな一玉を。', 'qr_grow'), ('絵と型紙', '出典を書けば、自由に。', 'qr_source')],
    # 内側 QR の中央に置く絵。flat.png の中の位置（幅・高さに対する比）
    'emblem_box': (0.414, 0.0653, 0.893, 0.1969),
}
# QR の札：種の下の格。左下は隅の翼が重なるので避ける（U, V は mm）
# 折り線は tools 側で印刷面に足す。絵には描かせない
QR_CARD = dict(u0=74.0, v0=76.0, w=58.0, h=58.0)
# QR のモジュール（300 dpi の px）と型番。舌の 2 つは同じ型番・同じ大きさにそろえる
X_QR = dict(mod=11, version=6, error='h', emblem_modules=20)
TONGUE_QR = dict(mod=9, version=5, error='q', emblem_modules=6)
TONGUE_H = 210 - V6
# 札は絵が透ける磨りガラスのような薄紙。下の絵の割合を QR の周りで控えめに、札の縁へ向けて濃くする
VEIL_CODE, VEIL_EDGE = 0.22, 0.42
FROST_MM = 0.30  # QR の下の絵だけ少しぼかして、読み取りの邪魔になる細かい輪郭を消す


def washi(w, h, seed=7, res=1):
    rng = np.random.default_rng(seed)
    base = np.ones((h, w, 3), np.float32) * np.array(WASHI, np.float32)
    n = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 6 * res)
    n = n / (n.std() + 1e-6)
    fine = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 0.5 * res)
    fine = fine / (fine.std() + 1e-6)
    v = (n * 1.8 + fine * 1.5)[:, :, None]
    return Image.fromarray(np.clip(base + v, 0, 255).astype(np.uint8))


def seal_icon(px):
    """正面の印と同じ意匠の小さな印"""
    s = px * 4
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, s - 1, s - 1), radius=s * 0.17, fill=RED + (255,))
    draw_text(d, (s / 2, s * 0.285), '岩', s * 0.41, fill=WASHI, anchor='mm', medium=True, scale=1)
    draw_text(d, (s / 2, s * 0.715), '美', s * 0.41, fill=WASHI, anchor='mm', medium=True, scale=1)
    return im.resize((px, px), Image.LANCZOS)


def pumpkin_icon(px):
    """育て方の目印。小さく刷るので、畝と軸だけの形にする"""
    s = px * 6
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    line = max(1, s // 64)
    d.rounded_rectangle((s * 0.44, s * 0.05, s * 0.57, s * 0.30), radius=s * 0.035, fill=(84, 108, 58), outline=(52, 70, 40), width=line)
    cy, ry = s * 0.59, s * 0.37
    for off, half, colour in ((-0.29, 0.195, (186, 84, 30)), (0.29, 0.195, (186, 84, 30)),
                              (-0.155, 0.22, (208, 100, 34)), (0.155, 0.22, (208, 100, 34)), (0, 0.205, (230, 122, 44))):
        cx = s * (0.5 + off)
        d.ellipse((cx - half * s, cy - ry, cx + half * s, cy + ry), fill=colour, outline=(120, 58, 24), width=line)
    return im.resize((px, px), Image.LANCZOS)


def art_cutout(flat, box, width):
    """原画から赤い生き物を切り抜く（紙の色は透かす）"""
    w, h = flat.size
    crop = flat.convert('RGB').crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
    big = np.asarray(crop.resize((crop.width * 3, crop.height * 3), Image.LANCZOS), np.uint8)
    lab = cv2.cvtColor(big, cv2.COLOR_RGB2LAB).astype(np.float32)
    mask = ((lab[..., 1] > 143) | (lab[..., 0] < 92)).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17)))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    keep = (labels == largest).astype(np.uint8) * 255
    contours, _ = cv2.findContours(keep, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(keep, contours, -1, 255, -1)
    keep = cv2.GaussianBlur(keep, (0, 0), 1.2)
    ys, xs = np.where(keep > 128)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    cut = Image.fromarray(np.dstack([big[y0:y1, x0:x1], keep[y0:y1, x0:x1]]), 'RGBA')
    return cut.resize((width, round(width * cut.height / cut.width)), Image.LANCZOS)


def card_art(hexagon, w, h):
    """札の座標で hexagon を引く。札の下の絵がそのまま透けて続く"""
    a = np.asarray(hexagon.convert('RGB'), np.float32)
    ih, iw = a.shape[:2]
    jj, ii = np.meshgrid((np.arange(h) + 0.5) / CPX, (np.arange(w) + 0.5) / CPX, indexing='ij')
    x, y = from_uv(QR_CARD['u0'] + ii, QR_CARD['v0'] + jj)
    return cv2.remap(a, (x / W * iw - 0.5).astype(np.float32), ((L - y) / L * ih - 0.5).astype(np.float32), cv2.INTER_LINEAR)


def make_back():
    """閉じたときの背面：種の表示だけ。QR は舌へ移した"""
    s = int(round(CELL * CPX))
    im = washi(s, s, 11, CARD_RES); d = ImageDraw.Draw(im)
    def text(x, y, value, mm, **kw):
        draw_text(d, (x * CPX, y * CPX), value, mm, scale=CPX, **kw)
    m = 6.0
    text(m, 10.2, '岩美のたね', 5.4, medium=True)
    y, pitch = 17.0, 6.8
    def rule(at):
        d.line([(m * CPX, at * CPX), ((CELL - m) * CPX, at * CPX)], fill=RULE, width=CARD_RES + 1)
    rule(y)
    for k, v in CONF['label']:
        text(m, y + pitch / 2, k, 2.6, fill=CAPTION)
        text(m + 13.5, y + pitch / 2, v, 2.9, medium=k == '注意')
        y += pitch
        rule(y)
    text(CELL - m, y + 6.2, CONF['credit'], 2.3, anchor='rm', fill=CAPTION)
    return im


def make_tongue(hexagon=None):
    """舌：ふたを持ち上げると最初に見える面。同じ大きさの QR を 2 つ並べ、下に海を置く。
    上端が舌の先、下端が折り目。この面に折り線は通らない"""
    w, h = int(round(CELL * CPX)), int(round(TONGUE_H * CPX))
    im = washi(w, h, 41, CARD_RES)
    if hexagon is not None:
        a = np.asarray(im, np.float32)
        band_mm = 14.0
        band = int(band_mm * CPX)
        iw, ih = hexagon.size
        # 全開の絵の波を、縮尺 1/1.8 で借りる（原画の解像度のまま締まって見える）
        zoom = 1.8
        bw = int(CELL * zoom / W * iw); bh = int(band_mm * zoom / L * ih)
        x0, y0 = int(iw * 0.20), int(ih * 0.655)
        sea = hexagon.convert('RGB').crop((x0, y0, x0 + bw, y0 + bh)).resize((w, band), Image.LANCZOS)
        t = np.linspace(0, 1, band, dtype=np.float32)
        t = np.clip((t - 0.04) / 0.55, 0, 1)
        t = (t * t * (3 - 2 * t))[:, None, None]
        a[h - band:] = a[h - band:] * (1 - t) + np.asarray(sea, np.float32) * t
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    def text(x, y, value, mm, **kw):
        draw_text(d, (x * CPX, y * CPX), value, mm, scale=CPX, **kw)
    text(CELL / 2, 4.8, CONF['tongue_note'], 2.5, anchor='mm')
    mod = TONGUE_QR['mod'] * CARD_RES
    side = qr_side(CONF['qr_grow'], mod, TONGUE_QR['version'], TONGUE_QR['error'])
    emblem_px = TONGUE_QR['emblem_modules'] * mod
    icons = {'qr_grow': pumpkin_icon(emblem_px), 'qr_source': seal_icon(emblem_px)}
    gap = (w - 2 * side) // 3
    top = int(6.9 * CPX)
    for i, (title, sub, key) in enumerate(CONF['tongue']):
        x = gap + i * (side + gap)
        draw_qr(im, (x, top), CONF[key], mod, version=TONGUE_QR['version'], error=TONGUE_QR['error'], emblem=icons.get(key))
        cx = (x + side / 2) / CPX
        y = (top + side) / CPX
        text(cx, y + 1.5, title, 3.0, anchor='mm', medium=True)
        text(cx, y + 5.5, sub, 2.6, anchor='mm')
    return im


def with_seal(img):
    """正面の右上に「岩美」の印を足す（絵には描かせない）"""
    im = img.convert('RGB').copy(); d = ImageDraw.Draw(im); w = im.width
    r = w * 0.066; cx, cy = w * 0.87, w * 0.13
    d.rounded_rectangle([cx - r, cy - r, cx + r, cy + r], radius=r * 0.2, fill=RED)
    draw_text(d, (cx, cy - r * 0.44), '岩', r * 0.82, fill=WASHI, anchor='mm', medium=True, scale=1)
    draw_text(d, (cx, cy + r * 0.44), '美', r * 0.82, fill=WASHI, anchor='mm', medium=True, scale=1)
    return im


def x_emblem(flat, mod):
    if flat is not None and CONF.get('emblem_box'):
        return art_cutout(flat, CONF['emblem_box'], X_QR['emblem_modules'] * mod)
    return seal_icon(int(mod * 7))


def frosted(paper, hexagon, code_side):
    """絵が透ける薄紙。QR の周りは控えめにぼかし、札の縁へ向けて絵をはっきりさせる"""
    w, h = paper.size
    art = card_art(hexagon, w, h)
    soft = cv2.GaussianBlur(art, (0, 0), FROST_MM * CPX)
    yy, xx = np.mgrid[0:h, 0:w]
    reach = np.maximum(np.abs(xx - w / 2), np.abs(yy - h / 2))
    t = np.clip((reach - code_side / 2) / (w / 2 - code_side / 2), 0, 1).astype(np.float32)
    t = (t * t * (3 - 2 * t))[..., None]
    picture = soft * (1 - t) + art * t
    share = VEIL_CODE + (VEIL_EDGE - VEIL_CODE) * t
    return Image.fromarray(np.clip(picture * share + np.asarray(paper, np.float32) * (1 - share), 0, 255).astype(np.uint8))


def make_card(hexagon=None, flat=None):
    """種の下の札。絵が透ける薄紙に、ぼかしの QR と原画の蟹を置く"""
    w, h = int(QR_CARD['w'] * CPX), int(QR_CARD['h'] * CPX)
    im = washi(w, h, 23, CARD_RES)
    mod = X_QR['mod'] * CARD_RES
    side = qr_side(CONF['qr_inside'], mod, X_QR['version'], X_QR['error'])
    if hexagon is not None:
        im = frosted(im, hexagon, side)
    x, y = (w - side) // 2, (h - side) // 2
    draw_qr(im, (x, y), CONF['qr_inside'], mod, version=X_QR['version'], error=X_QR['error'], emblem=x_emblem(flat, mod))
    d = ImageDraw.Draw(im)
    zone = y / CPX / 2 + 0.3
    draw_text(d, (w / 2, zone * CPX), CONF['qr_label'], 3.1, anchor='mm', medium=True, scale=CPX)
    draw_text(d, (w / 2, h - zone * CPX), CONF['qr_note'], 2.4, anchor='mm', medium=True, scale=CPX)
    return im


def qr_alone(key):
    """1 コードだけの画像（画面から試し読みする用）"""
    cfg = X_QR if key == 'qr_inside' else TONGUE_QR
    side = qr_side(CONF[key], cfg['mod'], cfg['version'], cfg['error'])
    im = Image.new('RGB', (side, side), WASHI)
    draw_qr(im, (0, 0), CONF[key], cfg['mod'], version=cfg['version'], error=cfg['error'])
    return im


def sampler(img):
    a = np.asarray(img.convert('RGB'), dtype=np.float32)
    h, w = a.shape[:2]

    def f(sx, sy):
        return cv2.remap(a, (sx * w - 0.5).astype(np.float32), (sy * h - 0.5).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return f


SAFE = 6.0  # 複合機が確実に刷れる端からの距離（mm）


def _xy(side, x, y):
    return ((x if side == 'P' else W - x) * PX, (L - y) * PX)


def _safe(x, y):
    return SAFE <= x <= W - SAFE and SAFE <= y <= L - SAFE


def fold_line(arr, side, p0, p1, on=3.0, off=2.0, width=0.3):
    """折り線。下の絵の明るさに合わせて濃淡を変え、絵を邪魔しない細い破線にする"""
    (x0, y0), (x1, y1) = p0, p1
    length = math.hypot(x1 - x0, y1 - y0)
    if length == 0:
        return
    h, w = arr.shape[:2]
    t = 0.0
    th = max(1, int(round(width * PX)))
    while t < length:
        e = min(t + on, length)
        a = (x0 + (x1 - x0) * t / length, y0 + (y1 - y0) * t / length)
        b = (x0 + (x1 - x0) * e / length, y0 + (y1 - y0) * e / length)
        t = e + off
        if not (_safe(*a) and _safe(*b)):
            continue
        pa, pb = _xy(side, *a), _xy(side, *b)
        x_min, x_max = int(max(min(pa[0], pb[0]) - 3, 0)), int(min(max(pa[0], pb[0]) + 4, w))
        y_min, y_max = int(max(min(pa[1], pb[1]) - 3, 0)), int(min(max(pa[1], pb[1]) + 4, h))
        roi = arr[y_min:y_max, x_min:x_max]
        m = np.zeros(roi.shape[:2], np.uint8)
        cv2.line(m, (int(pa[0] - x_min), int(pa[1] - y_min)), (int(pb[0] - x_min), int(pb[1] - y_min)), 255, th, cv2.LINE_AA)
        mask = (m / 255.0 * 0.62)[:, :, None]
        lum = float(roi.mean())
        color = np.array(INK if lum > 110 else WASHI, np.float32)
        arr[y_min:y_max, x_min:x_max] = roi * (1 - mask) + color * mask


def corner_mark(arr, side):
    """向きの印（IC チップの 1 番ピンの角）。紙の同じ隅に両面で入れる"""
    tri = [(SAFE + 1, L - SAFE - 1), (SAFE + 13, L - SAFE - 1), (SAFE + 1, L - SAFE - 13)]
    pts = np.array([_xy(side, *p) for p in tri], np.int32)
    cv2.fillPoly(arr, [pts], RED, cv2.LINE_AA)


def add_guides(page_p, page_q):
    # 内側：四隅の折り線は両端だけ（全開の絵を横切らない）
    for start, end in (((105, L), (0, 192)), ((105, L), (W, 192)), ((105, 0), (0, 105)), ((105, 0), (W, 105))):
        d = math.hypot(end[0] - start[0], end[1] - start[1])
        ux, uy = (end[0] - start[0]) / d, (end[1] - start[1]) / d
        for a, b in ((0, 34), (d - 34, d)):
            fold_line(page_p, 'P', (start[0] + ux * a, start[1] + uy * a), (start[0] + ux * b, start[1] + uy * b))
    # 内側：中帯の 3 と 4 の線。QR の両脇に来る
    fold_line(page_p, 'P', (105, 192), (192, 105))
    fold_line(page_p, 'P', (0, 192), (87, 105))
    # 外側：左上の隅の翼にある 3 の線（六角形で中心から星の辺の中点まで）
    fold_line(page_q, 'Q', (17, L - 17), (52.5, 244.5))
    # 外側：長条の両端に 5 と 6 の目印、舌の先の角
    for v in (V5, V6):
        fold_line(page_q, 'Q', from_uv(U4 - 1, v), from_uv(U4 - 12, v), on=2.5, off=1.5)
        fold_line(page_q, 'Q', from_uv(U3 + 1, v), from_uv(U3 + 12, v), on=2.5, off=1.5)
    fold_line(page_q, 'Q', from_uv(U4, 201), from_uv(U4 - 9, 210), on=2.0, off=1.2)
    fold_line(page_q, 'Q', from_uv(U3, 201), from_uv(U3 + 9, 210), on=2.0, off=1.2)
    corner_mark(page_p, 'P')
    corner_mark(page_q, 'Q')


def build_pages(art):
    pw, ph = int(round(W * PX)), int(round(L * PX))
    gx, gt = np.meshgrid((np.arange(pw) + 0.5) / PX, (np.arange(ph) + 0.5) / PX)
    y = L - gt
    hexa, flat, scroll, front = sampler(art['hexagon']), sampler(art['flat']), sampler(art['scroll']), sampler(with_seal(art['front']))
    back = sampler(art.get('back') or make_back())
    tongue = sampler(art.get('tongue') or make_tongue(art['hexagon']))

    # ---- P 面（内側）。そのまま x = gx
    x = gx
    page_p = flat(x / W, (L - y) / L)
    band = (y >= 105) & (y <= 192)
    page_p[band] = hexa(x / W, (L - y) / L)[band]
    u, v = to_uv(x, y)
    card = sampler(make_card(art['hexagon'], art['flat']))
    su, sv = (u - QR_CARD['u0']) / QR_CARD['w'], (v - QR_CARD['v0']) / QR_CARD['h']
    inside = (su >= 0) & (su <= 1) & (sv >= 0) & (sv <= 1)
    page_p[inside] = card(su, sv)[inside]

    # ---- Q 面（外側）。長辺とじなので左右が逆：x = W - gx
    x = W - gx
    u, v = to_uv(x, y)
    tl, tr, bl, br = (y - x > 192), (x + y > 402), (x + y < 105), (x - y > 105)
    corner = tl | tr | bl | br
    hx = x.copy(); hy = y.copy()
    hx[tl], hy[tl] = (y - 192)[tl], (x + 192)[tl]
    hx[tr], hy[tr] = (402 - y)[tr], (402 - x)[tr]
    hx[bl], hy[bl] = (105 - y)[bl], (105 - x)[bl]
    hx[br], hy[br] = (y + 105)[br], (x - 105)[br]
    wing_l = (u < U4) & ~corner
    wing_r = (u > U3) & ~corner
    up = u.copy()
    up[wing_l] = (2 * U4 - u)[wing_l]
    up[wing_r] = (2 * U3 - u)[wing_r]
    scroll_col = scroll((up - U4) / CELL, v / 210.0)
    cell = (~corner) & (~wing_l) & (~wing_r)
    is_front = cell & (v < V5)
    is_back = cell & (v >= V5) & (v < V6)
    is_tongue = cell & (v >= V6)
    page_q = np.array(washi(pw, ph, 31), dtype=np.float32)
    page_q[corner] = hexa(hx / W, (L - hy) / L)[corner]
    page_q[wing_l | wing_r] = scroll_col[wing_l | wing_r]
    page_q[is_front] = front((u - U4) / CELL, (V5 - v) / CELL)[is_front]
    page_q[is_back] = back(1 - (u - U4) / CELL, (v - V5) / CELL)[is_back]
    # 舌は V6 で折り上げてふたの下へ入る。ふたを持ち上げた向きで正立するよう、先端を上にする
    page_q[is_tongue] = tongue((u - U4) / CELL, (210 - v) / TONGUE_H)[is_tongue]
    add_guides(page_p, page_q)
    return (Image.fromarray(np.clip(page_p, 0, 255).astype(np.uint8)),
            Image.fromarray(np.clip(page_q, 0, 255).astype(np.uint8)))


def textures(page_p, page_q, margin=0.0):
    """予想図用。紙の座標で引くテクスチャに直す（Q は左右を戻す）"""
    tp = page_p.resize((TW, TH), Image.LANCZOS)
    tq = page_q.transpose(Image.FLIP_LEFT_RIGHT).resize((TW, TH), Image.LANCZOS)
    if margin:
        m = int(margin * SCALE)
        for t in (tp, tq):
            d = ImageDraw.Draw(t)
            d.rectangle([0, 0, TW, m], fill='white'); d.rectangle([0, TH - m, TW, TH], fill='white')
            d.rectangle([0, 0, m, TH], fill='white'); d.rectangle([TW - m, 0, TW, TH], fill='white')
    return tp, tq


STATES = [
    ('closed_front', '閉じた状態・表', state_closed, dict(kind='uv')),
    ('closed_back', '閉じた状態・裏', state_closed, dict(kind='uv', back=True)),
    ('flap_open', 'ふたを上げる', state_flap_open, dict(kind='uv')),
    ('scroll', 'ひとつ開く', state_strip, dict(kind='uv')),
    ('hexagon', '六角形に開く', state_hexagon, dict(kind='xy')),
    ('flat_p', '全開・内側', Sheet, dict(kind='xy')),
    ('flat_q', '全開・外側', Sheet, dict(kind='xy', back=True)),
]


def overview(tp, tq, path, scale=2.2, title=None):
    tiles = [(name, cap, render(fn(), tp, tq, scale=scale, pad=6, **kw)) for name, cap, fn, kw in STATES]
    gap = 26; cap_h = 60
    width = sum(t[2].width for t in tiles) + gap * (len(tiles) + 1)
    height = max(t[2].height for t in tiles) + cap_h + 20
    sheet = Image.new('RGB', (width, height), (250, 249, 245)); d = ImageDraw.Draw(sheet)
    x = gap
    for name, cap, im in tiles:
        sheet.paste(im, (x, height - cap_h - im.height))
        draw_text(d, (x + im.width / 2, height - cap_h + 10), cap, 26, scale=1, fill=INK, anchor='mt')
        x += im.width + gap
    sheet.save(path, quality=88)
    return sheet


RATIO = {'front': 1.0, 'scroll': CELL / 210, 'hexagon': W / L, 'flat': W / L}


def fit(im, name):
    """比率が違う絵は中央を切る（sampler は枠いっぱいに引き伸ばすので、そのままだと歪む）"""
    r, w, h = RATIO[name], *im.size
    if abs(w / h / r - 1) < 0.01:
        return im
    cw, ch = (round(h * r), h) if w / h > r else (w, round(w / r))
    x, y = (w - cw) // 2, (h - ch) // 2
    print(f'{name}: {w}x{h} の中央 {cw}x{ch} を使う')
    return im.crop((x, y, x + cw, y + ch))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('design'); ap.add_argument('--margin', type=float, default=4.5)
    a = ap.parse_args()
    src = ROOT / 'designs/a4' / a.design
    art = {k: fit(Image.open(src / f'{k}.png').convert('RGB'), k) for k in RATIO}
    for extra in ('back', 'tongue'):
        if (src / f'{extra}.png').exists():
            art[extra] = Image.open(src / f'{extra}.png')
    out = ROOT / 'dist/a4' / a.design; out.mkdir(parents=True, exist_ok=True)
    pp, pq = build_pages(art)
    pp.save(out / 'print.pdf', save_all=True, append_images=[pq], resolution=DPI, quality=92)
    pp.save(out / 'page_P.jpg', quality=90); pq.save(out / 'page_Q.jpg', quality=90)
    tp, tq = textures(pp, pq)
    for name, cap, fn, kw in STATES:
        render(fn(), tp, tq, scale=4.0, pad=12, **kw).save(out / f'{name}.jpg', quality=90)
    overview(tp, tq, out / 'overview.jpg')
    tp2, tq2 = textures(pp, pq, a.margin)
    overview(tp2, tq2, out / 'overview_printer_margin.jpg')
    half = lambda im: im.resize((im.width // CARD_RES, im.height // CARD_RES), Image.LANCZOS)
    half(make_card(art['hexagon'], art['flat'])).save(out / 'x_card.png')
    half(art.get('back') or make_back()).save(out / 'back_card.png')
    half(art.get('tongue') or make_tongue(art['hexagon'])).save(out / 'tongue_card.png')
    for name, key in (('qr_x', 'qr_inside'), ('qr_source', 'qr_source'), ('qr_grow', 'qr_grow')):
        qr_alone(key).save(out / f'{name}.png')
    # QR の読み取り確認：印刷面をそのまま・45 度起こして読む（300/150 dpi）
    res = {}
    for key, page_img in (('inside', pp), ('outside', pq)):
        found = set()
        arr = np.asarray(page_img)
        for k in (1.0, 0.5):
            small = cv2.resize(arr, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
            h, w = small.shape[:2]
            for ang in (0, 45, -45):
                M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1.0)
                rot = cv2.warpAffine(small, M, (w, h), borderValue=(255, 255, 255))
                found |= {f'{int(300 * k)}dpi {r.text}' for r in zxingcpp.read_barcodes(rot) if r.text}
        res[key] = sorted(found)
    expected = {'inside': [CONF['qr_inside']], 'outside': [CONF['qr_source'], CONF['qr_grow']]}
    for side, urls in expected.items():
        for dpi in (150, 300):
            for url in urls:
                if f'{dpi}dpi {url}' not in res[side]:
                    raise RuntimeError(f'QR preflight failed: {side} {dpi}dpi {url}')
    check = dict(cell_mm=round(CELL, 2), qr=res, quiet_zone_modules=QUIET, decoders=['zxing-cpp'],
                 note='Decoder union at 0/45/-45 degrees. See scan-sim.json for the print-and-camera simulation. Physical phone scan is not simulated.')
    (out / 'check.json').write_text(json.dumps(check, ensure_ascii=False, indent=2) + '\n')
    data = (out / 'print.pdf').read_bytes()
    page_count = len(re.findall(rb'/Type\s*/Page\b', data))
    boxes = [list(map(float, b.split())) for b in re.findall(rb'/MediaBox\s*\[([^\]]+)\]', data)]
    assert page_count == 2 and len(boxes) == 2
    assert all(abs(b[2] - W / 25.4 * 72) < 0.3 and abs(b[3] - L / 25.4 * 72) < 0.3 for b in boxes)
    inputs = {}
    for name in RATIO:
        p = src / f'{name}.png'
        original = Image.open(p)
        inputs[name] = dict(path=str(p.relative_to(ROOT)), pixels=original.size,
                            fitted_pixels=art[name].size, cropped=original.size != art[name].size,
                            sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    preflight = dict(design=a.design, inputs=inputs, pdf=dict(pages=page_count, dpi=DPI,
        media_boxes_points=boxes, page_order=['P inside', 'Q outside'], rasterized=True),
        fonts=['IBM Plex Sans JP', 'IBM Plex Sans'], qr=check,
        simulated_unprintable_margin_mm=a.margin,
        physical_validation='The earlier layout was home-printed and accepted by the user. The art QR codes and tongue need a physical print and phone scan.')
    (out / 'preflight.json').write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + '\n')
    print(a.design, res)


if __name__ == '__main__':
    main()
