"""既定デザインの印刷用 PDF と確認画像を作る:

  uv run --no-project --with pillow --with playwright --with numpy --with opencv-python-headless python tools/build.py

1. designs/art/*.png を印刷向けの JPEG にする
2. index.html?all=1 を A4 PDF にする（3 デザイン × 両面 = 6 ページ）
3. 裏面を実際の折り方どおりに切り貼りして「閉じた姿」を作り、絵が 1 枚に戻るか確かめる
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
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
ART = ROOT / "designs" / "art"
DIST = ROOT / "dist"
SHOTS = ROOT / "shots"
BRAVE = os.environ.get("CHROME_PATH", "/usr/bin/brave-browser")
ARGS = ["--no-sandbox", "--allow-file-access-from-files"]
MM = 8  # 確認画像の解像度（px/mm）
DESIGNS = ["kani", "umi", "eki"]
OFF = 6  # 紙の左右と上から切り落とす幅（mm）


def jpegs():
    for p in sorted(ART.glob("*.png")):
        out = p.with_suffix(".jpg")
        if out.exists() and out.stat().st_mtime >= p.stat().st_mtime:
            continue
        Image.open(p).convert("RGB").save(out, quality=88, optimize=True)


def virtual_fold(sheet: np.ndarray, S_mm=198) -> np.ndarray:
    """裏面の画像を、紙を四隅から折ったときの見え方に組み立て直す（版の計算とは別に、紙の動きだけで計算）。"""
    s = int(S_mm * MM)
    off = OFF * MM
    d = int(s / math.sqrt(2))
    out = np.full((d, d, 3), 255, np.uint8)
    c = math.sqrt(0.5)
    for v in range(d):
        for u in range(d):
            du, dv = u - d / 2, v - d / 2
            # 閉じた姿の点 → 広げた紙の上の位置（表から見た座標）
            x, y = s / 2 + (du + dv) * c, s / 2 + (dv - du) * c
            # 中心を挟む折り目で鏡映：その点に重なっている三角の、元の位置
            if v < u and u + v < d:  # 上
                qx, qy = s / 2 - y, s / 2 - x
            elif v < u:  # 右
                qx, qy = y + s / 2, x - s / 2
            elif u + v >= d:  # 下
                qx, qy = 3 * s / 2 - y, 3 * s / 2 - x
            else:  # 左
                qx, qy = y - s / 2, x + s / 2
            # 裏面は長辺とじで左右反転
            bx, by = int(off + s - qx), int(off + qy)
            if 0 <= bx < sheet.shape[1] and 0 <= by < sheet.shape[0]:
                out[v, u] = sheet[by, bx]
    return out


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
            print("pdf", pdf, pdf.stat().st_size)
            # 面ごとの画像（確認用）
            sheet = b.new_context(viewport={"width": 794, "height": 1123}, device_scale_factor=MM * 25.4 / 96)
            p2 = sheet.new_page()
            p2.goto(f"http://127.0.0.1:{port}/index.html?all=1", wait_until="load")
            p2.wait_for_function("() => window.TANE_READY === true")
            p2.emulate_media(media="print")
            p2.wait_for_timeout(800)
            svgs = p2.locator("#print svg")
            n = svgs.count()
            print("pages", n)
            ok = n == 6
            det = cv2.QRCodeDetector()
            for i, name in enumerate(DESIGNS):
                inside_png = SHOTS / f"{name}_inside.png"
                outside_png = SHOTS / f"{name}_outside.png"
                svgs.nth(i * 2).screenshot(path=str(inside_png))
                svgs.nth(i * 2 + 1).screenshot(path=str(outside_png))
                ins = cv2.imread(str(inside_png))
                out = cv2.imread(str(outside_png))
                closed = virtual_fold(out)
                cv2.imwrite(str(SHOTS / f"{name}_closed.jpg"), closed)
                # 内側の QR：紙を 45° 回して読む
                h, w = ins.shape[:2]
                m = cv2.getRotationMatrix2D((105 * MM, 105 * MM), -45, 1)
                rot = cv2.warpAffine(ins, m, (w, h), borderValue=(255, 255, 255))
                inner, _, _ = det.detectAndDecode(rot)
                # 裏の QR：背面を読む
                m2 = cv2.getRotationMatrix2D((105 * MM, 105 * MM), 45, 1)
                rot2 = cv2.warpAffine(out, m2, (w, h), borderValue=(255, 255, 255))
                cv2.imwrite(str(SHOTS / f"{name}_back.jpg"), rot2[int(105 * MM - 75 * MM) : int(105 * MM + 75 * MM), int(105 * MM - 75 * MM) : int(105 * MM + 75 * MM)])
                back, _, _ = det.detectAndDecode(rot2[int(105 * MM - 75 * MM) : int(105 * MM + 75 * MM), int(105 * MM - 75 * MM) : int(105 * MM + 75 * MM)])
                print(name, "inner QR:", inner, "| back QR:", back)
                ok = ok and inner == "https://x.com/iwami_kankou" and back == "https://github.com/social-calculus/tane-tsutsumi"
            print("errors", errors[:5])
            b.close()
        srv.shutdown()
    print("PASS" if ok and not errors else "FAIL")
    raise SystemExit(0 if ok and not errors else 1)


if __name__ == "__main__":
    main()
