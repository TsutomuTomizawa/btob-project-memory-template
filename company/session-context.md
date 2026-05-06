---
type: company_session_context
entity_type: company
entity_id: company
auto_generated: false
owner: management
last_reviewed: 2026-05-06
updated_at: 2026-05-06
update_summary: "BtoB 取引・社内プロジェクト管理向けの公開テンプレート文脈に更新。"
update_source: []
update_history:
  - "2026-05-06 BtoB 取引・社内プロジェクト管理向けの公開テンプレート文脈を作成。"
---

# セッション開始時コンテキスト

この vault は、BtoB 取引、顧客別商談、導入・納品プロジェクト、社内改善プロジェクトを、entity 別に安全に扱うための公開テンプレートです。

この vault で作業するエージェントは、会話の最初にこのファイルを読み、必要に応じて [[strategy]] と [[rules]] を確認します。クライアントや社内プロジェクトについて会話、議論、提案判断をするときは、会社方針を上位文脈として読み、そのうえで対象 entity の memory を確認します。

## 会話の指針

- この repository は公開テンプレートであり、実在顧客、担当者、契約金額、非公開 URL、個人情報を含めない。
- クライアントごとの商談、契約条件、見積、導入状況、リスク、社内評価を混ぜない。
- クライアントについて相談されたら、対象 client の `profile.md` と `states/current.md` を先に確認してから答える。外部資料が必要な場合だけ `sources.md`、監査性が必要な場合だけ recent events を確認する。
- 対象 client / internal が分かる業務メモは、軽い内容でも該当 entity の event にする。
- 対象 client / internal が分からない業務メモだけ、共有の `inbox/` に置く。業務で使う場合は、先に client / internal の event に昇格する。
- 月次総括を保存する場合は、月別 state file ではなく対象 entity の `monthly-review` event として残す。来月へ持ち越す active item だけ `states/current.md` に反映する。
- 顧客向けに出せる表現と、社内だけで扱う仮説、懸念、粗い評価、競合比較、価格交渉メモを分ける。
- BtoB 取引の判断では、事実、数値、推論、提案、顧客向け文面を分け、数字や外部資料を推測で補わない。
- 契約、価格、納期、法務、セキュリティ、購買条件に関わる内容は断定せず、確認事項と根拠を分ける。
- Google Workspace などの外部資料を使う場合は、対象 entity の `sources.md` に登録された URL を優先し、`context: yes` または `on_demand` の資料だけを必要範囲で取得する。取得できない場合は中身を推測しない。
- `views/` は Dataview に任せ、LLM は一覧を手書き更新しない。
- `company/` はマネジメントの方針・ルールの正本として扱い、通常の digest で自動更新しない。
- client / internal 配下の `profile.md`、`sources.md`、`states/current.md` と top-level `raw/` は Obsidian から手動編集できる。commit 前 lint で指定形式へ補正または停止する。
- 保存依頼では top-level `raw/` に生入力の原本を残し、関係する各 event から参照する。複数 client / internal を跨ぐ raw も client 配下へ複製しない。

## 読む順番

1. このファイル。
2. [[strategy]]
3. [[rules]]
4. 作業対象 entity の `profile.md` と `states/current.md`。
5. 契約、見積、導入計画、議事録など外部資料が必要な場合だけ、対象 entity の `sources.md` に登録された URL を読む。
6. 監査性が必要な場合だけ recent events を読む。
