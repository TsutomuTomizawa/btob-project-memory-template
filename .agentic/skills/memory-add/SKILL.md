---
name: memory-add
description: 新規顧客・社内プロジェクトを追加し、軽量な初期構造を作る。
---

# memory-add

新規クライアント、社内プロジェクトを追加するときに使うスキルです。会社レベルの戦略・ルールは、このスキルでは更新しません。マネジメントの明示依頼がある場合だけ、会社 context の guardrail に従って扱います。

## 必須読み込み

1. `company/session-context.md`
2. `company/strategy.md`
3. `company/rules.md`
4. `.agentic/skills/_shared/SCHEMA.md`
5. `templates/`
6. 既存 sample entity の書き方

## ワークフロー

1. `entity_type` を決める。
2. 安定した kebab-case の `entity_id` を決める。
3. template から軽量 folder structure を作る。
4. `profile.md` を作り、長期的な知識・背景・判断軸の置き場にする。
5. `sources.md` を作り、継続利用する外部資料 URL の registry にする。
6. `states/current.md` を作り、現在状態、進行中タスク、リスク、決定事項、次アクションだけを置く。
7. `events/` を作り、entity 作成理由を記録する初期 event を追加する。
8. raw 原本は top-level `raw/` に置くため、entity 配下には raw を作らない。
9. `views/` は Dataview で拾わせる。手書き更新しない。
10. `company/` はこのスキルで自動作成・自動更新しない。
11. 日本語の依頼で追加する場合、自然文は日本語で書く。

## 命名

- ID は lowercase kebab-case を使う。
- 短い運用名で足りる場合、クライアントの正式法人名を避ける。
- 必要がない限り、個人名を file path に含めない。
