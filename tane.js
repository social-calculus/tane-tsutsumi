// 包みの版面を SVG で組む。すべて mm 単位（A4 縦）。
//
// 切り方：点線の 4 辺を切って 198mm 四方にする。絵は紙の端まで刷るので、切った後に白い縁が残らない。
// 折り方（紙を角が上になるように置く。中央の四角の 4 辺が折り線）：
//   1. 内側の面を上に、種の袋を真ん中へ  2. 下の角を折る  3. 右、左の順に角を折る
//   4. 上の角を折り、先を左右の重なりの下へ差し込む
//   角がそれぞれ中心を越えて重なるので、シールなしで閉じ、中身もこぼれない。折り上がりは 110mm 四方。
// 表面（inside）＝開くと出てくる大きな絵。裏面（outside）＝閉じたときに見える面。
// 裏面の 4 枚の角は、折ったときに 1 枚の絵に戻るよう、折り返しを逆算して配置する。
// 両面印刷は「長辺とじ」が前提（裏面は左右が反転する）。

(function () {
  const OFF = 6; // 紙の左右と上から切り落とす幅
  const S = 198; // 切り上がりの一辺
  const R = S / Math.SQRT2; // 紙の中心から角までの長さ
  const W = 110; // 折り上がりの一辺（＝中央の四角）
  const H = W / 2;
  const BLEED = 3; // 切りずれに備えて、絵を切り線の外へ伸ばす幅
  const C = Math.SQRT1_2;
  const NS = 'http://www.w3.org/2000/svg';
  const reach = R - W + BLEED; // 角の先が中心を越える長さ

  // (u,v)：角を上にして置いた紙の座標（原点は紙の中心） → 紙の表面の座標
  const toSheet = (u, v) => [S / 2 + (u + v) * C, S / 2 + (v - u) * C];
  // 裏面は長辺とじで左右が反転する
  const toBack = ([x, y]) => [S - x, y];
  const backPoint = (u, v) => toBack(toSheet(u, v));

  // 閉じた姿の点 (U,V) に重なる、折る前の紙の位置（折り線で鏡映）。box は閉じた姿での範囲
  const FLAPS = {
    bottom: { box: [-H, -reach, W, H + reach], paper: (U, V) => [U, 2 * H - V] },
    right: { box: [-reach, -H, H + reach, W], paper: (U, V) => [2 * H - U, V] },
    left: { box: [-H, -H, H + reach, W], paper: (U, V) => [-2 * H - U, V] },
    top: { box: [-H, -H, W, H + reach], paper: (U, V) => [U, -2 * H - V] },
  };

  const matrixOf = (fn) => {
    const [ox, oy] = fn(0, 0);
    const [ax, ay] = fn(1, 0);
    const [bx, by] = fn(0, 1);
    return `matrix(${ax - ox} ${ay - oy} ${bx - ox} ${by - oy} ${ox} ${oy})`;
  };

  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const SERIF = `font-family="'Noto Serif CJK JP','Noto Serif JP','Yu Mincho','Hiragino Mincho ProN',serif"`;
  const PAPER = '#f8f2e4';

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

  // 閉じた姿の絵（外側）。座標は (U,V)、原点は包みの中心。
  // 題箋と印は右の帯に置く：どの順に折っても、この帯は右の角 1 枚だけで合わせ目がない
  function coverArt(design, base) {
    const chars = [...base.title];
    const tx = H - 11;
    const top = -H + 8;
    const height = chars.length * 6.1 + 7;
    const title = chars.map((c, i) => `<text x="${tx}" y="${top + 7.6 + i * 6.1}" text-anchor="middle" font-size="5.2" font-weight="700" fill="#2c2620" ${SERIF}>${esc(c)}</text>`).join('');
    const sealY = top + height + 4;
    return `<image href="${esc(design.cover)}" x="${-H - 2}" y="${-H - 2}" width="${W + 4}" height="${W + 4}" preserveAspectRatio="xMidYMid slice"/>
      <rect x="${tx - 5.2}" y="${top}" width="10.4" height="${height}" fill="${PAPER}" stroke="#2c2620" stroke-width="0.2"/>
      ${title}
      <rect x="${tx - 4.2}" y="${sealY}" width="8.4" height="11" rx="1" fill="#c0392b"/>
      <text x="${tx}" y="${sealY + 4.7}" text-anchor="middle" font-size="3.5" font-weight="700" fill="#fff" ${SERIF}>岩</text>
      <text x="${tx}" y="${sealY + 8.8}" text-anchor="middle" font-size="3.5" font-weight="700" fill="#fff" ${SERIF}>美</text>`;
  }

  // 裏の表示欄（閉じた姿の背面）。座標は (X,Y)、原点は包みの中心
  function backPanel(base) {
    const x0 = -H + 9;
    const rows = base.label
      .map(([k, v], i) => {
        const y = -H + 16 + i * 6.6;
        return `<text x="${x0}" y="${y}" font-size="2.9" font-weight="700" fill="#333" ${SERIF}>${esc(k)}</text>
        <text x="${x0 + 17}" y="${y}" font-size="2.9" fill="#333" ${SERIF}>${esc(v)}</text>
        <line x1="${x0}" x2="${H - 9}" y1="${y + 2}" y2="${y + 2}" stroke="#999" stroke-width="0.12"/>`;
      })
      .join('');
    const qy = H - 31;
    return `<rect x="${-H}" y="${-H}" width="${W}" height="${W}" fill="${PAPER}"/>
      ${rows}
      ${qrPath(base.licenseQr, x0, qy, 17)}
      <text x="${x0 + 21}" y="${qy + 4}" font-size="2.6" fill="#333" ${SERIF}>${esc(base.licenseText)}</text>
      <text x="${x0 + 21}" y="${qy + 8.4}" font-size="2.6" fill="#333" ${SERIF}>絵や QR は自由に差し替えられます。</text>
      <text x="${x0 + 21}" y="${qy + 12.8}" font-size="2.1" fill="#555" ${SERIF}>github.com/social-calculus/tane-tsutsumi</text>`;
  }

  // 裏面（閉じたときに見える面）
  function outside(design, base, uid) {
    let defs = `<g id="cover-${uid}">${coverArt(design, base)}</g>`;
    // 折ると隠れる部分は、紙の色の代わりにデザインの色で埋めておく
    let body = `<rect x="-${OFF}" y="-${OFF}" width="210" height="${S + OFF + BLEED}" fill="${esc(design.color)}"/>`;
    for (const [name, f] of Object.entries(FLAPS)) {
      const [x, y, w, h] = f.box;
      defs += `<clipPath id="clip-${uid}-${name}"><rect x="${x}" y="${y}" width="${w}" height="${h}"/></clipPath>`;
      const m = matrixOf((U, V) => backPoint(...f.paper(U, V)));
      body += `<g transform="${m}"><g clip-path="url(#clip-${uid}-${name})"><use href="#cover-${uid}"/></g></g>`;
    }
    // 背面：裏返すと左右が入れ替わる
    body += `<g transform="${matrixOf((X, Y) => backPoint(-X, Y))}">${backPanel(base)}</g>`;
    return { defs, body };
  }

  // 開いたときの小さな札。at は紙の座標（u,v）で札の中心
  function labelTag(item) {
    const lines = item.line.split('\n');
    const width = Math.max([...item.title].length * 3.8, ...lines.map((l) => [...l].length * 2.75)) + 6;
    const height = 8.6 + lines.length * 3.5;
    const [u, v] = item.at;
    return `<rect x="${u - width / 2}" y="${v - height / 2}" width="${width}" height="${height}" fill="${PAPER}" fill-opacity="0.93" stroke="#2c2620" stroke-width="0.15"/>
      <text x="${u}" y="${v - height / 2 + 5.1}" text-anchor="middle" font-size="3.5" font-weight="700" fill="#2c2620" ${SERIF}>${esc(item.title)}</text>
      ${lines.map((l, i) => `<text x="${u}" y="${v - height / 2 + 9.1 + i * 3.5}" text-anchor="middle" font-size="2.6" fill="#333" ${SERIF}>${esc(l)}</text>`).join('')}`;
  }

  // 表面（開いたときに見える面）
  function inside(design, base) {
    const q = 36;
    return `<rect x="-${OFF}" y="-${OFF}" width="210" height="${S + OFF + BLEED}" fill="${esc(design.color)}"/>
      <g transform="translate(${S / 2} ${S / 2}) rotate(-45)">
      <image href="${esc(design.inside)}" x="${-R - 4}" y="${-R - 4}" width="${2 * R + 8}" height="${2 * R + 8}" preserveAspectRatio="xMidYMid slice"/>
      ${design.labels.map(labelTag).join('')}
      <rect x="${-H}" y="${-H}" width="${W}" height="${W}" fill="${PAPER}" stroke="#2c2620" stroke-width="0.25" stroke-dasharray="1.4 1.2"/>
      <text x="0" y="${-q / 2 - 7.5}" text-anchor="middle" font-size="5" font-weight="700" fill="#2c2620" ${SERIF}>${esc(base.qrTitle)}</text>
      ${qrPath(base.qrUrl, -q / 2, -q / 2, q)}
      <text x="0" y="${q / 2 + 8}" text-anchor="middle" font-size="3.6" fill="#333" ${SERIF}>${esc(base.qrNote)}</text>
    </g>`;
  }

  // 切り線と、切り落とす部分の手順（切ったら捨てる）。ここは用紙座標
  function cutMarks(side) {
    if (side !== 'inside') return '';
    const line = 'stroke="#fff" stroke-width="0.25" stroke-dasharray="2 2"';
    const dark = 'stroke="#777" stroke-width="0.2" stroke-dasharray="2 2"';
    const b = OFF + S;
    return `<path d="M${OFF} 0V${b}M${b} 0V${b}M0 ${OFF}H210M0 ${b}H210" fill="none" ${line}/>
      <path d="M${OFF} ${b + 3}V${b + 8}M${b} ${b + 3}V${b + 8}" fill="none" ${dark}/>
      <text x="105" y="${b + 8}" text-anchor="middle" font-size="3.2" fill="#555" ${SERIF}>点線の 4 辺を切る（約 19.8cm 四方。下の部分は捨てる）</text>
      <text x="105" y="${b + 16}" text-anchor="middle" font-size="3.2" fill="#555" ${SERIF}>① この面を上に、角を上にして置き、種の袋を真ん中へ　② 下の角を四角の線で折る</text>
      <text x="105" y="${b + 22}" text-anchor="middle" font-size="3.2" fill="#555" ${SERIF}>③ 右、左の順に角を折る　④ 上の角を折り、先を左右の重なりの下へ差し込む</text>
      <text x="105" y="${b + 30}" text-anchor="middle" font-size="3.2" fill="#555" ${SERIF}>両面印刷は「長辺とじ」、倍率 100%</text>`;
  }

  function page(side, design, base, uid) {
    const made = side === 'outside' ? outside(design, base, uid) : { defs: '', body: inside(design, base) };
    return `<svg xmlns="${NS}" class="sheet-svg" viewBox="0 0 210 297" width="210mm" height="297mm">
      <defs>${made.defs}<clipPath id="page-${uid}"><rect x="0" y="0" width="210" height="${OFF + S + BLEED}"/></clipPath></defs>
      <rect x="0" y="0" width="210" height="297" fill="#fff"/>
      <g clip-path="url(#page-${uid})"><g transform="translate(${OFF} ${OFF})">${made.body}</g></g>
      ${cutMarks(side)}
    </svg>`;
  }

  window.TANE = { OFF, S, R, W, FLAPS, page, coverArt, qrPath };
})();
