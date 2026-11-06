// Replace ONE image per design. Both paper faces use that same whole painting.
// QR codes and Japanese type are vector elements, never AI-painted.
window.TANE_DEFAULTS = {
  title: 'いわみのたね',
  qrUrl: 'https://x.com/iwami_kankou',
  qrTitle: '岩美町の中の人',
  qrNote: 'X  /  @iwami_kankou',
  label: [
    ['名称', 'かぼちゃの種（栽培用）'],
    ['内容量', '3粒'],
    ['採種地', '鳥取県岩美町 岩美駅前'],
    ['採種', '2026年11月'],
    ['注意', '食べられません'],
    ['ひとこと', '何が育つかはお楽しみ']
  ],
  licenseQr: 'https://github.com/social-calculus/tane-tsutsumi'
};
window.TANE_DESIGNS = [
  {id:'umi',name:'海から、ひと粒',subtitle:'浦富海岸',art:'designs/art/umi_scene.jpg'},
  {id:'kani',name:'港の実り',subtitle:'松葉がにと岩美の港',art:'designs/art/kani_scene.jpg'},
  {id:'eki',name:'湯けむりの帰り道',subtitle:'岩井温泉から岩美駅へ',art:'designs/art/eki_scene.jpg'}
];
