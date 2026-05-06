# セキュリティ方針

この公開 repository はテンプレートであり、架空のサンプルデータだけを含める前提です。

## commit してはいけないもの

- 実在顧客名、アカウント情報、取引記録。
- 個人情報。
- secrets、tokens、`.env`、認証情報。
- 非公開の Google Workspace、CRM、BI、ticket URL。
- 契約金額、価格表、非公開の商取引条件。
- 実在の client や partner を特定できる社内懸念。

## 確認コマンド

変更を公開する前に、以下を実行してください。

```bash
scripts/memory privacy-scan
scripts/memory lint
```

`privacy-scan` は未マスクの email address と phone number を検出して止めます。ただし完全な DLP ではないため、人間のレビューも必須です。

## 報告

この公開テンプレートに機微情報を見つけた場合は、public issue に値を書かず、private security advisory または maintainer への直接連絡で報告してください。
