# ガードレール

## クライアント向け安全性

- `events/`、`profile.md`、`sources.md`、`states/current.md`、`raw/` はすべて社内用 memory として扱い、クライアントにそのまま出さない。
- クライアント向け文面は repository に保存せず、`memory-output` でチャット上に draft として作る。送付前に人間が本文を確認する。
- クライアント向け draft は、同じ client の event / profile / sources / states/current だけを材料にする。raw は event の source として辿り、draft から直接参照しない。別 client や internal project の情報を混ぜない。
- 内部懸念、未確定情報、他社情報、クライアントに見せる前提でない素材はクライアント向け draft に含めない。
- クライアント向け statement の根拠が弱い場合は、本文で弱さを明示するか、作成を止めて人間に確認する。
- 事実、推論、提案、copywriting を分ける。

## Conflict の扱い

- 矛盾する事実を削除しない。
- `Conflict` section を追加し、両方の version、source event、review need を書く。
- source が同等の場合に限り、最新の event を優先する。

## Event の完全性

- Event は原則追記専用。
- event は raw note の全文コピーではなく、短い構造化 index として書く。長文議事録や発言録は `raw/` に置き、event には要点、決定事項、タスク、リスク、未解決事項だけを残す。
- `memory-digest` は派生ファイル更新後に `derived_status` を `pending` から `applied` へ更新してよい。digest 中に event 本文、事実、日付、author、target entity を変えない。
- event を訂正する必要がある場合は correction event を追加し、両方をリンクする。
- 派生ファイルをきれいに見せるために event history を書き換えない。

## 派生コンテンツ

- ページ全体を再生成するのではなく、既存セクションを更新する。
- 手動セクションを保持する。
- 長期的に使う知識、背景、制約、商談・プロジェクト運用の学びは `profile.md` に集約する。
- 現在状態、進行中タスク、リスク、決定事項、次アクションは `states/current.md` だけを最新化する。
- 重要な claim には event への source link を戻す。
- `profile.md` / `states/current.md` の event 由来の箇条書きは、各 section 内でできるだけ source event の日付が新しい順に並べる。entity の基本説明、意味上の前提、手動セクションは無理に並べ替えない。
- source date は原則 `[[events/YYYY-MM-DD_...]]` または `[[../events/YYYY-MM-DD_...]]` から読む。複数 source がある項目は最も新しい source date を使い、source が曖昧な項目は section の末尾か手動セクションに残す。
- `clients/`、`internal/`、`company/`、`raw/` の markdown を更新したら、frontmatter の `updated_at`、`update_summary`、`update_source`、`update_history` も更新する。
- client / internal 配下の `events/` 以外は Obsidian から手動編集できます。commit 前に `scripts/memory lint --fix --staged` で機械的に補正し、意味判断が必要な不備は停止します。
- raw note は Obsidian で見える `raw/` に置きます。複数 client / internal を含む場合も raw 原本は複製せず、関係する各 entity の event から `source_refs` / `update_source` で参照してください。
- `inbox/` は共有 triage なので、更新したら frontmatter の `updated_at`、`update_summary`、`update_source`、`update_history` も更新する。
- 外部資料は対象 entity の `sources.md` にある URL だけを context に使う。ユーザーが会話内で直接 URL を渡した場合も、継続利用するなら `sources.md` に登録する。
- Google Workspace 資料は必要な範囲だけ `gws` CLI で取得し、取得内容から新しい事実・判断・タスクが見つかった場合は event として保存する。
- `gws` CLI が使えない、認証がない、または取得に失敗した場合は、その旨を明示し、URL の中身を推測しない。

## 読む順番

entity 固有の回答では以下の順に読む。

1. `profile.md`
2. `states/current.md`
3. 必要なときだけ `sources.md`
4. 監査性が必要なときだけ recent events

横断回答では以下の順に読む。

1. `company/session-context.md`
2. `company/strategy.md`
3. `company/rules.md`
4. `views/` の Dataview 結果
5. 関連 entity の `profile.md` と `states/current.md`
