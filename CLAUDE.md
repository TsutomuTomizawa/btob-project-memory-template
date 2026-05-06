# Claude Code 向け指示

このファイルは `AGENTS.md` と同じ運用を Claude Code から読めるようにしたものです。詳細な正本は `AGENTS.md` と `.agentic/` 配下の skill です。

## 必ず読むファイル

1. `company/session-context.md`
2. `company/strategy.md`
3. `company/rules.md`
4. `.agentic/AGENT_CONTRACT.md`
5. `.agentic/skills/_shared/SCHEMA.md`
6. `.agentic/skills/_shared/GUARDRAILS.md`
7. 関連する `.agentic/skills/{skill}/SKILL.md`

## ルーティング

- 保存依頼 -> まず `scripts/memory save ...` で prompt 生成、その後 `memory-save`。
- digest 依頼 -> まず `scripts/memory digest ...` で prompt 生成、その後 `memory-digest`。
- 新規 client / internal -> まず `scripts/memory add ...` で prompt 生成、その後 `memory-add`。
- 月次総括 -> まず `scripts/memory review ...` で prompt 生成、`memory-save` の monthly-review flow。
- 読み取り質問 -> `memory-query`。
- 顧客向け draft -> `memory-output`。repository に output file として保存しない。

## 公開テンプレートとしての注意

- 実在顧客、担当者、契約金額、単価、非公開 URL、個人情報、秘密情報を追加しない。
- 公開 repository に置けない内容は private fork で扱う。
- `events/` は追記専用。訂正は correction event として追加する。
- `company/` は通常の save / digest で自動更新しない。
