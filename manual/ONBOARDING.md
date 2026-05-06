# 初回導入マニュアル

この手順は、メンバーが Git と Obsidian を使って BtoB Project Memory を扱えるようにするためのものです。基本方針は「Git の細かい操作は覚えすぎない。clone した後は、最新化とプッシュをエージェントに頼めばよい」です。

## 事前に入れるもの

### macOS

- Git
- Python 3.10 以上
- Obsidian
- Codex または Claude Code

Homebrew がある場合:

```bash
brew install git python
```

### Windows

- Git for Windows
- Python 3.10 以上
- Obsidian
- Codex または Claude Code

Windows では PowerShell や Command Prompt ではなく、**Git Bash** から以下のコマンドを実行してください。`scripts/memory` は `python3`、`python`、`py -3` の順に利用できる Python を探します。

## 初回セットアップ

標準は HTTPS です。SSH key の登録は不要です。

```bash
git clone https://github.com/tsutomutomizawa/btob-project-memory-template.git
cd btob-project-memory-template
./scripts/setup-member.sh
```

`setup-member.sh` はローカル hook を有効化します。commit 前に privacy scan、role guard、必要なときだけ staged lint/fix が走ります。pre-push hook は使いません。

## Obsidian で開く

1. Obsidian を開く。
2. `Open folder as vault` を選ぶ。
3. clone した `btob-project-memory-template` folder を選ぶ。
4. まず `manual/README.md` を読む。
5. `views/updates.md` と `views/tasks.md` を見る。Dataview plugin が必要です。

## 日常の編集

手動編集してよい場所:

- `clients/{client_id}/profile.md`
- `clients/{client_id}/sources.md`
- `clients/{client_id}/states/current.md`
- `internal/{project_id}/profile.md`
- `internal/{project_id}/sources.md`
- `internal/{project_id}/states/current.md`
- `raw/*.md`
- `inbox/` の local memo

直接書き換えない場所:

- `clients/{client_id}/events/*.md`
- `internal/{project_id}/events/*.md`
- `company/`（マネジメント明示依頼がある場合だけ）
- `.agentic/skills/`、`tools/`、`scripts/`、`templates/` など仕組み側

## エージェントに頼む基本文

保存:

```text
この議事録を sample-saas-platform に保存してください。
```

新規 client / internal:

```text
新規クライアント example-client-gamma を作ってください。
表示名は Example Client Gamma です。
Google商談・プロジェクト運用の新規 client です。
```

質問:

```text
sample-industrial-supplier の現在の課題と次のアクションを教えてください。
```

下書き:

```text
sample-saas-platform 向けに、次回定例で共有する文章を作ってください。
```

push:

```text
プッシュしてください。
```

最新化:

```text
最新化してください。
```

通常メンバーは、`main` にいる状態で素の `git push` を使いません。共有するときはエージェントに「プッシュしてください」と依頼し、`scripts/memory publish` の作業ブランチ経由にします。

## 保存時に起きること

1. エージェントが `scripts/memory save ...` で agent 向け prompt を生成する。
2. 生入力を `raw/YYYY-MM-DD_{slug}.md` に残す。
3. 対象 entity ごとに `events/YYYY-MM-DD_{event_id}.md` を作る。event は全文コピーではなく、10-30 行程度の要点 index にする。
4. 複数 client / internal を含む場合は、raw 原本は 1 つのまま、event を entity ごとに分割する。
5. 必要なら `memory-digest` で `profile.md` と `states/current.md` を更新する。

`raw/` は厚く、`events/` は薄く、`profile.md` には長く使う知識、`states/current.md` には現在状態と task を置きます。旧来の細かい派生 file は作りません。

## 月次総括時に起きること

1. エージェントが `scripts/memory review --client {client_id} --month YYYY-MM` または `scripts/memory review --internal {project_id} --month YYYY-MM` で agent 向け prompt を生成する。
2. 同じ entity の月内 event を読み、`events/YYYY-MM-DD_monthly-review.md` を作る。
3. `event_type: review` として、良かったこと、課題、決定事項、来月への持ち越し、長期的な学び候補を整理する。
4. 来月も有効な task / risk / next action だけ `states/current.md` に残す。
5. 長く使える商談・プロジェクト運用の学びだけ `profile.md` に反映する。

月別 `states/YYYY-MM.md` や月次レポート file は作りません。クライアント提出用の月次レポート文面は `memory-output` でチャット上に作ります。同じ月の `monthly-review` event が既にある場合は上書きせず、必要なら correction event として追記します。

## 新規 client / internal 作成時に起きること

1. エージェントが `scripts/memory add ...` で agent 向け prompt を生成する。
2. `memory-add` に従って `profile.md`、`sources.md`、`states/current.md`、`events/` だけを作る。
3. 作成理由と初期文脈を初期 event として残す。
4. 初期 event を `states/current.md` に反映し、lint が通る形にする。
5. `raw/` は top-level の原本置き場なので、client / internal 配下には作らない。

## commit から merge まで

通常はエージェントに「プッシュしてください」と依頼します。

1. 差分を確認する。
2. `scripts/memory publish "日本語のコミットメッセージ"` を実行する。
3. `main` 上なら作業ブランチを作る。
4. pre-commit が走る。
5. commit する。
6. push する。
7. GitHub Actions が PR を自動作成する。
8. `memory-vault-ci` と `memory-role-guard` が走る。
9. CI が通り、merge conflict がなければ auto-merge される。
10. `publish` が remote branch の削除を検知し、`sync` 相当で main に戻って最新化する。

コミットメッセージ、PR title、PR body は日本語にします。

## よくあるエラー

### pending event がある

保存した event が `states/current.md` などへ反映されていません。エージェントに digest を依頼してください。

### 別 client の file を参照している

client / internal の分離違反です。同じ entity 内の source に直すか、一般化した学びとして internal / company に昇格する判断をしてください。

### URL が https ではない

`sources.md` の URL は `https://` から始めます。社内メモとして残すだけなら event に保存してください。

### 未マスクのメール・電話番号がある

CI log に値を出さないため、privacy scan は実値を表示せず止まります。`[email masked]`、`[phone masked]` などへ置換してください。

### role guard で止まる

通常メンバーは `clients/`、`internal/`、`raw/`、`inbox/` だけを更新できます。仕組み側や `company/` を変える必要がある場合は admin / developer に依頼してください。

### コンフリクトが起きた

同じ file を複数人が更新すると、`publish` / `sync` や PR の auto-merge が止まることがあります。これは安全に止まっている状態です。

エージェントに「コンフリクトを解消してください」と依頼してください。エージェントは両方の変更内容を確認し、片方を機械的に捨てず、`profile.md` / `states/current.md` は統合します。既存 event は直接書き換えず、訂正が必要な場合は correction event として残します。

## 運用上の注意

- 未確認数値を断定しない。
- 別 client の成功事例や提案文をそのまま流用しない。
- 景品表示法、契約条件、契約・表現、金融、求人、業界別提案などは表現リスクを疑う。
- `raw/` は社内用です。クライアント向け draft に直接使わず、event を経由します。
- `inbox/` は正式 memory ではありません。業務で使う前に event 化します。

## エージェントにセットアップを頼む文

```text
この repository の manual/ONBOARDING.md を読んで、メンバー向けセットアップを進めてください。
Windows の場合は Git Bash 前提で案内してください。
```
