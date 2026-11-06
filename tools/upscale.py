"""内側の大きな絵（1024px を 28cm に広げるので粗い）を 2 倍にする。

  uv run --no-project --with opencv-contrib-python-headless python tools/upscale.py モデル.pb

モデルは FSRCNN_x2.pb（https://github.com/Saafke/FSRCNN_Tensorflow）。CPU で数秒。出力は designs/art/*_inside_2x.png。
"""
import pathlib
import sys
import time

import cv2

ART = pathlib.Path(__file__).resolve().parent.parent / "designs" / "art"
sr = cv2.dnn_superres.DnnSuperResImpl_create()
sr.readModel(sys.argv[1])
sr.setModel("fsrcnn", 2)
for p in sorted(ART.glob("*_inside.png")):
    t = time.time()
    big = sr.upsample(cv2.imread(str(p)))
    cv2.imwrite(str(p.with_name(p.stem + "_2x.png")), big)
    print(p.name, big.shape, f"{time.time() - t:.0f}s", flush=True)
