---
type: company_rules
entity_type: company
entity_id: company
auto_generated: false
owner: management
last_reviewed: 2026-05-06
updated_at: 2026-05-06
update_summary: "BtoB 取引・社内プロジェクト管理向けの公開テンプレートルールに更新。"
update_source: []
update_history:
  - "2026-05-06 BtoB 取引・社内プロジェクト管理向けの公開テンプレートルールを作成。"
---

# 組織ルール

このファイルは、実運用ではマネジメントが編集します。通常の `memory-save` / `memory-digest` で自動更新しません。

## Memory 運用

- `company/` はマネジメントが書く戦略・ルール・会話指針の正本とする。
- 通常の `memory-save` / `memory-digest` は `company/` を自動更新しない。
- 会社ルールに昇格したい学びがある場合は、対象 entity の event に出典付きで保存し、マネジメント判断待ちにする。
- `views/` は Obsidian Dataview で自動表示する。LLM は一覧を手書き更新しない。
- `inbox/` は対象 entity を安全に特定できない業務メモの local triage として扱う。通常メモは gitignore し、Git 管理するのは `inbox/README.md` だけにする。
- client / internal 配下の `profile.md`、`sources.md`、`states/current.md` と top-level `raw/` は Obsidian から手動編集できる。
- client / internal 配下の `events/` は追記専用の時系列正本として扱い、既存本文や immutable frontmatter を直接変更しない。訂正は correction event で残す。
- 月次総括は `events/YYYY-MM-DD_monthly-review.md` の `event_type: review` として残し、月別 state file や repository 内の月次 report file は作らない。

## BtoB 取引・プロジェクト運用

- 商談、契約、見積、発注、納期、導入、更新、社内改善を扱う。
- 記録では、背景、判断理由、確認した資料、決定事項、未決事項、顧客確認、社内確認、次アクションをできるだけ分ける。
- 契約金額、単価、数量、納期、利用率、商談確度、予算、契約条件などの数値・条件は、根拠資料または event がない限り断定しない。
- Google Workspace、CRM、BI ダッシュボード、共有スプレッドシート、提案資料、議事録などの外部資料は、対象 entity の `sources.md` に登録してから継続利用する。
- `sources.md` の `context: yes` / `on_demand` 資料は、必要な範囲だけ取得する。取得失敗時は中身を推測しない。
- 顧客向け文面、提案文、見積回答、納期回答などは、事実主張、前提条件、未確認事項、社内懸念を分けて扱う。
- 契約、法務、セキュリティ、購買条件、価格、納期に関わる文面では、未確認事項を確約として書かない。
- 顧客へ出すレポートや提案は `memory-output` でチャット上に draft として作り、人間が最終確認してから送る。軽量構成では repository に output file として保存しない。

## クライアント分離

- 複数クライアントを含むメモは client ごとに event を分割する。
- 保存依頼では top-level `raw/` に生入力の原本を保存し、関係する各 entity の event から参照する。複数クライアントを含む raw note は client 配下へ複製しない。
- 対象 client / internal が分かる業務メモは、軽い内容でも該当 entity の event として保存する。派生更新しない場合は `derived_targets: []` にする。
- 対象が不明な業務メモだけ `inbox/` に置き、推測で client event にしない。
- `inbox/` は正式 memory ではない。業務で使う場合は、該当 client / internal の event に昇格してから扱う。
- `events/`、`profile.md`、`sources.md`、`states/current.md`、`raw/` はすべて社内用 memory として扱い、顧客にそのまま出さない。
- 顧客向け draft で source を参照する場合は、同じ client の event / profile / sources / states/current だけを使う。raw は event の source として辿る。
- 他クライアントの成功事例、契約条件、見積、納期、提案内容を、特定できる形で別クライアントへ流用しない。横断知見として使う場合は、匿名化・一般化して internal / company 側に昇格してから使う。

## 共有安全性

- 内部懸念、推測、未検証の主張、他社情報は顧客向け draft に含めない。
- `inbox/` の業務メモを顧客向け draft の根拠にしない。必要なら正式 event に昇格してから使う。
- 根拠が弱い claim は draft 本文で弱さを明示するか、作成を止めて人間に確認する。
- 文章として安全かどうかは、人間レビュー、CODEOWNERS の責任範囲表示、必須 CI で確認する。frontmatter の細かい共有可否ラベルには依存しない。
- 契約・法務・セキュリティに関わる文面は、AI の判断だけで通過可否を断定しない。リスクがある場合は、人間確認または専門家確認が必要なものとして扱う。
