# エージェント向け指示

このリポジトリは、BtoB 取引、顧客別商談、導入・納品プロジェクト、社内改善プロジェクトのための、スキルのみで動く entity 別 memory vault テンプレートです。

セッション開始時と memory 作業の前に、必ず以下を読んでください。

1. `company/session-context.md`
2. `company/strategy.md`
3. `company/rules.md`
4. `.agentic/AGENT_CONTRACT.md`
5. `.agentic/skills/_shared/SCHEMA.md`
6. `.agentic/skills/_shared/GUARDRAILS.md`
7. 関連する `.agentic/skills/{skill}/SKILL.md`

リポジトリ内 skill を正本として扱います。このファイル内で別ワークフローを作らないでください。

## 公開テンプレートとしての注意

- 実在顧客、担当者、契約金額、単価、非公開 URL、個人情報、秘密情報を追加しないでください。
- サンプル URL は `example.com` などの予約ドメインだけを使ってください。
- 公開 repository に出せない内容は、private fork または社内 repository で扱ってください。
- 顧客向け draft は repository に保存せず、`memory-output` でチャット上に作ります。

## 運用ルール

- 「保存して」「メモして」「記録して」などの保存依頼では、まず `scripts/memory save ...` で agent 向け prompt を生成し、その内容に従って `memory-save` を使う。
- 「5月を総括して」「月次振り返りを保存して」などの月次総括依頼では、まず `scripts/memory review --client {client_id} --month YYYY-MM` または `scripts/memory review --internal {project_id} --month YYYY-MM` で agent 向け prompt を生成し、`memory-save` の monthly-review event flow に従う。月別 state file は作らない。
- 読み取り専用の質問には `memory-query` を使う。
- クライアント・社内PJについて会話、議論、提案判断をするときは、対象 entity の `profile.md` と `states/current.md` を先に確認する。外部資料が必要な場合だけ、対象 entity の `sources.md` にある `context: yes` または `on_demand` の URL を取得する。取得できない場合は中身を推測しない。監査性が必要な場合だけ recent events を確認する。
- event から派生ファイルを更新するときは、まず `scripts/memory digest ...` で agent 向け prompt を生成し、その内容に従って `memory-digest` を使う。派生先は `profile.md` と `states/current.md` に集約する。
- クライアント向け下書きや打合せ準備には `memory-output` を使い、repository に output file として保存せずチャット上で draft を作る。
- PR 前と 10-15 回保存ごとに `scripts/memory lint` を使う。
- 新規クライアント・社内プロジェクト追加では、まず `scripts/memory add ...` で agent 向け prompt を生成し、その内容に従って `memory-add` を使う。
- ユーザーが「pushして」「プッシュしてください」と依頼した場合は、差分を確認し、通常は `scripts/memory publish "短い日本語のコミットメッセージ"` で作業ブランチ作成、commit、push、PR/CI/auto-merge 待機、main 最新化まで行う。`main` に直接 push しない。
- ユーザーが「pullして」「最新化して」「syncして」と依頼した場合は、未保存変更がないことを確認し、`scripts/memory sync` で `main` に戻って `origin/main` を fast-forward し、merge 済み作業ブランチを片付ける。

`scripts/memory` v1 は dry-run / prompt 生成用です。CLI 自体は memory file を更新しません。保存・digest・新規追加・月次総括の実更新は、CLI が生成した prompt と repository skill を正本としてエージェントが行ってください。

人間は主に Obsidian と PR 差分で内容を確認します。client / internal 配下の `profile.md`、`sources.md`、`states/current.md` と top-level `raw/`、gitignore された `inbox/` メモは手動編集できます。`events/` は skill なしで直接書き換えないでください。

ローカル hook は `HEAD` の `.memory-roles.json` と Git の `user.name` / `user.email` を照合します。`member` の人は、`clients/`、`internal/`、`raw/`、`inbox/` だけを更新します。skill、tool、docs、templates、hook、`company/` など repository 運用側の変更は `developer` または `admin` role の担当者で行ってください。

CI の role 正本は tracked file の `.memory-roles.json` です。公開テンプレートでは `tsutomutomizawa` を `admin` の例として置き、それ以外の GitHub actor は既定で `member` として `clients/`、`internal/`、`raw/`、`inbox/` を更新できます。自社運用では `.memory-roles.json` と CODEOWNERS を自分の組織に合わせて変更してください。
