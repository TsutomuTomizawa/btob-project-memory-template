# 検証

スキル、template、lint rule、routing behavior を変更したときに使います。

## CLI 確認

補助 CLI を変更したときは、以下を確認します。

```bash
scripts/memory py-compile
scripts/memory status
scripts/memory status --json
scripts/memory entities
scripts/memory save --client example-client-alpha "定例で提案資料更新を優先することになった"
scripts/memory digest --client example-client-alpha
scripts/memory add --client example-client-gamma --name "Example Client Gamma" "Google商談・プロジェクト運用の新規 client"
scripts/memory review --client example-client-alpha --month 2026-05 "5月を総括して保存"
scripts/memory prompt save --client example-client-alpha "定例で提案資料更新を優先することになった"
scripts/memory prompt save --unknown "対象不明だが商談レポートの数字が落ちている"
scripts/memory prompt add --internal sales-template-renewal --name "営業提案テンプレート刷新"
scripts/memory prompt digest --client example-client-alpha
scripts/memory prompt review --client example-client-alpha --month 2026-05
scripts/memory lint --fix --staged
scripts/memory privacy-scan
scripts/memory smoke
scripts/memory qa
scripts/memory role-guard --worktree
```

## スモークテスト

実行:

```bash
scripts/memory smoke
```

スモークテストは vault を一時ディレクトリにコピーし、以下を確認します。

- 基準 lint が通る。
- client / internal entity が軽量構成で作れる。
- top-level raw note を保存し、event から参照できる。
- raw 原本を厚く残し、event は長文を再コピーしない薄い index として扱う。
- 単一 client update を保存し、`profile.md` と `states/current.md` に digest できる。
- 複数 client の meeting が client 別 event に分割される。
- 対象不明の業務 note が `inbox/` に残る。
- 廃止済みの `tasks.md`、`wiki/`、`outputs/`、月次 state が reject される。
- 誤った場所に置かれた event が reject される。
- entity 配下の file が別 client / internal の file や raw note を直接参照すると reject される。
- pending event が reject される。
- sources の entity metadata、URL、context が検査される。
- 更新メタデータの欠落が reject される。
- staged client / internal 非 event file と raw note の機械的な不備が `lint --fix --staged` で補正され、再 stage される。
- コミットメッセージ、PR タイトル、PR 本文が日本語ではない場合に reject される。
- 未マスクの email address / phone number が `privacy-scan` で reject され、masked value なら通る。
- pre-commit は関連 staged path がない場合に Python syntax check と staged memory lint/fix を skip する。
- staged された既存 event の本文・immutable frontmatter 変更が reject される。
- company context file が存在し、`company/` 配下の markdown が 4 ファイルだけである。

一時 vault を確認用に残す場合は `scripts/memory smoke --keep` を使います。

## ローカル QA

実行:

```bash
scripts/memory qa
```

ローカル QA は改修時に任意で実行する重めの確認です。CI には入れません。

- CI と同じ smoke を先に実行する。
- `scripts/memory add` / `scripts/memory save` / `scripts/memory digest` の CLI-first prompt が repository skill へ routing することを確認する。
- `scripts/memory review` の CLI-first prompt が monthly-review event flow へ routing することを確認する。
- memory-add skill の規約に沿って、client / internal project を軽量構成で新規作成できることを確認する。
- memory-save / memory-digest skill の規約に沿って、単一 client 保存、複数 client 分割保存、internal project 保存、対象不明 inbox 保存を一時 vault 上で作り、lint で検証する。
- 月次総括は `event_type: review` の `monthly-review` event として作り、月別 state file を作らないことを確認する。
- 既存の monthly-review event がある月は `scripts/memory review` が上書きせず停止することを確認する。
- client + internal が混在する raw でも、raw 原本は 1 つにして entity 別 event に分割できることを確認する。
- LLM QA では raw note を持つ event が長文 raw を再掲しないことを確認する。
- save 直後の pending event が検出され、digest 反映後に `applied` と source reference が揃って通ることを確認する。
- digest 後の `profile.md` / `states/current.md` では、event 由来の箇条書きが各 section 内でできるだけ新しい source event 順に並ぶことを確認する。
- correction event で既存 event を直接書き換えずに訂正できることを確認する。
- `sources.md` への valid URL 登録と、不正 `context` の reject を確認する。
- 重複 `event_id` と重複 `raw_id` が reject されることを確認する。
- Obsidian 手動貼り付け相当の staged client / internal manual files と raw note が `lint --fix --staged` で補正され、再 stage されることを確認する。
- 日本語コミットメッセージの検査が通り、英語だけのコミットメッセージが reject されることを確認する。
- local `member` role の `allowed_roots` と CI `.memory-roles.json` が repository 保守 path を拒否することを確認する。
- pre-push hook が存在しないことを確認する。

一時 vault を確認用に残す場合は `scripts/memory qa --keep` を使います。

## LLM QA

実際の Codex / Claude Code が skill を読んで保存・digest できるかを、人手で確認するための任意 QA です。CI には入れません。

```bash
scripts/memory qa-llm prepare
```

生成された一時 vault の `llm-qa/RUNBOOK.md` を LLM agent に渡し、一時 vault 内で処理させます。その後、元 repository または一時 vault から以下を実行します。

```bash
scripts/memory qa-llm check /tmp/memory-llm-qa-.../vault --cleanup
```

確認する主なケース:

- 単一 client の raw / event / digest。
- 複数 client / internal を含む raw の entity 別 event 分割。
- 対象不明メモの `inbox/` 退避。
- Obsidian 手動追記済み current / profile の保持。
- internal project の保存と digest。
- `sources.md` への on-demand source 登録。
- 既存 event を書き換えない correction event。
- `derived_targets: []` の digest 不要 event。
- 月次総括の `monthly-review` event と current への carry-over。
- memory-add による client / internal project 新規作成。

## ロール guard

ローカル hook の更新範囲確認だけを手動で見る場合:

```bash
scripts/memory role-guard --staged
```

ローカルでは `HEAD` の `.memory-roles.json` と Git の `user.name` / `user.email` を照合し、`member` の人は `clients/`、`internal/`、`raw/`、`inbox/` 以外の変更が止まります。CI では trusted main の `.memory-roles.json` を正本にし、`tsutomutomizawa` 以外の GitHub actor は既定 `member` として同じ制限を受けます。
