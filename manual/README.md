# BtoB Project Memory 運用マニュアル

この repository は、Example Team がBtoB事業チームとしてクライアントの商談・プロジェクト運用、提案資料更新、制作、計測、レポーティング、社内プロジェクトを継続管理するための memory vault です。Obsidian から読みやすく、Codex / Claude Code が skill に従って更新できるようにしています。

説明会やデモでは、全体像を短く伝えるスライドとして [[PRESENTATION]] も使えます。

## まず覚えること

- `events/` は時系列の正本です。既存 event は直接書き換えません。訂正は新しい correction event で残します。
- `raw/` は生入力の原本置き場です。長い議事録や複数 client を含むメモも、まず top-level `raw/` に 1 つ保存します。event には全文を貼り直しません。
- `events/` の本文は薄い構造化 index です。要点、決定事項、タスク、リスク、未解決事項だけを残し、全文は raw を辿ります。
- `profile.md` は長く使う知識、背景、制約、商談・プロジェクト運用の学びを置く場所です。
- `states/current.md` は現在状態、進行中 task、リスク、決定事項、次アクションだけを最新化する場所です。
- `profile.md` / `states/current.md` の event 由来の箇条書きは、できるだけ各見出し内で出典日付が新しい順に並べます。基本説明や手動メモは無理に並べ替えません。
- `sources.md` は Google Drive / Docs / Sheets など、必要時に `gws` CLI で取得してよい外部資料 URL の索引です。
- クライアント向け文面は repository に保存せず、`memory-output` でチャット上に draft として作り、人間が送付前に確認します。
- 月次総括は月別 state file ではなく、`events/YYYY-MM-DD_monthly-review.md` の `event_type: review` として残します。

## フォルダ構成

```text
clients/{client_id}/
  profile.md
  sources.md
  states/current.md
  events/

internal/{project_id}/
  profile.md
  sources.md
  states/current.md
  events/

raw/
company/
views/
manual/
```

`company/` はマネジメントが管理する会社方針です。通常の保存や digest では自動更新しません。

`inbox/` は対象 client / internal を安全に特定できない local triage です。通常メモは gitignore されます。業務で使う場合は、先に client / internal event に昇格してください。

## Obsidian で手動編集できるもの

- `clients/{client_id}/profile.md`
- `clients/{client_id}/sources.md`
- `clients/{client_id}/states/current.md`
- `internal/{project_id}/profile.md`
- `internal/{project_id}/sources.md`
- `internal/{project_id}/states/current.md`
- `raw/*.md`
- `inbox/` の local memo

commit 前 hook が `scripts/memory lint --fix --staged` を走らせ、欠けた更新メタデータや手動セクション marker など、機械的に直せるものは自動補正します。event 改ざん、別 client 参照、不正 URL、pending event など意味判断が必要なものは commit を止めます。

## エージェントに頼む言い方

保存したいとき:

```text
sample-saas-platform の今日の定例を保存してください。
本文は以下です。
...
```

エージェントはまず `scripts/memory save ...` で prompt を生成し、`memory-save` に従って `raw/` と対象 entity の `events/` を更新します。raw には原文を残し、event は 10-30 行程度の要点 index にします。十分な文脈があれば `memory-digest` で `profile.md` / `states/current.md` に反映し、各 section の中では新しい出典の内容が上に来るように整えます。

月次で振り返りを残したいとき:

```text
sample-industrial-supplier の 2026年5月を総括して保存してください。
来月に持ち越すことも整理してください。
```

エージェントはまず `scripts/memory review --client sample-industrial-supplier --month 2026-05 ...` で prompt を生成し、同じ client の月内 event を根拠に `monthly-review` event を作ります。来月も有効な task だけ `states/current.md` に残し、長く使える学びだけ `profile.md` に反映します。`states/2026-05.md` や月次レポート file は作りません。同じ月の `monthly-review` event が既にある場合は上書きせず、必要なら correction event として追記します。

新しい client / internal project を作りたいとき:

```text
新規クライアント example-client-gamma を作ってください。
表示名は Example Client Gamma です。
Google商談・プロジェクト運用の新規 client です。
```

エージェントはまず `scripts/memory add ...` で prompt を生成し、`memory-add` に従って `profile.md`、`sources.md`、`states/current.md`、`events/` だけの軽量構成を作ります。初期 event は作りますが、client 配下に `raw/` や `tasks.md` は作りません。

状態を更新したいとき:

```text
sample-industrial-supplier の pending event を digest してください。
```

質問したいとき:

```text
sample-industrial-supplier の今の課題と次にやることを教えてください。
```

エージェントは `profile.md` と `states/current.md` を先に読みます。外部資料が必要な場合だけ `sources.md` の `context: yes` または `on_demand` の URL を `gws` CLI で取得します。

クライアント向け文面を作りたいとき:

```text
sample-saas-platform 向けに、次回定例の共有文を作ってください。
同じ client の情報だけを根拠にしてください。
```

draft はチャット上に出ます。内部懸念、未確定数値、別 client 情報は入れません。

## Google Workspace 資料

継続して context に使う資料は、対象 entity の `sources.md` に登録します。

| context | 意味 |
| --- | --- |
| `yes` | 会話や提案判断で必要なら読んでよい |
| `on_demand` | 必要なときだけ読んでよい |
| `no` | 登録はするが通常 context には使わない |

`gws` CLI で取得できない場合、エージェントは中身を推測しません。取得できた資料から新しい事実、判断、task が見つかった場合は、まず event として保存します。

## Git の日常運用

基本はエージェントに頼みます。

```text
プッシュしてください。
```

エージェントは差分を確認し、通常は以下を使います。

```bash
scripts/memory publish "日本語のコミットメッセージ"
```

公開テンプレートでは自動 PR / auto-merge を使わず、maintainer が現在の branch を commit / push します。push 後は GitHub Actions の結果を確認してください。

```bash
scripts/memory sync
```

別端末で更新した後は、未保存変更がないことを確認して `scripts/memory sync` を実行します。

## コンフリクトが起きたとき

コンフリクトが起きても、`publish` / `sync` は安全に止まります。

止まった場合は、エージェントに「コンフリクトを解消してください」と依頼してください。エージェントは両方の変更内容を確認し、片方を機械的に捨てず、`profile.md` / `states/current.md` は内容を統合します。既存 event の事実や本文は直接書き換えず、必要なら新しい correction event として訂正を残します。解消後は lint と必要なチェックを通してから再度 push します。

## ローカルで確認したいとき

軽い確認:

```bash
scripts/memory lint
scripts/memory smoke
```

改修後の詳しい確認:

```bash
scripts/memory qa
```

`qa` は CI には入れない任意チェックです。一時 vault 上で新規 client / internal 作成、raw / event / profile / current state / role guard / hook 相当のケースを作って、最後に片付けます。

## 共有安全性

- 別 client の情報を混ぜない。
- 未確認数値を断定しない。
- 景品表示法、契約条件、契約・表現、金融、求人、業界別提案などの表現リスクがある場合は断定表現を避ける。
- `raw/` は社内用です。クライアント向け draft から直接根拠にせず、event を経由します。
- `company/` は通常の save / digest で更新しません。会社方針へ昇格したい学びは、まず entity の event / profile に残し、マネジメント判断待ちにします。
