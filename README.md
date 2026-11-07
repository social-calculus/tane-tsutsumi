# 岩美のたね

**A4を切らずに折る、7.4 cm角の種の包み。** 開くたびに浦富海岸と岩美八宝の絵が現れます。中身は観賞用かぼちゃ **Big Max** の種、3粒。

[印刷用PDF](dist/a4/uradome/print.pdf) · [折り方](dist/a4/uradome/fold-guide.pdf) · [展開プレビュー](dist/a4/uradome/overview.jpg) · [Big Maxの育て方](https://social-calculus.github.io/tane-tsutsumi/grow.html) · [公開ページ](https://social-calculus.github.io/tane-tsutsumi/)

## 印刷

A4・両面・**長辺とじ／実際のサイズ100%**。1ページ目が内側、2ページ目が外側です。紙は切らず、最後の舌を差し込みます。ふちなし印刷は不要で、印刷できない紙端は白線として残ります。まず1枚で表裏・折り・3個のQRを確かめてください。

## つくり替える

`designs/a4/uradome/` に4枚の原画、`tools/` に配置・QR・折りの計算ツールがあります。日本語は IBM Plex Sans JP、英数字は IBM Plex Sans。フォントは同梱済みです。

```sh
uv sync --locked
uv run python tools/build_a4.py uradome
uv run python tools/build_guide.py uradome
uv run python -m unittest discover -s tools -p 'test_*.py'
```

絵・型紙・文章：**CC BY 4.0 / SOCIAL CALCULUS**。コード：**MIT**。フォント：**SIL OFL 1.1**。[素材とライセンス](ASSETS.md)
