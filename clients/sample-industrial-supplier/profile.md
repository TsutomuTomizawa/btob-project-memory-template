---
type: client_profile
entity_type: client
entity_id: sample-industrial-supplier
auto_generated: false
owner: human
updated_at: 2026-05-06
update_summary: "産業資材取引 client sample の安定コンテキストを公開用に作成。"
update_source:
  - [[events/2026-05-01_sample-created]]
  - [[events/2026-05-03_regular-meeting]]
update_history:
  - "2026-05-01 産業資材取引 client sample を作成。"
  - "2026-05-06 公開テンプレート用に安定コンテキストを一般化。"
---

# Sample Industrial Supplier

## 安定コンテキスト

- 産業資材の見積、受注、納期調整を扱う架空の BtoB client sample。出典: [[events/2026-05-01_sample-created]]
- 顧客別価格、在庫、納期、代替品提案、承認フローを分けて記録する必要がある。出典: [[events/2026-05-03_regular-meeting]]
- 実在の得意先名、単価、仕入先名、個別契約条件は公開テンプレートに含めない。出典: [[events/2026-05-01_sample-created]]

## 判断軸

- 見積の判断では、数量、希望納期、在庫有無、代替品可否、承認者を分ける。出典: [[events/2026-05-03_regular-meeting]]
- 受注後の進行では、発注確認、納期回答、出荷予定、請求条件、顧客連絡履歴を混ぜない。出典: [[events/2026-05-03_regular-meeting]]
- 顧客向け draft では、未確定納期を確約として書かず、確認中または候補として表現する。出典: [[events/2026-05-31_monthly-review]]

## 取引管理ナレッジ

- 短納期依頼では、在庫確認と代替品可否の判断を先に行うと、営業・調達・顧客対応の手戻りが減る。出典: [[events/2026-05-03_regular-meeting]]
- 値引き交渉は個別事情に依存しやすいため、社内メモと顧客共有文を分ける。出典: [[events/2026-05-31_monthly-review]]

## 手動メモ

<!-- BEGIN MANUAL -->
<!-- END MANUAL -->

## 共有しないメモ

<!-- BEGIN MANUAL -->
<!-- END MANUAL -->
