---
type: view
view_type: tasks
auto_generated: true
owner: dataview
last_digest: 2026-04-25
---

# タスク一覧

## 未完了

```dataview
TASK
FROM "clients" OR "internal"
WHERE !completed
GROUP BY file.link
SORT file.path ASC
```

## 完了

```dataview
TASK
FROM "clients" OR "internal"
WHERE completed
GROUP BY file.link
SORT file.path ASC
```
