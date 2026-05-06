---
type: source_index
entity_type: client
entity_id: sample-industrial-supplier
auto_generated: false
owner: human
updated_at: 2026-05-06
update_summary: "産業資材取引 client sample の source index を公開用に作成。"
update_source:
  - [[events/2026-05-01_sample-created]]
update_history:
  - "2026-05-01 産業資材取引 client sample の source index を作成。"
  - "2026-05-06 公開テンプレート用に URL と説明を一般化。"
---

# Sources

公開テンプレートのため、URL はすべて予約ドメインのサンプルです。実取引の単価表、得意先名、仕入先情報は入れないでください。

| 名称 | 種別 | URL | context | 備考 |
| --- | --- | --- | --- | --- |
| サンプル見積管理表 | spreadsheet | https://example.com/sample-industrial-supplier/quote-log | on_demand | 見積番号、数量、納期、承認状況を想定したサンプル。 |
| サンプル納期確認メモ | document | https://example.com/sample-industrial-supplier/delivery-notes | on_demand | 納期回答と顧客連絡履歴を想定したサンプル。 |
| サンプル価格表 | spreadsheet | https://example.com/sample-industrial-supplier/pricing | no | 公開テンプレートでは実価格を含めないため context には使わない。 |
