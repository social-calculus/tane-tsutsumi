// Original vector diagrams of a traditional fold; no tutorial images copied.
import {readFileSync, writeFileSync, mkdirSync} from 'node:fs';
import vm from 'node:vm';
const scope={};scope.window=scope;vm.createContext(scope);
vm.runInContext(readFileSync('tane.js','utf8'),scope);
const {text,creasePattern,pinwheel}=scope.TANE;
const ink='#263b3d', red='#b85d3d';
const svg=(body)=>`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 210 297" width="210mm" height="297mm"><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="${red}"/></marker></defs><rect width="210" height="297" fill="#fffdf8"/>${body}</svg>`;
const arrow=d=>`<path d="${d}" fill="none" stroke="${red}" stroke-width=".7" marker-end="url(#arrow)"/>`;
const lines=(x,y,arr)=>arr.map((s,i)=>text(x,y+i*4.8,s,3)).join('');
const title=(n,s)=>text(12,18,`折り方 ${n}/2　${s}`,6)+text(12,27,'たとう包み・風車差し込み式  /  192 mm → 64 mm',3.3);
const card=(x,y,n,name,diagram,notes)=>`<g transform="translate(${x} ${y})"><rect width="90" height="104" rx="1" fill="white" stroke="#d3d7cc" stroke-width=".25"/>${text(4,9,n+'　'+name,3.7)}${diagram}${lines(4,83,notes)}</g>`;
const square=`<rect x="12" y="15" width="64" height="64" fill="#eef4ec" stroke="${ink}" stroke-width=".3"/>`;
let p1=title(1,'折り筋をつくる');
p1+=card(12,36,'1','三等分の折り筋',`<g transform="translate(12 15) scale(.333333)"><rect width="192" height="192" fill="#faf1d7" stroke="${ink}"/><path d="M64 0V192M128 0V192M0 64H192M0 128H192" stroke="#247f86" stroke-width="1.7" stroke-dasharray="5 3"/>${text(96,101,'QR',14,'text-anchor="middle"')}</g>`,['A 面（QR 側）を上に置く。縦横を','64 mm ずつに三等分し、折って戻す。','中央の四角の中には折り筋を付けない。']);
p1+=card(108,36,'2','四隅の対角線',`${square}<path d="M12 15L33.333 36.333M54.667 57.667L76 79M76 15L54.667 36.333M33.333 57.667L12 79" stroke="#bc6841" stroke-width=".7" stroke-dasharray="2 1"/><rect x="33.333" y="36.333" width="21.334" height="21.334" fill="#e8f2e8"/>${text(44,48,'折らない',3,'text-anchor="middle"')}`,['四隅の小さな四角だけ、図の斜め線で','折って戻す。長い対角線を紙全体に','通さず、中央を平らに残す。']);
p1+=card(12,147,'3','角を 2/3 の位置へ',`${square}<path d="M33.333 79L76 36.333" stroke="#726b97" stroke-width=".7" stroke-dasharray="2 1"/><circle cx="33.333" cy="36.333" r="1.5" fill="${red}"/>${arrow('M75 76 Q41 76 34 38')}${text(44,24,'他の3つの角も同じ',2.7,'text-anchor="middle"')}`,['右下の角を赤点へ（対角線の 2/3）。','折って戻す。同じことを4つの角で','行う。練習用紙の紫の線が目安。']);
p1+=card(108,147,'4','風車の形にたたむ',`${pinwheel(0,14,14,.32)}${arrow('M37 29 Q62 21 64 42')}${arrow('M52 68 Q28 77 26 55')}`,['4辺を少し立て、四隅をつまむ。','隣の辺を時計回りに倒して重ねる。','中央と4枚の三角の翼を平らにする。']);
p1+=lines(12,261,['力を入れてひねらず、折り筋に沿って畳みます。難しいときは練習用紙から。','手順4の立体動作は、下記の写真付き折り方も参照してください。']);
p1+=text(12,276,'itrydiy.me/2016/02/origami-square-envelope',2.8)+text(12,284,'折り方の参照先：I Try DIY「Origami Square Envelope」。この折り図は独自に作図。',2.6);
let p2=title(2,'入れて、差し込む');
p2+=card(12,36,'5','袋を置き、左を折る',`${pinwheel(0,14,14,.32)}<rect x="36" y="36.7" width="14.4" height="16" rx=".8" fill="#ffffffb0" stroke="${ink}" stroke-width=".3"/><path d="M37 39H49" stroke="${ink}" stroke-width=".4"/>${arrow('M20 49 Q34 32 44 46')}`,['チャックを閉じた種の袋を中央へ。','袋は外寸45 × 50 mm以下。種を重ねない。','左の三角の翼を内側へ折る。']);
p2+=card(108,36,'6','下、右の順に折る',`${pinwheel(1,14,14,.32)}${arrow('M49 71 Q30 62 46 47')}${arrow('M72 36 Q61 59 49 45')}${text(58,69,'② 下',2.6)}${text(66,53,'③ 右',2.6)}`,['左を押さえ、下の翼を折る。','次に右の翼を折る。','順序は 左 → 下 → 右 → 上。']);
p2+=card(12,147,'7','最後の翼を差し込む',`${pinwheel(3,14,14,.32)}${arrow('M36 18 Q60 31 43 44')}<path d="M34.5 35L44.7 45.2" stroke="${red}" stroke-width="1.4"/>${text(54,63,'この縁の下',2.8)}<path d="M55 59L40 41" stroke="${red}" stroke-width=".4"/>`,['上の翼を下へ折る。左の翼の縁を','少し持ち上げ、上の翼の左半分を','その下に差し込む。上に載せるだけは不可。']);
p2+=card(108,147,'8','閉じた形',`${pinwheel(4,-20,-17,.67)}<path d="M23 73H66M23 71V75M66 71V75" stroke="${ink}" stroke-width=".3"/>${text(44.5,79,'64 mm',2.7,'text-anchor="middle"')}`,['4枚が輪のように重なれば完成。','開けるときは上の翼をゆっくり抜く。','図は構造模式図で、実物写真ではありません。']);
p2+=text(12,263,'11/8 試し刷り → 11/11 本刷り（各柄20枚・計60枚）',3.6);
p2+=lines(12,270,['□ 50 mm の線が実寸　□ 表裏の裁ち位置のずれが 2 mm 以内','□ 2つの QR を実機で読む　□ 実袋を入れて10回開閉・10回軽く振る','□ 逆さに30秒保持し、翼が抜けず袋が出ないことを確認してから本刷り']);
const practice=svg(`${text(14,216,'原寸練習用紙  /  A4・片面・100%',5)}${creasePattern(9,9)}
<rect x="82.5" y="80" width="45" height="50" rx="1" fill="none" stroke="#677b70" stroke-width=".3" stroke-dasharray="1 1"/>
${text(105,137,'点線の枠 = 袋の最大外寸 45 × 50 mm',2.2,'text-anchor="middle"')}
${lines(14,226,['外枠192 mm角で裁断。青 → 茶 → 紫の順に折り筋を付け、いったん開く。','中央64 mm角は折らない。折り筋を付け終えたら「折り方」手順4へ。','白いコピー用紙 70〜90 g/m² 推奨。まず実際の種と袋を入れて確認。','印刷・QR・寸法はデジタル検査済み。紙厚・摩擦・保持力の実測は別です。'])}
<path d="M14 260H64M14 258V262M64 258V262" stroke="${ink}" stroke-width=".3"/>${text(39,268,'この線が50 mmなら原寸',3,'text-anchor="middle"')}${text(14,285,'CC BY 4.0 / SOCIAL CALCULUS',2.7)}`);
mkdirSync('dist',{recursive:true});
writeFileSync('dist/fold-1.svg',svg(p1));writeFileSync('dist/fold-2.svg',svg(p2));writeFileSync('dist/practice.svg',practice);
writeFileSync('dist/guide.html',`<!doctype html><html lang="ja"><meta charset="utf-8"><title>折り方</title><style>@page{size:A4;margin:0}body{margin:0}svg{display:block;width:210mm;height:297mm;break-after:page}svg:last-child{break-after:auto}</style>${svg(p1)}${svg(p2)}</html>`);
writeFileSync('dist/practice.html',`<!doctype html><html lang="ja"><meta charset="utf-8"><style>@page{size:A4;margin:0}body{margin:0}svg{display:block;width:210mm;height:297mm}</style>${practice}</html>`);
