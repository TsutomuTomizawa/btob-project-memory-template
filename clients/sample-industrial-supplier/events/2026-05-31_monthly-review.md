---
type: event
event_id: 20260531-sample-industrial-supplier-monthly-review
event_date: 2026-05-31
created_at: 2026-05-31T18:10:00+09:00
author: template
entity_type: client
entity_id: sample-industrial-supplier
event_type: review
derived_status: applied
derived_targets:
  - state
source_refs:
  - "[[events/2026-05-01_sample-created]]"
  - "[[events/2026-05-03_regular-meeting]]"
updated_at: 2026-05-31
update_summary: "5月の見積・納期調整フローを振り返り。"
update_source:
  - "[[events/2026-05-03_regular-meeting]]"
update_history:
  - "2026-05-31 5月の見積・納期調整フローを振り返り。"
---

# 2026-05 月次総括

## 要約

5月は短納期見積と納期回答の分離が中心。来月は確認テンプレートと顧客回答文のサンプルを整える。

## 良かったこと

- 確認項目を分けたことで、営業と調達の役割が見えやすくなった。

## 課題

- 未確定納期をどの表現で顧客に伝えるか、文面の型が足りない。

## 決定事項

- 顧客向け回答では、確定情報、確認中、代替案を分ける。
- 社内の値引き仮説や仕入先情報を顧客向け draft に混ぜない。

## 来月へ持ち越すこと

- 短納期見積の確認テンプレートを作る。
- 顧客向け納期回答文のサンプルを作る。

## 長期的な学び候補

- BtoB 取引では、社内判断材料と顧客共有文を分けるだけで、誤共有と手戻りを減らせる。

## 参照イベント

- [[events/2026-05-01_sample-created]]
- [[events/2026-05-03_regular-meeting]]
