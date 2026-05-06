---
type: entity_state
entity_type: client
entity_id: sample-industrial-supplier
auto_generated: true
owner: memory-digest
last_digest: 2026-05-06
updated_at: 2026-05-06
update_summary: "産業資材取引 client sample の現在状態を公開用に作成。"
update_source:
  - [[../events/2026-05-03_regular-meeting]]
  - [[../events/2026-05-31_monthly-review]]
update_history:
  - "2026-05-01 産業資材取引 client sample の初期 current state を作成。"
  - "2026-05-06 公開テンプレート用に現在状態を一般化。"
---

# 状態

## 現在の状態

- 短納期見積の対応フローを整理中。数量、希望納期、在庫有無、代替品可否、承認者を分けて確認する。出典: [[../events/2026-05-03_regular-meeting]]
- 顧客向け納期回答は、確定情報と確認中の候補を分けて書く。出典: [[../events/2026-05-31_monthly-review]]

## リスク

- 未確定納期を確約として書くと、顧客期待と実際の調達状況がずれる。出典: [[../events/2026-05-31_monthly-review]]
- 個別価格や仕入先情報は公開・顧客共有前提の draft に含めない。出典: [[../events/2026-05-01_sample-created]]

## 決定事項

- 見積メモは「依頼内容」「社内確認」「顧客回答」「次アクション」に分ける。出典: [[../events/2026-05-03_regular-meeting]]
- 値引きや代替品提案の社内仮説は、顧客向け draft に直接混ぜない。出典: [[../events/2026-05-31_monthly-review]]

## 次のアクション

- [ ] 短納期見積の確認テンプレートを作る。出典: [[../events/2026-05-03_regular-meeting]]
- [ ] 納期回答文のサンプルを「確定」「確認中」「代替案」に分けて作る。出典: [[../events/2026-05-31_monthly-review]]
- [ ] 顧客向けに出せない社内メモの扱いをレビューする。出典: [[../events/2026-05-31_monthly-review]]

## 出典イベント

- [[../events/2026-05-01_sample-created]]
- [[../events/2026-05-03_regular-meeting]]
- [[../events/2026-05-31_monthly-review]]

## 手動メモ

<!-- BEGIN MANUAL -->
<!-- END MANUAL -->
