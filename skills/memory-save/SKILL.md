---
name: memory-save
description: 「保存して」「メモして」「記録して」で起動し、memory event と派生ナレッジ更新を開始する。
---

# memory-save

ユーザーが「保存して」「メモして」「記録して」など、情報の保存を依頼したときに使うスキルです。

## 必須読み込み

1. `.agentic/AGENT_CONTRACT.md`
2. `company/session-context.md`
3. `company/strategy.md`
4. `company/rules.md`
5. `.agentic/skills/_shared/SCHEMA.md`
6. `.agentic/skills/_shared/GUARDRAILS.md`
7. `.agentic/skills/_shared/COLLABORATION.md`

## CLI-first 受付

保存依頼では、ユーザーが CLI と明示していなくても、最初に `scripts/memory save ...` を実行して agent 向け prompt を生成します。CLI は dry-run / prompt 生成だけを行い、file は更新しません。

- 対象 client が明確なら `scripts/memory save --client {client_id} "{メモ}"`
- 対象 internal が明確なら `scripts/memory save --internal {project_id} "{メモ}"`
- 対象が不明なら `scripts/memory save --unknown "{メモ}"`
- 月次総括・振り返りなら `scripts/memory review --client {client_id} --month YYYY-MM "{総括依頼}"` または `scripts/memory review --internal {project_id} --month YYYY-MM "{総括依頼}"`
- 長文や議事録 file がある場合は `scripts/memory save --from-file {path}` を使う。

生成された prompt を routing checklist として扱い、この skill の workflow に従って実更新します。CLI が使えない場合は理由を明示し、この skill の workflow に従って進めます。

## ワークフロー

1. `entity_type` と `entity_id` を特定する。
2. `event_type` を分類する。
3. 入力を Obsidian で見える `raw/YYYY-MM-DD_{slug}.md` に raw note として保存する。複数 client / internal を含む場合も raw 原本は 1 つにし、client 配下へ複製しない。
4. 対象 entity 配下に追記専用 event を 1 つ作成する。event は薄い構造化 index とし、raw note の全文をコピーしない。
5. event frontmatter に `updated_at`、`update_summary`、`update_source`、`update_history` を入れる。
6. event の `source_refs` / `update_source` から top-level raw note を参照する。
7. `derived_status: pending` を設定する。
8. source link や raw reference があれば追加する。
9. 十分な文脈がある場合は、同じ entity に対して `memory-digest` workflow を実行する。
10. 分類に不確実性がある場合は、event 本文の `## 未解決事項` に明示する。

## events と draft の使い分け

- 「保存して」「メモして」「記録して」は原則 `events/` に保存する。event は起きたこと、聞いたこと、決まったことの source of truth。
- 提案文、共有文、月次レポート、打合せ準備などは `memory-output` でチャット上に draft として作る。軽量構成では `outputs/` に保存しない。
- 月次総括・振り返りを repository に残す場合は、`memory-output` の draft ではなく `monthly-review` event として保存する。
- draft の中に新しい事実や判断が含まれる場合は、先に event として保存し、draft はその event を source として cite する。
- Google Drive / Sheets / Docs などの URL を「今後も context として使う資料」として保存する依頼は、event ではなく対象 entity の `sources.md` に登録する。URL から読み取った新しい事実は event として保存する。

## ルーティングルール

- 入力が既存の 1 クライアントまたは 1 社内プロジェクトに明確に属する場合、その entity 配下に event を 1 つ作る。
- 入力が複数クライアントまたは複数プロジェクトの更新を含む場合、raw 原本は `raw/` に 1 つ保存し、entity ごとに event を分割する。混在 entity event は作らない。
- 対象 client / internal が分かる業務メモは、軽いメモでも該当 entity の event に保存する。派生更新しない場合は `derived_targets: []` にし、派生更新する場合は原則 `derived_targets: [state]` にする。
- 対象 entity が不明な業務メモだけ `inbox/` に保存し、まだ event 化しない。
- 対象 entity は分かるが分類詳細が不確実な場合は、event 本文の `## 未解決事項` に不確実性を書く。
- `raw/` や `inbox/` に未加工メモを残す場合も、frontmatter に `updated_at`、`update_summary`、`update_source`、`update_history` を入れる。
- Google Workspace URL を登録する場合は `sources.md` の table に追加し、context 利用可否を `yes` / `no` / `on_demand` で明示する。
- メモが entity 固有の事実と会社レベルの再利用可能な学びを含む場合は、まず entity event に出典付きで保存し、会社方針への昇格はマネジメント判断待ちとして記録する。通常の save で `company/` を自動更新しない。
- すべての event path は frontmatter の `entity_type` と `entity_id` と一致していなければならない。
- ユーザー入力が日本語の場合、event 本文と派生ファイルの自然文は日本語で書く。

## Event の保存場所

- クライアント: `clients/{client_id}/events/YYYY-MM-DD_{event_id}.md`
- 社内: `internal/{project_id}/events/YYYY-MM-DD_{event_id}.md`
- 会社方針: 通常の save では自動作成しない。マネジメントが明示した場合のみ `company/` の該当ファイルを更新する。
- 対象不明の業務メモ: `inbox/YYYY-MM-DD_unknown-{slug}.md`
- raw note: `raw/YYYY-MM-DD_{slug}.md`
- 月次総括: `clients/{client_id}/events/YYYY-MM-DD_monthly-review.md` または `internal/{project_id}/events/YYYY-MM-DD_monthly-review.md`

## 月次総括 event

月次総括は、月ごとの state file ではなく event として扱います。月の振り返り、次月への持ち越し、長期的な学び候補を 1 つの `event_type: review` にまとめます。

- 保存先は月末日を使った `events/YYYY-MM-DD_monthly-review.md` を基本にする。
- 参照した同一 entity の event を `source_refs` に入れる。別 client / internal の event や file は参照しない。
- ユーザーが新しい振り返りメモや議事録を渡した場合だけ top-level `raw/` に保存して cite する。月内 event だけから総括する場合は raw note を新規作成しなくてよい。
- event 本文は `## 要約`、`## 良かったこと`、`## 課題`、`## 決定事項`、`## 来月へ持ち越すこと`、`## 長期的な学び候補`、`## 参照イベント` を使う。
- 来月も有効な task / risk / decision / next action だけ `states/current.md` に反映する。完了済み・古い task は current に溜めない。
- 長期的に使える制約、判断軸、商談・プロジェクト運用の学びだけ `profile.md` に反映する。月次日記を profile に貼らない。
- `states/YYYY-MM.md`、`tasks.md`、`wiki/`、`outputs/`、entity-local `raw/`、月次 report file は作らない。

## Thin Event 方針

- `raw/` は入力原文の保管場所です。議事録全文、長文メモ、複数 entity 混在メモは raw note に残します。
- `event` は raw の再掲ではなく、後から検索・監査・digest しやすい短い index です。
- event 本文には、対象 entity に属する要点、決定事項、タスク、リスク、未解決事項だけを書く。
- 目安は 10-30 行程度です。長い議事録の段落、発言録、メール本文、URL 先の長文を event に貼り直さない。
- どうしても背景が必要な場合も、要点だけに圧縮し、全文は `source_refs` / `## 出典メモ` の raw note へ辿らせる。
- 複数 entity の raw から event を分ける場合、それぞれの event にはその entity に必要な要点だけを書く。他 entity の詳細を event 本文に混ぜない。

## 更新メタデータ

event または raw note を作るときは以下を設定します。raw note では `raw_id`、`scope`、`entity_refs` も設定します。

```yaml
updated_at: YYYY-MM-DD
update_summary: views/updates.md に表示する 1 行要約
update_source: []
update_history:
  - "YYYY-MM-DD 保存"
```

## 本文フォーマット

以下のセクションを使います。`## 詳細` は raw の全文コピーではなく、主要ポイントだけにします。

```md
## 要約

## 詳細

## タスク

## クライアント共有候補

## 未解決事項

## 出典メモ
```

空セクションは本当に不要な場合だけ省略します。
