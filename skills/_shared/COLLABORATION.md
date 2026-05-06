# コラボレーションルール

## デフォルト workflow

- GitHub pull request を使います。
- 1 回の保存または digest batch はレビューしやすい単位にします。
- 可能な限り、PR では event 追加と派生更新を分けて見えるようにします。
- Obsidian は閲覧・確認用です。client / internal 配下の `events/` 以外と top-level `raw/` は人間が手動編集できます。保存・digest や event 訂正は、人間の依頼を受けたエージェントが skill 経由で行います。

## 人間が主に持つ領域

- Obsidian と PR 差分での確認。
- 議事録、メモ、URL、修正依頼の提供。
- マネジメントが承認した `company/` 方針の提供。
- クライアント向け draft の review 判断。

## スキルが主に持つ領域

- `raw/`
- `inbox/`
- `events/`
- `profile.md`
- `sources.md`
- `states/current.md` の生成セクション
- チャット上で作る共有文・提案文・打合せ準備 draft
- `views/` の Dataview query（構造変更時のみ）
- 明示依頼がある場合の `company/`

## ロールと更新範囲

ローカル hook は `HEAD` の `.memory-roles.json` と Git の `user.name` / `user.email` を見て、通常メンバーが repository 運用側を誤って変更しないようにします。

- `member`: 通常メンバー。`clients/`、`internal/`、`inbox/`、`raw/` だけを更新します。
- `developer`: skill、tool、template、docs、hook など仕組み側を更新できます。
- `admin`: `company/` を含む管理方針や repository 全体を更新できます。

担当範囲をさらに絞る場合は、担当者の `allowed_roots` に `clients/{client_id}` または `internal/{project_id}` を設定します。設定されている member は、指定 entity と共有 `inbox/`、`raw/` だけを更新します。

## レビューチェックリスト

- 対象 entity は正しいか。
- クライアント向け draft が同じ client の情報だけで作られているか。
- 内部懸念、未確定情報、他社情報がクライアント向け draft に混ざっていないか。
- `inbox/` の業務メモを正式 memory として使う場合、client / internal event に昇格しているか。
- `states/current.md` の task は実行可能で、可能なら担当が明確か。
- conflict が隠されず明示されているか。
- 重要な派生 claim に source がリンクされているか。
- クライアント向け draft は同じ client の source を使っているか。
