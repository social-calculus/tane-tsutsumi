# 岩美のたね

**A4を切らずに折る、7.4 cm角の種の包み。** 開くたびに浦富海岸と岩美八宝の絵が現れます。中身は観賞用かぼちゃ **Big Max** の種、3粒。

[印刷用PDF](dist/a4/uradome/print.pdf) · [折り方](dist/a4/uradome/fold-guide.pdf) · [展開プレビュー](dist/a4/uradome/overview.jpg) · [Big Maxの育て方](https://social-calculus.github.io/tane-tsutsumi/grow.html) · [公開ページ](https://social-calculus.github.io/tane-tsutsumi/)

## 印刷

A4・両面・**長辺とじ／実際のサイズ100%**。1ページ目が内側、2ページ目が外側です。紙は切らず、最後の舌を差し込みます。舌には育て方と型紙のQRがあり、ふたを上げると最初に見えます。絵と、内側右上の赤い角印は紙の端まであります。いちばんきれいなのは印刷所のふちなし（塗り足し付き）印刷です。家庭用プリンターでも折れますが、紙端が白い線として残り、角印は小さく欠けます。まず1枚で表裏・折り・3個のQRを確かめてください。

印刷所への入稿データは `tools/build_printshop.py` で作ります。片面1ファイル、塗り足し3 mm（216×303 mm）、350 ppi、CMYK（Japan Color 2001 Coated）、総インキ量300%以下の統合済みPSDです。両面とも画像の上が天で、天と天を合わせれば長辺とじと同じ表裏になります。サイズが大きいため、PSDはリポジトリに入れていません。

## つくり替える

`designs/a4/uradome/` に4枚の原画、`tools/` に配置・QR・折りの計算ツールがあります。日本語は IBM Plex Sans JP、英数字は IBM Plex Sans。フォントは同梱済みです。

```sh
uv sync --locked
uv run python tools/build_a4.py uradome
uv run python tools/build_guide.py uradome
uv run python tools/build_printshop.py uradome --profile JapanColor2001Coated.icc  # 印刷所向け（ICCはAdobe配布のものを別途用意）
uv run python -m unittest discover -s tools -p 'test_*.py'
```

絵・型紙・文章：**CC BY 4.0 / SOCIAL CALCULUS**。コード：**MIT**。フォント：**SIL OFL 1.1**。[素材とライセンス](ASSETS.md)
