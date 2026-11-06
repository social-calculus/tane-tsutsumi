// 既定デザイン。ここを書き換える（または画面で差し替える）だけで、別の町の包みになる。
// front＝閉じたときの外側の絵、top/right/bottom/left＝角を開いたときの内側の絵（＋ひとこと）。
window.TANE_DEFAULTS = {
  // 中央の QR（好きな URL に変えられる）
  qrUrl: 'https://x.com/iwami_kankou',
  qrTitle: '岩美のいまは、こちらから',
  qrNote: '岩美町の中の人（X）',
  // 外側の題と小さな説明
  title: 'いわみのたね',
  subtitle: '岩美駅前で育ったかぼちゃのこども',
  // 裏の表示欄（名称・内容量…の順にそのまま並ぶ）
  label: [
    ['名称', 'かぼちゃの種（栽培用）'],
    ['内容量', '3粒'],
    ['採種地', '鳥取県岩美町 岩美駅前'],
    ['採種日', '2026年11月'],
    ['品種', '何が育つかはお楽しみ'],
    ['注意', '食べられません。種子消毒はしていません。'],
    ['まきどき', '春（4〜5月ごろ）'],
  ],
  licenseText: 'この包みのデザインは、CC BY 4.0 で誰でも無料で使えます。',
  licenseQr: 'https://github.com/social-calculus/tane-tsutsumi',
};

window.TANE_DESIGNS = [
  {
    id: 'kani',
    name: 'かに',
    color: '#16233f',
    front: 'designs/art/kani_front.jpg',
    top: { img: 'designs/art/kani_top.jpg', title: '松葉がに', line: '冬の日本海の主役。' },
    right: { img: 'designs/art/kani_right.jpg', title: '親がに', line: '山陰では、\nメスをこう呼びます。' },
    bottom: { img: 'designs/art/kani_bottom.jpg', title: 'もさえび', line: '冬に水揚げされる小さなえび。' },
    left: { img: 'designs/art/kani_left.jpg', title: 'ばばちゃん', line: '深い海の魚、\nタナカゲンゲ。' },
  },
  {
    id: 'umi',
    name: 'うみ',
    color: '#14535c',
    front: 'designs/art/umi_front.jpg',
    top: { img: 'designs/art/umi_top.jpg', title: '千貫松島', line: '岩のアーチのてっぺんに松が一本。' },
    right: { img: 'designs/art/umi_right.jpg', title: '遊覧船', line: '浦富海岸を、\n海から見る。' },
    bottom: { img: 'designs/art/umi_bottom.jpg', title: 'シーカヤック', line: '澄んだ海を、自分の手でこぐ。' },
    left: { img: 'designs/art/umi_left.jpg', title: 'あかもく', line: '田後漁港の\n海藻。' },
  },
  {
    id: 'eki',
    name: 'えき',
    color: '#7a2e1c',
    front: 'designs/art/eki_front.jpg',
    top: { img: 'designs/art/eki_top.jpg', title: '岩美駅', line: '赤い瓦に白い柱。' },
    right: { img: 'designs/art/eki_right.jpg', title: '駅前のかぼちゃ', line: 'この種の親。\n駅前で育ちました。' },
    bottom: { img: 'designs/art/eki_bottom.jpg', title: '岩井温泉', line: '頭に手ぬぐい、ひしゃくで「湯かむり」。' },
    left: { img: 'designs/art/eki_left.jpg', title: '干物', line: '田後漁港の\nカレイの干物。' },
  },
];
