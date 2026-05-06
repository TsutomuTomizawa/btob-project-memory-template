# エージェント契約

この契約は、このリポジトリで作業するすべてのエージェントに適用されます。

## 正本

- Event は「何が起きたか」の主要記録です。
- Profile は人間が意図を与え、エージェントが明示依頼と skill に従って整える安定コンテキストです。
- `states/current.md` は現在状態、進行中タスク、リスク、決定事項、次アクションだけを最新化する作業面です。
- `views/` は Obsidian Dataview の横断ダッシュボードです。LLM が一覧を手書き更新しません。
- `company/` はマネジメントが管理する戦略・ルール・会話指針の正本です。セッション開始時に `company/session-context.md`、`company/strategy.md`、`company/rules.md` を読みます。
- `inbox/` は共有の業務 triage です。対象 client / internal を安全に特定できない業務メモだけを置きます。
- `raw/` は Obsidian で見える原本置き場です。複数 client / internal を跨ぐ raw もここに 1 つだけ保存し、各 entity の event から参照します。
- 共通ルールは `.agentic/skills/_shared/` にあります。
- `.agentic/skills/*/SKILL.md` のスキル本体だけが実装上の authority です。

## コラボレーション

- GitHub Issues と push 後の GitHub Actions 確認を前提にします。Pull Request は原則として受け付けません。
- v1 では全メンバーが全クライアント・全社内プロジェクトを読める前提です。
- ローカル hook は `HEAD` の `.memory-roles.json` と Git の `user.name` / `user.email` を見ます。通常メンバーは `member` とし、更新範囲は `clients/`、`internal/`、`inbox/`、`raw/` に限定します。
- skill、tool、docs、templates、hook、`company/` など repository 運用側の変更は `developer` または `admin` role で行います。
- `.memory-roles.json` の担当者に `allowed_roots` が設定されている member は、指定された `clients/{client_id}` / `internal/{project_id}` と共有 `inbox/`、`raw/` だけを更新します。
- Obsidian は人間の閲覧・確認用です。client / internal 配下では `events/` 以外の memory file を人間が手動編集できます。top-level `raw/` も手動編集できます。commit 前に lint / fix で指定形式へ寄せます。
- 人間は議事録、メモ、URL、方針、修正依頼をエージェントに渡すこともできます。エージェントは skill 経由で repository を更新します。
- event は原則追記専用です。`memory-digest` は `derived_status` などの status metadata だけ更新できます。event の事実や本文は絶対に書き換えません。
- 事実を黙って削除しないでください。代わりに conflict として明示します。
- 内部懸念、未確定情報、他社情報をクライアント向け draft に混ぜないでください。
- `inbox/` の業務メモを正式 memory として使う場合は、先に client / internal event に昇格してください。

## スキルのみのルール

v1 ではスラッシュコマンドは不要です。ホストが command をサポートする場合でも、command はこれらのスキルへ routing するだけで、業務ロジックを持たせてはいけません。

`scripts/memory` CLI は、status / lint / smoke / prompt 生成のための薄い補助入口です。CLI に保存・digest・draft 生成の業務ロジックを持たせず、更新が必要な依頼は必ず該当 skill に route してください。

保存・digest・新規追加・月次総括系の更新では、ユーザーが CLI と明示していなくても、まず `scripts/memory save ...`、`scripts/memory digest ...`、`scripts/memory add ...`、または `scripts/memory review ...` で agent 向け prompt を生成し、その prompt と該当 skill を正本として実更新します。CLI が使えない場合は理由を明示してから skill に従って進めてください。

lint、smoke、role guard は原則 `scripts/memory` 経由で実行します。古い個別 script が残っていても、通常運用の入口にはしません。

メモリ更新では、`events/` は skill なしで直接書き換えないでください。client / internal 配下の `profile.md`、`sources.md`、`states/current.md` と top-level `raw/` は Obsidian から手動編集できますが、指定形式に合わない変更は commit 前 lint で補正または停止します。対象外の repository 保守作業を除き、ユーザーの更新依頼は該当 skill に route します。

## 派生ファイルのルール

生成セクションを持つ `profile.md` と `states/current.md` はスキル経由でも更新できます。client / internal 配下の非 event ファイルは人間の手動編集も許可し、エージェントは既存内容を保持しながら更新します。

## Company Context Rule

通常の `memory-save` / `memory-digest` は `company/` を自動更新しません。会社方針へ昇格したい学びは、まず対象 client / internal entity の event と profile に source 付きで残し、マネジメント判断待ちにします。
