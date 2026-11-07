"""完成図（画面ごとの絵）を切り分けて A4 両面の PDF にする。
  uv run ... python tools/build_a4.py <デザイン名> [--margin 4.5]

入力 designs/a4/<デザイン名>/
  front.png    合上の正面         1:1
  scroll.png   開いて最初の長い絵   74.25:210（約 1:2.83）
  hexagon.png  六角形に開いた絵    210:297（四隅は使わない）
  flat.png     全部開いた内側      210:297（真ん中の帯は hexagon で上書きする）
  back.png     任意。なければ表示欄を自動で作る

出力 dist/a4/<デザイン名>/：print.pdf（1 ページ目が内側 P、2 ページ目が外側 Q）と各画面の予想図。
PDF は紙の端まで絵を入れる。--margin は複合機が刷れない幅を予想図に白く出すだけで、PDF は変えない。
"""
from __future__ import annotations
import argparse, hashlib, json, math, pathlib, re, sys
import numpy as np, cv2
from PIL import Image, ImageDraw
from print_design import QUIET, draw_text, qr_image

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from a4fold import *
from a4fold_view import render, TW, TH, SCALE, state_top_mountain

DPI = 300
PX = DPI / 25.4
INK = (29, 48, 54)
WASHI = (240, 233, 216)
RED = (176, 58, 42)
CONF = {
    'qr_inside': 'https://x.com/iwami_kankou',
    'qr_source': 'https://github.com/social-calculus/tane-tsutsumi',
    'qr_grow': 'https://social-calculus.github.io/tane-tsutsumi/grow.html',
    'qr_label': '岩美町の中の人',
    'qr_note': '@iwami_kankou',
    'label': [('名称', '観賞用かぼちゃの種'), ('品種', 'ビッグマックス'), ('内容量', '3粒'),
              ('採種地', '鳥取県岩美町 岩美駅前'), ('採種', '2026年11月'), ('用途', '食べずに、育てて楽しむ')],
}
# QR の札：種の下の格。左下は隅の翼が重なるので避ける（U, V は mm）
# 折り線は tools 側で印刷面に足す。絵には描かせない
QR_CARD = dict(u0=74.0, v0=76.0, w=58.0, h=58.0, qr=40.0)


def washi(w, h, seed=7):
    rng = np.random.default_rng(seed)
    base = np.ones((h, w, 3), np.float32) * np.array(WASHI, np.float32)
    n = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 6)
    n = n / (n.std() + 1e-6)
    fine = rng.normal(0, 1, (h, w)).astype(np.float32)
    v = (n * 3.0 + fine * 1.5)[:, :, None]
    return Image.fromarray(np.clip(base + v, 0, 255).astype(np.uint8))


def make_back():
    s = int(round(CELL * PX))
    im = washi(s, s, 11); d = ImageDraw.Draw(im)
    def text(x, y, value, mm, **kw):
        draw_text(d, (x * PX, y * PX), value, mm, **kw)
    text(5.5, 7.2, '岩美のたね', 4.5, medium=True)
    text(CELL - 5.5, 8.0, 'BIG MAX', 2.2, anchor='rm', medium=True)
    text(5.5, 12.0, '観賞用の、大きなひと粒。', 1.9, fill=(110, 103, 89))
    for i, (k, v) in enumerate(CONF['label']):
        y = 17 + i * 4.1
        text(5.5, y, k, 2.0, fill=(110, 103, 89))
        text(19, y, v, 2.2)
    d.line([(5.5 * PX, 40.5 * PX), ((CELL - 5.5) * PX, 40.5 * PX)], fill=(175, 165, 145), width=1)
    text(5.5, 43.8, '絵と型紙', 2.1, medium=True)
    source = qr_image(CONF['qr_source'], 21)
    im.paste(source, (int(5.5 * PX), int(46.8 * PX)))
    text(5.5, 70.0, '（AI生成の絵です）', 1.65, fill=(110, 103, 89))
    text(30, 43.8, 'CC BY 4.0', 2.2, medium=True)
    text(30, 46.8, 'SOCIAL CALCULUS', 1.8)
    grow = qr_image(CONF['qr_grow'], 25)
    im.paste(grow, (int(45 * PX), int(47.8 * PX)))
    text(30, 55.8, '育て方', 2.7, medium=True)
    text(30, 60.3, '畑で、一株一果。', 1.6)
    # A small sprout in the free area, never inside the QR quiet zone.
    d.line([(36 * PX, 68 * PX), (36 * PX, 64 * PX)], fill=INK, width=2)
    d.ellipse((33 * PX, 62 * PX, 36 * PX, 64.5 * PX), fill=INK)
    d.ellipse((36 * PX, 61.4 * PX, 39 * PX, 63.9 * PX), fill=INK)
    return im


def with_seal(img):
    """正面の右上に「岩美」の印を足す（絵には描かせない）"""
    im = img.convert('RGB').copy(); d = ImageDraw.Draw(im); w = im.width
    r = w * 0.066; cx, cy = w * 0.87, w * 0.13
    d.rounded_rectangle([cx - r, cy - r, cx + r, cy + r], radius=r * 0.2, fill=RED)
    draw_text(d, (cx, cy - r * 0.44), '岩', r * 0.82, fill=WASHI, anchor='mm', medium=True, scale=1)
    draw_text(d, (cx, cy + r * 0.44), '美', r * 0.82, fill=WASHI, anchor='mm', medium=True, scale=1)
    return im


def make_card():
    w, h = int(QR_CARD['w'] * PX), int(QR_CARD['h'] * PX)
    im = washi(w, h, 23); d = ImageDraw.Draw(im)
    # A small editorial masthead, rounded X code, and a readable account handle.
    d.rectangle((6.7 * PX, 3.8 * PX, 7.4 * PX, 7.0 * PX), fill=RED)
    draw_text(d, (w / 2, 5.4 * PX), CONF['qr_label'], 3.1, anchor='mm', medium=True)
    draw_text(d, (w / 2, 9.7 * PX), '海と、暮らしの便り。', 1.8, anchor='mm', fill=(110, 103, 89))
    qr = qr_image(CONF['qr_inside'], QR_CARD['qr'], rounded=True, logo=True)
    im.paste(qr, ((w - qr.width) // 2, int(12.3 * PX)))
    draw_text(d, (w / 2, 55.0 * PX), CONF['qr_note'], 2.4, anchor='mm', medium=True)
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

    # ---- P 面（内側）。そのまま x = gx
    x = gx
    page_p = flat(x / W, (L - y) / L)
    band = (y >= 105) & (y <= 192)
    page_p[band] = hexa(x / W, (L - y) / L)[band]
    u, v = to_uv(x, y)
    card = sampler(make_card())
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
    if (src / 'back.png').exists():
        art['back'] = Image.open(src / 'back.png')
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
    make_card().save(out / 'x_card.png')
    make_back().save(out / 'back_card.png')
    qr_image(CONF['qr_inside'], 40, rounded=True, logo=True).save(out / 'qr_x.png')
    qr_image(CONF['qr_source'], 21).save(out / 'qr_source.png')
    qr_image(CONF['qr_grow'], 25).save(out / 'qr_grow.png')
    # QR の読み取り確認：印刷面を 45 度起こして読む（300/150 dpi）
    detectors = [cv2.QRCodeDetector(), cv2.QRCodeDetectorAruco()]
    res = {}
    for key, page_img in (('inside', pp), ('outside', pq)):
        found = set()
        arr = np.asarray(page_img)[:, :, ::-1]
        for k in (1.0, 0.5):
            small = cv2.resize(arr, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
            h, w = small.shape[:2]
            for ang in (0, 45, -45):
                M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1.0)
                rot = cv2.warpAffine(small, M, (w, h), borderValue=(255, 255, 255))
                for det in detectors:
                    ok, dec, _, _ = det.detectAndDecodeMulti(rot)
                    if ok:
                        found |= {f'{int(300 * k)}dpi {d}' for d in dec if d}
        res[key] = sorted(found)
    expected = {'inside': [CONF['qr_inside']], 'outside': [CONF['qr_source'], CONF['qr_grow']]}
    for side, urls in expected.items():
        for dpi in (150, 300):
            for url in urls:
                if f'{dpi}dpi {url}' not in res[side]:
                    raise RuntimeError(f'QR preflight failed: {side} {dpi}dpi {url}')
    check = dict(cell_mm=round(CELL, 2), qr=res, quiet_zone_modules=QUIET,
                 decoders=['OpenCV QRCodeDetector', 'OpenCV QRCodeDetectorAruco'],
                 note='Union of decoder results at 0/45/-45 degrees. Physical phone scan is not simulated.')
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
        physical_validation='Previous layout was home-printed and accepted by the user; new QR and typography require another physical scan.')
    (out / 'preflight.json').write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + '\n')
    print(a.design, res)


if __name__ == '__main__':
    main()
