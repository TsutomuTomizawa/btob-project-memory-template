# コントリビューション

このテンプレートの改善に協力してくれてありがとうございます。

## 基本ルール

- 実在顧客の情報、個人情報、秘密情報、非公開 URL、契約金額、機密の社内メモを含めないでください。
- サンプルは架空の内容にし、URL は `example.com` などの予約ドメインを使ってください。
- event file は追記専用として扱います。履歴を書き換えず、訂正は correction event として残してください。
- 変更範囲はできるだけ小さくし、workflow や schema を変える場合は理由を説明してください。

## Pull Request の前に

```bash
scripts/memory privacy-scan
scripts/memory lint
scripts/memory smoke
```

実行できなかったコマンドがある場合は、PR にその理由を書いてください。

## 公開サンプルデータ

sample client / internal project のデータは、汎用的で架空の内容にしてください。実在企業に見え始めた例は、さらに匿名化するか private fork に移してください。
