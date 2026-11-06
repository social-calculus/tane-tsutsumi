// 既定デザイン。ここを書き換える（または画面で差し替える）だけで、別の町の包みになる。
// cover＝閉じたときの外側の絵、inside＝開くと出てくる大きな絵（紙を角が上になるように置いたときの上下で描く）。
// labels＝開いたときの小さな札。at は紙の中心からの位置（mm、右が +、下が +）。
window.TANE_DEFAULTS = {
  // 中央の QR（好きな URL に変えられる）
  qrUrl: 'https://x.com/iwami_kankou',
  qrTitle: '岩美のいまは、こちらから',
  qrNote: '岩美町の中の人（X）',
  // 外側の題（縦書き）
  title: 'いわみのたね',
  // 裏の表示欄（名称・内容量…の順にそのまま並ぶ）
  label: [
    ['名称', 'かぼちゃの種（栽培用）'],
    ['内容量', '3粒'],
    ['採種地', '鳥取県岩美町 岩美駅前'],
    ['採種日', '2026年11月'],
    ['品種', '何が育つかはお楽しみ'],
    ['注意', '食べられません。種子消毒なし。'],
    ['まきどき', '春（4〜5月ごろ）'],
  ],
  licenseText: 'この包みのデザインは CC BY 4.0 で、誰でも無料で使えます。',
  licenseQr: 'https://github.com/social-calculus/tane-tsutsumi',
};

window.TANE_DESIGNS = [
  {
    id: 'umi',
    name: 'うみ（浦富海岸）',
    color: '#1d4f5c',
    cover: 'designs/art/umi_cover.jpg',
    inside: 'designs/art/umi_inside.jpg',
    labels: [
      { title: '浦富海岸', line: '白い岩と松の海岸。', at: [0, -67] },
      { title: '島めぐり', line: '小島のあいだを\n遊覧船が行く。', at: [70, 52] },
      { title: '浦富の砂浜', line: '夏は海水浴でにぎわう。', at: [0, 67] },
      { title: '山陰海岸', line: '国立公園の海。', at: [-84, -28] },
    ],
  },
  {
    id: 'kani',
    name: 'かに（冬の港）',
    color: '#14233f',
    cover: 'designs/art/kani_cover.jpg',
    inside: 'designs/art/kani_inside.jpg',
    labels: [
      { title: '冬の岩美', line: '雪の山と日本海。', at: [0, -67] },
      { title: 'かに船', line: '松葉がにの漁船。', at: [66, 52] },
      { title: '田後港', line: 'かにが揚がる港。', at: [0, 67] },
      { title: '港の家並み', line: '雪をのせた屋根。', at: [-84, 30] },
    ],
  },
  {
    id: 'eki',
    name: 'えき（駅と温泉）',
    color: '#5c3a1e',
    cover: 'designs/art/eki_cover.jpg',
    inside: 'designs/art/eki_inside.jpg',
    labels: [
      { title: '秋の山', line: '町のまわりの山なみ。', at: [0, -67] },
      { title: '岩美駅', line: '赤い瓦に白い柱。', at: [62, 52] },
      { title: '駅前のかぼちゃ', line: 'この種の親です。', at: [0, 112] },
      { title: '岩井温泉', line: '山陰最古級の湯のまち。', at: [-84, 30] },
    ],
  },
];
