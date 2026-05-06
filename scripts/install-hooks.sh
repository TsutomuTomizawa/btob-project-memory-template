#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$repo_root"

git config core.hooksPath .githooks
chmod +x .githooks/pre-commit .githooks/commit-msg scripts/install-hooks.sh scripts/memory scripts/memory-python scripts/setup-member.sh

echo "Git hooks installed."
echo "core.hooksPath=$(git config --get core.hooksPath)"
echo "memory role source=.memory-roles.json (local uses HEAD, CI uses trusted main)"
echo "memory cli=scripts/memory"
echo "memory python launcher=scripts/memory-python (python3 / python / py -3)"
echo
echo "pre-commit: diff-check / privacy-scan --staged / role-guard; py-compile and lint --fix --staged only for relevant staged paths"
echo "commit-msg: 日本語のコミットメッセージを必須にします"
echo "CI on working-branch push and PR to main: scripts/memory commit-language / py-compile / privacy-scan / lint / smoke plus diff whitespace checks"
