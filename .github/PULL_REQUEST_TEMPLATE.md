## Summary

## Memory Checklist

- [ ] No real customer data, personal information, secrets, private URLs, contract amounts, or confidential notes are included.
- [ ] Events are append-only, or corrections are recorded as new correction events.
- [ ] Raw notes are stored only in top-level `raw/` and linked from relevant events.
- [ ] Long-term knowledge is in `profile.md`; current tasks and risks are in `states/current.md`.
- [ ] Client-facing draft text uses only sources from the same client.
- [ ] Internal concerns, assumptions, and competitor comparisons are not included in client-facing draft text.
- [ ] Manual sections were preserved.
- [ ] `scripts/memory privacy-scan` passes.
- [ ] `scripts/memory lint` passes.
- [ ] `scripts/memory smoke` passes, or the change does not touch skills, templates, tools, or schema.

## Reviewer Notes
