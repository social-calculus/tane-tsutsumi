# HANDOFF

## 現在

完成。デザインはここで止める。ローカル正本は `/srv/archive/tane-tsutsumi`（`main`、GitHub と同期）。未公開の下書きと参照写真は公開していない。

- 赤い角印：内側（岩美町の中の人の X QR がある面）の右上だけ。直角を紙の角に合わせ、上辺・右辺に隙間なく沿わせる（辺 12 mm）。外側には入れない。2026-11-10 本人指示。11/7 に一度入れて戻した紙端版は、家庭用プリンターでは紙端が刷れず角印が欠ける。今回は印刷所のふちなしで刷るので採用。
- 今回の再ビルドは、11/7 採用版 PDF（`e07965542674e65b0555061328b3ca2e`）と比べて角の周り以外は 1 画素も変わっていない。折り順・絵・文言・QR はそのまま。
- 印刷所入稿：`tools/build_printshop.py` が プリントパック の Photoshop 入稿仕様（片面 1 ファイル、216×303 mm、350 ppi、CMYK、総インキ量 300% 以下、統合済み、天と天）で PSD 2 枚と zip を `dist/a4/uradome/printshop/` に作る（Git 外）。

印刷物：

- 公開：<https://social-calculus.github.io/tane-tsutsumi/dist/a4/uradome/print.pdf>（A4・塗り足しなし・RGB 300 dpi）。家庭用でも折れるが、紙端が白く残り角印は欠ける。
- 折り方：同じ場所の `fold-guide.pdf`。1 ページ目が内側。手順 1・3 は「右上の赤い角印」を目印にする（折り 3 の線 x+y=297 と同じ側）。

## 入口

- 公開ページ：<https://social-calculus.github.io/tane-tsutsumi/>、栽培案内：`grow.html`。
- 原画：`designs/a4/uradome/` の 4 枚。権利とフォントは `ASSETS.md`。ビルドと入稿の手順は `SOL_BRIEF.md`。
- 角印は `tools/build_a4.py` の `corner_mark`、塗り足しと解像度は `Grid`。文言と QR は同ファイル冒頭の `CONF`・`X_QR`・`TONGUE_QR`。

## 検証と注意

- 印刷所 PSD：Pillow・psd-tools で読み戻し一致（CMYK 8 bit、レイヤーなし、350 ppi、Japan Color 2001 Coated 埋め込み）。総インキ量は最大 300.0%。CMYK を画面色に戻した確認画像で 3 個の QR を 300/150 dpi 相当・0/±45 度で復号。塗り足しは絵を鏡映しで延ばし、角印は斜辺ごと外へ延ばす。実物の印刷・断裁ずれ・スマホ読み取りは未確認。
- PSD の CMYK は 0＝版いっぱいの反転値で書く（Pillow・psd-tools・Photoshop 共通）。逆にすると陰画になる。
- Hands の claude 槽には zbar・WeChat の復号器がない。`scan-sim.json` は QR が変わっていないので pi 槽で測った 11/7 の値のまま。
- push は `GITHUB_TOKEN` を `source-agent-env.sh` で読み、非対話で認証する。トークンをファイルや remote URL に残さない。

## 次

- 印刷所の納品物で、角印が紙の角まで届いているか・3 個の QR・折りを確かめる。担当：本人、11/14 の会場前。
