# コラボレーション

このリポジトリは GitHub Issues と push 後の GitHub Actions 確認を前提にします。Pull Request は原則として受け付けません。

## 編集責任

- Obsidian は閲覧・確認用です。client / internal 配下の `events/` 以外の `profile.md`、`sources.md`、`states/current.md` と top-level `raw/` は人間が手動編集できます。
- 人間はファイルを直接編集しても、議事録、メモ、URL、修正依頼、会社方針を Codex / Claude Code に渡しても構いません。commit 前 lint で指定形式へ寄せます。
- エージェントは repository 内 skill を読んで、決められた手順でファイルを更新します。
- commit / push 前後に、人間が差分と GitHub Actions の結果を確認します。

スキルが更新する領域:

- `raw/`
- `inbox/`
- `events/`
- `profile.md`
- `sources.md`
- `states/current.md`
- チャット上で作る共有文・提案文・打合せ準備 draft
- `views/` の Dataview query（構造変更時のみ）
- 明示依頼がある場合の `company/`

## レビュー運用

- save / digest / review batch はレビューしやすい単位にする。
- 可能な限り、未加工 event と派生 update を分ける。
- 共有前に安全チェックを実行する。
- クライアント向け draft は送付前に人間が本文を確認する。
- 別 client の source を使ったクライアント向け draft は作らない。
- `inbox/` の業務メモを正式 memory に使う場合は、client / internal event に昇格してから取り込む。

## ロールと更新範囲

ローカル hook は `HEAD` の `.memory-roles.json` と Git の `user.name` / `user.email` を見て、通常メンバーが repository 運用側を誤って変更しないようにします。CI では trusted main の `.memory-roles.json` と push actor を見て同じ範囲を強制します。

- `member`: 通常メンバー。`clients/`、`internal/`、`raw/`、`inbox/` を更新します。
- `developer`: skill、tool、template、docs、hook など仕組み側を更新できます。
- `admin`: `company/` を含む管理方針や repository 全体を更新できます。

`.memory-roles.json` では `tsutomutomizawa` を `admin`、それ以外を既定 `member` とします。担当範囲をさらに絞る場合は、担当者の `allowed_roots` に `clients/{client_id}`、`internal/{project_id}`、必要に応じて `raw`、`inbox` を設定します。

## 取り込み方針

- ローカル自動チェックで commit 前の安全チェックと staged fix を走らせる。
- 日常の push 依頼では `scripts/memory publish` を使い、現在の branch で commit / push する。
- 公開テンプレートでは自動 PR 作成、repository secret `AUTO_PR_TOKEN`、native auto-merge は使わない。
- Pull Request は原則受け付けない。必要な場合は事前に Issue で方針を確認し、maintainer が判断する。
- CODEOWNERS は責任範囲の目印として残すが、GitHub 上の必須 review 条件にはしない。
- 別端末で更新された場合は、未保存変更がないことを確認してから `scripts/memory sync` で `main` に戻り、最新版を取り込む。
- `company/`、skills、templates、検査 tool の変更は人間レビューを推奨する。

## ローカル自動チェック

初回セットアップでは、Codex / Claude Code に自動チェックの有効化を依頼します。

- 履歴保存前チェック: ファイルの書き方、Python syntax、安全ルールを確認する。
- ローカル負荷を抑えるため、Python syntax check と staged memory lint/fix は関連 path が staged されたときだけ実行する。
- push / 例外的な PR チェック: GitHub Actions で基本動作と lint を確認する。

レビューを厚めに見る変更:

- `company/` の変更。
- `.agentic/skills/`、template、検査 tool の変更。
- `raw/` の変更。
- 複数 client を含む変更。
