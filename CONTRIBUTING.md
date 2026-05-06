# コントリビューション

このテンプレートの改善に関心を持ってくれてありがとうございます。

## 受付方針

- Issue は受け付けます。
- Pull Request は原則として受け付けていません。
- 改善提案、バグ報告、質問はまず Issue に書いてください。
- maintainer が必要と判断した場合だけ、個別に PR の進め方を相談します。例外的に取り込む場合も auto-merge は使わず、基本は squash merge にします。
- 公開 repository の fork は推奨しません。個人アカウント所有の public repository では GitHub の仕様上 fork を無効化できない場合がありますが、自社データを扱う場合は fork ではなく GitHub の template 機能で private repository として作成してください。

## 基本ルール

- 実在顧客の情報、個人情報、秘密情報、非公開 URL、契約金額、機密の社内メモを含めないでください。
- サンプルは架空の内容にし、URL は `example.com` などの予約ドメインを使ってください。
- event file は追記専用として扱います。履歴を書き換えず、訂正は correction event として残してください。
- 変更範囲はできるだけ小さくし、workflow や schema を変える場合は理由を説明してください。

## 提案前の確認

```bash
scripts/memory privacy-scan
scripts/memory lint
scripts/memory smoke
```

実行できなかったコマンドがある場合は、Issue または事前に合意した PR にその理由を書いてください。

## 公開サンプルデータ

sample client / internal project のデータは、汎用的で架空の内容にしてください。実在企業に見え始めた例は、さらに匿名化するか private repository に移してください。
