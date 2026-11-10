# 素材とライセンス

## 絵・型紙・文章

CC BY 4.0 / SOCIAL CALCULUS。ライセンス本文は [LICENSE](LICENSE)。コードは [LICENSE-CODE](LICENSE-CODE) の MIT です。依存ライブラリには各ライセンスが適用されます。AIのみの出力に著作権が成立しない地域・範囲では、CC BYの条件もその範囲には及びません。岩美町の公式制作物ではありません。

- 現在の原画：`designs/a4/uradome/{front,scroll,hexagon,flat}.png`。本人がWeb GPTで生成して提供した4枚を、裁切・描き足し・AI拡大なしで使用しています。ピクセル寸法・SHA-256は `dist/a4/uradome/preflight.json`、元ファイルとの対応は `designs/a4/uradome/SOURCES.json`。
- 風景・物産は絵としての複合イメージです。実景の位置関係や、物産の形を正確に示す資料ではありません。全開図の上四品・下四品と、帯の継ぎ目は本人が試刷りを見たうえで採用した構成です。
- 折り方：本人のA4一枚折りを計算モデルにしたもの。192 mm正方形から作る旧風車式ではありません。実物写真・参照写真は配布データに含めません。展開・折り予想図は計算プレビューで、実物写真ではありません。
- 赤い角印は内側（XのQRがある面）の右上だけ。紙の角に隙間なく置き、外側には入れない。角印、折り線、文字、QR、背面表示、舌の案内はビルド時に追加。内側の札は下の絵を透かす薄紙で、中央の蟹は `flat.png` からの切り抜き。舌の波は `hexagon.png` からの切り抜き、舌のかぼちゃはビルド時に描く小さな目印です。原画ファイル自体は変更しません。PDFは300 dpiのラスター画像2ページで、フォントを別途インストールしなくても印刷できます。印刷所向けPSD（`tools/build_printshop.py`）は同じ配置を350 ppi・塗り足し3 mmで描き、AdobeのJapan Color 2001 CoatedでCMYKにします。ICCプロファイルは同梱していません。

## フォント

日本語は **IBM Plex Sans JP**、英数字は **IBM Plex Sans**。いずれもIBM公式リポジトリの未改変 Regular / Medium を同梱しています。

- 出典：[IBM/plex](https://github.com/IBM/plex)、取得リビジョン `48e8676114c04f29033b4b53da4ec579f8846297`。
- 印刷用TTFとWeb用WOFF2：`vendor/fonts/`。
- 著作権・SIL Open Font License 1.1：[日本語](vendor/fonts/OFL-JP.txt) / [英数字](vendor/fonts/OFL-Sans.txt)。フォント自体はCC BYではありません。

## QR

Segnoで静的URLをローカル生成します。第三者の短縮URL・有料動的QR・アクセス追跡は使いません。Xのアカウントへのリンクを載せた独自デザインで、X公式のプロフィールQRではありません。Xは各権利者の商標です。

全コード共通で、データ部は液状の丸み、色は藍から海色へのぼかし、位置検出パターンは読み取りを優先した控えめな角丸、静区は4モジュール。

- 内側：`https://x.com/iwami_kankou`。バージョン6・誤り訂正H、モジュール約0.93 mm、中央に蟹。
- 舌（ふたを上げた面）：Big Maxの育て方と、GitHubの絵と型紙。どちらもバージョン5・誤り訂正Q、モジュール約0.76 mmの同じ大きさ。中央にかぼちゃと岩美の印。

デジタル復号は `check.json` と `pdf-check.json`、印刷と撮影の模擬は `scan-sim.json`（`tools/scan_sim.py`）。実物スマホでの読み取りは試刷りで確認します。

## 栽培案内

`grow.html` は **Big Max・観賞用・露地で大果**を狙うための文章です。品種資料と大学Extension等の大果栽培技術を参照し、本文末尾に出典と適用範囲を記載しています。資料の写真・図・本文の転載はありません。
