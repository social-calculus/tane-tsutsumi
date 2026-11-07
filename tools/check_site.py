"""Own-site visual smoke check, through an existing Brave CDP session.

The optional local mode serves only this repository via in-memory Playwright
routes. It does not start a server, open a listener, or use site credentials.
On hap0py: use hands-exec pi and the slot's CDP port. Human interaction primitives
come from the shared headed_browser library; screenshots stay in /var/tmp.
"""
import argparse
import asyncio
import json
import mimetypes
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.path.insert(0, '/srv/stable/headed_browser')
from human_behavior import SessionContext, after_navigation
from human_behavior.playwright_adapter import PlaywrightAdapter

ROOT = Path(__file__).resolve().parent.parent


async def run(args):
    ctx = SessionContext()
    adapter = await PlaywrightAdapter.from_cdp(args.cdp, ctx, dedicated_page=True, prune_extra_tabs=False)
    page = adapter.page
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('requestfailed', lambda request: errors.append(request.url + ': ' + str(request.failure)))
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    origin = args.url.rstrip('/') + '/' if args.url else 'http://127.0.0.1:8765/'
    if not args.url:
        async def local(route):
            relative = unquote(urlsplit(route.request.url).path).lstrip('/') or 'index.html'
            target = (ROOT / relative).resolve()
            if not target.is_relative_to(ROOT) or not target.is_file():
                await route.fulfill(status=404, body='Not found')
                return
            mime = mimetypes.guess_type(str(target))[0] or 'application/octet-stream'
            if mime.startswith('text/'):
                mime += '; charset=utf-8'
            await route.fulfill(status=200, content_type=mime, body=target.read_bytes())
        await page.route(origin + '**', local)
    results = []
    try:
        for width, height, device in ((1280, 900, 'desktop'), (390, 844, 'mobile')):
            await page.set_viewport_size({'width': width, 'height': height})
            for filename in ('index.html', 'grow.html'):
                response = await page.goto(origin + filename, wait_until='networkidle')
                assert response and response.status == 200, (filename, response.status if response else None)
                await after_navigation(adapter, ctx)
                await page.evaluate('() => document.fonts.ready')
                info = await page.evaluate('''() => ({
                    title: document.title,
                    h1: document.querySelector('h1').innerText,
                    width: innerWidth,
                    scrollWidth: document.documentElement.scrollWidth,
                    fonts: document.fonts.status,
                    families: getComputedStyle(document.body).fontFamily,
                    japanese: document.fonts.check('16px "IBM Plex Sans JP"', '岩美のたね'),
                    latin: document.fonts.check('16px "IBM Plex Sans"', 'BIG MAX'),
                    brokenImages: [...document.images].filter(i => !i.complete || !i.naturalWidth).map(i => i.src)
                })''')
                assert info['scrollWidth'] <= width, info
                assert not info['brokenImages'], info
                assert info['fonts'] == 'loaded' and info['japanese'] and info['latin'], info
                path = output / f'{device}-{filename[:-5]}.png'
                await page.screenshot(path=str(path), full_page=True)
                results.append(dict(page=filename, device=device, screenshot=path.name, **info))
        assert not errors, errors
        (output / 'site-check.json').write_text(json.dumps(dict(origin=origin, results=results, errors=errors), ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(results, ensure_ascii=False, indent=2))
    finally:
        if not args.url:
            await page.unroute(origin + '**')
        await adapter.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cdp', required=True)
    parser.add_argument('--url', help='Public deployment; omit to preview repository in memory')
    parser.add_argument('--output', default='/var/tmp/hap0py/tane-tsutsumi-site-check')
    asyncio.run(run(parser.parse_args()))
