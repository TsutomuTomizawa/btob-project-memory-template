---
type: source_index
entity_type: client
entity_id: sample-saas-platform
auto_generated: false
owner: human
updated_at: 2026-05-06
update_summary: "BtoB SaaS client sample の source index を公開用に作成。"
update_source:
  - [[events/2026-05-01_sample-created]]
update_history:
  - "2026-05-01 BtoB SaaS client sample の source index を作成。"
  - "2026-05-06 公開テンプレート用に URL と説明を一般化。"
---

# Sources

この entity で context として使ってよい外部資料の URL を管理します。公開テンプレートではすべて予約ドメインのサンプル URL です。

| 名称 | 種別 | URL | context | 備考 |
| --- | --- | --- | --- | --- |
| サンプル契約一覧 | spreadsheet | https://example.com/sample-saas-platform/contracts | on_demand | 契約期間、更新日、契約範囲を想定したサンプル。 |
| サンプル導入計画 | document | https://example.com/sample-saas-platform/onboarding-plan | on_demand | 初期設定、移行、トレーニングの計画を想定したサンプル。 |
| サンプル利用状況メモ | spreadsheet | https://example.com/sample-saas-platform/usage-summary | no | 公開テンプレートでは実データを含めないため context には使わない。 |
