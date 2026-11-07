# HANDOFF

## 現在

pi（gpt-6.1-sol）→ A4を切らない本人式の包み、浦富海岸1款をmainとGitHub Pagesに公開済み。本人は従来レイアウトの家庭用プリンター試刷りを採用し、白線・全開の上四品／下四品を残したまま、字体・QR・種の案内を整えて公開する方針。元の絵と折法は変更していない。

- 日本語 **IBM Plex Sans JP**、英数字 **IBM Plex Sans**。Regular/MediumのTTF/WOFF2とOFLを同梱。
- 内側は「岩美町の中の人」の小さな誌面風デザインとX字入り静的QR。背面はGitHubと育て方の2コード。全コードに4モジュールの静区、XはH訂正。第三者QRサービスや短縮URLは使わない。
- 中身は **Big Max・観賞用・3粒**。育て方は岩美の畑で大果を狙う露地栽培で、十分な面積・親づると葉・人工授粉・一株一果・水肥・果実保護を扱う。一般食用の多収仕立てや鉢栽培ではない。
- READMEは22行。旧192 mm正方形の風車式・ブラウザー編集画面は現行配布から除き、Git履歴に残した。未選択の正面候補や参照写真は公開しない。

## 入口

- 公開ページ：<https://social-calculus.github.io/tane-tsutsumi/>
- 栽培案内：`grow.html`。Big Max品種資料と通用する大果栽培資料の出典・適用範囲を末尾に記載。25〜50 m²や地域の時期は本案内の目安で、品種の最低規格や収量保証ではない。
- 印刷：`dist/a4/uradome/print.pdf`、A4両面2ページ・長辺とじ・100%・裁紙なし。図入りの手順は同ディレクトリの `fold-guide.pdf`。
- 原画：`designs/a4/uradome/` の4枚。元名は `SOURCES.json`、権利とフォントは `ASSETS.md`、出稿方法は `SOL_BRIEF.md`。
- `tools/build_a4.py` が切り分け・配置・文字・QR・展開予想図、`build_guide.py` が折り方。`a4fold.py` の計算モデルは未変更。

## 検証と注意

- 回帰7件成功。4原画は裁切なし。2ページ/A4寸法、字体、静区、単体QR、背面の複数QR、HTML内リンクと栽培条件を検査。
- `check.json` は印刷面画像、`pdf-check.json` は**実際のPDFをPyMuPDFで再描画**し、3 URLを150/300 dpiで復号。標準OpenCVとAruco・0/±45度の結果を併用。背面の近い2コードは標準検出器だけでは一方を見落とすため、全てが全デコーダ／全角度で読めるとは書かない。
- `preflight.json` に入力ハッシュ・寸法・裁切・PDF寸法・字体・境界。`x_card.png` と `back_card.png` で原寸の文字・QRを見られる。
- `tools/check_site.py` をHandsのpi Braveでローカル版・公開版とも実行。390 px/1280 pxの両ページでIBM字体読込、画像、横はみ出し、ページエラーを確認。公開HTML2枚と配布PDFはローカルとバイト一致。ブラウザー証拠は宿主 `/var/tmp/hap0py/tane-tsutsumi-site-check/` と同名の `-live/`。
- 宿主GitはCursor/VSCodeのAskpassを継承する場合がある。pushは既存の `GITHUB_TOKEN` を正規の `source-agent-env.sh` で読み、APIで対象リポジトリ権限を確認して非対話認証する。パスワードを要求せず、トークンをファイルやremote URLに残さない。全局Git設定は変更していない。
- 計算プレビューと実物試刷りは別。従来版は本人が試刷り採用、**新版の3 QRのスマホ実読取は未確認**。紙端の白線は許容済みで、4.5 mmはプリンター不可印幅の想定値。絵の物産の形を正確な資料とは扱わない。
- `yakuho` の `work/`、参照画像、試験柄や写真対比、未選択候補はローカル作業材料。既存の未公開 `GPT_PROMPTS.md`・guide PNG・`a4_testart.py`・`a4fold_verify.py`・`contact.py` も勝手に消さない。

## 次

公開用コード・PDFのデジタル検証は完了。次に刷る1枚で、新字体の小字と3個のQRをスマホで確認する。残りの柄を自動生成したり、白線を消すために縮小・裁紙・折法変更をしない。
