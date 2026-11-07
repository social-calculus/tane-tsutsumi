# HANDOFF

## 現在

完成。公開の `print.pdf` が正本で、デザインはここで止める。ローカルの正本は `/srv/archive/tane-tsutsumi`（`main`）。`/srv/hot` の副本と `yakuho` 作業樹は捨てた。未公開の下書きと参照写真は公開していない。

印刷物：

- 公開：<https://social-calculus.github.io/tane-tsutsumi/dist/a4/uradome/print.pdf>
- 折り方：同じ場所の `fold-guide.pdf`。A4両面・長辺とじ・100%・裁紙なし。1ページ目が内側。
- 赤い角印は、紙端へ寄せる前の採用版に戻した。両面の同じ隅、端から約 7 mm。紙端へ移した版は全体の見え方がずれたため破棄。
- 折り順・絵・文言・QR の中身は、採用版から変えていない。

中身は Big Max 由来・観賞用・3粒。育て方は岩美の露地で大果を狙う案内。日本語は IBM Plex Sans JP、英数字は IBM Plex Sans。

## 入口

- 公開ページ：<https://social-calculus.github.io/tane-tsutsumi/>、栽培案内：`grow.html`。
- 原画：`designs/a4/uradome/` の4枚。権利とフォントは `ASSETS.md`。ビルド手順は `SOL_BRIEF.md`。
- 赤印は `tools/build_a4.py` の `corner_mark`。文言と QR は同ファイル冒頭の `CONF`・`X_QR`・`TONGUE_QR`。

## 検証と注意

- 公開する `print.pdf` は、紙端へ赤印を移す前に本人が採用したファイルと同一（ハッシュ `e07965542674e65b0555061328b3ca2e`）。作り直さず、その版をそのまま戻した。
- 家庭用プリンターは紙端約 4.5 mm を刷れないことがある。採用版の赤印はその内側にある。
- push は `GITHUB_TOKEN` を `source-agent-env.sh` で読み、非対話で認証する。トークンをファイルや remote URL に残さない。

## 次

なし
