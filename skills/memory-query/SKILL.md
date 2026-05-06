---
name: memory-query
description: 顧客・社内PJ・会社 context に読み取り専用で問い合わせる。
---

# memory-query

クライアント、社内プロジェクト、会社方針、現在状態、tasks、risks、履歴に関する読み取り専用質問で使うスキルです。

## 必須読み込み

まず以下を読む。

1. `company/session-context.md`
2. `company/strategy.md`
3. `company/rules.md`

entity 固有の質問では以下を読む。

1. 対象 entity の `profile.md`
2. 対象 entity の `states/current.md`
3. 外部資料が必要な場合だけ対象 entity の `sources.md` を読み、`context: yes` または `on_demand` の URL を `gws` CLI で取得する。取得できない場合は失敗理由を伝え、中身を推測しない。
4. 監査性が必要な場合だけ recent events を読む。

横断質問では以下を読む。

1. 関連 `views/` の Dataview 結果
2. `company/session-context.md`
3. `company/strategy.md`
4. `company/rules.md`
5. 関連 entity の `profile.md` と `states/current.md`

inbox に関する質問では、`inbox/` 配下を読み、共有の業務 triage として扱う。正式 memory ではないため、client / internal の確定情報として使う前に event 昇格が必要だと明示する。

## ルール

- ファイルを書き換えない。
- 重要な事実には source file または event を cite する。
- 確認済み事実と推論を分ける。
- 根拠が弱い event や未確定情報に依存する場合は明示する。
- クライアント向け表現に内部懸念、未確定情報、他社情報を使わない。
- 日本語で聞かれたら日本語で答える。
