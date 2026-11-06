# 画像・図・ライセンス

3柄とも、1枚の連続した AI 生成画を紙の両面に使います。名所の小画像を貼り合わせたものではありません。QR・日本語・裁ち位置・折り図は別のベクター要素です。

- 原画：2026-11-06、Yuzu Gemini の `pro` で生成。プロンプトは [`designs/prompts.json`](designs/prompts.json)。外部写真の複写・トレースはしていません。
- 公開画像：`designs/art/{umi,kani,eki}_scene.jpg`。ネイティブ1024 px。海の絵だけ生成された囲み罫を除くため周囲2.5%を裁ち、972 px。引き伸ばしやAI高解像度化はしていません。実効約125〜131 ppi、QRと文字はベクターです。コピー機での線・粒状感は試し刷りで確認します。
- 実景の複合イメージ：浦富海岸の白い岩と松、松葉がに、赤瓦の岩美駅、岩井温泉。建物や位置関係を正確に記録したものではありません。
- 折り構造の参照：[I Try DIY / Origami Square Envelope](https://itrydiy.me/2016/02/origami-square-envelope/)。参照先の写真・文章・ロゴは配布物に含めず、手順を独自に作図しています。`shots/*_closed.jpg` は構造模式図であり、実物写真でも紙の物理シミュレーションでもありません。
- 日本語フォント：ビルド環境の Noto CJK（SIL Open Font License）。PDFにサブセット埋め込み。SVGの文字は編集可能なまま残しています。
- `vendor/qrcode.js`：Kazuhiko Arase, QR Code Generator for JavaScript（MIT）。原作者のライセンス表記をファイル内に保持。

デザインは CC BY 4.0 / SOCIAL CALCULUS、コードは MIT。詳しくは [README](README.md#ライセンス)。
