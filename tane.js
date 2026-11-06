// 包みの版面を SVG で組む。すべて mm 単位（A4 縦）。
//
// 切り方：点線の 4 辺を切って 198mm 四方にする。絵は紙の端まで刷るので、打ちぬいた後に白い縁が残らない。
//         （印刷機は紙の端を刷れない。底だけ切ると、白い縁が折り上がりの表に大きな × として出る）
// 折り方：四隅を中心へ折る（封筒折り）。折ると、外から見えるのは紙の裏面だけになる。
//   表面（inside）＝開くと出てくる面。中央の四角＋四隅の三角。斜め 45° に組む。
//   裏面（outside）＝閉じたときに見える面。4 枚の三角が 1 枚の絵に戻るよう、折り返しを逆算して配置する。
// 両面印刷は「長辺とじ」が前提（裏面は左右が反転する）。

(function () {
  const OFF = 6; // 紙の左右と上から切り落とす幅
  const S = 198; // 切り上がりの一辺
  const D = S / Math.SQRT2; // 折り上がりの一辺（約 140mm）
  const BLEED = 3; // 切りずれに備えて、絵を切り線の外へ伸ばす幅
  const C = Math.SQRT1_2;
  const NS = 'http://www.w3.org/2000/svg';
  const B = BLEED * Math.SQRT2;

  // 閉じた姿の座標 (u,v) → 紙を広げた表面の座標 (x,y)
  const unfolded = (u, v) => {
    const du = u - D / 2;
    const dv = v - D / 2;
    return [S / 2 + (du + dv) * C, S / 2 + (dv - du) * C];
  };

  // 折り目で鏡映して、閉じた姿で見える点が紙のどこにあるかを返す。clip は合わせ目の外へ BLEED だけ広げてある
  const FLAPS = {
    top: { clip: [[-B, 0], [D + B, 0], [D / 2, D / 2 + B]], unfold: ([x, y]) => [S / 2 - y, S / 2 - x] },
    right: { clip: [[D, -B], [D, D + B], [D / 2 - B, D / 2]], unfold: ([x, y]) => [y + S / 2, x - S / 2] },
    bottom: { clip: [[D + B, D], [-B, D], [D / 2, D / 2 - B]], unfold: ([x, y]) => [(3 * S) / 2 - y, (3 * S) / 2 - x] },
    left: { clip: [[0, D + B], [0, -B], [D / 2 + B, D / 2]], unfold: ([x, y]) => [y - S / 2, x + S / 2] },
  };

  // 裏面は長辺とじで左右が反転する
  const toBack = ([x, y]) => [S - x, y];

  const matrixOf = (fn) => {
    const [ox, oy] = fn(0, 0);
    const [ax, ay] = fn(1, 0);
    const [bx, by] = fn(0, 1);
    return `matrix(${ax - ox} ${ay - oy} ${bx - ox} ${by - oy} ${ox} ${oy})`;
  };

  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const pts = (list) => list.map((p) => p.join(',')).join(' ');
  const SERIF = `font-family="'Noto Serif CJK JP','Noto Serif JP','Yu Mincho','Hiragino Mincho ProN',serif"`;

  function qrPath(text, x, y, size, color = '#222') {
    const qr = window.qrcode(0, 'M');
    qr.addData(text);
    qr.make();
    const n = qr.getModuleCount();
    const m = size / n;
    let d = '';
    for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) if (qr.isDark(r, c)) d += `M${x + c * m} ${y + r * m}h${m}v${m}h${-m}z`;
    return `<rect x="${x - m * 2}" y="${y - m * 2}" width="${size + m * 4}" height="${size + m * 4}" fill="#fff"/><path d="${d}" fill="${color}"/>`;
  }

  // 閉じた姿の絵（外側）。AI の絵は縁に紙色が残りやすいので、少し拡大して縁を外へ逃がす
  function frontArt(design, base) {
    return `
      <image href="${esc(design.front)}" x="-7" y="-7" width="${D + 14}" height="${D + 14}" preserveAspectRatio="xMidYMid slice"/>
      <text x="${D / 2}" y="17" text-anchor="middle" font-size="9" font-weight="700" fill="#fff" stroke="${esc(design.color)}" stroke-width="1.6" paint-order="stroke" ${SERIF}>${esc(base.title)}</text>
      <text x="${D / 2}" y="${D - 9}" text-anchor="middle" font-size="4.2" font-weight="700" fill="#fff" stroke="${esc(design.color)}" stroke-width="1" paint-order="stroke" ${SERIF}>${esc(base.subtitle)}</text>`;
  }

  // 裏の表示欄（閉じた姿の背面）
  function backPanel(base) {
    const rows = base.label
      .map(
        ([k, v], i) => `<text x="17" y="${36 + i * 8.2}" font-size="3.5" font-weight="700" fill="#333" ${SERIF}>${esc(k)}</text>
        <text x="39" y="${36 + i * 8.2}" font-size="3.5" fill="#333" ${SERIF}>${esc(v)}</text>
        <line x1="17" x2="${D - 17}" y1="${38.4 + i * 8.2}" y2="${38.4 + i * 8.2}" stroke="#999" stroke-width="0.15"/>`,
      )
      .join('');
    return `<rect x="-${BLEED}" y="-${BLEED}" width="${D + BLEED * 2}" height="${D + BLEED * 2}" fill="#fbf6ea"/>
      ${rows}
      ${qrPath(base.licenseQr, 17, 100, 16)}
      <text x="37" y="106" font-size="3" fill="#333" ${SERIF}>${esc(base.licenseText)}</text>
      <text x="37" y="111" font-size="3" fill="#333" ${SERIF}>絵や QR は自由に差し替えられます。</text>
      <text x="37" y="116" font-size="2.6" fill="#555" ${SERIF}>github.com/social-calculus/tane-tsutsumi</text>`;
  }

  // 裏面（閉じたときに見える面）
  function outside(design, base, uid) {
    let defs = `<g id="front-${uid}">${frontArt(design, base)}</g>`;
    let body = '';
    // 背面を先に置き、三角を上に重ねる（裁ち落としの分だけ重なっても、三角が勝つ）
    const backM = matrixOf((u, v) => toBack(unfolded(D - u, v)));
    defs += `<clipPath id="clip-${uid}-back"><rect x="0" y="0" width="${D}" height="${D}"/></clipPath>`;
    body += `<g transform="${backM}"><g clip-path="url(#clip-${uid}-back)">${backPanel(base)}</g></g>`;
    for (const [name, f] of Object.entries(FLAPS)) {
      defs += `<clipPath id="clip-${uid}-${name}"><polygon points="${pts(f.clip)}"/></clipPath>`;
      // 閉じた姿 (u,v) → 表面の位置 → 折り返し前の位置 → 裏面の印刷位置
      const m = matrixOf((u, v) => toBack(f.unfold(unfolded(u, v))));
      body += `<g transform="${m}"><g clip-path="url(#clip-${uid}-${name})"><use href="#front-${uid}"/></g></g>`;
    }
    return { defs, body };
  }

  // 表面の三角 1 枚（開いたときに正立する）。line の \n は細い三角での改行位置
  function flapInside(name, flap, color, uid) {
    const A = 34; // 絵は正方形
    const cx = D / 2;
    const tri = {
      top: { p: [[0, 0], [D, 0], [cx, -D / 2]], img: [cx - A / 2, -47], tx: cx, ty: -8 },
      bottom: { p: [[D, D], [0, D], [cx, D + D / 2]], img: [cx - A / 2, D + 13], tx: cx, ty: D + 6 },
      left: { p: [[0, D], [0, 0], [-D / 2, D / 2]], img: [-38, cx - 23], tx: -21, ty: cx + 16 },
      right: { p: [[D, 0], [D, D], [D + D / 2, cx]], img: [D + 4, cx - 23], tx: D + 21, ty: cx + 16 },
    }[name];
    const narrow = name === 'left' || name === 'right';
    const lines = narrow ? flap.line.split('\n') : [flap.line.replace('\n', '')];
    const id = `fl-${uid}-${name}`;
    const zoom = A * 0.08; // 絵の縁の紙色を外へ逃がす
    return `<clipPath id="${id}"><rect x="${tri.img[0]}" y="${tri.img[1]}" width="${A}" height="${A}" rx="2"/></clipPath>
      <image href="${esc(flap.img)}" x="${tri.img[0] - zoom}" y="${tri.img[1] - zoom}" width="${A + zoom * 2}" height="${A + zoom * 2}" preserveAspectRatio="xMidYMid slice" clip-path="url(#${id})"/>
      <text x="${tri.tx}" y="${tri.ty}" text-anchor="middle" font-size="4" font-weight="700" fill="${esc(color)}" ${SERIF}>${esc(flap.title)}</text>
      ${lines.map((l, i) => `<text x="${tri.tx}" y="${tri.ty + 4.4 + i * 3.7}" text-anchor="middle" font-size="${narrow ? 2.8 : 3.1}" fill="#333" ${SERIF}>${esc(l)}</text>`).join('')}`;
  }

  // 表面（開いたときに見える面）
  function inside(design, base, uid) {
    const q = 40;
    const qx = (D - q) / 2;
    const qy = (D - q) / 2 + 3;
    const flaps = ['top', 'right', 'bottom', 'left'].map((n) => flapInside(n, design[n], design.color, uid)).join('');
    return `<rect x="-${OFF}" y="-${OFF}" width="210" height="${S + OFF + BLEED}" fill="#fbf6ea"/>
      <g transform="translate(${S / 2} ${S / 2}) rotate(-45) translate(${-D / 2} ${-D / 2})">
      ${flaps}
      <rect x="0" y="0" width="${D}" height="${D}" fill="#fffdf6" stroke="${esc(design.color)}" stroke-width="0.25" stroke-dasharray="1.2 1.2"/>
      <text x="${D / 2}" y="${qy - 9}" text-anchor="middle" font-size="5.2" font-weight="700" fill="${esc(design.color)}" ${SERIF}>${esc(base.qrTitle)}</text>
      ${qrPath(base.qrUrl, qx, qy, q)}
      <text x="${D / 2}" y="${qy + q + 8}" text-anchor="middle" font-size="3.8" fill="#333" ${SERIF}>${esc(base.qrNote)}</text>
    </g>`;
  }

  // 切り線と、切り落とす部分の手順（切ったら捨てる）。ここは用紙座標
  function cutMarks(side) {
    if (side !== 'inside') return '';
    const line = 'stroke="#777" stroke-width="0.2" stroke-dasharray="2 2"';
    const b = OFF + S;
    return `<path d="M${OFF} 0V${b + 8}M${b} 0V${b + 8}M0 ${OFF}H210M0 ${b}H210" fill="none" ${line}/>
      <text x="105" y="${b + 7}" text-anchor="middle" font-size="3.2" fill="#666" ${SERIF}>点線の 4 辺を切る（約 19.8cm 四方。下の部分は捨てる）</text>
      <text x="105" y="${b + 15}" text-anchor="middle" font-size="3.2" fill="#666" ${SERIF}>この面を上にして、種の袋を真ん中に置き、斜めの点線で四隅を中心へ折って丸シールでとめる</text>
      <text x="105" y="${b + 23}" text-anchor="middle" font-size="3.2" fill="#666" ${SERIF}>両面印刷は「長辺とじ」、倍率 100%</text>`;
  }

  function page(side, design, base, uid) {
    const made = side === 'outside' ? outside(design, base, uid) : { defs: '', body: inside(design, base, uid) };
    return `<svg xmlns="${NS}" class="sheet-svg" viewBox="0 0 210 297" width="210mm" height="297mm">
      <defs>${made.defs}<clipPath id="page-${uid}"><rect x="0" y="0" width="210" height="${OFF + S + BLEED}"/></clipPath></defs>
      <rect x="0" y="0" width="210" height="297" fill="#fff"/>
      <g clip-path="url(#page-${uid})"><g transform="translate(${OFF} ${OFF})">${made.body}</g></g>
      ${cutMarks(side)}
    </svg>`;
  }

  window.TANE = { OFF, S, D, FLAPS, page, frontArt, unfolded, toBack, qrPath };
})();
