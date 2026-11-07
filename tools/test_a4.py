"""Offline regression tests: uv run python -m unittest discover -s tools -p 'test_*.py'."""
import re
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import cv2
import numpy as np
import zxingcpp
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from a4fold import CELL, U4, V6, state_closed, state_hexagon, area
from a4fold_view import render, state_flap_open
from build_a4 import (CONF, QR_CARD, RATIO, RED, TONGUE_H, TONGUE_QR, WASHI, X_QR, build_pages, corner_mark,
                      fit, make_back, make_card, make_tongue, pumpkin_icon, qr_alone, seal_icon, textures, x_emblem)
from print_design import FONTS, PAPER, QUIET, draw_text, emblem_knock, font, qr_alpha, qr_matrix, qr_side

ART = Path(__file__).resolve().parent.parent / 'designs/a4/uradome'


def load_art():
    return {k: fit(Image.open(ART / f'{k}.png').convert('RGB'), k) for k in RATIO}


def read(image):
    return {r.text for r in zxingcpp.read_barcodes(np.asarray(image.convert('RGB')))}


class PrintTests(unittest.TestCase):
    def test_font_families(self):
        self.assertEqual(font(3).getname()[0], 'IBM Plex Sans JP')
        self.assertEqual(font(3, latin=True).getname()[0], 'IBM Plex Sans')
        self.assertEqual(font(3, medium=True).getname()[1], 'Medium')
        canvas = Image.new('RGB', (800, 100), PAPER)
        draw_text(ImageDraw.Draw(canvas), (400, 50), '岩美町の中の人 / Big Max 3粒', 3, anchor='mm')
        self.assertNotEqual(np.asarray(canvas).min(), min(PAPER))

    def test_quiet_zones_and_each_code_alone(self):
        self.assertEqual(QUIET, 4)
        for key, cfg in (('qr_inside', X_QR), ('qr_source', TONGUE_QR), ('qr_grow', TONGUE_QR)):
            with self.subTest(key=key):
                a = np.asarray(qr_alone(key))
                q = QUIET * cfg['mod'] - 1
                for edge in (a[:q], a[-q:], a[:, :q], a[:, -q:]):
                    self.assertTrue(np.all(edge == WASHI))
                for k in (1, 0.5):
                    resized = cv2.resize(a, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
                    self.assertIn(CONF[key], read(Image.fromarray(resized)))

    def test_module_centres(self):
        """Liquid edges may move, but every module centre must stay on its correct side."""
        for key, cfg in (('qr_inside', X_QR), ('qr_source', TONGUE_QR), ('qr_grow', TONGUE_QR)):
            with self.subTest(key=key):
                matrix = qr_matrix(CONF[key], cfg['version'], cfg['error'])
                mod = cfg['mod']
                alpha = qr_alpha(matrix, mod)
                n = matrix.shape[0]
                centre = (QUIET * mod + mod // 2) + np.arange(n) * mod
                sampled = alpha[np.ix_(centre, centre)] > 0.5
                self.assertTrue(np.array_equal(sampled, matrix), int((sampled != matrix).sum()))

    def test_emblems_stay_within_error_correction(self):
        """Blocked modules must stay well inside what each error-correction level recovers."""
        cases = (('qr_inside', X_QR, x_emblem(load_art()['flat'], X_QR['mod']), 0.14),
                 ('qr_grow', TONGUE_QR, pumpkin_icon(TONGUE_QR['emblem_modules'] * TONGUE_QR['mod']), 0.05),
                 ('qr_source', TONGUE_QR, seal_icon(TONGUE_QR['emblem_modules'] * TONGUE_QR['mod']), 0.05))
        for key, cfg, emblem, limit in cases:
            with self.subTest(key=key):
                matrix = qr_matrix(CONF[key], cfg['version'], cfg['error'])
                blocked = emblem_knock(emblem, matrix.shape[0], cfg['mod']).mean()
                self.assertLess(blocked, limit)

    def test_face_codes_at_final_size(self):
        art = load_art()
        for image, expected in ((make_card(art['hexagon'], art['flat']), {CONF['qr_inside']}),
                                (make_tongue(art['hexagon']), {CONF['qr_source'], CONF['qr_grow']})):
            for k in (1, 0.5, 0.25):
                small = image.resize((int(image.width * k), int(image.height * k)), Image.LANCZOS)
                self.assertTrue(expected <= read(small), (k, read(small)))

    def test_back_label_is_only_the_label(self):
        """The back keeps no code at all; both moved to the tongue."""
        self.assertEqual(read(make_back()), set())
        self.assertEqual([k for k, _ in CONF['label']], ['名称', '内容量', '採種地', '採種', '注意', 'ひとこと'])
        self.assertNotIn('AI', repr(CONF))

    def test_tongue_codes_match(self):
        keys = [key for _, _, key in CONF['tongue']]
        self.assertEqual(sorted(keys), ['qr_grow', 'qr_source'])
        sides = {qr_side(CONF[k], TONGUE_QR['mod'], TONGUE_QR['version'], TONGUE_QR['error']) for k in keys}
        shapes = {qr_matrix(CONF[k], TONGUE_QR['version'], TONGUE_QR['error']).shape for k in keys}
        self.assertEqual(len(sides), 1)
        self.assertEqual(len(shapes), 1)
        # 2 コードの静区が舌の幅に収まる（300 dpi の px で比べる）
        self.assertLessEqual(2 * sides.pop(), CELL * (300 / 25.4))

    def test_tongue_upright_when_flap_is_lifted(self):
        """Fold a marked tongue with the real model and read which corner lands where."""
        art = load_art()
        marker = Image.new('RGB', (200, 160), (0, 0, 255))
        ImageDraw.Draw(marker).rectangle((0, 0, 99, 79), fill=(255, 0, 0))
        art['tongue'] = marker
        art['back'] = Image.new('RGB', (100, 100), (255, 255, 255))
        page_p, page_q = build_pages(art)
        tp, tq = textures(page_p, page_q)
        view = np.asarray(render(state_flap_open(), tp, tq, kind='uv', scale=4.0, pad=0, shadow=False))
        at = lambda u, v: view[int(v * 4.0), int(u * 4.0)]
        tip_v = 2 * V6 - 210
        # 正立なら、見た目の左上が目印の赤。右上と左下は青
        self.assertGreater(at(CELL * 0.25, tip_v + TONGUE_H * 0.25)[0], 200)
        self.assertGreater(at(CELL * 0.75, tip_v + TONGUE_H * 0.25)[2], 200)
        self.assertGreater(at(CELL * 0.25, tip_v + TONGUE_H * 0.75)[2], 200)

    def test_corner_mark_flush_on_inside_top_right(self):
        blank = np.zeros((400, 300, 3), np.float32)
        corner_mark(blank)
        h, w = blank.shape[:2]
        red = np.array(RED, np.float32)
        self.assertTrue(np.all(blank[0, w - 1] == red))
        self.assertTrue(np.all(blank[0, w - 2] == red))
        self.assertTrue(np.all(blank[1, w - 1] == red))
        self.assertTrue(np.all(blank[0, 0] == 0))
        self.assertTrue(np.all(blank[h - 1, w - 1] == 0))
        art = load_art()
        page_p, page_q = build_pages(art)
        inside, outside = np.asarray(page_p), np.asarray(page_q)
        self.assertTrue(np.all(inside[0, -1] == RED))
        self.assertTrue(np.all(inside[0, -8] == RED))
        self.assertFalse(np.all(inside[0, 0] == RED))
        self.assertFalse(np.all(outside[0, -1] == RED))
        self.assertFalse(np.all(outside[0, 0] == RED))

    def test_user_art_not_cropped(self):
        for name in RATIO:
            with Image.open(ART / f'{name}.png') as im:
                self.assertEqual(fit(im, name).size, im.size)

    def test_fold_model_unchanged(self):
        self.assertAlmostEqual(CELL, 74.246212, places=5)
        for state in (state_hexagon(), state_closed()):
            self.assertAlmostEqual(sum(area(layer.poly) for layer in state.layers), 210 * 297, places=4)
        self.assertEqual(QR_CARD['w'], 58)
        self.assertEqual(QR_CARD['h'], 58)


class SiteTests(unittest.TestCase):
    def test_local_links_and_fonts_exist(self):
        root = Path(__file__).resolve().parent.parent
        class Links(HTMLParser):
            def handle_starttag(self, tag, attrs):
                for name, value in attrs:
                    if name in ('href', 'src') and value:
                        parsed = urlsplit(value)
                        if not parsed.scheme and not parsed.netloc and parsed.path:
                            target = (root / unquote(parsed.path)).resolve()
                            if target.is_dir():
                                target /= 'index.html'
                            assert target.is_relative_to(root) and target.is_file(), str(target)
        for name in ('index.html', 'grow.html'):
            Links().feed((root / name).read_text())
        css = (root / 'site.css').read_text()
        for name in re.findall(r'url\("([^\"]+)"\)', css):
            self.assertTrue((root / name).is_file())
        self.assertIn('IBM Plex Sans JP', css)
        self.assertIn('IBM Plex Sans', css)

    def test_bigmax_ornamental_field_contract(self):
        root = Path(__file__).resolve().parent.parent
        text = (root / 'grow.html').read_text()
        for phrase in ('Big Max', '観賞用', '露地栽培', '一株一果', '25〜50', '人工授粉'):
            self.assertIn(phrase, text)
        self.assertIn(('注意', '食べられません'), CONF['label'])
        self.assertEqual(urlsplit(CONF['qr_grow']).path, '/tane-tsutsumi/grow.html')
        self.assertLessEqual(len((root / 'README.md').read_text().splitlines()), 40)


if __name__ == '__main__':
    unittest.main()
