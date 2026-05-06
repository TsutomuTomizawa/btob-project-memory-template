---
type: view
view_type: updates
auto_generated: true
owner: dataview
last_digest: 2026-04-25
---

# 更新一覧

```dataview
TABLE WITHOUT ID updated_at AS "更新日", update_summary AS "サマリ", file.link AS "ファイル", update_source AS "出典"
FROM "clients" OR "internal" OR "company" OR "inbox" OR "raw"
WHERE updated_at
SORT updated_at DESC, file.mtime DESC
```
