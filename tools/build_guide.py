"""Build the current uncut-A4 fold guide, not the retired windmill design."""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps
from a4fold import Sheet, state_hexagon, state_after3, state_strip, state_top_folded, state_closed
from a4fold_view import render
from build_a4 import DPI, PX, textures
from print_design import INK, PAPER, draw_text

ROOT = Path(__file__).resolve().parent.parent
STEPS = [
    ('内側を上に', ['印刷したA4を、内側の絵が上になるように置きます。', '紙は切りません。右上の赤い角印が向きの目印です。'], Sheet, 'xy'),
    ('四つの角を折る', ['四隅を斜めの折り線で内側へ折り込みます。', 'まず、六角形をつくります。'], state_hexagon, 'xy'),
    ('長い辺を一つ折る', ['右上の赤い角印の側の長い辺を、折り線で内側へ。', '図の形になるように折ります。'], state_after3, 'xy'),
    ('反対側の長い辺も折る', ['反対側も同じように内側へ。', '長い巻物の形になります。'], state_strip, 'uv'),
    ('種袋を入れて、上を折る', ['巻物を縦に持ち、中央へ種の小袋を置きます。', '上の四角を、折り線で手前に折ります。'], state_top_folded, 'uv'),
    ('舌を差し込む', ['下の舌を折り上げ、手前の折りの下へ差し込みます。', '舌のQRは、ふたを上げると最初に見えます。'], state_closed, 'uv'),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('design')
    args = parser.parse_args()
    out = ROOT / 'dist/a4' / args.design
    p, q = [Image.open(out / f'page_{side}.jpg').convert('RGB') for side in ('P', 'Q')]
    tp, tq = textures(p, q)
    width, height = round(210 * PX), round(297 * PX)
    page = Image.new('RGB', (width, height), PAPER)
    d = ImageDraw.Draw(page)
    draw_text(d, (15 * PX, 17 * PX), '岩美のたね｜折り方', 6.0, medium=True)
    draw_text(d, (15 * PX, 28 * PX), 'A4・両面長辺とじ・100%　／　切らない、のりを使わない。', 2.8)
    margin, gap, top = round(14 * PX), round(8 * PX), round(39 * PX)
    cw = (width - margin * 2 - gap) // 2
    ch = round(74 * PX)
    for i, (title, lines, state, kind) in enumerate(STEPS):
        x = margin + (i % 2) * (cw + gap)
        y = top + (i // 2) * (ch + gap)
        d.rounded_rectangle((x, y, x + cw, y + ch), radius=10, fill=(255, 253, 246))
        draw_text(d, (x + 4 * PX, y + 6 * PX), f'{i + 1:02d}  {title}', 3.3, medium=True)
        art = render(state(), tp, tq, kind=kind, scale=2.0, pad=10)
        art = ImageOps.contain(art.convert('RGB'), (cw - round(12 * PX), round(47 * PX)))
        page.paste(art, (x + (cw - art.width) // 2, y + round(12 * PX) + (round(47 * PX) - art.height) // 2))
        for j, line in enumerate(lines):
            draw_text(d, (x + 4 * PX, y + (62.0 + j * 4.5) * PX), line, 2.0)
    draw_text(d, (15 * PX, 289 * PX), '種は内袋に。画像は計算プレビューです。｜ SOCIAL CALCULUS · CC BY 4.0', 2.0)
    page.save(out / 'fold-guide.jpg', quality=90)
    page.save(out / 'fold-guide.pdf', resolution=DPI)
    print(out / 'fold-guide.pdf')


if __name__ == '__main__':
    main()
