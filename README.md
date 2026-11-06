# 種つつみ（tane-tsutsumi）

四隅を折る、薬包のような種の包みです。絵と QR を差し替えて、A4 で印刷できます。誰でも無料で使えます。

既定のデザインは、鳥取県岩美町の駅前で育ったかぼちゃの種を配るために作りました。

- **絵を差し替えて使う：** https://social-calculus.github.io/tane-tsutsumi/ （ブラウザだけで動きます。入れた絵はどこにも送られません）
- **そのまま印刷する：** [`dist/tane-tsutsumi_iwami_a4.pdf`](dist/tane-tsutsumi_iwami_a4.pdf)（3 デザイン・両面 6 ページ）

## 作り方

1. 両面、**長辺とじ**、倍率 100% で A4 に印刷します。ふつうのコピー用紙が折りやすいです。
2. 点線の 4 辺を切ります（約 19.8cm 四方）。下の部分は捨てます。
3. QR のある面を上にして、種の袋を真ん中に置きます。
4. 斜めの点線で四隅を中心へ折り、丸シールでとめます。約 14cm 四方になります。

## 差し替える

ページの画面で、デザインごとに外側の絵 1 枚と角の絵 4 枚を選び、中央の QR の行き先と文字を変えられます。「印刷する」から PDF に保存できます。

手元で作るなら、`designs/designs.js` を書き換えて `index.html` を開きます。絵は正方形を用意してください。折り上がりの版面の計算は `tane.js` にあります。

## ライセンス

- デザイン（絵・版面・文章）：[CC BY 4.0](LICENSE)
- コード：[MIT](LICENSE-CODE)
- 表示の例：「種つつみ（SOCIAL CALCULUS）を改変」と、このページへのリンク

既定の絵は AI で生成しました。国によっては著作権が生じない場合があり、その範囲では CC BY の条件もかかりません。

このデザインは岩美町の公式なものではありません。町章やキャラクターは含みません。別の用途で使うときは、中央の QR と裏の表示欄を自分のものに差し替えてください。

種を配るときは、登録品種でないことを確かめ、「食べられません」など必要な表示を入れてください。

---

## English

A seed packet you fold from one sheet of A4, like an old paper medicine wrap. Swap the pictures and the QR code in your browser and print. Free to use under [CC BY 4.0](LICENSE); the code is [MIT](LICENSE-CODE). The default design comes from pumpkins grown in front of Iwami Station, Tottori, Japan.

Print double-sided (flip on long edge) at 100%, trim the four dashed lines, put the seeds in the middle, and fold the four corners to the center. The default artwork is AI-generated. This project is not an official work of Iwami Town.
