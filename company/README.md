---
type: company_readme
entity_type: company
entity_id: company
auto_generated: false
owner: management
last_reviewed: 2026-05-06
updated_at: 2026-05-06
update_summary: "公開テンプレート向け company context の入口に更新。"
update_source: []
update_history:
  - "2026-05-06 公開テンプレート向け company context の入口を作成。"
---

# Company Context

`company/` は、BtoB 取引・社内プロジェクト管理の方針、ルール、会話指針を書く場所です。

公開テンプレートでは架空の例を置いています。実運用で使う場合は、自社の事業、守秘ルール、顧客共有ポリシー、法務・セキュリティ確認フローに合わせて書き換えてください。

## ファイル

- [[session-context]]: エージェントがセッション開始時に読む会話指針。
- [[strategy]]: 組織の重点、判断基準。
- [[rules]]: memory 運用、BtoB 取引、クライアント分離、共有安全性のルール。

## 重要

通常の `memory-save` / `memory-digest` は `company/` を自動更新しません。クライアントや社内プロジェクトから見つかった再利用可能な学びは、まず各 entity の `events/` と `profile.md` に保存し、匿名化・一般化したうえで会社方針へ昇格するかをマネジメントが判断します。
