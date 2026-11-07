"""Print-and-photo simulation for the art QR codes, offline.

  uv run python tools/scan_sim.py <design> [--trials 120]

Reads each code from dist/a4/<design>/ as printed (dot gain, darker ink), then
photographed (perspective, any rotation, resolution, uneven light, blur, noise,
JPEG). zxing-cpp is always used; zbar and the WeChat engine are added when the
environment has them. This compares designs. It is not a phone or paper test.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import cv2
import numpy as np
import zxingcpp

ROOT = Path(__file__).resolve().parent.parent
WECHAT_MODELS = Path('/var/cache/hap0py/wechat_qr')


def photograph(image, rng):
    a = np.asarray(image.convert('RGB'), np.float32)
    a = cv2.GaussianBlur(a, (0, 0), rng.uniform(0.5, 1.2))
    a = 255 * (a / 255) ** rng.uniform(1.0, 1.35) * rng.uniform(0.85, 1.0)
    h, w = a.shape[:2]
    pad = int(w * 0.25)
    table = np.array(rng.choice([(120, 150, 160), (225, 220, 205), (60, 80, 90)]), np.float32)
    canvas = np.ones((h + 2 * pad, w + 2 * pad, 3), np.float32) * table
    canvas[pad:pad + h, pad:pad + w] = a
    ch, cw = canvas.shape[:2]
    skew = rng.uniform(0.0, 0.16)
    src = np.float32([[0, 0], [cw, 0], [cw, ch], [0, ch]])
    dst = src + np.float32([[rng.uniform(-skew, skew) * cw, rng.uniform(-skew, skew) * ch] for _ in range(4)])
    warped = cv2.warpPerspective(canvas, cv2.getPerspectiveTransform(src, dst), (cw, ch), borderValue=(200, 200, 200))
    rot = cv2.getRotationMatrix2D((cw / 2, ch / 2), rng.uniform(0, 360), 1.0)
    warped = cv2.warpAffine(warped, rot, (cw, ch), borderValue=(200, 200, 200))
    size = rng.choice([420, 560, 760, 1000])
    small = cv2.resize(warped, (size, size), interpolation=cv2.INTER_AREA)
    small = small * np.linspace(rng.uniform(0.75, 1.1), rng.uniform(0.75, 1.1), size, dtype=np.float32)[None, :, None]
    small = cv2.GaussianBlur(small, (0, 0), rng.uniform(0.4, 1.6))
    small = small + np.random.default_rng(rng.randint(0, 10 ** 6)).normal(0, rng.uniform(2, 6), small.shape)
    small = np.clip(small, 0, 255).astype(np.uint8)
    _, jpeg = cv2.imencode('.jpg', small[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, rng.choice([50, 70, 85])])
    return cv2.imdecode(jpeg, cv2.IMREAD_COLOR)


def decoders():
    def zxing(bgr):
        return {r.text for r in zxingcpp.read_barcodes(bgr[:, :, ::-1])}
    found = {'zxing-cpp': zxing}
    try:
        from pyzbar.pyzbar import decode
        found['zbar'] = lambda bgr: {r.data.decode('utf8', 'ignore') for r in decode(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY))}
    except Exception:
        pass
    try:
        names = ['detect.prototxt', 'detect.caffemodel', 'sr.prototxt', 'sr.caffemodel']
        engine = cv2.wechat_qrcode_WeChatQRCode(*[str(WECHAT_MODELS / n) for n in names])
        found['wechat'] = lambda bgr: set(engine.detectAndDecode(bgr)[0])
    except Exception:
        pass
    classic = cv2.QRCodeDetector()

    def opencv(bgr):
        try:
            return {classic.detectAndDecode(bgr)[0]}
        except cv2.error:
            return set()
    found['opencv'] = opencv
    return found


def score(image, url, trials=120, seed=5):
    rng = random.Random(seed)
    readers = decoders()
    hits = dict.fromkeys(readers, 0)
    for _ in range(trials):
        shot = photograph(image, rng)
        for name, read in readers.items():
            if url in read(shot):
                hits[name] += 1
    return {name: round(100 * value / trials) for name, value in hits.items()}


def correction_left(url, version, error, knock, trials=24, step=2):
    """Random module flips still readable half the time, with and without the emblem.

    The emblem's modules are randomised, as a camera may read them either way.
    Returns (flips with emblem, flips without): what is left for dirt, creases and glare.
    """
    from print_design import qr_matrix
    matrix = qr_matrix(url, version, error)
    n = matrix.shape[0]
    free = np.ones((n, n), bool)
    free[:9, :9] = free[:9, n - 8:] = free[n - 8:, :9] = False
    free[6, :] = free[:, 6] = False
    rng = np.random.default_rng(3)

    def limit(blocked):
        pool = np.argwhere(free & ~blocked)
        last = 0
        for flips in range(0, 400, step):
            read = 0
            for _ in range(trials):
                m = matrix.copy()
                m[blocked] = rng.random(int(blocked.sum())) < 0.5
                pick = pool[rng.choice(len(pool), flips, replace=False)]
                m[pick[:, 0], pick[:, 1]] ^= True
                image = np.full(((n + 8) * 4, (n + 8) * 4), 255, np.uint8)
                image[16:16 + n * 4, 16:16 + n * 4] = np.kron(~m, np.ones((4, 4), bool)) * 255
                read += url in {r.text for r in zxingcpp.read_barcodes(image)}
            if read * 2 < trials:
                break
            last = flips
        return last
    return limit(knock), limit(np.zeros_like(knock))


def main():
    from PIL import Image
    from build_a4 import CONF, TONGUE_QR, X_QR, fit, pumpkin_icon, seal_icon, x_emblem
    from print_design import emblem_knock, qr_matrix
    parser = argparse.ArgumentParser()
    parser.add_argument('design')
    parser.add_argument('--trials', type=int, default=120)
    args = parser.parse_args()
    out = ROOT / 'dist/a4' / args.design
    tongue = Image.open(out / 'tongue_card.png')
    half = tongue.width // 2
    # カメラを向けるのは 1 コードずつなので、舌は左右に分けて撮る
    cases = {'x': (Image.open(out / 'x_card.png'), CONF['qr_inside']),
             'grow': (tongue.crop((0, 0, half, tongue.height)), CONF['qr_grow']),
             'source': (tongue.crop((half, 0, tongue.width, tongue.height)), CONF['qr_source'])}
    flat = fit(Image.open(ROOT / 'designs/a4' / args.design / 'flat.png').convert('RGB'), 'flat')
    icon = TONGUE_QR['emblem_modules'] * TONGUE_QR['mod']
    emblems = {'x': (X_QR, x_emblem(flat, X_QR['mod'])), 'grow': (TONGUE_QR, pumpkin_icon(icon)), 'source': (TONGUE_QR, seal_icon(icon))}
    report = {}
    for name, (image, url) in cases.items():
        cfg, emblem = emblems[name]
        n = qr_matrix(url, cfg['version'], cfg['error']).shape[0]
        knock = emblem_knock(emblem, n, cfg['mod'])
        left, whole = correction_left(url, cfg['version'], cfg['error'], knock)
        report[name] = dict(url=url, read_percent=score(image, url, args.trials), version=cfg['version'], error=cfg['error'],
                            module_mm=round(cfg['mod'] * 25.4 / 300, 2), blocked_percent=round(100 * float(knock.mean()), 1),
                            flips_left=left, flips_without_emblem=whole)
        print(name, report[name], flush=True)
    note = 'Simulated print and photo, aimed at one code at a time; compares designs. Not a phone or paper test.'
    (out / 'scan-sim.json').write_text(json.dumps(dict(trials=args.trials, note=note, codes=report), ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
