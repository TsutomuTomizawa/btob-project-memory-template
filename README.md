# BtoB Project Memory Template

Entity-based memory vault template for BtoB client work, deal notes, delivery projects, renewals, and internal project management.

This repository is designed to be opened as an Obsidian vault and operated by coding agents such as Codex or Claude Code through repository-local skills. It includes only fictional sample data and `example.com` URLs. Do not add real customer data, secrets, personal information, contract amounts, or private URLs to a public fork.

## What This Is

- `clients/`: client-specific `profile.md`, `sources.md`, `states/current.md`, and append-only events.
- `internal/`: internal project-specific `profile.md`, `sources.md`, `states/current.md`, and append-only events.
- `raw/`: source notes and meeting transcripts. Raw notes are internal memory and should not be copied into client-facing drafts.
- `company/`: management-owned strategy, rules, and session context.
- `.agentic/skills/`: canonical agent skills for save, digest, query, output, lint, and add flows.
- `scripts/memory`: helper CLI for status, lint, smoke tests, prompt generation, publish, and sync.

Obsidian users may edit `clients/*/profile.md`, `clients/*/sources.md`, `clients/*/states/current.md`, `internal/*/profile.md`, `internal/*/sources.md`, `internal/*/states/current.md`, and `raw/*.md`. Events are append-only and should be created or corrected through the skills.

## Quick Start

```bash
git clone https://github.com/tsutomutomizawa/btob-project-memory-template.git
cd btob-project-memory-template
./scripts/setup-member.sh
scripts/memory status --with-lint
```

Python 3.10+ is required. On Windows, use Git Bash.

## Daily Loop

1. Give the agent meeting notes, URLs, decisions, or correction requests.
2. The agent runs `scripts/memory save ...` first to generate a skill prompt.
3. `memory-save` creates a raw note and thin append-only event.
4. `memory-digest` updates `profile.md` and `states/current.md` from pending events.
5. `memory-query` answers read-only questions from the relevant entity context.
6. `memory-output` drafts client-facing messages in chat, without saving output files.
7. `scripts/memory lint` and `scripts/memory smoke` keep the vault healthy.

## Public-Repo Safety

This template follows a clean-history public release approach:

- no original private git history;
- no real client or internal data;
- no real contact information;
- no private Google Workspace URLs;
- no `.env` files or local caches;
- MIT license and contribution guidance included.

Before publishing your own fork, run:

```bash
scripts/memory privacy-scan
scripts/memory lint
scripts/memory smoke
```

## Included Samples

- `clients/sample-saas-platform`: BtoB SaaS renewal and rollout sample.
- `clients/sample-industrial-supplier`: industrial supplier quote and delivery sample.
- `internal/sales-process-improvement`: sales note and quote approval process sample.

All samples are fictional and safe to replace.

## License

MIT. See [LICENSE](LICENSE).
