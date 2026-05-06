# Schema リファレンス

正規 schema は `.agentic/skills/_shared/SCHEMA.md` です。この document は人間向けの要約です。

## Entity 構成

client / internal は軽量構成で運用します。

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
```

- `profile.md`: 長く使う知識、背景、商談・プロジェクト運用上の学び、制約、判断軸。
- `sources.md`: Google Workspace など、必要時に `gws` CLI で取得してよい外部資料 URL。
- `states/current.md`: 現在状態、進行中タスク、リスク、決定事項、次アクション。
- `events/`: 追記専用の時系列正本。

廃止済みの `tasks.md`、`wiki/`、`outputs/`、client 月次 state、client `states/00-current.md`、internal `state.md` は新規作成しません。月次総括は `states/YYYY-MM.md` ではなく、`events/YYYY-MM-DD_monthly-review.md` の `event_type: review` として保存します。

## Event

Event は entity memory の source of truth です。`memory-digest` は派生 file 更新後に `derived_status` だけを更新できます。

Event 本文は raw note の全文コピーではなく、entity ごとの薄い構造化 index です。長文議事録や発言録は `raw/` に置き、event には要点、決定事項、タスク、リスク、未解決事項だけを残します。

月次総括や振り返りも event です。参照した同一 entity の events を `source_refs` に入れ、来月も有効なものだけ `states/current.md` に反映します。クライアント提出用の月次レポート draft は `memory-output` でチャット上に作ります。

必須 field:

- `type`
- `event_id`
- `event_date`
- `created_at`
- `author`
- `entity_type`
- `entity_id`
- `event_type`
- `derived_status`
- `derived_targets`
- `source_refs`
- `updated_at`
- `update_summary`
- `update_source`
- `update_history`

新規 event の `derived_targets` は原則 `state` のみです。旧 event に残る `tasks` / `entity_wiki` は legacy 履歴として扱います。

## 安全モデル

`events/`、`profile.md`、`sources.md`、`states/current.md`、`raw/` はすべて社内用 memory です。クライアントにそのまま出しません。

クライアントに見せる文面は `memory-output` でチャット上に draft として作り、人間が送付前に本文を確認します。軽量構成では repository に output file として保存しません。

## 更新メタデータ

`views/updates.md` は、各 memory file の frontmatter にある更新メタデータを Dataview で表示します。

- `updated_at`: 最後に意味のある内容を更新した日付。
- `update_summary`: 更新一覧に出す 1 行要約。
- `update_source`: 根拠 event、raw note、または管理者更新の出典。
- `update_history`: 更新履歴。古い履歴を消さずに追記します。

## Sources

client / internal project は `sources.md` を持ちます。Google Drive、共有スプレッドシート、Google Docs など、LLM が context として使ってよい外部資料 URL を管理します。

必須 table:

```md
| 名称 | 種別 | URL | context | 備考 |
| --- | --- | --- | --- | --- |
```

- `種別`: `drive_folder`、`drive_file`、`spreadsheet`、`document`、`slide`、`form`、`other`
- `context`: `yes`、`no`、`on_demand`
- URL は `https://` から始めます。

URL から読み取った新しい事実、判断、タスクは event として保存します。`sources.md` 自体は registry です。

## Raw Notes

保存依頼では、event に要約変換する前の入力を Obsidian で見える `raw/YYYY-MM-DD_{slug}.md` に残します。複数 client / internal を含む raw も 1 つの原本として保存し、client 配下には複製しません。関係する各 entity の event が raw note を `source_refs` / `update_source` で参照します。

raw note の基本 frontmatter:

- `type: raw_note`
- `raw_id`
- `scope: single_entity | multi_entity | unknown`
- `entity_refs`
- `updated_at`
- `update_summary`
- `update_source`
- `update_history`

## Company

`company/` は management-owned context です。通常の `memory-save` / `memory-digest` では自動更新せず、company event は作りません。会社方針は `company/README.md`、`company/session-context.md`、`company/strategy.md`、`company/rules.md` の 4 ファイルだけで管理します。

`inbox/` は entity ではありません。対象 client / internal を安全に特定できない業務メモの local triage です。正式 memory の根拠にする場合は、先に client / internal event に昇格します。
