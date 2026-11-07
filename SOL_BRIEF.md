# 岩美のたね：出稿

本人の原画を配置して、A4両面PDFと折り予想図にする。現在の状態・本人の確認範囲は `HANDOFF.md`、素材の権利とフォントは `ASSETS.md`。

## 入力

`designs/a4/<題材名>/` に `front.png`（1:1）、`scroll.png`（1:2.828）、`hexagon.png` と `flat.png`（各1:1.414）。比率差1%以内はそのまま使い、超える場合は中央裁切するので、出力の寸法と主体を必ず確認する。今回の `uradome` は4枚とも裁切なし。

原画を描き足さない。足りない絵は本人に伝える。折法と絵はすでに本人が実物試刷りを見て採用しているため、印刷白線や帯の継ぎ目を理由に勝手に修正しない。Yuzuでの再生成は本人が明示した場合のみ。

## ビルドと検査

この樹は完成済みで、ローカル正本は `/srv/archive/tane-tsutsumi`。公開PDFを正とし、柄や折りを足さない。フォントはリポジトリ内のIBM Plexを使い、ホストのフォントには依存しない。作り直すときだけ、樹を `/srv/hot` か `/srv/oneoff` に戻してからHandsのpi槽で実行する（アーカイブパスのままでは `hands-exec` が受け付けない）。

```sh
hands-exec pi /srv/hot/tane-tsutsumi -- env \
  UV_PROJECT_ENVIRONMENT=/var/cache/hap0py/venv/pi/tane-tsutsumi \
  uv run python tools/build_a4.py uradome
```

同じ実行環境で `tools/build_guide.py uradome`、`python -m unittest discover -s tools -p 'test_*.py'` も実行する。QRを変えたら `tools/verify_pdf.py uradome`（要 `--group dev`）と `tools/scan_sim.py uradome` も実行する。成果物は `dist/a4/uradome/`。

- `print.pdf`：300 dpi、A4 2ページ（内側→外側）。長辺とじ、100%、裁紙なし。
- `overview.jpg`：各層の向きと絵。`flap_open.jpg`：ふたを上げて舌が見える状態。`overview_printer_margin.jpg`：既定4.5 mmの不可印幅の想定。
- `x_card.png`、`back_card.png`、`tongue_card.png`：文字と3個のQRを原寸確認。
- `check.json`：印刷面画像を300/150 dpiで zxing-cpp 復号。`pdf-check.json`：実際のPDFを再描画して復号。
- `scan-sim.json`：印刷と撮影の模擬。zxing-cpp に、環境にあれば zbar と WeChat を加えて比べる。OpenCV標準は丸い位置検出パターンと2コード同時の画面が苦手なので合否に使わない。位置検出パターンの角丸を大きくすると zbar の成績が急に落ちるので、`EYE_RADII` を変えたら必ず測り直す。
- `preflight.json`：入力の寸法・裁切・ハッシュ、PDFのページ数と寸法、フォント、検証境界。

デジタル復号は実機のスマホや印刷品の検査ではない。公開する正本は浦富海岸の1款だけ。未採用の下書きと参照写真は公開物に入れない。
