# 岩美のたね：出稿

本人の原画を配置して、A4両面PDFと折り予想図にする。現在の状態・本人の確認範囲は `HANDOFF.md`、素材の権利とフォントは `ASSETS.md`。

## 入力

`designs/a4/<題材名>/` に `front.png`（1:1）、`scroll.png`（1:2.828）、`hexagon.png` と `flat.png`（各1:1.414）。比率差1%以内はそのまま使い、超える場合は中央裁切するので、出力の寸法と主体を必ず確認する。今回の `uradome` は4枚とも裁切なし。

原画を描き足さない。足りない絵は本人に伝える。折法と絵はすでに本人が実物試刷りを見て採用しているため、印刷白線や帯の継ぎ目を理由に勝手に修正しない。Yuzuでの再生成は本人が明示した場合のみ。

## ビルドと検査

hap0pyではHandsのpi槽で実行する。フォントはリポジトリ内のIBM Plexを使い、ホストのフォントには依存しない。

```sh
hands-exec pi /srv/hot/tane-tsutsumi-yakuho -- env \
  UV_PROJECT_ENVIRONMENT=/var/cache/hap0py/venv/pi/tane-tsutsumi-yakuho \
  uv run python tools/build_a4.py uradome
```

同じ実行環境で `tools/build_guide.py uradome`、`python -m unittest discover -s tools -p 'test_*.py'` も実行する。成果物は `dist/a4/uradome/`。

- `print.pdf`：300 dpi、A4 2ページ（内側→外側）。長辺とじ、100%、裁紙なし。
- `overview.jpg`：各層の向きと絵。`overview_printer_margin.jpg`：既定4.5 mmの不可印幅の想定。
- `x_card.png` と `back_card.png`：文字と3個のQRを原寸確認。
- `check.json`：印刷面画像を300/150 dpiで復号。OpenCV標準とArucoの検出結果を併用する。二つのQRが近い背面ではArucoが必要になるため、標準デコーダだけで全コードが読めたとは書かない。
- `preflight.json`：入力の寸法・裁切・ハッシュ、PDFのページ数と寸法、フォント、検証境界。

デジタル復号は実機のスマホや印刷品の検査ではない。新しいQRや文字位置を変更したら、本人に再度実物で見てもらう。原画、他人の未コミット変更、未選択の別柄を勝手に変更・削除しない。
