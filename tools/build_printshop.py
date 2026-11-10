"""印刷所に出す入稿データ（ふちなし・塗り足し付き・CMYK）を作る。
  uv run python tools/build_printshop.py uradome --profile JapanColor2001Coated.icc

既定はプリントパックの Photoshop 入稿に合わせる：片面 1 ファイル、仕上がり A4 に塗り足し上下左右 3 mm（216×303 mm）、
350 ppi、CMYK（Japan Color 2001 Coated・相対的な色域を維持＋黒点の補正）、総インキ量 300% 以下、画像は 1 枚に統合した PSD。
両面とも画像の上が天。天と天を合わせる（縦型どうしの標準の合わせ方）と、長辺とじの A4 と同じ表裏になる。

出力 dist/a4/<デザイン名>/printshop/（大きいので Git には入れない）
  1_omote_uchigawa.psd  表＝内側（X の QR と右上の赤い角印がある面）
  2_ura_sotogawa.psd    裏＝外側（表示欄と舌の QR）
  <デザイン名>_printshop.zip  上の 2 つだけを入れた入稿用の圧縮ファイル
  proof_*.jpg           CMYK を画面の色に戻した確認用。マゼンタの点線が仕上がり線
  printshop.json        寸法・総インキ量・QR の読み取り・PSD の読み戻し
"""
from __future__ import annotations
import argparse, json, os, pathlib, struct, sys, zipfile
import numpy as np, cv2, zxingcpp
from PIL import Image, ImageCms, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from a4fold import W, L
from build_a4 import CONF, RATIO, Grid, build_pages, fit

DEFAULT_PROFILE = os.environ.get('TANE_CMYK_PROFILE', '/srv/data/kamihikoki/print/icc/JapanColor2001Coated.icc')
SIDES = (('1_omote_uchigawa', '表＝内側', [CONF['qr_inside']]),
         ('2_ura_sotogawa', '裏＝外側', [CONF['qr_source'], CONF['qr_grow']]))


def to_cmyk(rgb, profile):
    t = ImageCms.buildTransform(ImageCms.createProfile('sRGB'), profile, 'RGB', 'CMYK',
                                renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,
                                flags=ImageCms.Flags.BLACKPOINTCOMPENSATION)
    return np.asarray(ImageCms.applyTransform(rgb, t))


def proof(cmyk, profile):
    t = ImageCms.buildTransform(profile, ImageCms.createProfile('sRGB'), 'CMYK', 'RGB',
                                renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,
                                flags=ImageCms.Flags.BLACKPOINTCOMPENSATION)
    return ImageCms.applyTransform(Image.fromarray(cmyk, 'CMYK'), t)


def limit_ink(cmyk, tac):
    """総インキ量を tac（%）以下にする。まず C・M・Y の灰色分を K に置き換え（暗さを保つ）、足りなければ C・M・Y を縮める"""
    c = cmyk.astype(np.float32) / 255
    limit = tac / 100
    over = c.sum(2) > limit
    if over.any():
        s = c[over]
        r = np.minimum.reduce([(s.sum(1) - limit) / 2, s[:, :3].min(1), 1 - s[:, 3]])
        s[:, :3] -= r[:, None]
        s[:, 3] += r
        excess = s.sum(1) - limit
        cmy = s[:, :3].sum(1)
        k = np.where(excess > 0, np.clip((cmy - excess) / np.maximum(cmy, 1e-6), 0, 1), 1)
        s[:, :3] *= k[:, None]
        c[over] = s
    out = np.floor(c * 255 + 0.5)
    out[over] = np.floor(c[over] * 255)  # 丸めで上限を越えないよう、削った画素は切り捨て
    return out.astype(np.uint8), int(over.sum())


def write_psd(path, cmyk, dpi, icc):
    """レイヤーのない（統合済みの）CMYK 8 bit PSD。解像度と ICC を埋め込む。PSD の CMYK は 0 が版いっぱいの反転値"""
    h, w, _ = cmyk.shape

    def resource(rid, data):
        block = b'8BIM' + struct.pack('>H', rid) + b'\0\0' + struct.pack('>I', len(data)) + data
        return block + (b'\0' if len(data) % 2 else b'')
    fixed = int(round(dpi * 65536))
    res = resource(0x03ED, struct.pack('>IHHIHH', fixed, 1, 2, fixed, 1, 2)) + resource(0x040F, icc)
    with open(path, 'wb') as f:
        f.write(b'8BPS' + struct.pack('>H6xHIIHH', 1, 4, h, w, 8, 4))
        f.write(struct.pack('>I', 0))
        f.write(struct.pack('>I', len(res)) + res)
        f.write(struct.pack('>I', 0))
        f.write(struct.pack('>H', 0))
        for ch in range(4):
            f.write(np.ascontiguousarray(255 - cmyk[:, :, ch]).tobytes())


def trim_box(g):
    x0, y0 = g.bleed * g.px, g.bleed * g.px
    return x0, y0, x0 + W * g.px, y0 + L * g.px


def read_qr(img, g):
    """仕上がりの内側を 300・150 dpi 相当に縮め、0・±45 度で読む"""
    x0, y0, x1, y1 = (int(round(v)) for v in trim_box(g))
    arr = np.asarray(img.convert('RGB'))[y0:y1, x0:x1]
    found = set()
    for dpi in (300, 150):
        k = dpi / (g.px * 25.4)
        small = cv2.resize(arr, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
        h, w = small.shape[:2]
        for ang in (0, 45, -45):
            rot = cv2.warpAffine(small, cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1.0), (w, h), borderValue=(255, 255, 255))
            found |= {(dpi, r.text) for r in zxingcpp.read_barcodes(rot) if r.text}
    return found


def mark_trim(img, g):
    im = img.copy(); d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = trim_box(g)
    dash = int(3 * g.px)
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) // dash)
        for i in range(0, n, 2):
            p = (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)
            q = (a[0] + (b[0] - a[0]) * (i + 1) / n, a[1] + (b[1] - a[1]) * (i + 1) / n)
            d.line([p, q], fill=(230, 0, 126), width=3)
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('design')
    ap.add_argument('--profile', default=DEFAULT_PROFILE, help='CMYK の ICC（Japan Color 2001 Coated）')
    ap.add_argument('--dpi', type=float, default=350)
    ap.add_argument('--bleed', type=float, default=3.0)
    ap.add_argument('--tac', type=float, default=300)
    a = ap.parse_args()
    icc = pathlib.Path(a.profile).read_bytes()
    profile = ImageCms.ImageCmsProfile(pathlib.Path(a.profile).open('rb'))
    src = ROOT / 'designs/a4' / a.design
    art = {k: fit(Image.open(src / f'{k}.png').convert('RGB'), k) for k in RATIO}
    out = ROOT / 'dist/a4' / a.design / 'printshop'
    out.mkdir(parents=True, exist_ok=True)
    g = Grid(a.dpi, a.bleed)
    pages = build_pages(art, dpi=a.dpi, bleed=a.bleed)
    report = dict(design=a.design, profile=pathlib.Path(a.profile).name,
                  intent='relative colorimetric + black point compensation', dpi=a.dpi, bleed_mm=a.bleed,
                  pixels=[g.w, g.h], size_mm=[round(g.w / g.px, 2), round(g.h / g.px, 2)],
                  trim_mm=[W, L], orientation='両面とも画像の上が天。天と天を合わせる（縦型・長辺とじと同じ表裏）', sides={})
    for (name, label, urls), rgb in zip(SIDES, pages):
        cmyk, limited = limit_ink(to_cmyk(rgb, profile), a.tac)
        psd = out / f'{name}.psd'
        write_psd(psd, cmyk, a.dpi, icc)
        back = Image.open(psd)
        assert back.mode == 'CMYK' and back.size == (g.w, g.h) and np.array_equal(np.asarray(back), cmyk), psd
        soft = proof(cmyk, profile)
        mark_trim(soft, g).resize((g.w // 3, g.h // 3), Image.LANCZOS).save(out / f'proof_{name}.jpg', quality=88)
        found = read_qr(soft, g)
        missing = [f'{dpi}dpi {u}' for u in urls for dpi in (300, 150) if (dpi, u) not in found]
        if missing:
            raise RuntimeError(f'QR not read on {name}: {missing}')
        tac = cmyk.astype(np.int32).sum(2)
        report['sides'][name] = dict(label=label, file=psd.name, bytes=psd.stat().st_size,
                                     tac_max_percent=round(float(tac.max()) / 255 * 100, 1),
                                     pixels_ink_limited=limited, qr=sorted(f'{d}dpi {t}' for d, t in found))
        assert tac.max() <= a.tac / 100 * 255, (name, tac.max())
    zpath = out / f'{a.design}_printshop.zip'
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, _, _ in SIDES:
            z.write(out / f'{name}.psd', f'{name}.psd')
    report['zip'] = dict(file=zpath.name, bytes=zpath.stat().st_size)
    (out / 'printshop.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
