"""既定デザインの印刷用 PDF と確認画像を作る:

  uv run --no-project --with pillow --with playwright --with numpy --with opencv-python-headless python tools/build.py

1. designs/art の絵を印刷向けの JPEG にする
2. index.html?all=1 を A4 PDF にする（3 デザイン × 両面 = 6 ページ）
3. 印刷面の画像を、紙の動きどおりに折ったときの見え方に組み直す（版の計算とは別に確かめる）
   折り工程の図を作り、閉じた姿に穴がないこと、内側の面が外へ出ないことを確かめる
4. 内側と裏の QR を読めるか確かめる
"""
import http.server
import math
import os
import pathlib
import socketserver
import threading
from functools import partial

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
ART = ROOT / "designs" / "art"
DIST = ROOT / "dist"
SHOTS = ROOT / "shots"
BRAVE = os.environ.get("CHROME_PATH", "/usr/bin/brave-browser")
FONT = os.environ.get("CJK_FONT", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
ARGS = ["--no-sandbox", "--allow-file-access-from-files"]
MM = 8  # 確認画像の解像度（px/mm）
DESIGNS = ["umi", "kani", "eki"]
OFF = 6  # 紙の左右と上から切り落とす幅（mm）
S = 198  # 切り上がりの一辺
R = S / math.sqrt(2)  # 紙の中心から角まで
H = 55  # 折り上がりの半分（中央の四角の半分）
C = math.sqrt(0.5)
HOLE = np.array([255, 0, 255], np.uint8)  # 紙がないはずの所に塗る色（穴の検出）
STEPS = ["① 種の袋を真ん中へ", "② 下の角を折る", "③ 右の角を折る", "③ 左の角を折る", "④ 上の角を折り、先を差し込む"]


def jpegs():
    for p in sorted(ART.glob("*.png")):
        name = p.stem
        if name.endswith("_inside"):
            continue
        out = ART / (name.removesuffix("_2x") + ".jpg")
        Image.open(p).convert("RGB").save(out, quality=88, optimize=True)


def sample(page: np.ndarray, u: np.ndarray, v: np.ndarray, back: bool) -> np.ndarray:
    """紙の座標 (u,v) の色を印刷面の画像から取る。裏面は長辺とじで左右反転"""
    x = S / 2 + (u + v) * C
    y = S / 2 + (v - u) * C
    if back:
        x = S - x
    ix = np.clip(((x + OFF) * MM).astype(int), 0, page.shape[1] - 1)
    iy = np.clip(((y + OFF) * MM).astype(int), 0, page.shape[0] - 1)
    return page[iy, ix]


def on_paper(u, v):
    return np.abs(u) + np.abs(v) <= R


def fold_view(a: np.ndarray, b: np.ndarray, step: int, px_mm: float = 3.0):
    """手順 step（0〜4）まで折った姿を上から見る。紙の動きだけで計算し、見える面を貼り合わせる"""
    half = R + 5
    n = int(2 * half * px_mm)
    axis = np.linspace(-half, half, n)
    U, V = np.meshgrid(axis, axis)
    out = np.full((n, n, 3), 238, np.uint8)
    covered = np.zeros((n, n), bool)

    def paint(mask, u, v, back):
        out[mask] = sample(b if back else a, u[mask], v[mask], back)
        covered[mask] = True

    # 土台：まだ折っていない部分（内側の面が見える）
    base = on_paper(U, V)
    if step >= 1:
        base &= V <= H
    if step >= 2:
        base &= U <= H
    if step >= 3:
        base &= U >= -H
    if step >= 4:
        base &= V >= -H
    paint(base, U, V, False)
    # 下の角：折り返すと裏面が見える
    if step >= 1:
        u, v = U, 2 * H - V
        mask = (V <= H) & (v > H) & on_paper(u, v)
        if step >= 2:
            mask &= U <= H
        if step >= 3:
            mask &= U >= -H
        paint(mask, u, v, True)
    # 上の角：左右の下へ差し込むので、左右より先に塗る
    if step >= 4:
        u, v = U, -2 * H - V
        paint((V >= -H) & (v < -H) & on_paper(u, v) & (np.abs(u) <= H), u, v, True)
    # 右の角
    if step >= 2:
        u, v = 2 * H - U, V
        mask = (U <= H) & (u > H) & on_paper(u, v) & (v <= H)
        if step >= 4:
            mask &= v >= -H
        paint(mask, u, v, True)
    # 左の角（右の上に重なる）
    if step >= 3:
        u, v = -2 * H - U, V
        mask = (U >= -H) & (u < -H) & on_paper(u, v) & (v <= H)
        if step >= 4:
            mask &= v >= -H
        paint(mask, u, v, True)
    return out, covered, U, V


def closed_holes(a, b) -> int:
    """閉じた姿の四角の中で、紙に覆われていない所の面積（px）"""
    _, covered, U, V = fold_view(a, b, 4)
    inner = (np.abs(U) < H - 0.5) & (np.abs(V) < H - 0.5)
    return int((inner & ~covered).sum())


def step_sheet(a, b, path):
    """折り工程の図（横一列）"""
    panels = [cv2.cvtColor(fold_view(a, b, s)[0], cv2.COLOR_BGR2RGB) for s in range(5)]
    size = 360
    sheet = Image.new("RGB", (size * 5 + 60, size + 64), (247, 241, 228))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(FONT, 19)
    for i, p in enumerate(panels):
        im = Image.fromarray(p).resize((size, size), Image.LANCZOS)
        sheet.paste(im, (10 + i * (size + 10), 10))
        d.text((16 + i * (size + 10), size + 22), STEPS[i], font=font, fill=(44, 38, 32))
    sheet.save(path, quality=88)


def main():
    jpegs()
    DIST.mkdir(exist_ok=True)
    SHOTS.mkdir(exist_ok=True)
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as srv:
        port = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        with sync_playwright() as pw:
            b = pw.chromium.launch(executable_path=BRAVE, headless=True, args=ARGS)
            ctx = b.new_context(viewport={"width": 1400, "height": 1000})
            page = ctx.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("requestfailed", lambda r: errors.append("failed " + r.url) if "fonts.g" not in r.url else None)
            page.goto(f"http://127.0.0.1:{port}/index.html?all=1", wait_until="load")
            page.wait_for_function("() => window.TANE_READY === true")
            page.wait_for_timeout(1500)
            page.screenshot(path=str(SHOTS / "tool.png"))
            pdf = DIST / "tane-tsutsumi_iwami_a4.pdf"
            page.emulate_media(media="print")
            page.pdf(path=str(pdf), prefer_css_page_size=True, print_background=True)
            print("pdf", pdf.name, pdf.stat().st_size)
            # 面ごとの画像（確認用）
            sheet = b.new_context(viewport={"width": 794, "height": 1123}, device_scale_factor=MM * 25.4 / 96)
            p2 = sheet.new_page()
            p2.goto(f"http://127.0.0.1:{port}/index.html?all=1", wait_until="load")
            p2.wait_for_function("() => window.TANE_READY === true")
            p2.emulate_media(media="print")
            p2.wait_for_timeout(1200)
            svgs = p2.locator("#print svg")
            n = svgs.count()
            print("pages", n)
            ok = n == 6
            det = cv2.QRCodeDetector()
            centre = 105 * MM
            for i, name in enumerate(DESIGNS):
                inside_png = SHOTS / f"{name}_inside.png"
                outside_png = SHOTS / f"{name}_outside.png"
                svgs.nth(i * 2).screenshot(path=str(inside_png))
                svgs.nth(i * 2 + 1).screenshot(path=str(outside_png))
                ins = cv2.imread(str(inside_png))
                out = cv2.imread(str(outside_png))
                # 閉じた姿と開いた姿
                closed, _, _, _ = fold_view(ins, out, 4, px_mm=MM)
                mid = closed.shape[0] // 2
                span = int(H * MM)
                closed_crop = closed[mid - span : mid + span, mid - span : mid + span]
                cv2.imwrite(str(SHOTS / f"{name}_closed.jpg"), closed_crop)
                opened, _, _, _ = fold_view(ins, out, 0, px_mm=4)
                cv2.imwrite(str(SHOTS / f"{name}_open.jpg"), opened)
                holes = closed_holes(ins, out)
                step_sheet(ins, out, SHOTS / f"{name}_steps.jpg")
                # 内側の QR：紙を 45° 回して読む
                h, w = ins.shape[:2]
                rot = cv2.warpAffine(ins, cv2.getRotationMatrix2D((centre, centre), -45, 1), (w, h), borderValue=(255, 255, 255))
                inner, _, _ = det.detectAndDecode(rot[centre - 60 * MM : centre + 60 * MM, centre - 60 * MM : centre + 60 * MM])
                # 裏の QR：背面を読む
                rot2 = cv2.warpAffine(out, cv2.getRotationMatrix2D((centre, centre), 45, 1), (w, h), borderValue=(255, 255, 255))
                back_crop = rot2[centre - 56 * MM : centre + 56 * MM, centre - 56 * MM : centre + 56 * MM]
                cv2.imwrite(str(SHOTS / f"{name}_back.jpg"), back_crop)
                back, _, _ = det.detectAndDecode(back_crop)
                print(name, "| 穴(px):", holes, "| inner QR:", inner, "| back QR:", back)
                ok = ok and holes == 0 and inner == "https://x.com/iwami_kankou" and back == "https://github.com/social-calculus/tane-tsutsumi"
            print("errors", errors[:5])
            b.close()
        srv.shutdown()
    # README 用の折り工程の図
    Image.open(SHOTS / "umi_steps.jpg").save(DIST / "fold_steps.jpg", quality=86)
    print("PASS" if ok and not errors else "FAIL")
    raise SystemExit(0 if ok and not errors else 1)


if __name__ == "__main__":
    main()
