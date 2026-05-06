---
type: event
event_id: 20260501-sample-saas-platform-created
event_date: 2026-05-01
created_at: 2026-05-01T09:00:00+09:00
author: template
entity_type: client
entity_id: sample-saas-platform
event_type: note
derived_status: applied
derived_targets:
  - state
source_refs:
  - "[[raw/2026-05-01_sample-business-entities]]"
updated_at: 2026-05-01
update_summary: "BtoB SaaS client sample を作成。"
update_source:
  - "[[raw/2026-05-01_sample-business-entities]]"
update_history:
  - "2026-05-01 BtoB SaaS client sample を作成。"
---

# BtoB SaaS client sample を作成

## 要約

公開テンプレート用の架空 client として、BtoB SaaS の更新商談、部門展開、導入支援を扱う `sample-saas-platform` を作成した。

## 詳細

- 実在企業、実担当者、実契約、実 URL は含めない。
- `profile.md`、`sources.md`、`states/current.md`、`events/` だけの軽量構成で管理する。
- BtoB SaaS の商談・導入・更新のサンプルとして、メモリ運用の流れを説明する。

## タスク

- サンプル契約一覧と導入計画を `sources.md` に登録する。
- 更新商談の確認事項を `states/current.md` に反映する。

## 出典メモ

[[raw/2026-05-01_sample-business-entities]]
