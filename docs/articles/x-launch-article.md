# X 公開記事ドラフト: BtoB Project Memory Template

## X 投稿文

LLM に業務を手伝ってもらうとき、いちばん難しいのは「良いプロンプトを書くこと」よりも「必要なコンテキストを渡し続けること」だと思っています。

特に BtoB 取引は、商談、導入、運用、更新、社内調整が長く続きます。議事録、チャット、資料、CRM、手元メモに情報が散り、顧客ごとの境界も守る必要があります。

そこで、BtoB の顧客対応・商談・社内プロジェクトを LLM が読める形で蓄積するテンプレートを公開しました。

https://github.com/TsutomuTomizawa/btob-project-memory-template

fork ではなく、GitHub の `Use this template` から各チームの private repository として使う想定です。

## X Article 本文

# LLM に BtoB の文脈を渡すための memory vault テンプレートを公開しました

LLM を業務で使うとき、モデルの性能やプロンプトの書き方はもちろん大事です。

ただ、実際に使っていて一番効くのは「コンテキストをどう渡すか」だと感じています。

商談の背景、過去の約束、相手の関心、社内の判断理由、未解決のリスク、次に取るべきアクション。こうした文脈が抜けていると、LLM はそれっぽい一般論を返します。

逆に、必要な文脈が揃っていると、LLM はかなり具体的に手伝えます。

たとえば、

- 次回商談に向けた論点整理
- 顧客向けの共有文
- 提案資料の修正方針
- 社内プロジェクトの進捗整理
- 未完了タスクやリスクの洗い出し
- 月次の振り返り

こういう仕事は、文脈があるほど質が上がります。

## BtoB ではコンテキストを渡すのが難しい

BtoB 取引や社内プロジェクトでは、文脈がとにかく散らばります。

- 商談、導入、運用、更新、請求、社内調整が数週間から数か月にまたがる
- 顧客ごと、部門ごと、担当者ごとに前提や関心が違う
- 議事録、チャット、Google Workspace、CRM、手元メモに情報が分散する
- 結果だけ残り、「なぜそう判断したか」が抜け落ちる
- ほかの顧客情報、内部懸念、非公開 URL、契約条件を混ぜてはいけない
- 毎回すべてをプロンプトに貼るには長すぎる

つまり、LLM に「全部読んでおいて」と渡すには重すぎるし、人間が毎回必要な情報だけを選ぶのも大変です。

そこで、LLM に全部覚えさせるのではなく、必要な文脈を安全に取り出せる構造を作ることにしました。

## 公開したもの

`BtoB Project Memory Template` という repository を公開しました。

https://github.com/TsutomuTomizawa/btob-project-memory-template

これは、BtoB の顧客対応、商談メモ、導入・納品プロジェクト、更新商談、社内プロジェクトを entity 別に管理するための memory vault テンプレートです。

Obsidian vault として人間が読めて、Codex や Claude Code などのエージェントが repository 内の skill に従って更新する想定です。

## どういう構造か

情報を用途ごとに分けています。

- `events/`: いつ何が起きたかを残す追記専用の時系列記録
- `raw/`: 議事録や長文メモの原本
- `profile.md`: 長く使う背景、判断軸、制約、関係性
- `states/current.md`: 現在の状態、未完了タスク、リスク、次アクション
- `sources.md`: LLM が継続的に参照してよい外部資料の索引
- `.agentic/skills/`: 保存、digest、query、output の読み書き手順

ポイントは、原本と使いやすい文脈を分けていることです。

議事録や長文メモは `raw/` に残します。そこから「何が起きたか」を `events/` に追記します。そして重要な変化だけを `profile.md` と `states/current.md` に反映します。

これを繰り返すと、顧客や社内プロジェクトごとに、LLM が読むべき文脈が少しずつ育っていきます。

## データが育つ流れ

基本の流れはこうです。

1. 人間が議事録、メモ、URL、決定事項、修正依頼をエージェントに渡す
2. エージェントが `scripts/memory save ...` で保存用 prompt を作る
3. `memory-save` が raw note と薄い event を作る
4. `memory-digest` が event から `profile.md` と `states/current.md` を更新する
5. 次回以降、LLM は `profile.md`、`states/current.md`、必要に応じて `sources.md` を読んで回答や提案を作る
6. その会話や決定もまた保存され、memory が育つ

この循環が大事です。

単発のプロンプトではなく、仕事の文脈を repository に積み上げていく。そうすると、LLM は毎回ゼロから説明されなくても、対象顧客や社内プロジェクトの前提を読めるようになります。

## 安全性の考え方

BtoB では、便利さだけでなく安全性も重要です。

このテンプレートでは、顧客ごと、社内プロジェクトごとに entity を分けます。別顧客の情報を混ぜない、event を後から直接書き換えない、顧客向け draft に内部懸念を混ぜない、外部資料は `sources.md` に登録されたものだけを使う、といったルールを skill と lint で確認します。

公開 repository には架空のサンプルだけを入れています。

実データを扱う場合は、fork ではなく GitHub の `Use this template` から各チームの private repository として作ってもらう想定です。

## 何に使えるか

たとえば、こんな使い方を想定しています。

- BtoB SaaS の商談・更新・部門展開の記録
- 導入・納品プロジェクトの進行管理
- 見積、納期、依頼事項、リスクの整理
- 社内の営業プロセス改善
- 提案資料や共有文の下書き作成
- 月次振り返り

LLM に「この顧客について次回商談の準備をして」「このプロジェクトの未完了タスクを整理して」「顧客向け共有文を作って」と頼むとき、必要な文脈を毎回人間が貼らなくてよくなることを目指しています。

## まとめ

LLM 活用で大事なのは、モデルに何でも覚えさせることではなく、必要な文脈を、必要なときに、安全に渡せる状態を作ることだと思っています。

BtoB の仕事は、文脈が長く、散らばりやすく、混ぜてはいけない情報も多い。

だからこそ、顧客や社内プロジェクトごとに memory を育てる repository があると、LLM がかなり使いやすくなります。

公開したテンプレートはこちらです。

https://github.com/TsutomuTomizawa/btob-project-memory-template

興味がある方は、fork ではなく `Use this template` から private repository として試してみてください。

## 添付画像メモ

X Article に画像を添える場合は、README の以下の図を使う想定です。

- `docs/assets/context-challenge.svg`: BtoB でコンテキストが散らばる理由
- `docs/assets/memory-growth-flow.svg`: データが蓄積して memory が育つ流れ

## スレッド版

### 1

LLM を業務で使うとき、一番効くのは「良いプロンプト」だけではなく「必要なコンテキストを渡し続けられること」だと思っています。

BtoB の顧客対応や社内プロジェクト向けに、LLM が読める memory vault テンプレートを公開しました。

https://github.com/TsutomuTomizawa/btob-project-memory-template

### 2

BtoB では文脈が散らばります。

商談、導入、運用、更新、請求、社内調整が長く続く。議事録、チャット、資料、CRM、手元メモに情報が分かれる。顧客ごとの境界も守らないといけない。

毎回ぜんぶ prompt に貼るのは現実的ではありません。

### 3

このテンプレートでは、顧客・社内プロジェクトごとに memory を分けます。

- raw: 長文原本
- events: 起きたことの時系列
- profile: 長く使う背景や判断軸
- current: 現在の状態、タスク、リスク
- sources: 参照してよい外部資料

### 4

流れはシンプルです。

1. 議事録やメモを渡す
2. raw と event に保存する
3. digest で profile / current に反映する
4. 次回以降、LLM がそれを読んで回答や提案を作る
5. 新しい会話や決定もまた保存する

保存を繰り返すほど、文脈が育ちます。

### 5

LLM に「全部覚えさせる」のではなく、必要な文脈を必要なときに読める状態にする、という考え方です。

顧客向け draft に内部情報を混ぜない、別顧客情報を混ぜない、event を後から書き換えない、といったルールも skill と lint で見ます。

### 6

公開 repo はテンプレートです。実データを扱う場合は fork ではなく、GitHub の `Use this template` から各チームの private repository として使う想定です。

BtoB で LLM に文脈を渡す方法を考えている方のたたき台になれば嬉しいです。

https://github.com/TsutomuTomizawa/btob-project-memory-template
