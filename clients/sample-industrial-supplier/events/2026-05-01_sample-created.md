---
type: event
event_id: 20260501-sample-industrial-supplier-created
event_date: 2026-05-01
created_at: 2026-05-01T09:10:00+09:00
author: template
entity_type: client
entity_id: sample-industrial-supplier
event_type: note
derived_status: applied
derived_targets:
  - state
source_refs:
  - "[[raw/2026-05-01_sample-business-entities]]"
updated_at: 2026-05-01
update_summary: "産業資材取引 client sample を作成。"
update_source:
  - "[[raw/2026-05-01_sample-business-entities]]"
update_history:
  - "2026-05-01 産業資材取引 client sample を作成。"
---

# 産業資材取引 client sample を作成

## 要約

公開テンプレート用の架空 client として、産業資材の見積、受注、納期調整を扱う `sample-industrial-supplier` を作成した。

## 詳細

- 実在の得意先名、単価、仕入先、個別契約条件は含めない。
- BtoB 取引の見積・納期・顧客回答の分離を説明するためのサンプル。

## タスク

- サンプル見積管理表と納期確認メモを `sources.md` に登録する。
- 短納期見積の確認テンプレートを `states/current.md` に残す。

## 出典メモ

[[raw/2026-05-01_sample-business-entities]]
