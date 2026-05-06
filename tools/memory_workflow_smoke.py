#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PRIMARY_CLIENT = "example-client-alpha"
SECONDARY_CLIENT = "example-client-beta"
INTERNAL_PROJECT = "example-internal-project"


def copy_vault(prefix: str = "memory-workflow-smoke-") -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
    target = temp_dir / "vault"

    def ignore(_dir: str, names: list[str]) -> set[str]:
        ignored = {".git", "__pycache__", ".DS_Store", ".memory-audit", ".memory-cache"}
        ignored.update(name for name in names if name.endswith(".pyc"))
        return ignored.intersection(names)

    shutil.copytree(ROOT, target, ignore=ignore)
    return target


def run_lint(vault: Path) -> tuple[int, str]:
    return run_cmd(vault, [sys.executable, "tools/memory_lint.py"])


def run_lint_args(vault: Path, args: list[str]) -> tuple[int, str]:
    return run_cmd(vault, [sys.executable, "tools/memory_lint.py", *args])


def run_memory_cli(vault: Path, args: list[str]) -> tuple[int, str]:
    return run_cmd(vault, [sys.executable, "tools/memory_cli.py", *args])


def run_cmd(vault: Path, args: list[str], env: dict[str, str] | None = None) -> tuple[int, str]:
    result = subprocess.run(
        args,
        cwd=vault,
        env={**os.environ, **(env or {})},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return result.returncode, result.stdout


def assert_lint_passes(vault: Path, label: str) -> None:
    code, output = run_lint(vault)
    if code != 0:
        raise AssertionError(f"{label}: lint が通る想定でした\n{output}")
    print(f"成功: {label}")


def assert_lint_fails(vault: Path, label: str, expected: str) -> None:
    code, output = run_lint(vault)
    if code == 0:
        raise AssertionError(f"{label}: lint が失敗する想定でした")
    if expected not in output:
        raise AssertionError(f"{label}: lint 出力に {expected!r} が含まれる想定でした\n{output}")
    print(f"成功: {label}")


def assert_lint_args_passes(vault: Path, args: list[str], label: str) -> None:
    code, output = run_lint_args(vault, args)
    if code != 0:
        raise AssertionError(f"{label}: lint {args} が通る想定でした\n{output}")
    print(f"成功: {label}")


def assert_lint_args_fails(vault: Path, args: list[str], label: str, expected: str) -> None:
    code, output = run_lint_args(vault, args)
    if code == 0:
        raise AssertionError(f"{label}: lint {args} が失敗する想定でした")
    if expected not in output:
        raise AssertionError(f"{label}: lint 出力に {expected!r} が含まれる想定でした\n{output}")
    print(f"成功: {label}")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append(path: Path, text: str) -> None:
    path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")


def raw_note_text(raw_id: str, scope: str, entity_refs: list[str], title: str, summary: str, details: str) -> str:
    refs = "\n".join(f"  - {item}" for item in entity_refs) or "[]"
    entity_refs_block = f"entity_refs:\n{refs}" if refs != "[]" else "entity_refs: []"
    return f"""---
type: raw_note
raw_id: {raw_id}
scope: {scope}
{entity_refs_block}
updated_at: 2026-04-26
update_summary: "{summary}"
update_source: []
update_history:
  - "2026-04-26 {summary}"
---

# {title}

{details}
"""


def event_text(
    *,
    event_id: str,
    entity_type: str,
    entity_id: str,
    event_type: str,
    title: str,
    summary: str,
    details: str,
    source_ref: str,
    derived_status: str = "applied",
    derived_targets: list[str] | None = None,
    tasks: list[str] | None = None,
) -> str:
    targets = derived_targets if derived_targets is not None else ["state"]
    target_block = "\n".join(f"  - {target}" for target in targets)
    task_lines = "\n".join(f"- {task}" for task in (tasks or [])) or "なし。"
    return f"""---
type: event
event_id: {event_id}
event_date: 2026-04-26
created_at: 2026-04-26T10:00:00+09:00
author: smoke
entity_type: {entity_type}
entity_id: {entity_id}
event_type: {event_type}
derived_status: {derived_status}
derived_targets:
{target_block}
source_refs:
  - "{source_ref}"
updated_at: 2026-04-26
update_summary: "{summary}"
update_source:
  - "{source_ref}"
update_history:
  - "2026-04-26 {summary}"
---

# {title}

## 要約

{summary}

## 詳細

{details}

## タスク

{task_lines}

## 出典メモ

{source_ref}
"""


def source_index_text(entity_type: str, entity_id: str, name: str) -> str:
    return f"""---
type: source_index
entity_type: {entity_type}
entity_id: {entity_id}
auto_generated: false
owner: human
updated_at: 2026-04-26
update_summary: "{name} の source index。"
update_source: []
update_history:
  - "2026-04-26 {name} の source index を作成。"
---

# Sources

| 名称 | 種別 | URL | context | 備考 |
| --- | --- | --- | --- | --- |
"""


def create_entity_fixture(vault: Path, entity_type: str, entity_id: str, name: str) -> None:
    root = vault / ("clients" if entity_type == "client" else "internal") / entity_id
    (root / "events").mkdir(parents=True, exist_ok=True)
    (root / "states").mkdir(parents=True, exist_ok=True)
    profile_type = "client_profile" if entity_type == "client" else "internal_profile"
    write(
        root / "profile.md",
        f"""---
type: {profile_type}
entity_type: {entity_type}
entity_id: {entity_id}
auto_generated: false
owner: human
updated_at: 2026-04-26
update_summary: "{name} の profile。"
update_source: []
update_history:
  - "2026-04-26 {name} の profile を作成。"
---

# {name}

## 安定コンテキスト

Google商談・プロジェクト運用の smoke fixture。

## 商談・プロジェクト運用ナレッジ

<!-- BEGIN MANUAL -->
<!-- END MANUAL -->
""",
    )
    write(root / "sources.md", source_index_text(entity_type, entity_id, name))
    write(
        root / "states" / "current.md",
        f"""---
type: entity_state
entity_type: {entity_type}
entity_id: {entity_id}
auto_generated: true
owner: memory-digest
last_digest: 2026-04-26
updated_at: 2026-04-26
update_summary: "{name} の current state。"
update_source: []
update_history:
  - "2026-04-26 {name} の current state を作成。"
---

# 状態

## 現在の状態

- 初期状態。

## 次のアクション

- [ ] 初期 task を確認する。

## 出典イベント

## 手動メモ

<!-- BEGIN MANUAL -->
<!-- END MANUAL -->
""",
    )


def create_client_fixture(vault: Path, client_id: str, name: str) -> None:
    create_entity_fixture(vault, "client", client_id, name)


def create_internal_fixture(vault: Path, project_id: str, name: str) -> None:
    create_entity_fixture(vault, "internal", project_id, name)


def create_event_with_digest(
    vault: Path,
    *,
    entity_type: str,
    entity_id: str,
    slug: str,
    summary: str,
    details: str,
    source_ref: str,
    task: str,
) -> Path:
    root = vault / ("clients" if entity_type == "client" else "internal") / entity_id
    path = root / "events" / f"2026-04-26_{slug}.md"
    write(
        path,
        event_text(
            event_id=f"20260426-{entity_id}-{slug}",
            entity_type=entity_type,
            entity_id=entity_id,
            event_type="meeting",
            title=f"{entity_id} {slug}",
            summary=summary,
            details=details,
            source_ref=source_ref,
            tasks=[task],
        ),
    )
    append(root / "states" / "current.md", f"\n- {summary} 出典: [[../events/2026-04-26_{slug}]]\n")
    append(root / "states" / "current.md", f"- [ ] {task} 出典: [[../events/2026-04-26_{slug}]]\n")
    append(root / "profile.md", f"\n- {summary} 出典: [[events/2026-04-26_{slug}]]\n")
    return path


def apply_positive_scenarios(vault: Path) -> None:
    create_client_fixture(vault, PRIMARY_CLIENT, "Example Client Alpha")
    create_client_fixture(vault, SECONDARY_CLIENT, "Example Client Beta")
    create_internal_fixture(vault, INTERNAL_PROJECT, "Example Internal Project")
    write(
        vault / "raw" / "2026-04-26_smoke-multi-entity.md",
        raw_note_text(
            raw_id="2026-04-26_smoke-multi-entity",
            scope="multi_entity",
            entity_refs=[f"client/{PRIMARY_CLIENT}", f"client/{SECONDARY_CLIENT}", f"internal/{INTERNAL_PROJECT}"],
            title="Smoke 複数 entity 定例",
            summary="複数 entity の raw 原本を保存。",
            details="Alpha は提案資料更新、Beta は問い合わせ整理、internal は営業提案を確認した。",
        ),
    )
    source_ref = "[[raw/2026-04-26_smoke-multi-entity]]"
    create_event_with_digest(
        vault,
        entity_type="client",
        entity_id=PRIMARY_CLIENT,
        slug="smoke-alpha",
        summary="提案資料更新を優先する。",
        details="Alpha は次回提案で提案資料の不安解消を扱う。",
        source_ref=source_ref,
        task="提案資料更新案を作る。",
    )
    create_event_with_digest(
        vault,
        entity_type="client",
        entity_id=SECONDARY_CLIENT,
        slug="smoke-beta",
        summary="問い合わせを分類する。",
        details="Beta は問い合わせ意図と情報収集語句を分ける。",
        source_ref=source_ref,
        task="問い合わせ分類を作る。",
    )
    create_event_with_digest(
        vault,
        entity_type="internal",
        entity_id=INTERNAL_PROJECT,
        slug="smoke-internal",
        summary="営業提案の型を整理する。",
        details="internal は業界別提案向け提案観点を整理する。",
        source_ref=source_ref,
        task="営業提案の型を整理する。",
    )
    write(
        vault / "inbox" / "2026-04-26_unknown-ad-report.md",
        """---
type: inbox_note
updated_at: 2026-04-26
update_summary: "対象不明の商談レポートメモ。"
update_source: []
update_history:
  - "2026-04-26 対象不明の商談レポートメモを保存。"
---

# 対象不明メモ

商談レポートの数字が落ちているが、対象 entity は未確定。
""",
    )


def apply_misfiled_event(vault: Path) -> Path:
    path = vault / "clients" / PRIMARY_CLIENT / "events" / "2026-04-26_smoke-misfiled.md"
    write(
        path,
        event_text(
            event_id="20260426-smoke-misfiled",
            entity_type="client",
            entity_id=SECONDARY_CLIENT,
            event_type="note",
            title="誤配置 event",
            summary="path と entity_id が違う。",
            details="lint が拒否する。",
            source_ref="[[raw/2026-04-26_smoke-multi-entity]]",
        ),
    )
    return path


def append_bad_reference(path: Path, text: str) -> str:
    original = path.read_text(encoding="utf-8")
    path.write_text(original + text, encoding="utf-8")
    return original


def apply_pending_event(vault: Path) -> Path:
    path = vault / "clients" / PRIMARY_CLIENT / "events" / "2026-04-26_smoke-pending.md"
    write(
        path,
        event_text(
            event_id="20260426-smoke-pending",
            entity_type="client",
            entity_id=PRIMARY_CLIENT,
            event_type="note",
            title="pending event",
            summary="pending event を検出する。",
            details="digest 前の想定。",
            source_ref="[[raw/2026-04-26_smoke-multi-entity]]",
            derived_status="pending",
        ),
    )
    return path


def apply_source_entity_mismatch(vault: Path) -> tuple[Path, str]:
    path = vault / "clients" / PRIMARY_CLIENT / "sources.md"
    original = path.read_text(encoding="utf-8")
    path.write_text(original.replace(f"entity_id: {PRIMARY_CLIENT}", f"entity_id: {SECONDARY_CLIENT}", 1), encoding="utf-8")
    return path, original


def apply_bad_source_url(vault: Path) -> tuple[Path, str]:
    path = vault / "clients" / PRIMARY_CLIENT / "sources.md"
    original = path.read_text(encoding="utf-8")
    append(path, "\n| NG URL | document | http://example.com/doc | yes | invalid |\n")
    return path, original


def init_git_fixture(vault: Path) -> None:
    for args in [
        ["git", "init"],
        ["git", "config", "user.name", "Smoke Tester"],
        ["git", "config", "user.email", "smoke@example.com"],
        ["git", "add", "."],
        ["git", "commit", "-m", "初期テストデータ"],
    ]:
        code, output = run_cmd(vault, args)
        if code != 0:
            raise AssertionError(f"{' '.join(args)} failed\n{output}")


def reset_git_fixture(vault: Path) -> None:
    for args in [["git", "reset", "--hard", "HEAD"], ["git", "clean", "-fd"]]:
        code, output = run_cmd(vault, args)
        if code != 0:
            raise AssertionError(f"{' '.join(args)} failed\n{output}")


def assert_staged_manual_fix(vault: Path) -> None:
    path = vault / "clients" / PRIMARY_CLIENT / "profile.md"
    path.write_text("# Manual Paste\n\n## 手動メモ\n\nObsidian から貼り付け。\n", encoding="utf-8")
    code, output = run_cmd(vault, ["git", "add", "clients/example-client-alpha/profile.md"])
    if code != 0:
        raise AssertionError(f"git add failed\n{output}")
    assert_lint_args_passes(vault, ["--fix", "--staged"], "staged manual file の frontmatter / marker 補正")
    code, staged = run_cmd(vault, ["git", "show", ":clients/example-client-alpha/profile.md"])
    if code != 0:
        raise AssertionError(f"git show failed\n{staged}")
    for token in ["type: client_profile", "entity_id: example-client-alpha", "<!-- BEGIN MANUAL -->"]:
        if token not in staged:
            raise AssertionError(f"補正後 staged file に {token!r} がありません\n{staged}")
    reset_git_fixture(vault)


def assert_event_body_immutability(vault: Path) -> None:
    path = vault / "clients" / PRIMARY_CLIENT / "events" / "2026-04-26_smoke-alpha.md"
    append(path, "\n本文を直接変更してはいけない。\n")
    code, output = run_cmd(vault, ["git", "add", "clients/example-client-alpha/events/2026-04-26_smoke-alpha.md"])
    if code != 0:
        raise AssertionError(f"git add failed\n{output}")
    assert_lint_args_fails(vault, ["--staged"], "既存 event 本文変更を拒否", "既存 event 本文")
    reset_git_fixture(vault)


def assert_event_frontmatter_immutability(vault: Path) -> None:
    path = vault / "clients" / PRIMARY_CLIENT / "events" / "2026-04-26_smoke-alpha.md"
    path.write_text(path.read_text(encoding="utf-8").replace("event_type: meeting", "event_type: note", 1), encoding="utf-8")
    code, output = run_cmd(vault, ["git", "add", "clients/example-client-alpha/events/2026-04-26_smoke-alpha.md"])
    if code != 0:
        raise AssertionError(f"git add failed\n{output}")
    assert_lint_args_fails(vault, ["--staged"], "既存 event immutable frontmatter 変更を拒否", "immutable frontmatter")
    reset_git_fixture(vault)


def assert_privacy_scan_masks_values(vault: Path) -> None:
    path = vault / "clients" / PRIMARY_CLIENT / "states" / "current.md"
    unmasked_email = "customer" + "@example.net"
    unmasked_phone = "090-" + "1234-" + "5678"
    append(path, f"\n未マスク連絡先: {unmasked_email} / {unmasked_phone}\n")
    code, output = run_memory_cli(vault, ["privacy-scan", "--worktree"])
    if code == 0:
        raise AssertionError("privacy-scan が未マスク連絡先を拒否する想定でした")
    if unmasked_email in output or unmasked_phone in output:
        raise AssertionError(f"privacy-scan が CI log に実値を出しています\n{output}")
    path.write_text(
        path.read_text(encoding="utf-8")
        .replace(unmasked_email, "[email masked]")
        .replace(unmasked_phone, "[phone masked]"),
        encoding="utf-8",
    )
    code, output = run_memory_cli(vault, ["privacy-scan", "--worktree"])
    if code != 0:
        raise AssertionError(f"privacy-scan はマスク済み連絡先を通す想定でした\n{output}")
    print("成功: privacy-scan が未マスク連絡先を拒否し、実値を log に出さない")
    reset_git_fixture(vault)


def assert_pre_push_hook_absent(vault: Path) -> None:
    if (vault / ".githooks" / "pre-push").exists():
        raise AssertionError("pre-push hook は置かない想定です")
    print("成功: pre-push hook は存在しない")


def main() -> int:
    vault = copy_vault()
    keep_temp = "--keep" in sys.argv[1:] or "1" in sys.argv[1:]
    print(f"スモーク vault: {vault}")
    try:
        assert_lint_passes(vault, "基準 lint")
        apply_positive_scenarios(vault)
        assert_lint_passes(vault, "軽量 entity、raw、event、profile/current digest、inbox 振り分け")

        bad_event = apply_misfiled_event(vault)
        assert_lint_fails(vault, "誤配置 event を拒否", "path の entity_id")
        bad_event.unlink()
        assert_lint_passes(vault, "誤配置 event 削除後に lint が回復")

        beta_current = vault / "clients" / SECONDARY_CLIENT / "states" / "current.md"
        original = append_bad_reference(beta_current, "\n別 client 参照: [[../../example-client-alpha/profile]]\n")
        assert_lint_fails(vault, "別 client file 参照を拒否", "別 client の file")
        beta_current.write_text(original, encoding="utf-8")
        assert_lint_passes(vault, "別 client file 参照削除後に lint が回復")

        alpha_current = vault / "clients" / PRIMARY_CLIENT / "states" / "current.md"
        original = append_bad_reference(alpha_current, "\nraw 直接参照: [[../../../raw/2026-04-26_smoke-multi-entity]]\n")
        assert_lint_fails(vault, "entity file の raw note 直接参照を拒否", "raw note を直接参照")
        alpha_current.write_text(original, encoding="utf-8")
        assert_lint_passes(vault, "raw note 直接参照削除後に lint が回復")

        retired = vault / "clients" / PRIMARY_CLIENT / "tasks.md"
        write(retired, "# retired\n")
        assert_lint_fails(vault, "廃止済み tasks.md を拒否", "lite 構成では使いません")
        retired.unlink()
        assert_lint_passes(vault, "廃止済み path 削除後に lint が回復")

        pending_event = apply_pending_event(vault)
        assert_lint_fails(vault, "pending event を拒否", "pending event")
        pending_event.unlink()
        assert_lint_passes(vault, "pending event 削除後に lint が回復")

        source_path, source_original = apply_source_entity_mismatch(vault)
        assert_lint_fails(vault, "sources entity 不一致を拒否", "sources entity_id")
        source_path.write_text(source_original, encoding="utf-8")
        assert_lint_passes(vault, "sources entity 不一致復旧後に lint が回復")

        bad_source, bad_source_original = apply_bad_source_url(vault)
        assert_lint_fails(vault, "不正な source URL を拒否", "source URL")
        bad_source.write_text(bad_source_original, encoding="utf-8")
        assert_lint_passes(vault, "不正な source URL 復旧後に lint が回復")

        init_git_fixture(vault)
        assert_staged_manual_fix(vault)
        assert_event_body_immutability(vault)
        assert_event_frontmatter_immutability(vault)
        assert_privacy_scan_masks_values(vault)
        assert_pre_push_hook_absent(vault)

        assert_lint_passes(vault, "最終 lint")
        print("Memory workflow smoke passed.")
        return 0
    finally:
        if keep_temp:
            print(f"一時 vault を残しました: {vault}")
        else:
            shutil.rmtree(vault.parent, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
