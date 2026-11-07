# HANDOFF

## 現在

完成。公開の `print.pdf` が正本で、デザインはここで止める。ローカルの正本は `/srv/archive/tane-tsutsumi`（`main`）。`/srv/hot` の副本と `yakuho` 作業樹は捨てた。未公開の下書きと参照写真は公開していない。

印刷物：

- 公開：<https://social-calculus.github.io/tane-tsutsumi/dist/a4/uradome/print.pdf>
- 折り方：同じ場所の `fold-guide.pdf`。A4両面・長辺とじ・100%・裁紙なし。1ページ目が内側。
- 赤い角印は、岩美町の中の人の X QR がある内側だけ。見た目の右上に、直角を紙の角へ置き、上辺と右辺に隙間なく沿わせる（一辺 12 mm）。外側には赤印を入れない。
- 折り順・絵・文言・QR の中身は変えていない。最初の長い折りは、赤印がある右上側。

中身は Big Max 由来・観賞用・3粒。育て方は岩美の露地で大果を狙う案内。日本語は IBM Plex Sans JP、英数字は IBM Plex Sans。

## 入口

- 公開ページ：<https://social-calculus.github.io/tane-tsutsumi/>、栽培案内：`grow.html`。
- 原画：`designs/a4/uradome/` の4枚。権利とフォントは `ASSETS.md`。ビルド手順は `SOL_BRIEF.md`。
- 赤印は `tools/build_a4.py` の `corner_mark`。文言と QR は同ファイル冒頭の `CONF`・`X_QR`・`TONGUE_QR`。

## 検証と注意

- 回帰13件成功。内側右上の紙端画素が赤であること、外側の両上角に赤印がないことを含む。QR は 150/300 dpi で3 URL を復号。
- 家庭用プリンターは紙端約 4.5 mm を刷れないことがある。PDF 自体は紙端まで赤印を置く。届かない分は白く欠ける。
- スマホ実読取は、赤印を紙端へ移す前の試刷りで本人が採用済み。QR の中身と位置はこの移動で変えていない。赤印だけを端へ寄せた版の再印刷はしていない。
- push は `GITHUB_TOKEN` を `source-agent-env.sh` で読み、非対話で認証する。トークンをファイルや remote URL に残さない。

## 次

なし
