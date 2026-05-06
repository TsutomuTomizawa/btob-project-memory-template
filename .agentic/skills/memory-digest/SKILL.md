---
name: memory-digest
description: event から profile と states/current.md を追記更新する。
---

# memory-digest

pending event を軽量な派生作業面に反映するためのスキルです。新規の派生先は `profile.md` と `states/current.md` だけです。

## 必須読み込み

1. `.agentic/AGENT_CONTRACT.md`
2. `company/session-context.md`
3. `company/strategy.md`
4. `company/rules.md`
5. `.agentic/skills/_shared/SCHEMA.md`
6. `.agentic/skills/_shared/GUARDRAILS.md`
7. 対象 entity の `profile.md`
8. 対象 entity の `states/current.md`

## CLI-first 受付

digest / 更新依頼では、ユーザーが CLI と明示していなくても、最初に `scripts/memory digest ...` を実行して agent 向け prompt を生成します。CLI は dry-run / prompt 生成だけを行い、file は更新しません。

- 対象 client が明確なら `scripts/memory digest --client {client_id}`
- 対象 internal が明確なら `scripts/memory digest --internal {project_id}`
- pending event 全体を扱う依頼なら `scripts/memory digest --all-pending`

生成された prompt を routing checklist として扱い、この skill の workflow に従って実更新します。CLI が使えない場合は理由を明示し、この skill の workflow に従って進めます。

## ワークフロー

1. 対象 client / internal entity の pending event を探す。company event は作らない。
2. 長期的に使う知識、背景、制約、商談・プロジェクト運用の学びは `profile.md` に追記・更新する。
3. 現在状態、進行中タスク、リスク、決定事項、次アクションは `states/current.md` だけに反映する。
4. 更新した各ファイルの frontmatter で `updated_at`、`update_summary`、`update_source`、`update_history` を更新する。
5. `views/` は Dataview が frontmatter と Markdown task から自動表示するため、digest では一覧を手書き更新しない。
6. `company/` は management-owned context なので、通常の digest で自動更新しない。会社方針へ昇格したい内容は対象 entity 側に出典付きで残す。
7. 派生ファイル更新後に限り、event を `derived_status: applied` にする。これは status-only metadata update であり、event の事実や本文を書き換えない。

## 更新スタイル

- 小さな section edit を優先する。
- 手動セクションを保持する。
- event は薄い index であり、raw note の全文は通常 digest しない。event の要点で足りない場合だけ raw を辿り、派生ファイルへは必要な結論だけを書く。
- `profile.md` には毎回の議事録要約を積まない。長期的な制約、判断軸、商談・プロジェクト運用上の学びだけを残す。
- `states/current.md` には現在の決定事項、進行中タスク、リスク、次アクションを残し、過去の発言録を再掲しない。
- `profile.md` / `states/current.md` の event 由来の箇条書きは、各 section 内でできるだけ source event の日付が新しい順に並べる。ファイル全体を時系列で再構成せず、見出し構造と意味のまとまりは保つ。
- source date は `[[events/YYYY-MM-DD_...]]` または `[[../events/YYYY-MM-DD_...]]` から読む。複数 source がある項目は最も新しい source date を採用する。
- entity の基本説明、意味上の前提、source が曖昧な手動メモは無理に並べ替えない。source がない生成項目は、source 付き項目の後ろに置く。
- `states/current.md` の task は active なものだけにする。digest や月次総括のタイミングで重複 task をまとめ、完了済み・古い・不要になった task は source が明確なら current から閉じるか削除する。
- `states/current.md` の task は、期限が明確なら期限を優先し、期限がない場合は source event の日付が新しい順に並べる。
- 未解決かどうか判断できない task は消さず、確認事項や risk として残す。
- 月次総括は `events/YYYY-MM-DD_monthly-review.md` の `event_type: review` に保存する。`states/YYYY-MM.md` や月別 current は作らない。
- 月次総括 event を digest するときは、来月も有効な carry-over だけを `states/current.md` に反映し、長期的に再利用できる学びだけを `profile.md` に反映する。
- `<!-- BEGIN MANUAL -->` と `<!-- END MANUAL -->` の間は保持する。
- 重要な claim には source event link を残す。
- 古い claim を削除せず、必要なら conflict note を追加する。
- `update_summary` は「このファイルが最新でどう変わったか」が分かる 1 行にする。
- `update_source` には反映元 event への wiki link を入れる。
- `update_history` は新しい履歴を追記し、古い履歴を削除しない。
- ユーザー入力が日本語の場合、派生ファイルの自然文は日本語で書く。
