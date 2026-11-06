"""Build and inspect the print deliverables using an EXISTING Chromium CDP session.

uv run python tools/build.py --cdp http://127.0.0.1:9224
No browser download or new browser process. Image generation is a separate opt-in.
QR tests inspect rasterized SVG sheets, not paper; retention needs a physical test.
"""
from __future__ import annotations
import argparse
import asyncio
import base64
import http.server
import json
import math
import pathlib
import re
import socketserver
import threading
import zipfile
import xml.etree.ElementTree as ET
from functools import partial

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
SHOTS = ROOT / "shots"
ART = ROOT / "designs/art"
IDS = ["umi", "kani", "eki"]
URLS = ["https://x.com/iwami_kankou", "https://github.com/social-calculus/tane-tsutsumi"]
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"


def make_images():
    for name in IDS:
        png, jpg = ART / f"{name}_scene.png", ART / f"{name}_scene.jpg"
        if not png.exists() or (jpg.exists() and jpg.stat().st_mtime >= png.stat().st_mtime):
            continue  # published JPEGs are sufficient; never overwrite a user's newer edit
        im = Image.open(png).convert("RGB")
        # Remove the AI's unwanted 18 px rule around the seascape, NOT upscale.
        if name == "umi":
            b = round(im.width * .025)
            im = im.crop((b, b, im.width-b, im.height-b))
        im.save(ART / f"{name}_scene.jpg", quality=95, subsampling=0)
    data={f'designs/art/{name}_scene.jpg':'data:image/jpeg;base64,'+base64.b64encode((ART/f'{name}_scene.jpg').read_bytes()).decode() for name in IDS}
    (ROOT/'designs/art-data.js').write_text('// Generated offline image data. Regenerate with tools/build.py.\nwindow.TANE_ART_DATA='+json.dumps(data)+';\n')


async def raster_svg(client, locator, path, dpi=300):
    rect=await locator.evaluate('(el)=>{const b=el.getBoundingClientRect();return {x:b.left+scrollX,y:b.top+scrollY,width:b.width,height:b.height}}')
    result=await client.send('Page.captureScreenshot',{'format':'png','captureBeyondViewport':True,'clip':{**rect,'scale':dpi/96}})
    path.write_bytes(base64.b64decode(result['data']))
    assert abs(Image.open(path).width-210/25.4*dpi)<4, (path,Image.open(path).size,dpi)


def check_pdf(path, pages):
    raw = path.read_bytes()
    actual = len(re.findall(rb"/Type\s*/Page\b", raw))
    assert actual == pages, (path, actual, pages)
    # Chromium embeds CFF/TTC glyphs as Type 3 CharProcs, not FontFile streams.
    embedded = b"/FontFile" in raw or (b"/Subtype /Type3" in raw and b"/CharProcs" in raw and b"/ToUnicode" in raw)
    assert embedded, f"Neither embedded fonts nor self-contained Type 3 glyphs: {path}"
    boxes = re.findall(rb"/MediaBox\s*\[([^]]+)\]", raw)
    assert boxes
    for box in boxes:
        v = [float(x) for x in box.split()]
        assert abs((v[2]-v[0])-595.28)<1 and abs((v[3]-v[1])-841.89)<1, v
    return {"file":path.name,"pages":actual,"a4":True,"embedded_fonts":True,"font_representation":"Type3 embedded glyphs" if b"/Subtype /Type3" in raw else "FontFile"}


def inspect_qr(path, expected):
    image = cv2.imread(str(path))
    assert image.shape[1]>=2400, '300dpi test must not upscale a 96dpi screenshot'
    results = []
    for dpi in (300, 150):
        width = round(210/25.4*dpi)
        resized = cv2.resize(image, (width, round(image.shape[0]*width/image.shape[1])), interpolation=cv2.INTER_AREA)
        # QR is on a flat central panel; no transformed/reassembled surrogate.
        # Crop avoids large pictorial regions confusing the detector.
        mm = width/210
        crop = resized[round(73*mm):round(136*mm), round(73*mm):round(136*mm)]
        decoded,_,_ = cv2.QRCodeDetector().detectAndDecode(crop)
        assert decoded == expected, (path.name,dpi,decoded)
        results.append({"dpi":dpi,"decoded":decoded})
    return {"file":path.name,"tests":results}


def geometry_checks():
    # Check the uncreased 64 mm body, guide diagonals, QR clearances and the
    # cyclic interlock's projected overlap. This does NOT test paper friction.
    a=64
    qrs=[(81,81,30),(69,101.8,20.5)]  # relative to 192 mm square
    for x,y,w in qrs:
        assert min(x,y)>=a and max(x+w,y+w)<=2*a
    assert (a-45)/2>=9 and (a-50)/2>=7
    # Every offset precrease touches at most a corner of the centre, never its interior.
    for x in np.linspace(64.01,127.99,64):
        for y in np.linspace(64.01,127.99,64):
            assert not any(abs(z)<.001 for z in [x+y-128,x+y-256,y-x-64,y-x+64])
    # Four folded wings are half-squares. Their cyclic pair overlaps are quarter-squares.
    p=np.linspace(.01,63.99,640)
    x,y=np.meshgrid(p,p)
    wings=[y>=x,y>=a-x,y<=x,y<=a-x]  # L B R T
    assert np.all(np.logical_or.reduce(wings))
    for i in range(4):
        area=np.mean(wings[i]&wings[(i+1)%4])*a*a
        assert abs(area-a*a/4)<5
    return {"square_mm":192,"finished_mm":[64,64],"bag_max_external_mm":[45,50],
            "qr_crease_clearance_checked":True,"cyclic_projected_overlap_mm2":1024,
            "physical_retention_test":"NOT PERFORMED — 11/8 proof required",
            "construction_reference":"https://itrydiy.me/2016/02/origami-square-envelope"}


async def build(cdp):
    make_images()
    DIST.mkdir(exist_ok=True); SHOTS.mkdir(exist_ok=True)
    report={"geometry":geometry_checks(),"pdfs":[],"qr":[],"art":[]}
    for name in IDS:
        im=Image.open(ART/f"{name}_scene.jpg")
        report['art'].append({"id":name,"native_pixels":list(im.size),"effective_ppi":round(im.width/(198/25.4),1),"upscaled":False})
    server=socketserver.TCPServer(('127.0.0.1',0),partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    origin=f'http://127.0.0.1:{server.server_address[1]}'
    adapter=None; pw=None; page=None
    try:
        # Platform integration is optional; no host-specific path is in this repo.
        try:
            from human_behavior import SessionContext, after_navigation
            from human_behavior.playwright_adapter import PlaywrightAdapter
        except ImportError:
            pw=await async_playwright().start()
            browser=await pw.chromium.connect_over_cdp(cdp)
            page=await browser.contexts[0].new_page()
        else:
            ctx=SessionContext()
            adapter=await PlaywrightAdapter.from_cdp(cdp,ctx,dedicated_page=True,prune_extra_tabs=False)
            page=adapter.page
        errors=[]
        page.on('pageerror',lambda error: errors.append(str(error)))
        await page.set_viewport_size({'width':1000,'height':1200})
        client=await page.context.new_cdp_session(page)
        await client.send('Emulation.setDeviceMetricsOverride',{'width':1000,'height':1200,'deviceScaleFactor':1,'mobile':False})
        await page.goto(origin+'/index.html?all=1',wait_until='load')
        if adapter: await after_navigation(adapter,ctx)
        await page.wait_for_function('window.TANE_READY === true')
        await page.evaluate('TANE_APP.readyImages()')
        await page.emulate_media(media='print')
        path=DIST/'tane-tsutsumi_iwami_a4.pdf'
        await page.pdf(path=str(path),prefer_css_page_size=True,print_background=True)
        report['pdfs'].append(check_pdf(path,6))
        svgs=page.locator('#print > svg')
        assert await svgs.count()==6
        qr_metrics=await page.locator('#print [data-qr]').evaluate_all('(els)=>els.map(e=>({url:e.dataset.qr,modules:+e.dataset.modules,module_mm:+e.dataset.moduleMm}))')
        assert min(x['module_mm'] for x in qr_metrics)>=.49
        report['qr_metrics']=qr_metrics
        for i,name in enumerate(IDS):
            for side in range(2):
                shot=SHOTS/f'{name}_{["inside","outside"][side]}.png'
                await raster_svg(client,svgs.nth(i*2+side),shot)
                report['qr'].append(inspect_qr(shot,URLS[side]))
                data=await svgs.nth(i*2+side).evaluate('(el)=>el.outerHTML')
                jpg=ART/f'{name}_scene.jpg'
                encoded='data:image/jpeg;base64,'+base64.b64encode(jpg.read_bytes()).decode()
                data=data.replace(f'designs/art/{name}_scene.jpg',encoded)
                ET.fromstring(data)  # standalone XML, not just HTML-tolerant SVG
                (DIST/f'{name}-{["inside","outside"][side]}.svg').write_text(data)
            # Print each design on precisely one physical sheet (2 PDF pages).
            pdf=DIST/f'{name}-a4.pdf'
            await page.pdf(path=str(pdf),prefer_css_page_size=True,print_background=True,page_ranges=f'{i*2+1}-{i*2+2}')
            report['pdfs'].append(check_pdf(pdf,2))
        # Confirm BOTH QR configuration fields really change the vector output.
        changed=await page.evaluate('''()=>{const old={...TANE_APP.base};TANE_APP.base.qrUrl='https://example.org/main';TANE_APP.base.licenseQr='https://example.org/source';TANE_APP.printPages([TANE_APP.designs[0]]);const urls=[...document.querySelectorAll('#print [data-qr]')].map(e=>e.dataset.qr);Object.assign(TANE_APP.base,old);return urls}''')
        assert changed==['https://example.org/main','https://example.org/source']
        report['editable_qrs_pass']=True
        for html,output,count in [('dist/guide.html','fold-guide.pdf',2),('dist/practice.html','practice.pdf',1)]:
            await page.goto(origin+'/'+html,wait_until='load')
            await page.evaluate('document.fonts.ready')
            pdf=DIST/output
            await page.pdf(path=str(pdf),prefer_css_page_size=True,print_background=True)
            report['pdfs'].append(check_pdf(pdf,count))
            for i in range(count):
                await raster_svg(client,page.locator('svg').nth(i),DIST/f'{output[:-4]}-{i+1}.png',dpi=150)
        # Explicitly labelled construction schematic for downstream slide users.
        for name in IDS:
            diagram=await page.evaluate('''async name=>{const r=await fetch('/tane.js');(0,eval)(await r.text());return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 84 94" width="640" height="716"><rect width="84" height="94" fill="#fffaf0"/>${TANE.pinwheel(4,-54,-54,1)}${TANE.text(42,82,'閉じ方の模式図',3,'text-anchor="middle"')}${TANE.text(42,88,'実物写真ではありません',2.3,'text-anchor="middle"')}</svg>`}''',name)
            await page.set_content(diagram)
            await page.locator('svg').screenshot(path=str(SHOTS/f'{name}_closed.jpg'),type='jpeg',quality=92)
        # Check the delivered app under file:// as well, including image embedding.
        await page.goto((ROOT/'index.html').as_uri(),wait_until='load')
        await page.wait_for_function('window.TANE_READY===true')
        offline=await page.evaluate('''async()=>{const data=await dataImage(TANE_APP.designs[0].art);const d={...TANE_APP.designs[0],art:data};return {embedded:data.startsWith('data:image/'),svg:TANE.page('inside',d,TANE_APP.base,'test'),labels:TANE_APP.base.label}}''')
        assert offline['embedded'] and len(offline['labels'])==6
        ET.fromstring(offline['svg'])
        await page.evaluate('''()=>{TANE_APP.designs[0].art=TANE_ART_DATA['designs/art/kani_scene.jpg'];render()}''')
        assert await page.locator('#previews image').first.get_attribute('href') == 'data:image/jpeg;base64,'+base64.b64encode((ART/'kani_scene.jpg').read_bytes()).decode()
        saved=await page.evaluate('''async()=>{const original=window.download;let result;window.download=(data)=>{result=data};try{await document.getElementById('save').onclick();return result}finally{window.download=original}}''')
        saved_obj=json.loads(saved)
        assert len(saved_obj['designs'])==3 and all(d['art'].startswith('data:image/') for d in saved_obj['designs'])
        await page.evaluate("TANE_APP.base.qrTitle='テスト';populate();render()")
        await page.locator('#load').set_input_files({'name':'settings.json','mimeType':'application/json','buffer':saved.encode()})
        await page.wait_for_function("TANE_APP.base.qrTitle==='岩美町の中の人'")
        assert await page.evaluate('''()=>{const old=TANE_APP.base.qrUrl;TANE_APP.base.qrUrl='javascript:alert(1)';const rejected=!render();TANE_APP.base.qrUrl=old;render();return rejected}''')
        report['offline_image_replacement_and_svg_export_pass']=True
        report['offline_settings_json_roundtrip_pass']=True
        report['invalid_qr_scheme_rejected']=True
        assert not errors, errors
        report['browser_errors']=errors
    finally:
        if adapter: await adapter.close()
        elif page: await page.close()
        if pw: await pw.stop()
        server.shutdown(); server.server_close()
    # Contact sheet and compatibility previews (actual laid-flat layout only).
    previews=[]
    for name in IDS:
        im=Image.open(SHOTS/f'{name}_inside.png').convert('RGB')
        m=im.width/210
        crop=im.crop(tuple(round(v*m) for v in (9,9,201,201)))
        crop.save(SHOTS/f'{name}_open.jpg',quality=94)
        previews.append(crop.resize((640,640),Image.Resampling.LANCZOS))
    preview=Image.new('RGB',(1920,710),'#fffaf0');d=ImageDraw.Draw(preview)
    font=ImageFont.truetype(FONT,28)
    for i,(im,name) in enumerate(zip(previews,['海から、ひと粒','港の実り','湯けむりの帰り道'])):
        preview.paste(im,(i*640,0));d.text((i*640+24,655),name,font=font,fill='#263b3d')
    preview.save(DIST/'preview.jpg',quality=94)
    Image.open(DIST/'fold-guide-1.png').convert('RGB').resize((1050,1485)).save(DIST/'fold_steps.jpg',quality=93)
    (DIST/'preflight.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    with zipfile.ZipFile(DIST/'source.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        files=['index.html','tane.js','designs/designs.js','designs/prompts.json','vendor/qrcode.js','LICENSE','LICENSE-CODE','README.md','ASSETS.md','tools/build.py','tools/guide.mjs','tools/gen_art.mjs','pyproject.toml','uv.lock','designs/art-data.js']
        files += [str(p.relative_to(ROOT)) for p in ART.glob('*_scene.jpg')]
        files += [str(p.relative_to(ROOT)) for p in DIST.iterdir() if p.is_file() and p.suffix in {'.svg','.pdf','.html','.json','.jpg','.png'}]
        for name in files: z.write(ROOT/name,'tane-tsutsumi/'+name)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    print('DIGITAL PREFLIGHT PASS — physical proof not performed')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--cdp',required=True)
    asyncio.run(build(parser.parse_args().cdp))
