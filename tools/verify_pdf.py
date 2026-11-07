"""Rasterize the actual delivery PDF and decode all three URLs, offline."""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
import pymupdf

from build_a4 import CONF

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('design')
    args = parser.parse_args()
    out = ROOT / 'dist/a4' / args.design
    pdf = out / 'print.pdf'
    detectors = [cv2.QRCodeDetector(), cv2.QRCodeDetectorAruco()]
    evidence = []
    expected = [{CONF['qr_inside']}, {CONF['qr_source'], CONF['qr_grow']}]
    with pymupdf.open(pdf) as document:
        assert len(document) == 2
        for page_index, page in enumerate(document):
            for dpi in (150, 300):
                pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB, alpha=False)
                array = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3)[:, :, ::-1]
                h, w = array.shape[:2]
                found = set()
                scans = []
                for angle in (0, 45, -45):
                    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1)
                    image = cv2.warpAffine(array, matrix, (w, h), borderValue=(255, 255, 255))
                    for detector in detectors:
                        ok, decoded, _, _ = detector.detectAndDecodeMulti(image)
                        urls = sorted(set(filter(None, decoded))) if ok else []
                        found.update(urls)
                        scans.append(dict(angle=angle, decoder=type(detector).__name__, urls=urls))
                assert expected[page_index] <= found, (page_index + 1, dpi, found)
                evidence.append(dict(page=page_index + 1, dpi=dpi, pixels=[w, h],
                                     media_box_points=list(page.rect), urls=sorted(found), scans=scans))
    report = dict(pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),
                  renderer='PyMuPDF', pages=2, results=evidence,
                  physical_scan=False, note='All URLs found by the union of decoder/angle results. This is not a phone or physical paper test.')
    (out / 'pdf-check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({str(i['page']) + ':' + str(i['dpi']): i['urls'] for i in evidence}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
