# Memory Schema

## Entity 種別

- `client`: クライアントアカウント。
- `internal`: 社内プロジェクト。
- `company`: 会社レベルの戦略、ルール、セッション指針。
- `inbox/`: entity ではありません。対象 client / internal を安全に特定できない業務メモの共有 triage です。

## 軽量構成

client / internal の entity 配下は、速度と運用しやすさを優先して以下だけを持ちます。

```text
clients/{client_id}/
  profile.md
  sources.md
  states/
    current.md
  events/

internal/{project_id}/
  profile.md
  sources.md
  states/
    current.md
  events/
```

- `profile.md`: 長く使う知識、背景、商談・プロジェクト運用上の学び、制約、判断軸を集約する安定コンテキスト。
- `sources.md`: Google Drive / Docs / Sheets など、必要時に `gws` CLI で取得してよい外部資料の索引。
- `states/current.md`: 現在状態、進行中タスク、リスク、決定事項、次アクションだけを最新化する作業面。
- `events/`: 時系列の正本。原則追記専用。

廃止済みの `tasks.md`、`wiki/`、`outputs/`、client 月次 state、client `states/00-current.md`、internal `state.md` は新規作成しません。既存 event の `derived_targets` に legacy の `tasks` / `entity_wiki` が残っていても履歴として扱い、新しい保存・digest では `state` のみを使います。月次総括は `states/YYYY-MM.md` ではなく、`events/YYYY-MM-DD_monthly-review.md` の `event_type: review` として保存します。

## Event Frontmatter

```yaml
type: event
event_id:
event_date:
created_at:
author:
entity_type: client | internal
entity_id:
event_type: meeting | note | decision | request | proposal | task | risk | source | review
derived_status: pending | applied
derived_targets:
  - state
source_refs: []
updated_at:
update_summary:
update_source: []
update_history: []
```

## Derived Status

- `pending`: `states/current.md` などの派生反映が未完了。
- `applied`: event から `profile.md` / `states/current.md` への反映が完了済み。

作成後に `memory-digest` が変更してよい event metadata は原則 `derived_status` だけです。event 本文、事実、日付、author、target entity は訂正 event で扱います。

## Event Body

Event 本文は raw note の全文コピーではなく、短い構造化 index として書きます。

- `raw/`: 入力原文、議事録全文、長文メモ、複数 entity 混在メモを保管する。
- `event`: entity ごとの要点、決定事項、タスク、リスク、未解決事項だけを残す。
- `profile.md`: 長期的な知識、制約、判断軸、商談・プロジェクト運用上の学びだけを残す。
- `states/current.md`: 現在状態、進行中タスク、リスク、決定事項、次アクションだけを最新化する。

長文 raw を event に再掲しないでください。event は raw への `source_refs` を持つため、全文が必要なときは raw note を辿ります。

## Monthly Review Event

月次総括、月の振り返り、今月のまとめを保存する場合は、月別 state file を作らず、対象 entity の event として保存します。

```text
clients/{client_id}/events/YYYY-MM-DD_monthly-review.md
internal/{project_id}/events/YYYY-MM-DD_monthly-review.md
```

- `event_type: review` を使う。
- `source_refs` には参照した同一 entity の events と、必要に応じて raw note / source URL を入れる。
- 本文には `要約`、`良かったこと`、`課題`、`決定事項`、`来月へ持ち越すこと`、`長期的な学び候補`、`参照イベント` を置く。
- 来月も有効なタスク、リスク、決定事項だけ `states/current.md` へ反映する。
- 長期的に再利用する学びだけ `profile.md` へ反映する。
- 月次レポートのクライアント提出 draft は `memory-output` でチャット上に作る。提出物 file は repository に保存しない。

Company event は作りません。`company/` は management-owned context なので、会社方針は `company/README.md`、`company/session-context.md`、`company/strategy.md`、`company/rules.md` の 4 ファイルに置きます。通常の save / digest では更新せず、マネジメントの明示依頼を受けたエージェントが guardrail に従って更新します。

## Safety Model

- `events/`、`profile.md`、`sources.md`、`states/current.md`、`raw/` は社内用 memory です。クライアントにそのまま出しません。
- クライアント向け文面は repository に成果物として保存せず、`memory-output` でチャット上に draft を作り、人間が送付前に確認します。
- 迷う素材、内部懸念、未確定情報、他社情報はクライアント向け draft に含めません。
- `inbox/` は共有 triage であり、正式 memory ではありません。業務で使う場合は client / internal event に昇格してから使います。

## Update Metadata

`views/updates.md` は Dataview で各 memory file の frontmatter を読むため、`clients/`、`internal/`、`company/`、`inbox/`、`raw/` の markdown には以下を持たせます。

```yaml
updated_at: YYYY-MM-DD
update_summary: 最新更新の短い要約
update_source:
  - "[[events/YYYY-MM-DD_event-id]]"
update_history:
  - "YYYY-MM-DD 更新内容"
```

- `updated_at` は最後に意味のある内容を更新した日付です。
- `update_summary` は `views/updates.md` に表示する 1 行要約です。
- `update_source` は根拠 event、raw note、または管理者更新の出典です。出典がない管理ファイルでは `[]` でよいです。
- `update_history` は新しい更新を追記し、古い履歴を消さないでください。

## Source Index

client / internal project は `sources.md` を持ちます。Google Drive、共有スプレッドシート、Google Docs など、LLM が context として使ってよい外部資料 URL を人間がエージェントに渡し、エージェントが登録する場所です。

```yaml
type: source_index
entity_type: client | internal
entity_id:
auto_generated: false
owner: human
updated_at:
update_summary:
update_source: []
update_history: []
```

本文には以下の table を置きます。

```md
| 名称 | 種別 | URL | context | 備考 |
| --- | --- | --- | --- | --- |
```

- `種別`: `drive_folder`、`drive_file`、`spreadsheet`、`document`、`slide`、`form`、`other`
- `context`: `yes`、`no`、`on_demand`
- URL は `https://` から始めます。
- LLM は `context: yes` または `on_demand` の資料だけを、必要なときに `gws` CLI で読みます。
- 取得した資料から新しい事実、判断、タスクが見つかった場合は、まず event として保存します。`sources.md` 自体は source registry であり、event の代替ではありません。

## Raw Notes

保存依頼では、event に要約変換する前の入力を Obsidian で見える top-level `raw/` に raw note として残します。raw 原本は複数 client / internal を跨ぐ可能性があるため、client 配下には複製しません。関係する各 entity の event が `source_refs` / `update_source` で raw note を参照します。

```yaml
type: raw_note
raw_id:
scope: single_entity | multi_entity | unknown
entity_refs:
  - client/{client_id}
updated_at:
update_summary:
update_source: []
update_history: []
```

保存場所:

```text
raw/YYYY-MM-DD_{slug}.md
```

`entity_refs` は `client/{client_id}` または `internal/{project_id}` の list です。複数 entity を含む raw は `scope: multi_entity` とし、特定できない raw は `scope: unknown` にします。raw note 自体は社内用 memory であり、クライアントにそのまま出しません。

## Manual Editing

人間は Obsidian から以下を手動編集できます。

- `clients/*/profile.md`
- `clients/*/sources.md`
- `clients/*/states/current.md`
- `internal/*/profile.md`
- `internal/*/sources.md`
- `internal/*/states/current.md`
- `raw/*.md`
- gitignore された `inbox/`

commit 前 hook は staged された client / internal / raw の非 event markdown について、欠けた更新メタデータなど機械的に直せるものを `scripts/memory lint --fix --staged` で補正します。意味判断が必要な不備、event 改ざん、cross-client 参照、invalid URL は停止します。
