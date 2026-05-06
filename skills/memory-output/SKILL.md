---
name: memory-output
description: profile / states/current / event から打合せ準備、共有文、提案下書き、月次レポートなどの draft を作る。
---

# memory-output

提案文、共有文、月次レポート、打合せ準備など、memory を材料にした draft をチャット上で作るためのスキルです。軽量構成では `outputs/` に成果物ファイルを保存しません。

## 必須読み込み

1. `.agentic/AGENT_CONTRACT.md`
2. `company/session-context.md`
3. `company/strategy.md`
4. `company/rules.md`
5. `.agentic/skills/_shared/SCHEMA.md`
6. `.agentic/skills/_shared/GUARDRAILS.md`
7. 対象 entity の `profile.md`
8. 対象 entity の `states/current.md`
9. 対象 entity の `sources.md`
10. 必要な recent events

## ワークフロー

1. draft の対象 entity と用途を決める。
2. クライアント共有用の場合は、同じ client の event / profile / sources / states/current だけを使う。raw は event の source として辿り、draft から直接参照しない。
3. 内部用の場合も、別 entity の情報を使うときは出典と前提を明示する。
4. 新しい事実、決定、依頼、リスクが見つかった場合は、先に `memory-save` で event 化する。
5. 外部資料が必要な場合だけ `sources.md` の `context: yes` または `on_demand` の URL を `gws` CLI で取得する。取得できない場合は失敗理由を明示し、中身を推測しない。
6. 本文の重要な claim には、同じ client の source file / event / source URL を示す。
7. draft は source of truth ではない。後から状態に反映すべき内容は event として保存し、`profile.md` または `states/current.md` に digest する。
8. `monthly-report` はクライアント提出用・内部確認用の draft であり、repository に保存しない。月次の振り返りを memory に残したい場合は `scripts/memory review ...` から `monthly-review` event を作る。

## Draft の種類

- `meeting-prep`: 打合せ準備
- `proposal`: 提案下書き
- `share-draft`: 共有文
- `monthly-report`: 月次レポート
- `memo`: 内部整理メモ
- `playbook`: 社内プレイブック
- `update`: 短い更新共有

## 禁止事項

- クライアント共有用 draft で別 client の event / file を cite しない。
- 内部懸念、未確定情報、他社情報、クライアントに見せる前提でない素材をクライアント共有用 draft に含めない。
- `inbox/` の業務メモをクライアント共有用 draft の根拠にしない。使いたい場合は先に正式 event に昇格する。
- 同じ client の source がない claim を、確定事実のようにクライアント共有用 draft に書かない。
- draft を根拠にさらに draft を作り、出典を曖昧にしない。
- `sources.md` にない外部資料を継続的な context として使わない。
