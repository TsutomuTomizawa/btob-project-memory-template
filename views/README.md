# Views

この folder は Obsidian Dataview で表示する横断ビューです。

LLM は `views/` の一覧を手で更新しません。更新情報は各 memory file の `updated_at` / `update_summary` frontmatter から、タスクは `clients/` と `internal/` 配下の Markdown task から Dataview が自動で拾います。軽量構成では進行中 task は主に `states/current.md` に置きます。

Obsidian 側で Dataview plugin を有効にして見る前提です。plugin が無効な場合は query がコードブロックとして表示されます。

- [[updates]]: memory file の最新更新一覧。
- [[tasks]]: 未完了・完了タスク一覧。
