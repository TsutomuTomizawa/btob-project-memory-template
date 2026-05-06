# Memory CLI

`scripts/memory` は、この vault の補助 CLI です。v1 は dry-run 中心で、保存・digest・output 生成の業務ロジックを持ちません。

CLI が行うこと:

- status と entity 一覧を read-only で表示する。
- 既存の lint、smoke、local QA、role guard を統一入口から呼び出す。
- 実 LLM 確認用の一時 vault と検証 runbook を作る。
- `memory-add` / `memory-save` / `memory-digest` / monthly-review flow に渡す agent 向け prompt を生成する。
- `publish` / `sync` で、日常の commit / push / main 最新化を Git の安全な入口に寄せる。

CLI が行わないこと:

- entity を推定して event を作る。
- event を分割、要約、digest する。
- 保存・digest の判断として `clients/`、`internal/`、`inbox/`、`raw/`、`company/` を直接更新する。
- 例外として、`lint --fix --staged` は staged 済み client / internal 非 event file の機械的な形式補正だけを行う。
- 例外として、`publish` は既存差分の stage / commit / branch push を行う。memory 内容の判断はしない。
- Codex CLI を自動実行して repository を更新する。
- `qa-llm` も LLM を自動起動しません。一時 vault とシナリオを作り、Codex / Claude が実際に skill を使った後の結果を検査します。

## Commands

```bash
scripts/memory status
scripts/memory status --json
scripts/memory status --with-lint
scripts/memory status --strict --with-lint
scripts/memory entities
scripts/memory entities --json
scripts/memory lint
scripts/memory lint --fix --staged
scripts/memory smoke
scripts/memory smoke --keep
scripts/memory qa
scripts/memory qa --keep
scripts/memory qa-llm prepare
scripts/memory qa-llm check /tmp/memory-llm-qa-.../vault
scripts/memory qa-llm check /tmp/memory-llm-qa-.../vault --cleanup
scripts/memory qa-llm cleanup /tmp/memory-llm-qa-.../vault
scripts/memory add --client example-client-gamma --name "Example Client Gamma" "Google商談・プロジェクト運用の新規 client"
scripts/memory add --internal sales-template-renewal --name "営業提案テンプレート刷新" "社内 project"
scripts/memory review --client example-client-alpha --month 2026-05 "5月を総括して保存"
scripts/memory review --internal sales-template-renewal --month 2026-05 "5月を総括して保存"
scripts/memory publish "クライアントメモを更新"
scripts/memory publish --branch codex/client-notes "クライアントメモを更新"
scripts/memory publish --no-wait "クライアントメモを更新"
scripts/memory sync
scripts/memory sync --prune-gone
scripts/memory privacy-scan
scripts/memory privacy-scan --staged
scripts/memory role-guard --staged
scripts/memory role-guard --ci --actor some-user --base origin/main --head HEAD
scripts/memory py-compile
scripts/memory diff-check
```

`status` は branch、dirty 状態、known entities、pending event、duplicate event_id、inbox 件数、未完了 task 件数を表示します。`--with-lint` を付けたときだけ lint を実行します。`--strict` は pending event、duplicate event_id、または実行した lint の失敗で non-zero を返します。

`lint --fix --staged` は pre-commit 用です。staged された `clients/` / `internal/` 配下の非 event markdown と `raw/` 配下の raw note を対象に、欠けた更新メタデータ、raw note の基本 frontmatter、手動セクション marker を補正して再 stage します。staged された既存 event の本文・immutable frontmatter 変更も止めます。cross-client 参照、invalid URL、source 不足など full vault の意味検査は `scripts/memory lint` と GitHub Actions で確認します。

`privacy-scan` は、未マスクの email address と日本の phone number らしき文字列を検出して止めます。CI log に実値を出さないため、検出時は file と line だけを表示します。`example.com` など予約ドメインのサンプル email は許可します。

`role-guard` は、local では通常 `HEAD` の `.memory-roles.json` と Git の `user.name` / `user.email`、または `MEMORY_ACTOR` を照合します。`--ci` では trusted main の `.memory-roles.json` と GitHub actor を見て、admin 以外の actor が `clients/`、`internal/`、`raw/`、`inbox/` 以外を更新していないか確認します。`.memory-local.json`、`git config memory.role`、`MEMORY_ROLE` は fallback または明示テスト用です。`raw/` は保存時の原本置き場として member も commit できます。`inbox/` は gitignore された local triage です。

`review` は月次総括用の prompt 生成です。`events/YYYY-MM-DD_monthly-review.md` に `event_type: review` の event を作る指示を出します。対象月の review event が既にある場合は上書きせず停止します。月別 `states/YYYY-MM.md` や repository 内の月次 report file は作りません。

`qa` は、CI と同じ smoke に加えて、CLI-first prompt、memory-add 相当の client / internal 新規作成、memory-save / memory-digest 相当の保存・反映シナリオ、monthly-review event、manual edit fix、local / CI role guard、pre-push hook を置いていないことを一時 vault 上で確認します。CI には入れず、改修時の手動確認に使います。

`qa-llm` は、実際の LLM agent が skill を読んで新規作成・保存・digest・月次総括を行えるかを確認するための手動 QA です。`prepare` は `memory-llm-qa-*` の一時 vault と `llm-qa/RUNBOOK.md` を作ります。その runbook を Codex / Claude に渡して一時 vault 内で処理させた後、`check` が raw 保存、薄い event、複数 entity 分割、inbox 退避、手動 current/profile 保持、internal 保存、sources 登録、correction event、digest 不要 event、monthly-review event、client / internal 新規作成、lint 通過を確認します。重いため CI には入れません。

`publish` は、ユーザーが「pushして」と依頼した時の標準入口です。`main` 上に未保存変更がある場合は、`origin/main` から `codex/memory-publish-...` の作業ブランチを作り、変更を戻してから `git add -A`、`git commit`、`git push -u origin <branch>` を実行します。commit 時には `.githooks/pre-commit` と `.githooks/commit-msg` が走り、日本語ではないコミットメッセージを止めます。push 後は GitHub Actions による PR 作成、CI、auto-merge を待ち、remote branch の削除を検知したら `sync` 相当で `main` に戻して最新化します。`main` 以外の branch で実行した場合は、その branch に commit して push し、同じように auto-merge 完了を待ちます。`gh` CLI は不要です。待たずに push だけで終える場合は `--no-wait` を使います。

`sync` は、PR が merge された後の標準入口です。未保存変更がないことを確認し、`git fetch origin --prune`、`git checkout main`、`git merge --ff-only origin/main` を実行します。現在の `codex/*` 作業ブランチの remote が merge 後に削除済みなら、local branch も削除します。`--prune-gone` を付けると、remote が消えている他の `codex/*` branch もまとめて片付けます。

## Prompt Generation

```bash
scripts/memory save --client example-client-alpha "定例で提案資料更新を優先することになった"
scripts/memory digest --client example-client-alpha
scripts/memory add --client example-client-gamma --name "Example Client Gamma" "Google商談・プロジェクト運用の新規 client"
scripts/memory review --client example-client-alpha --month 2026-05 "5月を総括して保存"
scripts/memory prompt save --client example-client-alpha "定例で提案資料更新を優先することになった"
scripts/memory prompt save --unknown "対象不明だが商談レポートの数字が落ちている"
scripts/memory prompt save --from-file meeting-notes.md --digest
scripts/memory prompt add --internal sales-template-renewal --name "営業提案テンプレート刷新"
scripts/memory prompt digest --client example-client-alpha
scripts/memory prompt digest --all-pending
scripts/memory prompt review --client example-client-alpha --month 2026-05
```

`scripts/memory save`、`scripts/memory add`、`scripts/memory digest`、`scripts/memory review` は、`scripts/memory prompt save` / `prompt add` / `prompt digest` / `prompt review` の短い alias です。生成された prompt を Codex / Claude Code に渡すと、agent が repository 内の正本 skill を読んで処理します。CLI 自体は保存、新規作成、digest、月次総括 event 作成を実行しません。

## Boundary

自然言語で「保存して」「更新して」「新規顧客を作って」「5月を総括して」と依頼する運用は変わりません。保存・digest・新規追加・月次総括系の依頼では、ユーザーが CLI と明示していなくても、agent はまず `scripts/memory save`、`scripts/memory digest`、`scripts/memory add`、または `scripts/memory review` で受付 prompt を生成します。CLI は、その依頼を安定した入口に乗せるための補助です。判断の authority は `.agentic/skills/` の skill 本体にあります。

lint、smoke、local QA、role guard も原則 `scripts/memory` 経由で実行します。古い個別 script が残っていても、通常運用の入口にはしません。
