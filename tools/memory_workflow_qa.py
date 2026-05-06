#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import shutil
import sys

import memory_workflow_smoke as smoke


def run_smoke(keep_temp: bool) -> int:
    old_argv = sys.argv[:]
    sys.argv = ["memory_workflow_smoke.py"] + (["--keep"] if keep_temp else [])
    try:
        return smoke.main()
    finally:
        sys.argv = old_argv


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise AssertionError(f"{path}: replace target が見つかりません: {old}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def assert_cli_first_prompts(vault: Path) -> None:
    notes_path = vault / "qa-meeting-notes.txt"
    notes_path.write_text("Alpha の定例。提案資料更新と問い合わせ分類を保存する。\n", encoding="utf-8")
    cases = [
        (
            ["save", "--client", smoke.PRIMARY_CLIENT, "Alpha の次回定例で提案資料更新を優先する"],
            [
                "Use skill: `memory-save`.",
                f"Target hint: client `{smoke.PRIMARY_CLIENT}`",
                "top-level `raw/` note",
                "Keep event bodies thin",
            ],
            "client save prompt",
        ),
        (
            ["save", "--client", smoke.PRIMARY_CLIENT, "--from-file", str(notes_path.relative_to(vault))],
            ["Use skill: `memory-save`.", "Source file:", "Alpha の定例。提案資料更新", "do not copy the raw transcript"],
            "from-file save prompt",
        ),
        (
            ["save", "--unknown", "対象不明だが商談レポートの数字が落ちている"],
            ["Use skill: `memory-save`.", "Target hint: unknown; use `inbox/`", "do not guess a target"],
            "unknown save prompt",
        ),
        (
            ["digest", "--client", smoke.PRIMARY_CLIENT],
            [
                "Use skill: `memory-digest`.",
                f"Target hint: client `{smoke.PRIMARY_CLIENT}`",
                "profile.md",
                "states/current.md",
                "Treat events as thin indexes",
                "newest source event date",
            ],
            "client digest prompt",
        ),
        (
            ["review", "--client", smoke.PRIMARY_CLIENT, "--month", "2026-04", "4月を総括して保存"],
            [
                "Use skill: `memory-save`.",
                "Monthly review event flow",
                "Event type: `review`",
                f"Target event path: `clients/{smoke.PRIMARY_CLIENT}/events/2026-04-30_monthly-review.md`",
                "Do not create `states/YYYY-MM.md`",
            ],
            "monthly review prompt",
        ),
        (
            [
                "add",
                "--client",
                "qa-added-client-cli",
                "--name",
                "QA Added Client CLI",
                "Google商談・プロジェクト運用の新規 client を作る",
            ],
            [
                "Use skill: `memory-add`.",
                "Entity type: client",
                "Entity id: `qa-added-client-cli`",
                "Display name: QA Added Client CLI",
                "profile.md",
                "states/current.md",
                "events/",
            ],
            "client add prompt",
        ),
        (
            [
                "prompt",
                "add",
                "--internal",
                "qa-added-internal-cli",
                "--name",
                "QA Added Internal CLI",
                "営業提案テンプレート整備の社内PJを作る",
            ],
            [
                "Use skill: `memory-add`.",
                "Entity type: internal",
                "Entity id: `qa-added-internal-cli`",
                "Display name: QA Added Internal CLI",
                "profile.md",
                "states/current.md",
                "events/",
            ],
            "internal add prompt",
        ),
    ]
    for args, expected_tokens, label in cases:
        code, output = smoke.run_memory_cli(vault, args)
        if code != 0:
            raise AssertionError(f"{label}: prompt 生成が失敗しました\n{output}")
        missing = [token for token in expected_tokens if token not in output]
        if missing:
            raise AssertionError(f"{label}: prompt に必要 token がありません: {missing}\n{output}")
    notes_path.unlink()
    print("成功: CLI-first prompt が memory-add / memory-save / memory-digest skill へ routing")


def digest_client_event(vault: Path, client_id: str, slug: str, summary: str, task: str) -> None:
    event_path = vault / "clients" / client_id / "events" / f"2026-04-26_{slug}.md"
    root = vault / "clients" / client_id
    child_link = f"[[../events/2026-04-26_{slug}]]"
    root_link = f"[[events/2026-04-26_{slug}]]"
    smoke.append(root / "states" / "current.md", f"\n- QA digest 反映: {summary} 出典: {child_link}\n")
    smoke.append(root / "states" / "current.md", f"- [ ] {task} 出典: {child_link}\n")
    smoke.append(root / "profile.md", f"\n- QA 長期知識: {summary} 出典: {root_link}\n")
    replace_once(event_path, "derived_status: pending", "derived_status: applied")


def add_initial_event_text(entity_type: str, entity_id: str, slug: str, name: str, marker: str) -> str:
    return f"""---
type: event
event_id: 20260426-{entity_id}-{slug}
event_date: 2026-04-26
created_at: 2026-04-26T10:00:00+09:00
author: qa
entity_type: {entity_type}
entity_id: {entity_id}
event_type: note
derived_status: applied
derived_targets:
  - state
source_refs: []
updated_at: 2026-04-26
update_summary: "{name} を新規作成。"
update_source: []
update_history:
  - "2026-04-26 {name} を新規作成。"
---

# {name} initial event

## 要約

{marker}: {name} を memory-add の軽量構成で新規作成する。

## 詳細

profile.md、sources.md、states/current.md、events/ だけを作り、初期 event を current に反映する。

## タスク

- 初期状態を確認する。

## 出典メモ

memory-add QA。
"""


def assert_skill_add_entities(vault: Path) -> None:
    scenarios = [
        ("client", "qa-added-client", "QA Added Client", "qa-added-client", "QA-ADD-CLIENT"),
        ("internal", "qa-added-internal", "QA Added Internal", "qa-added-internal", "QA-ADD-INTERNAL"),
    ]
    for entity_type, entity_id, name, slug, marker in scenarios:
        root_name = "clients" if entity_type == "client" else "internal"
        root = vault / root_name / entity_id
        smoke.create_entity_fixture(vault, entity_type, entity_id, name)
        event_path = root / "events" / f"2026-04-26_{slug}.md"
        smoke.write(event_path, add_initial_event_text(entity_type, entity_id, slug, name, marker))
        smoke.append(root / "states" / "current.md", f"\n- {marker}: 初期状態を作成。出典: [[../events/2026-04-26_{slug}]]\n")
        smoke.append(root / "profile.md", f"\n- {marker}: 新規 entity の初期コンテキスト。出典: [[events/2026-04-26_{slug}]]\n")

        for required in [root / "profile.md", root / "sources.md", root / "states" / "current.md", root / "events"]:
            if not required.exists():
                raise AssertionError(f"memory-add required path がありません: {required}")
        for retired in [root / "tasks.md", root / "wiki", root / "outputs", root / "raw", root / "state.md", root / "states" / "00-current.md"]:
            if retired.exists():
                raise AssertionError(f"memory-add が lite 構成外 path を作っています: {retired}")

    smoke.assert_lint_passes(vault, "memory-add client / internal 新規作成シナリオ")


def assert_skill_save_digest_single_client(vault: Path) -> None:
    slug = "qa-single-client-save"
    raw_link = "[[raw/2026-04-26_qa-single-client-save]]"
    smoke.write(
        vault / "raw" / "2026-04-26_qa-single-client-save.md",
        smoke.raw_note_text(
            raw_id="2026-04-26_qa-single-client-save",
            scope="single_entity",
            entity_refs=[f"client/{smoke.PRIMARY_CLIENT}"],
            title="QA 単一 client 保存",
            summary="単一 client の raw 原本を保存。",
            details="Alpha の次回定例では提案資料更新と問い合わせ分類を確認する。",
        ),
    )
    event_path = vault / "clients" / smoke.PRIMARY_CLIENT / "events" / f"2026-04-26_{slug}.md"
    smoke.write(
        event_path,
        smoke.event_text(
            event_id="20260426-qa-single-client-save",
            entity_type="client",
            entity_id=smoke.PRIMARY_CLIENT,
            event_type="note",
            title="QA Single Client Save",
            summary="次回定例では提案資料更新と問い合わせ分類を確認する。",
            details="memory-save skill に従い raw から単一 client event を作成する。",
            tasks=["提案資料更新と問い合わせ分類を次回定例で確認する"],
            source_ref=raw_link,
            derived_status="pending",
        ),
    )
    smoke.assert_lint_fails(vault, "save 直後の pending event を検出", "pending event")
    digest_client_event(
        vault,
        smoke.PRIMARY_CLIENT,
        slug,
        "提案資料更新と問い合わせ分類を確認する。",
        "提案資料更新と問い合わせ分類を次回定例で確認する。",
    )
    smoke.assert_lint_passes(vault, "単一 client save + digest シナリオ")


def assert_skill_save_multi_entity_split(vault: Path) -> None:
    raw_link = "[[raw/2026-04-26_qa-multi-entity]]"
    smoke.write(
        vault / "raw" / "2026-04-26_qa-multi-entity.md",
        smoke.raw_note_text(
            raw_id="2026-04-26_qa-multi-entity",
            scope="multi_entity",
            entity_refs=[f"client/{smoke.PRIMARY_CLIENT}", f"client/{smoke.SECONDARY_CLIENT}", f"internal/{smoke.INTERNAL_PROJECT}"],
            title="QA 複数 entity 保存",
            summary="複数 entity の raw 原本を保存。",
            details="Alpha、Beta、internal project の話題を含む。",
        ),
    )
    scenarios = [
        ("client", smoke.PRIMARY_CLIENT, "qa-multi-alpha", "Alpha は提案資料不安解消を優先する。", "提案資料不安解消案を作る。"),
        ("client", smoke.SECONDARY_CLIENT, "qa-multi-beta", "Beta は商談品質を見る。", "商談品質の確認表を作る。"),
        ("internal", smoke.INTERNAL_PROJECT, "qa-multi-internal", "internal は営業提案の型を整える。", "営業提案の型を更新する。"),
    ]
    for entity_type, entity_id, slug, summary, task in scenarios:
        smoke.create_event_with_digest(
            vault,
            entity_type=entity_type,
            entity_id=entity_id,
            slug=slug,
            summary=summary,
            details="multi entity raw から entity 別 event に分割する。",
            source_ref=raw_link,
            task=task,
        )
    smoke.assert_lint_passes(vault, "複数 client / internal split save シナリオ")
    raw_dirs = [path for path in vault.glob("clients/*/raw") if path.exists()]
    if raw_dirs:
        raise AssertionError(f"client 配下に raw directory が作られています: {raw_dirs}")
    print("成功: raw 原本は top-level のみで entity 別 event に分割")


def assert_unknown_inbox_save(vault: Path) -> None:
    smoke.write(
        vault / "inbox" / "2026-04-26_qa-unknown.md",
        """---
type: inbox_note
updated_at: 2026-04-26
update_summary: "対象不明のQAメモ。"
update_source: []
update_history:
  - "2026-04-26 対象不明のQAメモを保存。"
---

# 対象不明QA

商談レポートの数値低下があるが client は未確定。
""",
    )
    smoke.assert_lint_passes(vault, "対象不明 inbox 保存シナリオ")


def assert_correction_event(vault: Path) -> None:
    raw_link = "[[raw/2026-04-26_qa-single-client-save]]"
    slug = "qa-correction"
    smoke.write(
        vault / "clients" / smoke.PRIMARY_CLIENT / "events" / f"2026-04-26_{slug}.md",
        smoke.event_text(
            event_id="20260426-qa-correction",
            entity_type="client",
            entity_id=smoke.PRIMARY_CLIENT,
            event_type="decision",
            title="QA Correction",
            summary="既存 event を直接書き換えず訂正 event で補足する。",
            details="訂正内容は新しい event として残す。",
            source_ref=raw_link,
            tasks=[],
        ),
    )
    smoke.append(
        vault / "clients" / smoke.PRIMARY_CLIENT / "states" / "current.md",
        f"\n- correction event を反映。出典: [[../events/2026-04-26_{slug}]]\n",
    )
    smoke.assert_lint_passes(vault, "correction event シナリオ")


def assert_monthly_review_event(vault: Path) -> None:
    root = vault / "clients" / smoke.PRIMARY_CLIENT
    event_path = root / "events" / "2026-04-30_monthly-review.md"
    source_one = f"[[clients/{smoke.PRIMARY_CLIENT}/events/2026-04-26_qa-single-client-save]]"
    source_two = f"[[clients/{smoke.PRIMARY_CLIENT}/events/2026-04-26_qa-multi-alpha]]"
    smoke.write(
        event_path,
        f"""---
type: event
event_id: 20260430-{smoke.PRIMARY_CLIENT}-monthly-review
event_date: 2026-04-30
created_at: 2026-04-30T18:00:00+09:00
author: qa
entity_type: client
entity_id: {smoke.PRIMARY_CLIENT}
event_type: review
derived_status: applied
derived_targets:
  - state
source_refs:
  - "{source_one}"
  - "{source_two}"
updated_at: 2026-04-30
update_summary: "2026-04 の月次総括。"
update_source:
  - "{source_one}"
  - "{source_two}"
update_history:
  - "2026-04-30 2026-04 の月次総括を保存。"
---

# 2026-04 月次総括

## 要約

QA-MONTHLY-REVIEW: 問い合わせフォーム改善と提案資料不安解消を翌月も継続する。

## 良かったこと

- 提案資料更新と問い合わせ分類の確認観点が整理できた。

## 課題

- 導入前FAQの優先順位をまだ実装に落とせていない。

## 決定事項

- 5月も費用不安への回答を先頭に置く。

## 来月へ持ち越すこと

- [ ] 導入前FAQの費用不安回答を実装候補にする。

## 長期的な学び候補

- 不安解消系提案資料では費用不安を先に扱う。

## 参照イベント

- {source_one}
- {source_two}
""",
    )
    smoke.append(root / "states" / "current.md", "\n- [ ] QA-MONTHLY-REVIEW: 導入前FAQの費用不安回答を5月へ持ち越す。出典: [[../events/2026-04-30_monthly-review]]\n")
    retired_monthly_state = root / "states" / "2026-04.md"
    if retired_monthly_state.exists():
        raise AssertionError(f"月別 state file が作られています: {retired_monthly_state}")
    smoke.assert_lint_passes(vault, "monthly-review event シナリオ")
    code, output = smoke.run_memory_cli(vault, ["review", "--client", smoke.PRIMARY_CLIENT, "--month", "2026-04"])
    if code == 0 or "既に存在" not in output:
        raise AssertionError(f"既存 monthly-review event は上書き停止する想定でした\n{output}")
    print("成功: 月次総括は monthly-review event と current carry-over に集約")


def assert_duplicate_ids_rejected(vault: Path) -> None:
    path = vault / "clients" / smoke.SECONDARY_CLIENT / "events" / "2026-04-26_qa-duplicate-id.md"
    smoke.write(
        path,
        smoke.event_text(
            event_id="20260426-qa-correction",
            entity_type="client",
            entity_id=smoke.SECONDARY_CLIENT,
            event_type="note",
            title="Duplicate ID",
            summary="event_id 重複を検出する。",
            details="lint が拒否する。",
            source_ref="[[raw/2026-04-26_qa-multi-entity]]",
        ),
    )
    smoke.assert_lint_fails(vault, "重複 event_id を拒否", "event_id が重複")
    path.unlink()
    smoke.assert_lint_passes(vault, "重複 event_id 削除後に lint が回復")


def assert_duplicate_raw_ids_rejected(vault: Path) -> None:
    path = vault / "raw" / "2026-04-26_qa-duplicate-raw.md"
    smoke.write(
        path,
        smoke.raw_note_text(
            raw_id="2026-04-26_qa-single-client-save",
            scope="single_entity",
            entity_refs=[f"client/{smoke.PRIMARY_CLIENT}"],
            title="Duplicate raw",
            summary="raw_id 重複を検出する。",
            details="lint が拒否する。",
        ),
    )
    smoke.assert_lint_fails(vault, "重複 raw_id を拒否", "raw_id が重複")
    path.unlink()
    smoke.assert_lint_passes(vault, "重複 raw_id 削除後に lint が回復")


def assert_invalid_source_context_rejected(vault: Path) -> None:
    path = vault / "clients" / smoke.PRIMARY_CLIENT / "sources.md"
    original = path.read_text(encoding="utf-8")
    smoke.append(path, "\n| invalid context | spreadsheet | https://example.com/sheet | always | NG |\n")
    smoke.assert_lint_fails(vault, "不正 source context を拒否", "context は yes/no/on_demand")
    path.write_text(original, encoding="utf-8")
    smoke.assert_lint_passes(vault, "不正 source context 復旧後に lint が回復")


def assert_commit_language(vault: Path) -> None:
    smoke.init_git_fixture(vault)
    path = vault / "clients" / smoke.PRIMARY_CLIENT / "states" / "current.md"
    smoke.append(path, "\n- [ ] 日本語コミット検査用 task。\n")
    for args in [["git", "add", "clients/example-client-alpha/states/current.md"], ["git", "commit", "-m", "日本語の確認コミット"]]:
        code, output = smoke.run_cmd(vault, args)
        if code != 0:
            raise AssertionError(f"{' '.join(args)} failed\n{output}")
    code, output = smoke.run_memory_cli(vault, ["commit-language", "--base", "HEAD~1", "--head", "HEAD"])
    if code != 0:
        raise AssertionError(f"日本語 commit-language は通る想定でした\n{output}")
    smoke.append(path, "\n- [ ] English commit check.\n")
    for args in [["git", "add", "clients/example-client-alpha/states/current.md"], ["git", "commit", "-m", "Update docs"]]:
        code, output = smoke.run_cmd(vault, args)
        if code != 0:
            raise AssertionError(f"{' '.join(args)} failed\n{output}")
    code, output = smoke.run_memory_cli(vault, ["commit-language", "--base", "HEAD~1", "--head", "HEAD"])
    if code == 0:
        raise AssertionError("英語のみ commit message は拒否される想定でした")
    print("成功: 日本語 commit message 検査")
    smoke.reset_git_fixture(vault)


def assert_role_guard_member_rejects_repo_ops(vault: Path) -> None:
    path = vault / "docs" / "qa-role-guard.md"
    smoke.write(path, "# role guard test\n")
    code, output = smoke.run_cmd(vault, ["git", "add", "docs/qa-role-guard.md"])
    if code != 0:
        raise AssertionError(f"git add failed\n{output}")
    code, output = smoke.run_cmd(
        vault,
        [sys.executable, "tools/memory_cli.py", "role-guard", "--staged"],
        env={"MEMORY_ROLE": "member"},
    )
    if code == 0:
        raise AssertionError("member role は docs 変更を拒否する想定でした")
    if "member" not in output and "更新できません" not in output:
        raise AssertionError(f"role guard 出力が想定外です\n{output}")
    smoke.reset_git_fixture(vault)
    print("成功: member role は repository 保守 path を拒否")


def main() -> int:
    keep_temp = "--keep" in sys.argv[1:] or "1" in sys.argv[1:]
    smoke_result = run_smoke(keep_temp)
    if smoke_result != 0:
        return smoke_result

    vault = smoke.copy_vault(prefix="memory-workflow-qa-")
    print(f"QA vault: {vault}")
    try:
        smoke.assert_lint_passes(vault, "QA 基準 lint")
        smoke.create_client_fixture(vault, smoke.PRIMARY_CLIENT, "Example Client Alpha")
        smoke.create_client_fixture(vault, smoke.SECONDARY_CLIENT, "Example Client Beta")
        smoke.create_internal_fixture(vault, smoke.INTERNAL_PROJECT, "Example Internal Project")
        smoke.assert_lint_passes(vault, "QA fixture 作成")
        assert_cli_first_prompts(vault)
        assert_skill_add_entities(vault)
        assert_skill_save_digest_single_client(vault)
        assert_skill_save_multi_entity_split(vault)
        assert_unknown_inbox_save(vault)
        assert_correction_event(vault)
        assert_monthly_review_event(vault)
        assert_duplicate_ids_rejected(vault)
        assert_duplicate_raw_ids_rejected(vault)
        assert_invalid_source_context_rejected(vault)
        assert_commit_language(vault)
        assert_role_guard_member_rejects_repo_ops(vault)
        smoke.assert_pre_push_hook_absent(vault)
        smoke.assert_lint_passes(vault, "QA 最終 lint")
        print("Memory workflow QA passed.")
        return 0
    finally:
        if keep_temp:
            print(f"一時 QA vault を残しました: {vault}")
        else:
            shutil.rmtree(vault.parent, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
