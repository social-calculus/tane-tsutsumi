"""designs/art を一覧 1 枚にまとめて確かめる。

  uv run --with pillow python tools/contact_sheet.py 保存先.jpg [元フォルダ]
"""
import pathlib
import sys

from PIL import Image, ImageDraw

out = pathlib.Path(sys.argv[1])
src = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path(__file__).resolve().parent.parent / "designs" / "art"
files = sorted(p for p in src.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
cell = 300
cols = 5
rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (cols * cell, rows * cell), "white")
for i, p in enumerate(files):
    im = Image.open(p).convert("RGB")
    size = im.size
    im.thumbnail((cell, cell))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 170, 14), fill="white")
    d.text((2, 1), f"{p.stem} {size[0]}x{size[1]}", fill="black")
    sheet.paste(im, ((i % cols) * cell, (i // cols) * cell))
sheet.save(out, quality=85)
print(out, sheet.size)
