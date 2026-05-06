# Memory

この repository は、BtoB 取引や社内プロジェクトを entity 別に扱うための memory vault です。

## 基本単位

- `client`: 顧客、商談、導入、更新、取引履歴。
- `internal`: 社内プロジェクト、改善活動、横断ナレッジ。
- `company`: 会社レベルの方針、ルール、会話指針。

## 主要ファイル

- `profile.md`: 長く使う背景、制約、判断軸、学び。
- `states/current.md`: 現在状態、進行中タスク、リスク、決定事項、次アクション。
- `sources.md`: 外部資料の索引。
- `events/`: 何が起きたかの追記専用記録。
- `raw/`: 保存時の原本。

## Skill

- 保存 -> `memory-save`
- 派生反映 -> `memory-digest`
- 読み取り質問 -> `memory-query`
- 下書き作成 -> `memory-output`
- 新規追加 -> `memory-add`
- 検査 -> `memory-lint`

保存・digest・新規追加・月次総括では、まず `scripts/memory ...` で agent 向け prompt を生成し、その prompt と repository skill を正本として実更新します。
