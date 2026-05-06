# 運用

## 毎日のループ

1. セッション開始時に `company/session-context.md`、`company/strategy.md`、`company/rules.md` を確認する。
2. 人間が議事録、メモ、URL、修正依頼を Codex / Claude Code に渡す。
3. 未加工メモを `memory-save` で保存する。生入力は top-level `raw/`、時系列正本は entity の `events/` に置く。
4. 未処理 event を `memory-digest` で `profile.md` と `states/current.md` に反映する。event 由来の箇条書きは、各 section 内でできるだけ source event の日付が新しい順に整える。
5. `memory-query` で質問する。
6. `memory-output` でクライアント向け下書きや打合せ準備をチャット上に作る。
7. 月次で振り返る場合は `scripts/memory review ...` で `monthly-review` event を作り、来月へ持ち越すものだけ `states/current.md` に残す。
8. 安全チェック用の skill で vault を確認する。

Obsidian は基本的に閲覧・確認用ですが、client / internal 配下の `profile.md`、`sources.md`、`states/current.md` と top-level `raw/` は手動編集できます。client / internal markdown や event が staged された commit では、`scripts/memory lint --fix --staged` が機械的な形式不備を補正し、既存 event 改ざんを止めます。full vault の意味検査は GitHub Actions の必須 CI で確認します。

## 補助 CLI

`scripts/memory` は、日常運用を安定させるための dry-run 中心 CLI です。status、entity 一覧、lint / smoke / local QA の呼び出し、agent に渡す prompt 生成、日常の publish / sync だけを行います。

CLI は `memory-save` や `memory-digest` の代わりに判断しません。保存・digest・月次総括系の更新では、ユーザーが CLI と明示していなくても、まず `scripts/memory save`、`scripts/memory digest`、または `scripts/memory review` で agent 向け prompt を生成し、その prompt と該当 skill 経由で更新します。詳細は `docs/CLI.md` を参照してください。

ユーザーが「pushして」と依頼した場合、エージェントは通常 `scripts/memory publish "短い日本語のコミットメッセージ"` を使います。コミットメッセージ、PR タイトル、PR 本文は日本語で作成します。`main` 上にいる場合も direct push せず、作業ブランチを作って commit / push し、PR/CI/auto-merge 完了後に main へ戻って最新化します。ユーザーが「最新化して」と依頼した場合は、未保存変更がないことを確認してから `scripts/memory sync` を使います。

## 初回セットアップ

複数人で運用する場合、各メンバーは repository を clone した後に以下を実行します。

```bash
./scripts/setup-member.sh
```

これにより履歴保存前に `scripts/memory privacy-scan --staged` と `scripts/memory role-guard` が走ります。Python syntax check と `scripts/memory lint --fix --staged` は、関連する staged path がある場合だけ走ります。commit-msg hook は日本語ではないコミットメッセージを止めます。pre-push hook は置きません。

作業ブランチへの push と main 向け PR では GitHub Actions が `scripts/memory commit-language`、`scripts/memory py-compile`、`scripts/memory privacy-scan`、`scripts/memory lint`、`scripts/memory smoke`、diff whitespace check を実行し、PR ではタイトルと本文も日本語か確認します。さらに trusted workflow が `.memory-roles.json` と push actor を見て `memory-role-guard` status を付けます。

仕組み側の改修後に保存・digest・hook 周りまで確認したい場合は、ローカルで `scripts/memory qa` を任意実行します。これは CI には入れません。

## ロール

- `member`: 通常メンバー。`clients/`、`internal/`、`raw/`、`inbox/` を更新します。
- `developer`: skill、tool、template、docs、hook など仕組み側を更新します。
- `admin`: `company/` を含む管理方針や repository 全体を更新します。

通常セットアップでは、tracked file の `.memory-roles.json` が role の正本です。ローカル pre-commit は `HEAD` の `.memory-roles.json` と Git の `user.name` / `user.email` を照合します。CI では trusted main の `.memory-roles.json` と GitHub actor を照合します。`tsutomutomizawa` は `admin`、それ以外は既定 `member` として扱います。

## GitHub 接続

GitHub 側では以下を設定します。

- `main` への direct push を禁止し、PR 経由で取り込む。
- GitHub Actions / commit status の `memory-vault-ci` と `memory-role-guard` を必須 check にする。
- CODEOWNERS は責任範囲を示す目印として残すが、GitHub 上の必須 review 条件にはしない。
- 作業ブランチ push 後の PR 自動作成には、repository secret `AUTO_PR_TOKEN` を設定する。
- GitHub の native auto-merge を有効化できる場合は有効化し、作業ブランチ push 後に自動作成された PR が CI 通過後に merge されるようにする。

## ルーティング確認

- 単一 client のメモは、その client 配下の event になる。
- 保存依頼では、top-level `raw/` に生入力の原本を残す。
- 複数 client を含むメモは raw 原本を 1 つ残し、client ごとの event に分割する。
- 対象 client / internal が分かる業務メモは、軽い内容でも event にする。派生更新しない場合は `derived_targets: []` にする。
- 月次総括は `events/YYYY-MM-DD_monthly-review.md` に `event_type: review` で保存する。月別 `states/YYYY-MM.md` や output file は作らない。
- 対象が不明な業務メモだけ `inbox/` に置き、対象が分かるまで event 化しない。
- `inbox/` の内容を業務に使う場合は、先に client / internal の event に昇格する。
- `company/` は通常の save / digest で自動更新しない。会社方針にしたい学びは、まず対象 entity に保存してマネジメント判断待ちにする。

## 定期確認

- `views/updates.md` と `views/tasks.md` を確認する。
- 必要な Google Workspace 資料 URL をエージェントに渡し、entity の `sources.md` に追加してもらう。
- 完了した task はエージェントに依頼し、entity の `states/current.md` で閉じてもらう。
- active entity ごとに `profile.md`、`states/current.md`、`sources.md` の古い情報を確認する。
- 月末や翌月初に「5月を総括して」と依頼し、月内 events から `monthly-review` event を作る。
- マネジメントが承認した pattern は、明示依頼としてエージェントに渡し、必要に応じて `company/strategy.md` または `company/rules.md` に反映してもらう。
