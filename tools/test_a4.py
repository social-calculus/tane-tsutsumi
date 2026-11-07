"""Offline regression tests: uv run python -m unittest discover -s tools -p 'test_*.py'."""
import re
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import cv2
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from a4fold import CELL, state_closed, state_hexagon, area
from build_a4 import CONF, QR_CARD, RATIO, fit, make_back, make_card
from print_design import FONTS, PAPER, QUIET, draw_text, font, qr_image


class PrintTests(unittest.TestCase):
    def test_font_families(self):
        self.assertEqual(font(3).getname()[0], 'IBM Plex Sans JP')
        self.assertEqual(font(3, latin=True).getname()[0], 'IBM Plex Sans')
        self.assertEqual(font(3, medium=True).getname()[1], 'Medium')
        canvas = Image.new('RGB', (800, 100), PAPER)
        draw_text(ImageDraw.Draw(canvas), (400, 50), '岩美町の中の人 / Big Max 3粒', 3, anchor='mm')
        self.assertNotEqual(np.asarray(canvas).min(), min(PAPER))

    def test_quiet_zones_and_styled_codes(self):
        cases = [('qr_inside', 40, True, True), ('qr_source', 21, False, False), ('qr_grow', 25, False, False)]
        detector = cv2.QRCodeDetector()
        for key, size, rounded, logo in cases:
            with self.subTest(key=key):
                im = qr_image(CONF[key], size, rounded=rounded, logo=logo)
                a = np.asarray(im)
                self.assertTrue(np.all(a[0] == PAPER))
                self.assertTrue(np.all(a[-1] == PAPER))
                self.assertTrue(np.all(a[:, 0] == PAPER))
                self.assertTrue(np.all(a[:, -1] == PAPER))
                for k in (1, 0.5):
                    resized = cv2.resize(a, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
                    self.assertEqual(detector.detectAndDecode(resized)[0], CONF[key])
        self.assertEqual(QUIET, 4)

    def test_face_codes_at_final_size(self):
        # Aruco multi-code detection handles two adjacent utility codes;
        # the classic decoder is tested independently on each code above.
        detector = cv2.QRCodeDetectorAruco()
        for image, expected in ((make_card(), {CONF['qr_inside']}),
                                (make_back(), {CONF['qr_source'], CONF['qr_grow']})):
            for k in (1, 0.5):
                a = cv2.resize(np.asarray(image), None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
                ok, decoded, _, _ = detector.detectAndDecodeMulti(a)
                self.assertTrue(ok)
                self.assertTrue(expected.issubset(set(decoded)), (k, decoded))

    def test_user_art_not_cropped(self):
        source = Path(__file__).resolve().parent.parent / 'designs/a4/uradome'
        for name in RATIO:
            with Image.open(source / f'{name}.png') as im:
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
        self.assertIn(('品種', 'ビッグマックス'), CONF['label'])
        self.assertIn(('用途', '食べずに、育てて楽しむ'), CONF['label'])
        self.assertEqual(urlsplit(CONF['qr_grow']).path, '/tane-tsutsumi/grow.html')
        self.assertLessEqual(len((root / 'README.md').read_text().splitlines()), 40)


if __name__ == '__main__':
    unittest.main()
