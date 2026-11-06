/* MIT — millimetres throughout. Traditional pinwheel/tato envelope.
 * 192 mm square -> 64 mm packet. There is NO crease through the central square.
 * This is a print layout, not a paper-thickness/retention simulation.
 */
(function (root) {
  'use strict';
  const S = 192, A = S / 3, OFF = 9, BLEED = 3;
  const NS = 'http://www.w3.org/2000/svg';
  const INK = '#263b3d', PAPER = '#fffaf0';
  const FONT = `font-family="'Noto Serif CJK JP','Noto Serif JP','Yu Mincho',serif"`;
  const SANS = `font-family="'Noto Sans CJK JP','Noto Sans JP','Yu Gothic',sans-serif"`;
  const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
  function text(x,y,s,size=3,extra='') {
    return `<text x="${x}" y="${y}" font-size="${size}" fill="${INK}" ${extra.includes('font-family=')?'':FONT} ${extra}>${esc(s)}</text>`;
  }
  // size INCLUDES the mandatory four-module quiet zone on every edge.
  function qr(textValue, x, y, size) {
    const q = root.qrcode(0, 'M'); q.addData(textValue, 'Byte'); q.make();
    const n = q.getModuleCount(), m = size / (n + 8);
    let d = '';
    for(let r=0;r<n;r++) for(let c=0;c<n;c++) if(q.isDark(r,c))
      d += `M${x+(c+4)*m},${y+(r+4)*m}h${m}v${m}h${-m}z`;
    return `<g data-qr="${esc(textValue)}" data-modules="${n}" data-module-mm="${m}"><rect x="${x}" y="${y}" width="${size}" height="${size}" fill="white"/><path d="${d}" fill="#000"/></g>`;
  }
  function cropMarks() {
    const e = OFF+S; let d='';
    for(const x of [OFF,e]) for(const y of [OFF,e]) {
      const dx=x===OFF?-1:1, dy=y===OFF?-1:1;
      d+=`M${x+dx*1.2},${y}h${dx*2.5}M${x},${y+dy*1.2}v${dy*2.5}`;
    }
    return `<path d="${d}" fill="none" stroke="#333" stroke-width=".18"/>`;
  }
  // All PRECREASES used by the referenced traditional fold. Some are only aids;
  // do not assign a single mountain/valley sense to the entire preparation grid.
  function creasePattern(x=0,y=0,scale=1) {
    return `<g transform="translate(${x} ${y}) scale(${scale})" fill="none" stroke-linecap="round">
      <rect width="192" height="192" stroke="${INK}" stroke-width=".55"/>
      <path d="M64 0V192M128 0V192M0 64H192M0 128H192" stroke="#247f86" stroke-width=".7" stroke-dasharray="3 2"/>
      <path d="M0 0L64 64M128 128L192 192M192 0L128 64M64 128L0 192" stroke="#bc6841" stroke-width=".7" stroke-dasharray="3 2"/>
      <path d="M0 128L128 0M64 0L192 128M0 64L128 192M64 192L192 64" stroke="#726b97" stroke-width=".7" stroke-dasharray="3 2"/>
      <rect x="65" y="65" width="62" height="62" fill="#e8f2e8" stroke="none"/>
      ${text(96,92,'中央は折らない',8,'text-anchor="middle"')}${text(96,106,'64 × 64 mm',7,'text-anchor="middle"')}
    </g>`;
  }
  function label(base) {
    const lines = base.label;
    let rows = '';
    lines.forEach(([key,value],i)=> {
      const y=83.2+i*4.1;
      rows+=text(79,y,key,2.35, SANS)+text(91,y,value,2.35,SANS);
      if(i<lines.length-1) rows+=`<path d="M78 ${y+1.1}H132" stroke="#a8aaa1" stroke-width=".12"/>`;
    });
    return `<rect x="76" y="76" width="58" height="58" rx=".7" fill="${PAPER}"/>
      ${rows}${qr(base.licenseQr,78,110.8,20.5)}
      ${text(101,115,'CC BY 4.0',2.65,SANS)}
      ${text(101,119.2,'SOCIAL CALCULUS',2.1,SANS)}
      ${text(101,123.2,'絵・型紙を公開',2.35,SANS)}
      ${text(101,127.2,'改変・再配布できます',2.2,SANS)}`;
  }
  function page(side,design,base,uid='sheet',guides=false) {
    const art = `<image href="${esc(design.art)}" x="6" y="6" width="198" height="198" preserveAspectRatio="xMidYMid slice"/>`;
    let body = art;
    if(side==='inside') {
      body+=`<rect x="84" y="80" width="42" height="50" rx=".6" fill="${PAPER}"/>
        ${text(105,86.2,base.qrTitle,3.1,'text-anchor="middle"')}
        ${qr(base.qrUrl,90,90,30)}
        ${text(105,125.7,base.qrNote,2.4,'text-anchor="middle" '+SANS)}
        <rect x="17" y="17" width="11" height="48" fill="${PAPER}" fill-opacity=".94"/>
        ${[...base.title].map((c,i)=>text(22.5,24+i*6.8,c,5.5,'text-anchor="middle"')).join('')}
        ${text(32,24,design.subtitle,3.2,'paint-order="stroke" stroke="#fffaf0" stroke-width=".8" stroke-linejoin="round"')}
        ${text(32,29.5,'鳥取県 岩美町',2.5,'paint-order="stroke" stroke="#fffaf0" stroke-width=".7" stroke-linejoin="round"')}`;
    } else body+=label(base);
    if(guides) body+=`<g opacity=".65">${creasePattern(OFF,OFF)}</g>`;
    const footer=side==='inside'
      ? `${text(14,216,'岩美のたね  /  '+design.name,5)}
         ${text(14,225,'A 面：開くと一枚の絵。QR のある面を上にして折ります。',3.2)}
         ${text(14,232,'A4・両面・長辺とじ・実際のサイズ（100%）・フチなし指定は不要。',3.2)}
         ${text(14,239,'四隅のトンボで 192 × 192 mm に裁断。64 mm ずつの三等分が基本です。',3.2)}
         ${text(14,249,'折り方は別紙「折り方と試し刷り」。中央の QR には折り目を付けません。',3.2)}
         ${text(14,256,'種は閉じたチャック袋へ。袋の外寸は 45 × 50 mm 以下、種は重ねず平らに。',3.2)}
         ${text(14,266,'この下の余白は切り落とします。',2.8)}
         <path d="M145 268H195M145 266V270M195 266V270" stroke="${INK}" stroke-width=".25"/>
         ${text(170,275,'この線は 50 mm',2.7,'text-anchor="middle"')}`
      : `${text(14,217,'B 面：外側  /  '+design.name,4)}
         ${text(14,226,'折り上がりは 64 × 64 mm。最後の翼を最初の翼の下へ差し込んで閉じます。',3.1)}
         ${text(14,233,'のり・シール・切り込みは不要。中の種の漏れ止めはチャック袋が担います。',3.1)}
         ${text(14,242,'イラストは AI 生成。実景を組み合わせた創作風景です（地図ではありません）。',2.8)}
         ${text(14,250,'デザイン CC BY 4.0  /  コード MIT',2.8)}
         ${text(14,257,'github.com/social-calculus/tane-tsutsumi',2.8)}`;
    return `<svg xmlns="${NS}" viewBox="0 0 210 297" width="210mm" height="297mm" role="img" aria-label="${esc(design.name+' '+side)}">
      <defs><clipPath id="${uid}"><rect x="6" y="6" width="198" height="198"/></clipPath></defs>
      <rect width="210" height="297" fill="white"/><g clip-path="url(#${uid})">${body}</g>${cropMarks()}${footer}
    </svg>`;
  }
  // A schematic of the already-collapsed pinwheel, NOT a rendered photograph.
  // Its four triangular wings each reflect into a half-square. Final stacking
  // is cyclic: bottom over left, right over bottom, top over right, left over top.
  function pinwheel(step=0,x=0,y=0,scale=1) {
    const a=64, palette=['#e5bd6b','#8cbbc0','#c67d5a','#91a876'];
    const open=[ [[64,64],[64,128],[0,128]], [[64,128],[128,128],[128,192]], [[128,64],[128,128],[192,64]], [[64,64],[128,64],[64,0]] ];
    const closed=[ [[64,64],[64,128],[128,128]], [[64,128],[128,128],[128,64]], [[128,64],[128,128],[64,64]], [[64,64],[128,64],[64,128]] ];
    const poly=(p,c)=>`<polygon points="${p.map(q=>q.join(',')).join(' ')}" fill="${c}" stroke="${INK}" stroke-width=".7"/>`;
    let out=`<rect x="64" y="64" width="64" height="64" fill="${PAPER}" stroke="${INK}" stroke-width=".7"/>`;
    for(let i=0;i<4;i++) out+=poly(i<step?closed[i]:open[i],palette[i]);
    if(step===4) out+=poly([[64,64],[64,128],[96,96]],palette[0]);
    return `<g transform="translate(${x} ${y}) scale(${scale})">${out}</g>`;
  }
  root.TANE = {S,A,OFF,BLEED,esc,text,qr,page,creasePattern,pinwheel};
})(typeof window==='undefined'?globalThis:window);
