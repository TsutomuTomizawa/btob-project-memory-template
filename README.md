# BtoB Project Memory Template

BtoB の顧客対応、商談メモ、導入・納品プロジェクト、更新商談、社内プロジェクトを entity 別に管理するための memory vault テンプレートです。

この repository は、Obsidian vault として開き、Codex や Claude Code などのエージェントが repository 内の skill に従って更新する前提で作っています。含まれるデータはすべて架空のサンプルで、URL も `example.com` だけを使っています。公開 fork に、実在顧客の情報、秘密情報、個人情報、契約金額、非公開 URL は追加しないでください。

## これは何か

- `clients/`: 顧客別の `profile.md`、`sources.md`、`states/current.md`、追記専用 event。
- `internal/`: 社内プロジェクト別の `profile.md`、`sources.md`、`states/current.md`、追記専用 event。
- `raw/`: 議事録や長文メモの原本置き場。社内用 memory として扱い、顧客向け draft に直接コピーしません。
- `company/`: マネジメントが管理する戦略、ルール、セッション指針。
- `.agentic/skills/`: 保存、digest、query、output、lint、新規追加の正本 skill。
- `scripts/memory`: status、lint、smoke test、prompt 生成、publish、sync の補助 CLI。

Obsidian からは、`clients/*/profile.md`、`clients/*/sources.md`、`clients/*/states/current.md`、`internal/*/profile.md`、`internal/*/sources.md`、`internal/*/states/current.md`、`raw/*.md` を手動編集できます。`events/` は追記専用なので、作成や訂正は skill 経由で行います。

## クイックスタート

```bash
git clone https://github.com/tsutomutomizawa/btob-project-memory-template.git
cd btob-project-memory-template
./scripts/setup-member.sh
scripts/memory status --with-lint
```

Python 3.10 以上が必要です。Windows では Git Bash から実行してください。

## 日常の流れ

1. 議事録、メモ、URL、決定事項、修正依頼をエージェントに渡す。
2. エージェントがまず `scripts/memory save ...` を実行し、skill 用 prompt を生成する。
3. `memory-save` が raw note と薄い追記専用 event を作る。
4. `memory-digest` が pending event から `profile.md` と `states/current.md` を更新する。
5. `memory-query` が対象 entity の文脈から読み取り専用で回答する。
6. `memory-output` が顧客向け共有文や提案文をチャット上で draft として作る。output file は repository に保存しない。
7. `scripts/memory lint` と `scripts/memory smoke` で vault の健全性を確認する。

## 公開 repository としての安全性

このテンプレートは、公開用に履歴を切り離した clean history の repository として作っています。

- 元の private repository の git 履歴を含めない。
- 実在顧客や社内プロジェクトのデータを含めない。
- 実在の連絡先を含めない。
- 非公開の Google Workspace URL を含めない。
- `.env` や local cache を含めない。
- MIT license、協力ガイド、セキュリティ方針を含める。

自分の fork を公開する前に、以下を実行してください。

```bash
scripts/memory privacy-scan
scripts/memory lint
scripts/memory smoke
```

## 含まれるサンプル

- `clients/sample-saas-platform`: BtoB SaaS の更新商談と部門展開のサンプル。
- `clients/sample-industrial-supplier`: 産業資材取引の見積・納期調整のサンプル。
- `internal/sales-process-improvement`: 商談メモと見積承認フロー改善のサンプル。

すべて架空のサンプルなので、自社用途に合わせて安全に置き換えてください。

## ライセンス

MIT。詳細は [LICENSE](LICENSE) を確認してください。
