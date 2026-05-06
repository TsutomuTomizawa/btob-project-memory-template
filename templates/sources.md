---
type: source_index
entity_type:
entity_id:
auto_generated: false
owner: human
updated_at:
update_summary:
update_source: []
update_history: []
---

# Sources

この entity で context として使ってよい Google Workspace / 外部資料の URL を管理します。

LLM は必要になった資料だけを `gws` で読み、取得した内容から新しい事実・判断・タスクが見つかった場合は event として保存します。

`gws` で取得できない場合、LLM は中身を推測せず、認証や URL の確認を依頼します。

| 名称 | 種別 | URL | context | 備考 |
| --- | --- | --- | --- | --- |
| _未登録_ | other | - | no | 必要な Google Drive / Sheets / Docs URL を追加してください。 |
