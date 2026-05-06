# Google Workspace 資料の使い方

この資料は、`sources.md` に登録した Google Drive / Google Docs / 共有スプレッドシート などを、エージェントが読むための補助メモです。

## 基本方針

- Google Workspace 資料を使う場合は、まず対象 client / internal project の `sources.md` に URL を登録します。
- `context: yes` または `context: on_demand` の資料だけを、必要なときに `gws` CLI で読みます。
- `context: no` の資料は、所在の記録だけに使い、エージェントの判断材料にはしません。
- `gws` で取得できない場合、エージェントは中身を推測しません。
- 取得した資料から新しい事実、判断、タスクが見つかった場合は、`sources.md` ではなく event として保存します。

## 初回確認

Google Workspace 資料を読む担当者だけ、以下を確認します。

```bash
gws --help
gws auth status
```

認証がない、または失敗する場合は、環境に応じて次を使います。

```bash
gws auth login
```

OAuth client や Google Cloud project の設定から必要な場合は、次を使います。

```bash
gws auth setup
```

`gws auth setup` は `gcloud` が必要になる場合があります。Google Workspace 資料を読まないメンバーは、ここまで設定しなくても通常の保存・digest・push はできます。

## よく使う確認コマンド

Google Drive file:

```bash
gws drive files get --params '{"fileId":"FILE_ID"}'
```

Google Docs:

```bash
gws docs documents get --params '{"documentId":"DOCUMENT_ID"}'
```

共有スプレッドシート:

```bash
gws sheets spreadsheets get --params '{"spreadsheetId":"SPREADSHEET_ID"}'
```

共有スプレッドシート の値を読む場合:

```bash
gws sheets spreadsheets.values get --params '{"spreadsheetId":"SPREADSHEET_ID","range":"Sheet1!A1:Z100"}'
```

## sources.md への書き方

例:

```md
| 名称 | 種別 | URL | context | 備考 |
| --- | --- | --- | --- | --- |
| 2026-05 月次レポート | spreadsheet | https://docs.google.com/spreadsheets/d/... | on_demand | 月次レポート作成時だけ読む。 |
| 提案資料 | slide | https://docs.google.com/presentation/d/... | yes | 打合せ準備で参照する。 |
| 契約書 | drive_file | https://drive.google.com/file/d/... | no | 所在のみ記録。本文は判断材料にしない。 |
```

`sources.md` に URL がない外部資料を継続的な context として使わないでください。会話中に URL を受け取った場合も、継続利用するなら対象 entity の `sources.md` に登録します。
