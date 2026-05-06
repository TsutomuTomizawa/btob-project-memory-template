---
name: memory-lint
description: schema違反、共有NG情報の混入、リンク切れ、矛盾、未処理TODOを検査する。
---

# memory-lint

PR 前、10-15 回保存後、またはユーザーが vault のチェック・整理を依頼したときに使うスキルです。

## 必須読み込み

1. `company/session-context.md`
2. `company/strategy.md`
3. `company/rules.md`

## チェック項目

- Event frontmatter に必須 key がある。
- Event の `entity_type` と `entity_id` が event file path と一致する。
- Event ID が重複していない。
- top-level `raw/` がある。
- client / internal entity に `profile.md`、`sources.md`、`states/current.md`、`events/` がある。
- client / internal entity に廃止済みの `tasks.md`、`wiki/`、`outputs/`、client 月次 state、client `states/00-current.md`、internal `state.md` が残っていない。
- `sources.md` の URL table が定義済み形式で、context が許可値を使っている。
- `views/updates.md` が `updated_at`、`update_summary`、`file.link`、`update_source`、`inbox` を見ている。
- `clients/`、`internal/`、`company/`、`inbox/`、`raw/` の markdown に `updated_at`、`update_summary`、`update_source`、`update_history` がある。
- `pending` event が残っていない。
- active な derived target `state` が source event への reference を持っている。
- generated file の手動セクションに明示的な BEGIN/END marker がある。
- staged された client / internal 非 event file と raw note は `scripts/memory lint --fix --staged` で機械的な frontmatter / manual marker 不備を補正できる。
- staged された既存 event は本文と immutable frontmatter が変更されていない。
- entity 配下の wikilink が別 client / internal の file や event を参照していない。
- `company/README.md`、`company/session-context.md`、`company/strategy.md`、`company/rules.md` がある。
- `company/` 配下の markdown は、`README.md`、`session-context.md`、`strategy.md`、`rules.md` の 4 ファイルだけである。
- `company/` 配下の markdown は、owner が `management` で `auto_generated: true` ではない。
- 矛盾が既知の場合、`Conflict` section が見える。

## ツール

利用できる場合は以下を実行する。

```bash
scripts/memory lint
scripts/memory lint --fix --staged
```

tool が利用できない場合は、同じ確認を手動で行う。
