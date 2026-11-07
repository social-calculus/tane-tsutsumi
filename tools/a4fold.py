"""A4 一枚折りの計算モデル（本人の折り方、2026-11-06 の写真 IMG_0809〜0822 から）。

座標は mm。紙の座標 (x, y)：A4 縦置き、左下が原点、y は上向き。面は 2 つ：
  P 面 … 内側。種の下に QR が来る面。最初に上を向いている面。
  Q 面 … 外側。折り上がりの正面・裏面がある面。

折り順（すべて P 面の側へ山なしの谷折り）：
  1. 長辺どうしを合わせて中心線 x=105 をつける（目印だけ）
  2. 四隅を中心線へ（短辺の半分が中心線に重なる）→ 六角形
  3. 星の辺を二つ折り：線 x+y=297 で右上側を手前へ
  4. 3 の縁に沿って：線 x+y=192 で左下側を手前へ（3 の上に重なる）→ 長条 74.2×210
  5. 黒点を通る線で上側を手前へ → 上の面が正面になる
  6. 残りの尾（舌）を上へ返し、正面の下へ差し込む → 74.2 mm 角

写真が斜めに見えるのは折り線が A4 の辺と 45 度だから。U, V は長条をまっすぐ立てた向きの座標：
  U = (x + y - 105) / √2   左→右（0〜210）
  V = (x - y + 192) / √2   上→下（0〜210）
"""
from __future__ import annotations
import math
import numpy as np

W, L = 210.0, 297.0
RT2 = math.sqrt(2)

# 折り線（紙の座標で a*x + b*y = c）
CREASES = {
    '2TL': (-1, 1, 192.0),   # y - x = 192
    '2TR': (1, 1, 402.0),    # x + y = 402
    '2BL': (1, 1, 105.0),    # x + y = 105
    '2BR': (1, -1, 105.0),   # x - y = 105
    '3': (1, 1, 297.0),      # x + y = 297
    '4': (1, 1, 192.0),      # x + y = 192
}
U3 = (297 - 105) / RT2       # 135.76
U4 = (192 - 105) / RT2       # 61.52
CELL = (U3 - U4)             # 74.25：長条の幅
V5 = CELL                    # 74.25：黒点を通る線
V6 = 2 * CELL                # 148.49：舌を返す線


def to_uv(x, y):
    return (x + y - 105) / RT2, (x - y + 192) / RT2


def from_uv(u, v):
    a = u * RT2 + 105   # x + y
    b = v * RT2 - 192   # x - y
    return (a + b) / 2, (a - b) / 2


def clip(poly, a, b, c, keep_ge=True):
    """凸多角形を半平面 a*x+b*y>=c（または <=）で切る"""
    out = []
    n = len(poly)
    s = 1 if keep_ge else -1
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        dp = s * (a * p[0] + b * p[1] - c)
        dq = s * (a * q[0] + b * q[1] - c)
        if dp >= -1e-9:
            out.append(p)
        if (dp > 1e-9 and dq < -1e-9) or (dp < -1e-9 and dq > 1e-9):
            t = dp / (dp - dq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def area(poly):
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))) / 2


def reflect_matrix(a, b, c):
    """直線 a*x+b*y=c についての鏡映（3x3）"""
    n = a * a + b * b
    return np.array([
        [1 - 2 * a * a / n, -2 * a * b / n, 2 * a * c / n],
        [-2 * a * b / n, 1 - 2 * b * b / n, 2 * b * c / n],
        [0, 0, 1],
    ])


class Layer:
    __slots__ = ('poly', 'm', 'flips', 'tag')

    def __init__(self, poly, m=None, flips=0, tag=''):
        self.poly, self.m, self.flips, self.tag = poly, (np.eye(3) if m is None else m), flips, tag

    def world(self):
        p = np.array([[x, y, 1.0] for x, y in self.poly]).T
        q = self.m @ p
        return [(q[0, i], q[1, i]) for i in range(q.shape[1])]

    def side(self):
        return 'P' if self.flips % 2 == 0 else 'Q'


class Sheet:
    """重なりを下から順に持つ。単純折りは片側を裏返して一番上へ積む。世界座標は紙と同じ向き。"""

    def __init__(self):
        self.layers = [Layer([(0, 0), (W, 0), (W, L), (0, L)])]

    def clone(self):
        s = Sheet.__new__(Sheet)
        s.layers = [Layer(list(l.poly), l.m.copy(), l.flips, l.tag) for l in self.layers]
        return s

    def fold(self, a, b, c, moving_ge=True, tag=''):
        """世界座標の線で折る。moving_ge なら a*x+b*y>=c の側を手前へ返す"""
        stay, move = [], []
        R = reflect_matrix(a, b, c)
        for l in self.layers:
            inv = np.linalg.inv(l.m)
            # 世界座標の線を紙の座標へ戻して切る
            na = a * l.m[0, 0] + b * l.m[1, 0]
            nb = a * l.m[0, 1] + b * l.m[1, 1]
            nc = c - a * l.m[0, 2] - b * l.m[1, 2]
            front = clip(l.poly, na, nb, nc, keep_ge=moving_ge)
            back = clip(l.poly, na, nb, nc, keep_ge=not moving_ge)
            if len(back) >= 3 and area(back) > 1e-6:
                stay.append(Layer(back, l.m.copy(), l.flips, l.tag))
            if len(front) >= 3 and area(front) > 1e-6:
                move.append(Layer(front, R @ l.m, l.flips + 1, tag or l.tag))
        self.layers = stay + list(reversed(move))
        return self


def state_flat():
    return Sheet()


def state_hexagon():
    s = Sheet()
    s.fold(-1, 1, 192, True, 'TL')    # 左上の隅
    s.fold(1, 1, 402, True, 'TR')     # 右上の隅
    s.fold(1, 1, 105, False, 'BL')    # 左下の隅
    s.fold(1, -1, 105, True, 'BR')    # 右下の隅
    return s


def state_after3():
    return state_hexagon().fold(1, 1, 297, True)


def state_after4_only():
    """3 を開いて 4 だけ折った形（写真 0815・0816）"""
    return state_hexagon().fold(1, 1, 192, False)


def state_strip():
    """3 と 4 を折った長条（写真 0820）"""
    return state_after3().fold(1, 1, 192, False)


def uv_line(a_u, a_v, c):
    """U,V での直線 a_u*U + a_v*V = c を紙の座標の a,b,c へ"""
    a = (a_u + a_v) / RT2
    b = (a_u - a_v) / RT2
    return a, b, c + a_u * 105 / RT2 - a_v * 192 / RT2


def state_top_folded():
    """5 を折った形。舌はまだ下に出ている（写真 0821）"""
    a, b, c = uv_line(0, 1, V5)
    return state_strip().fold(a, b, c, False)


def state_closed():
    """6 まで。舌は正面の層の下へ入る。舌を裏返してから、上の面（正面）より下へ積み直す"""
    s = state_top_folded()
    a, b, c = uv_line(0, 1, V6)
    stay, move = [], []
    R = reflect_matrix(a, b, c)
    top_part = []
    for l in s.layers:
        na = a * l.m[0, 0] + b * l.m[1, 0]
        nb = a * l.m[0, 1] + b * l.m[1, 1]
        nc = c - a * l.m[0, 2] - b * l.m[1, 2]
        f = clip(l.poly, na, nb, nc, keep_ge=True)
        bk = clip(l.poly, na, nb, nc, keep_ge=False)
        if len(bk) >= 3 and area(bk) > 1e-6:
            stay.append(Layer(bk, l.m.copy(), l.flips, l.tag))
        if len(f) >= 3 and area(f) > 1e-6:
            move.append(Layer(f, R @ l.m, l.flips + 1, l.tag))
    # 5 で手前へ返した層（flips が増えたもの）は stay の後半にある。その直前へ舌を入れる
    n_mid = len(state_strip().fold(a, b, c, False).layers)  # 目安用（未使用）
    mid, upper = [], []
    a5, b5, c5 = uv_line(0, 1, V5)
    for l in stay:
        pts = l.world()
        vs = [to_uv(px, py)[1] for px, py in pts]
        src = np.array([[x, y, 1.0] for x, y in l.poly]).T
        # 紙の上の位置で判定：V<V5 の部分が 5 で返された層
        pv = [to_uv(px, py)[1] for px, py in l.poly]
        (upper if max(pv) <= V5 + 1e-6 else mid).append(l)
    s.layers = mid + list(reversed(move)) + upper
    return s


def world_uv_polygon(layer):
    return [to_uv(px, py) for px, py in layer.world()]
