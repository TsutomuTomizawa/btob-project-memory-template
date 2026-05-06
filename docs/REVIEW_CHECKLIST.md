# レビューチェックリスト

- [ ] 対象 entity は正しいか。
- [ ] `events/` は追記専用として扱われ、既存 event 本文や immutable frontmatter を直接変更していないか。
- [ ] 長期知識は `profile.md`、現在状態と task は `states/current.md` にまとまっているか。
- [ ] client / internal の file が別 client / internal や raw note を直接参照していないか。
- [ ] クライアント向け draft は同じ client の情報だけで作られているか。
- [ ] 内部懸念、未確定情報、他社情報がクライアント向け draft に含まれていないか。
- [ ] `inbox/` の業務メモを正式 memory に使う場合、client / internal event に昇格しているか。
- [ ] 重要な claim に source event または source file があるか。
- [ ] `sources.md` の URL と context が妥当か。
- [ ] raw note が複数 entity を跨ぐ場合、raw 原本を複製せず各 event から参照しているか。
- [ ] 月次総括は `event_type: review` の `monthly-review` event で残し、月別 state file や output file を作っていないか。
- [ ] commit message が日本語になっているか。例外的に PR を扱う場合は PR title / body も日本語になっているか。
