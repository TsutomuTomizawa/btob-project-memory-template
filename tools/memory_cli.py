#!/usr/bin/env python3
from __future__ import annotations

import argparse
import calendar
import contextlib
import datetime as dt
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import memory_llm_qa
import memory_lint
import memory_workflow_qa
import memory_workflow_smoke


ROOT = memory_lint.ROOT
MAIN_BRANCH = "main"
PUBLISH_WAIT_TIMEOUT_SECONDS = 900
PUBLISH_WAIT_INTERVAL_SECONDS = 10
ROLE_REGISTRY_PATH = ROOT / ".memory-roles.json"
LOCAL_ROLE_CONFIG_PATH = ROOT / ".memory-local.json"
ALLOWED_EVENT_TYPES = sorted(memory_lint.ALLOWED["event_type"])
PRIVACY_ALLOWED_EMAIL_DOMAINS = {
    "example.com",
    "example.net",
    "example.org",
    "example.jp",
    "example.co.jp",
}
PRIVACY_EMAIL_RE = re.compile(r"(?<![\w.+-])([A-Za-z0-9._%+-]{1,64})@([A-Za-z0-9.-]+\.[A-Za-z]{2,})(?![\w.-])")
PRIVACY_PHONE_RE = re.compile(
    r"(?<!\d)(?:0\d{1,4}[- ]\d{1,4}[- ]\d{3,4}|0[789]0[- ]?\d{4}[- ]?\d{4}|\+81[- ]?(?:0[- ]?)?\d{1,4}[- ]?\d{1,4}[- ]?\d{3,4})(?!\d)"
)
JAPANESE_TEXT_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
ENTITY_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MONTH_RE = re.compile(r"^(\d{4})-(\d{2})$")
PRIVACY_SCAN_EXCLUDED_PREFIXES = (
    ".git/",
    ".memory-cache/",
    ".memory-audit/",
    "node_modules/",
)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def run_command(args: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        check=False,
    )


def git_output(args: list[str]) -> str:
    result = run_command(["git", *args], capture=True)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def git_lines(args: list[str]) -> list[str]:
    return [line for line in git_output(args).splitlines() if line.strip()]


def git_name_status_paths(args: list[str]) -> list[str]:
    paths = []
    for line in git_lines(args):
        fields = line.split("\t")
        if len(fields) < 2:
            continue
        paths.extend(field for field in fields[1:] if field)
    return sorted(set(paths))


def git_success(args: list[str]) -> bool:
    return run_command(["git", *args], capture=True).returncode == 0


def current_git_branch() -> str:
    return git_output(["branch", "--show-current"])


def worktree_is_dirty() -> bool:
    return bool(git_lines(["status", "--porcelain"]))


def run_git_step(args: list[str], label: str) -> int:
    print(f"[memory] {label}: git {' '.join(args)}", flush=True)
    return run_command(["git", *args]).returncode


def ensure_not_git_operation_in_progress() -> bool:
    git_dir = git_output(["rev-parse", "--git-dir"])
    if not git_dir:
        print("[memory] git repository が見つかりません", file=sys.stderr)
        return False
    git_path = Path(git_dir)
    if not git_path.is_absolute():
        git_path = ROOT / git_path
    markers = [
        "MERGE_HEAD",
        "CHERRY_PICK_HEAD",
        "REVERT_HEAD",
        "rebase-apply",
        "rebase-merge",
    ]
    active = [marker for marker in markers if (git_path / marker).exists()]
    if active:
        print("[memory] publish/sync を続ける前に、進行中の git 操作を解決してください:", file=sys.stderr)
        for marker in active:
            print(f"- {marker}", file=sys.stderr)
        return False
    return True


def changed_files_for_mode(mode: str) -> list[str]:
    if mode == "staged":
        return git_name_status_paths(["diff", "--cached", "--name-status"])
    if mode == "worktree":
        files = set(git_name_status_paths(["diff", "--name-status", "HEAD"]))
        files.update(git_lines(["ls-files", "--others", "--exclude-standard"]))
        return sorted(files)
    raise ValueError(f"unknown mode: {mode}")


def changed_files_for_range(base: str, head: str) -> list[str]:
    return git_name_status_paths(["diff", "--name-status", f"{base}..{head}"])


def privacy_scan_paths(mode: str) -> list[str]:
    if mode == "staged":
        return git_lines(["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    if mode == "worktree":
        return changed_files_for_mode("worktree")
    return git_lines(["ls-files"])


def is_privacy_scan_candidate(path: str) -> bool:
    normalized = path.strip().removeprefix("./")
    if not normalized:
        return False
    if any(normalized.startswith(prefix) for prefix in PRIVACY_SCAN_EXCLUDED_PREFIXES):
        return False
    suffix = Path(normalized).suffix.lower()
    if suffix in {".md", ".txt", ".json", ".py", ".yml", ".yaml", ".sh", ".css", ".toml"}:
        return True
    return normalized in {"scripts/memory", ".gitignore"}


def read_privacy_scan_bytes(path: str, *, staged: bool) -> bytes | None:
    if staged:
        result = subprocess.run(
            ["git", "show", f":{path}"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode != 0:
            return None
        return result.stdout
    full_path = ROOT / path
    if not full_path.is_file():
        return None
    try:
        return full_path.read_bytes()
    except OSError:
        return None


def privacy_findings_for_text(path: str, text: str) -> list[str]:
    findings = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for match in PRIVACY_EMAIL_RE.finditer(line):
            domain = match.group(2).lower()
            if domain in PRIVACY_ALLOWED_EMAIL_DOMAINS:
                continue
            findings.append(f"{path}:{line_no}: 未マスクの email address があります。`[email masked]` などに置換してください。")
        for match in PRIVACY_PHONE_RE.finditer(line):
            digits = re.sub(r"\D", "", match.group(0))
            if match.group(0).startswith("+81"):
                digits = "0" + digits[2:].lstrip("0")
            if len(digits) in {10, 11}:
                findings.append(f"{path}:{line_no}: 未マスクの phone number があります。`[phone masked]` などに置換してください。")
    return findings


def command_privacy_scan(args: argparse.Namespace) -> int:
    mode = "tracked"
    if args.staged:
        mode = "staged"
    elif args.worktree:
        mode = "worktree"

    findings = []
    scanned = 0
    for path in privacy_scan_paths(mode):
        if not is_privacy_scan_candidate(path):
            continue
        data = read_privacy_scan_bytes(path, staged=(mode == "staged"))
        if not data or b"\0" in data:
            continue
        text = data.decode("utf-8", errors="replace")
        scanned += 1
        findings.extend(privacy_findings_for_text(path, text))

    if findings:
        print("Memory privacy scan で未マスクの連絡先らしき文字列が見つかりました:")
        for finding in findings:
            print(f"- {finding}")
        print("CI log に値を出さないため、検出した email / phone の実値は表示していません。")
        return 1

    print(f"Memory privacy scan 合格: {scanned} files を確認しました。")
    return 0


def event_records() -> list[dict]:
    records = []
    for path in memory_lint.event_paths():
        fm, body = memory_lint.split_frontmatter(path)
        records.append({"path": path, "frontmatter": fm, "body": body})
    return records


def pending_events(events: list[dict]) -> list[dict]:
    return [
        {
            "path": rel(event["path"]),
            "entity_type": event["frontmatter"].get("entity_type", ""),
            "entity_id": event["frontmatter"].get("entity_id", ""),
            "event_id": event["frontmatter"].get("event_id", ""),
        }
        for event in events
        if event["frontmatter"].get("derived_status") == "pending"
    ]


def duplicate_event_ids(events: list[dict]) -> list[dict]:
    by_id: dict[str, list[str]] = {}
    for event in events:
        event_id = event["frontmatter"].get("event_id", "")
        if not event_id:
            continue
        by_id.setdefault(event_id, []).append(rel(event["path"]))
    return [
        {"event_id": event_id, "paths": paths}
        for event_id, paths in sorted(by_id.items())
        if len(paths) > 1
    ]


def task_counts() -> dict:
    files = []
    total_open = 0
    total_done = 0
    for pattern in ["clients/*/states/current.md", "internal/*/states/current.md"]:
        for path in sorted(ROOT.glob(pattern)):
            open_count = 0
            done_count = 0
            for line in path.read_text(encoding="utf-8").splitlines():
                stripped = line.lstrip()
                if stripped.startswith("- [ ] "):
                    open_count += 1
                elif stripped.lower().startswith("- [x] "):
                    done_count += 1
            total_open += open_count
            total_done += done_count
            files.append({"path": rel(path), "open": open_count, "done": done_count})
    return {"open": total_open, "done": total_done, "files": files}


def entity_summary(entity_type: str, root_name: str, events: list[dict], tasks: dict) -> list[dict]:
    entities = []
    for root in sorted((ROOT / root_name).glob("*")):
        if not root.is_dir():
            continue
        entity_events = [
            event
            for event in events
            if event["frontmatter"].get("entity_type") == entity_type
            and event["frontmatter"].get("entity_id") == root.name
        ]
        task_path = root / "states" / "current.md"
        task_file = next((item for item in tasks["files"] if item["path"] == rel(task_path)), None)
        entities.append(
            {
                "type": entity_type,
                "id": root.name,
                "path": rel(root),
                "has_profile": (root / "profile.md").exists(),
                "event_count": len(entity_events),
                "pending_events": sum(
                    1 for event in entity_events if event["frontmatter"].get("derived_status") == "pending"
                ),
                "open_tasks": task_file["open"] if task_file else 0,
            }
        )
    return entities


def collect_status(*, with_lint: bool) -> dict:
    branch = git_output(["branch", "--show-current"]) or "(unknown)"
    status_lines = [line for line in git_output(["status", "--short"]).splitlines() if line.strip()]
    events = event_records()
    tasks = task_counts()
    entities = {
        "clients": entity_summary("client", "clients", events, tasks),
        "internal": entity_summary("internal", "internal", events, tasks),
    }
    inbox_files = [
        rel(path)
        for path in sorted((ROOT / "inbox").glob("*.md"))
        if path.name != "README.md"
    ]
    lint_result = {"checked": False}
    if with_lint:
        output_buffer = io.StringIO()
        with contextlib.redirect_stdout(output_buffer):
            lint_returncode = memory_lint.main([])
        output = output_buffer.getvalue()
        lint_result = {
            "checked": True,
            "returncode": lint_returncode,
            "passed": lint_returncode == 0,
            "summary": output.splitlines()[0] if output.splitlines() else "",
        }

    return {
        "git": {
            "branch": branch,
            "dirty": bool(status_lines),
            "dirty_count": len(status_lines),
        },
        "entities": entities,
        "events": {
            "total": len(events),
            "pending": pending_events(events),
            "duplicate_event_ids": duplicate_event_ids(events),
        },
        "inbox": {"count": len(inbox_files), "files": inbox_files},
        "tasks": tasks,
        "lint": lint_result,
    }


def print_status(data: dict) -> None:
    clients = data["entities"]["clients"]
    internal = data["entities"]["internal"]
    pending = data["events"]["pending"]
    duplicates = data["events"]["duplicate_event_ids"]
    print("Memory CLI status")
    print(f"- Branch: {data['git']['branch']}")
    dirty_label = "dirty" if data["git"]["dirty"] else "clean"
    print(f"- Worktree: {dirty_label} ({data['git']['dirty_count']} changed paths)")
    print(f"- Entities: {len(clients)} clients, {len(internal)} internal projects")
    print(f"- Events: {data['events']['total']} total, {len(pending)} pending")
    print(f"- Duplicate event_id: {len(duplicates)}")
    print(f"- Inbox notes: {data['inbox']['count']}")
    print(f"- Open tasks: {data['tasks']['open']}")
    lint = data["lint"]
    if lint["checked"]:
        status = "passed" if lint["passed"] else f"failed ({lint['returncode']})"
        print(f"- Lint: {status}: {lint['summary']}")
    else:
        print("- Lint: not checked (use --with-lint)")
    if pending:
        print()
        print("Pending events:")
        for item in pending[:20]:
            print(f"- {item['path']}")
        if len(pending) > 20:
            print(f"- ... {len(pending) - 20} more")
    if duplicates:
        print()
        print("Duplicate event_id:")
        for item in duplicates[:20]:
            print(f"- {item['event_id']}: {', '.join(item['paths'])}")
        if len(duplicates) > 20:
            print(f"- ... {len(duplicates) - 20} more")


def status_is_strict_failure(data: dict) -> bool:
    lint = data["lint"]
    lint_failed = lint["checked"] and not lint["passed"]
    return bool(data["events"]["pending"] or data["events"]["duplicate_event_ids"] or lint_failed)


def command_status(args: argparse.Namespace) -> int:
    data = collect_status(with_lint=args.with_lint)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_status(data)
    if args.strict and status_is_strict_failure(data):
        return 1
    return 0


def command_entities(args: argparse.Namespace) -> int:
    events = event_records()
    tasks = task_counts()
    data = {
        "clients": entity_summary("client", "clients", events, tasks),
        "internal": entity_summary("internal", "internal", events, tasks),
    }
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    print("Clients")
    if data["clients"]:
        for item in data["clients"]:
            profile = "yes" if item["has_profile"] else "no"
            print(
                f"- {item['id']} "
                f"(events={item['event_count']}, pending={item['pending_events']}, "
                f"open_tasks={item['open_tasks']}, profile={profile})"
            )
    else:
        print("- none")

    print()
    print("Internal")
    if data["internal"]:
        for item in data["internal"]:
            profile = "yes" if item["has_profile"] else "no"
            print(
                f"- {item['id']} "
                f"(events={item['event_count']}, pending={item['pending_events']}, "
                f"open_tasks={item['open_tasks']}, profile={profile})"
            )
    else:
        print("- none")
    return 0


def command_lint(args: argparse.Namespace) -> int:
    lint_args = []
    if args.fix:
        lint_args.append("--fix")
    if args.staged:
        lint_args.append("--staged")
    return memory_lint.main(lint_args)


def command_smoke(args: argparse.Namespace) -> int:
    old_argv = sys.argv[:]
    sys.argv = ["memory_workflow_smoke.py"] + (["--keep"] if args.keep else [])
    try:
        return memory_workflow_smoke.main()
    finally:
        sys.argv = old_argv


def command_qa(args: argparse.Namespace) -> int:
    old_argv = sys.argv[:]
    sys.argv = ["memory_workflow_qa.py"] + (["--keep"] if args.keep else [])
    try:
        return memory_workflow_qa.main()
    finally:
        sys.argv = old_argv


def read_json_config(config_path: Path, label: str) -> dict:
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[memory] role guard: failed to read {label}: {exc}", file=sys.stderr)
        raise SystemExit(2)
    if not isinstance(data, dict):
        print(f"[memory] role guard: {label} must be a JSON object", file=sys.stderr)
        raise SystemExit(2)
    return data


def read_json_text(text: str, label: str) -> dict:
    try:
        data = json.loads(text)
    except Exception as exc:
        print(f"[memory] role guard: failed to read {label}: {exc}", file=sys.stderr)
        raise SystemExit(2)
    if not isinstance(data, dict):
        print(f"[memory] role guard: {label} must be a JSON object", file=sys.stderr)
        raise SystemExit(2)
    return data


def as_string_list(value: object, field: str, config_path: Path) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    print(f"[memory] role guard: {rel(config_path)}.{field} must be a string array", file=sys.stderr)
    raise SystemExit(2)


def norm(value: object) -> str:
    return str(value or "").strip().lower()


def member_tokens(member: dict) -> set[str]:
    tokens = []
    for field in ("id", "name", "email", "github", "github_login", "login"):
        value = member.get(field)
        if isinstance(value, str):
            tokens.append(value)
    for field in ("names", "emails", "actors", "githubs", "github_logins", "logins"):
        value = member.get(field)
        if isinstance(value, str):
            tokens.append(value)
        elif isinstance(value, list):
            tokens.extend(item for item in value if isinstance(item, str))
    return {norm(token) for token in tokens if norm(token)}


def role_config_from_data(data: dict, config_path: Path, actors: set[str]) -> tuple[str, list[str]]:
    default_role = data.get("default_role", data.get("role", "member"))
    if not isinstance(default_role, str):
        print(f"[memory] role guard: {rel(config_path)}.default_role must be a string", file=sys.stderr)
        raise SystemExit(2)
    default_roots = as_string_list(
        data.get("default_allowed_roots", data.get("allowed_roots", data.get("allowedRoots", []))),
        "default_allowed_roots",
        config_path,
    )

    members = data.get("members", [])
    if not isinstance(members, list):
        print(f"[memory] role guard: {rel(config_path)}.members must be an array", file=sys.stderr)
        raise SystemExit(2)
    matched = None
    for member in members:
        if not isinstance(member, dict):
            print(f"[memory] role guard: {rel(config_path)}.members[] must be an object", file=sys.stderr)
            raise SystemExit(2)
        if actors & member_tokens(member):
            matched = member
            break

    if matched is None:
        role = default_role
        roots = default_roots
    else:
        matched_role = matched.get("role", default_role)
        if not isinstance(matched_role, str):
            print("[memory] role guard: matched member role must be a string", file=sys.stderr)
            raise SystemExit(2)
        role = matched_role
        roots = as_string_list(
            matched.get("allowed_roots", matched.get("allowedRoots", default_roots)),
            "members[].allowed_roots",
            config_path,
        )
    return role, roots


def local_role_actors() -> set[str]:
    env_actor = os.environ.get("MEMORY_ACTOR", "")
    if norm(env_actor):
        return {norm(env_actor)}
    actors = {
        norm(git_output(["config", "--get", "user.name"])),
        norm(git_output(["config", "--get", "user.email"])),
    }
    actors.discard("")
    return actors


def read_trusted_role_registry_for_local() -> dict | None:
    if git_success(["rev-parse", "--is-inside-work-tree"]):
        text = git_output(["show", "HEAD:.memory-roles.json"])
        if text:
            return read_json_text(text, "HEAD:.memory-roles.json")
    if ROLE_REGISTRY_PATH.exists():
        return read_json_config(ROLE_REGISTRY_PATH, ".memory-roles.json")
    return None


def resolve_role_config() -> tuple[str, list[str]]:
    role = ""
    roots: list[str] = []
    actors = local_role_actors()
    role_registry = read_trusted_role_registry_for_local()
    if role_registry is not None:
        role, roots = role_config_from_data(role_registry, ROLE_REGISTRY_PATH, actors)
    elif LOCAL_ROLE_CONFIG_PATH.exists():
        data = read_json_config(LOCAL_ROLE_CONFIG_PATH, ".memory-local.json")
        role, roots = role_config_from_data(data, LOCAL_ROLE_CONFIG_PATH, actors)
    else:
        role = git_output(["config", "--get", "memory.role"]) or "member"
        roots = git_lines(["config", "--get-all", "memory.allowedRoot"])

    role = os.environ.get("MEMORY_ROLE", role) or "member"
    extra_roots = os.environ.get("MEMORY_ALLOWED_ROOTS", "")
    if extra_roots:
        roots.extend(root for root in re.split(r"[:,]", extra_roots) if root.strip())
    return role, [normalize_path(root) for root in roots if normalize_path(root)]


def resolve_ci_role_config(actor: str) -> tuple[str, list[str]]:
    if not actor.strip():
        print("[memory] role guard: --actor is required in --ci mode", file=sys.stderr)
        raise SystemExit(2)
    if not ROLE_REGISTRY_PATH.exists():
        print("[memory] role guard: .memory-roles.json がありません", file=sys.stderr)
        raise SystemExit(2)
    data = read_json_config(ROLE_REGISTRY_PATH, ".memory-roles.json")
    role, roots = role_config_from_data(data, ROLE_REGISTRY_PATH, {norm(actor)})
    return role, [normalize_path(root) for root in roots if normalize_path(root)]


def normalize_path(path: str) -> str:
    return path.strip().removeprefix("./").rstrip("/")


def is_under_root(path: str, root: str) -> bool:
    return path == root or path.startswith(f"{root}/")


def is_member_allowed_path(path: str, allowed_roots: list[str]) -> bool:
    file = normalize_path(path)
    roots = allowed_roots or ["clients", "internal", "raw", "inbox"]
    return any(is_under_root(file, root) for root in roots)


def print_member_blocked(blocked: list[str], role_label: str = "role=member") -> None:
    print(f"[memory] role guard: blocked paths for {role_label}", file=sys.stderr)
    for path in blocked:
        print(f"  - {path}", file=sys.stderr)
    print(
        """
通常メンバーは、clients/、internal/、raw/、inbox/ を更新できます。

skill / tool / docs / company / hook / template など repository 運用側の変更は、
admin role の担当者で行ってください。

ローカル事故防止は通常 HEAD の .memory-roles.json と git user.name/user.email を見ます。
.memory-local.json / git config / MEMORY_ROLE は fallback または明示テスト用です。
CI の強制チェックは trusted main の .memory-roles.json と GitHub actor を見ます。
""".strip(),
        file=sys.stderr,
    )


def command_role_guard(args: argparse.Namespace) -> int:
    mode = "staged"
    if args.worktree:
        mode = "worktree"

    if args.ci:
        if not args.base or not args.head:
            print("[memory] role guard: --ci requires --base and --head", file=sys.stderr)
            return 2
        role, allowed_roots = resolve_ci_role_config(args.actor)
        changed = changed_files_for_range(args.base, args.head)
        if role in {"admin", "developer"}:
            print(f"[memory] role guard: actor={args.actor} role={role} allows repository maintenance paths")
            return 0
        if role != "member":
            print(f"[memory] role guard: invalid role={role}", file=sys.stderr)
            print("Allowed roles: member, developer, admin", file=sys.stderr)
            return 2
        blocked = [path for path in changed if not is_member_allowed_path(path, allowed_roots)]
        if not blocked:
            roots = ", ".join(allowed_roots or ["clients", "internal", "raw", "inbox"])
            print(f"[memory] role guard: actor={args.actor} role=member path check ok ({roots})")
            return 0
        print_member_blocked(blocked, role_label=f"actor={args.actor} role=member")
        return 1

    role, allowed_roots = resolve_role_config()
    if role in {"admin", "developer"}:
        print(f"[memory] role guard: role={role} allows repository maintenance paths")
        return 0
    if role != "member":
        print(f"[memory] role guard: invalid role={role}", file=sys.stderr)
        print("Allowed roles: member, developer, admin", file=sys.stderr)
        return 2

    blocked = [
        path
        for path in changed_files_for_mode(mode)
        if not is_member_allowed_path(path, allowed_roots)
    ]
    if not blocked:
        print("[memory] role guard: role=member path check ok")
        return 0

    print_member_blocked(blocked)
    return 1


def command_py_compile(_args: argparse.Namespace) -> int:
    env = os.environ.copy()
    env.setdefault("PYTHONPYCACHEPREFIX", str(ROOT / ".memory-cache" / "pycache"))
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "tools/memory_lint.py",
            "tools/memory_llm_qa.py",
            "tools/memory_workflow_qa.py",
            "tools/memory_workflow_smoke.py",
            "tools/memory_cli.py",
        ],
        cwd=ROOT,
        env=env,
        check=False,
    ).returncode


def command_diff_check(_args: argparse.Namespace) -> int:
    return run_command(["git", "diff", "--cached", "--check"]).returncode


def command_commit_language(args: argparse.Namespace) -> int:
    if args.range:
        rev_range = args.range
    elif args.base:
        base = args.base
        if not base or re.match(r"^0+$", base) or not git_success(["cat-file", "-e", f"{base}^{{commit}}"]):
            rev_range = f"{args.head}^..{args.head}" if git_success(["rev-parse", "--verify", f"{args.head}^"]) else args.head
        else:
            rev_range = f"{base}..{args.head}"
    else:
        rev_range = args.head

    result = run_command(["git", "log", "--format=%H%x00%s", "--no-merges", rev_range], capture=True)
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout.rstrip(), file=sys.stderr)
        return result.returncode

    checked = 0
    failures = []
    for line in result.stdout.splitlines():
        if "\x00" not in line:
            continue
        sha, subject = line.split("\x00", 1)
        checked += 1
        if not JAPANESE_TEXT_RE.search(subject):
            failures.append(sha[:12])

    if failures:
        print("[memory] commit-language: 日本語を含まないコミットメッセージがあります。", file=sys.stderr)
        for sha in failures:
            print(f"- {sha}", file=sys.stderr)
        return 1

    print(f"Memory commit-language 合格: {checked} 件のコミットメッセージを確認しました。")
    return 0


def command_publish(args: argparse.Namespace) -> int:
    if not ensure_not_git_operation_in_progress():
        return 1

    message = " ".join(args.message).strip() or "メモリ保管庫を更新"
    if not JAPANESE_TEXT_RE.search(message):
        print("[memory] publish: コミットメッセージは日本語で入力してください。例: `scripts/memory publish \"導入手順を更新\"`", file=sys.stderr)
        return 2
    branch = current_git_branch()
    if not branch:
        print("[memory] publish: detached HEAD では実行できません。branch を checkout してください。", file=sys.stderr)
        return 1

    if args.branch:
        print("[memory] publish: この公開テンプレートでは --branch は使いません。現在の branch を commit / push します。")
    if not args.no_wait:
        print("[memory] publish: 自動 PR / auto-merge は使いません。push 後は GitHub Actions の結果を確認してください。")

    if worktree_is_dirty():
        if run_git_step(["add", "-A"], "publish stage") != 0:
            return 1
        if not git_success(["diff", "--cached", "--quiet"]):
            if run_git_step(["commit", "-m", message], "publish commit") != 0:
                return 1
        else:
            print("[memory] publish: stage 対象の変更がありません。")
    else:
        if not git_lines(["log", "--oneline", f"origin/{branch}..{branch}"]):
            print("[memory] publish: 共有する変更がありません。")
            return 0
        print("[memory] publish: file 変更はありません。既存 commit を push します。")

    if run_git_step(["push", "-u", "origin", branch], "publish push") != 0:
        return 1

    print()
    print("[memory] publish: push 完了。GitHub Actions の結果を確認してください。")
    return 0


def branch_tracking_remote(branch: str) -> str | None:
    remote = git_output(["config", f"branch.{branch}.remote"])
    merge_ref = git_output(["config", f"branch.{branch}.merge"])
    if remote and merge_ref.startswith("refs/heads/"):
        return f"{remote}/{merge_ref.removeprefix('refs/heads/')}"
    return None


def tracking_remote_exists(branch: str) -> bool:
    tracking = branch_tracking_remote(branch)
    if tracking is None:
        return False
    return git_success(["show-ref", "--verify", f"refs/remotes/{tracking}"])


def tracking_remote_is_gone(branch: str) -> bool:
    tracking = branch_tracking_remote(branch)
    return bool(tracking and not tracking_remote_exists(branch))


def is_memory_work_branch(branch: str) -> bool:
    return branch.startswith("codex/")


def gone_memory_branches() -> list[str]:
    branches = []
    for branch in git_lines(["for-each-ref", "--format=%(refname:short)", "refs/heads"]):
        if branch == MAIN_BRANCH or not is_memory_work_branch(branch):
            continue
        if tracking_remote_is_gone(branch):
            branches.append(branch)
    return branches


def command_sync(args: argparse.Namespace) -> int:
    if not ensure_not_git_operation_in_progress():
        return 1
    if worktree_is_dirty():
        print("[memory] sync: 未保存の変更があります。先に `scripts/memory publish \"短い日本語のコミットメッセージ\"` を実行してください。", file=sys.stderr)
        return 1

    starting_branch = current_git_branch()
    if not starting_branch:
        print("[memory] sync: detached HEAD では実行できません。branch を checkout してください。", file=sys.stderr)
        return 1

    if run_git_step(["fetch", "origin", "--prune"], "sync fetch") != 0:
        return 1

    current_branch_after_fetch = current_git_branch()
    pending_branch = current_branch_after_fetch if current_branch_after_fetch != MAIN_BRANCH else ""
    pending_remote = branch_tracking_remote(pending_branch) if pending_branch else None
    pending_remote_exists = bool(pending_branch and pending_remote and tracking_remote_exists(pending_branch))
    pending_remote_gone = bool(pending_branch and tracking_remote_is_gone(pending_branch))

    if current_branch_after_fetch != MAIN_BRANCH:
        if run_git_step(["checkout", MAIN_BRANCH], "sync checkout main") != 0:
            return 1

    if run_git_step(["merge", "--ff-only", "origin/main"], "sync update main") != 0:
        return 1

    cleanup_targets = []
    if pending_branch and is_memory_work_branch(pending_branch) and pending_remote_gone:
        cleanup_targets.append(pending_branch)
    if args.prune_gone:
        for branch in gone_memory_branches():
            if branch not in cleanup_targets:
                cleanup_targets.append(branch)

    for branch in cleanup_targets:
        if run_git_step(["branch", "-D", branch], "sync delete local branch") != 0:
            return 1

    if pending_branch and pending_remote_exists:
        print(f"[memory] sync: {pending_branch} はまだ origin にあります。PR / CI / merge 待ちの可能性があります。")
    elif pending_branch and pending_remote is None:
        print(f"[memory] sync: {pending_branch} は upstream 未設定のため削除しませんでした。")
    elif cleanup_targets:
        print("[memory] sync: merge 済みまたは remote 削除済みの作業 branch を片付けました。")

    print("[memory] sync: main は最新です。")
    return 0


def read_prompt_input(args: argparse.Namespace) -> tuple[str, str]:
    text = " ".join(args.text or []).strip()
    file_text = ""
    if args.from_file:
        path = Path(args.from_file)
        if not path.is_absolute():
            path = ROOT / path
        if not path.exists() or not path.is_file():
            raise SystemExit(f"from-file not found: {args.from_file}")
        file_text = path.read_text(encoding="utf-8").strip()
    return text, file_text


def parse_month(value: str) -> tuple[int, int] | None:
    match = MONTH_RE.fullmatch(value or "")
    if not match:
        return None
    year = int(match.group(1))
    month = int(match.group(2))
    if month < 1 or month > 12:
        return None
    return year, month


def month_bounds(value: str) -> tuple[dt.date, dt.date] | None:
    parsed = parse_month(value)
    if parsed is None:
        return None
    year, month = parsed
    last_day = calendar.monthrange(year, month)[1]
    return dt.date(year, month, 1), dt.date(year, month, last_day)


def target_lines(args: argparse.Namespace) -> list[str]:
    if getattr(args, "client", None):
        return [f"- Target hint: client `{args.client}`"]
    if getattr(args, "internal", None):
        return [f"- Target hint: internal `{args.internal}`"]
    if getattr(args, "all_pending", False):
        return ["- Target hint: all pending client/internal entities."]
    if getattr(args, "unknown", False):
        return ["- Target hint: unknown; use `inbox/` unless the target is safe to identify."]
    return ["- Target hint: not specified; identify safely before updating."]


def add_entity_target(args: argparse.Namespace) -> tuple[str, str, str]:
    if getattr(args, "client", None):
        return "client", args.client, "clients"
    if getattr(args, "internal", None):
        return "internal", args.internal, "internal"
    raise AssertionError("memory-add requires --client or --internal")


def review_entity_target(args: argparse.Namespace) -> tuple[str, str, str]:
    if getattr(args, "client", None):
        return "client", args.client, "clients"
    if getattr(args, "internal", None):
        return "internal", args.internal, "internal"
    raise AssertionError("memory-review requires --client or --internal")


def command_prompt_add(args: argparse.Namespace) -> int:
    entity_type, entity_id, root_name = add_entity_target(args)
    if not ENTITY_ID_RE.fullmatch(entity_id):
        print(
            "[memory] add: entity_id は lowercase kebab-case にしてください。"
            " 例: `example-client-alpha`",
            file=sys.stderr,
        )
        return 2

    entity_root = ROOT / root_name / entity_id
    if entity_root.exists():
        print(f"[memory] add: 既に存在します: {root_name}/{entity_id}", file=sys.stderr)
        return 1

    text, file_text = read_prompt_input(args)
    lines = [
        "注意: `scripts/memory` v1 は dry-run / prompt 生成だけを行います。この command 自体は repository を更新していません。",
        "",
        "この依頼を repository 内の正本 skill に従って処理してください。",
        "",
        "Use skill: `memory-add`.",
        "",
        "Required reading:",
        "- `company/session-context.md`",
        "- `company/strategy.md`",
        "- `company/rules.md`",
        "- `.agentic/AGENT_CONTRACT.md`",
        "- `.agentic/skills/_shared/SCHEMA.md`",
        "- `.agentic/skills/_shared/GUARDRAILS.md`",
        "- `.agentic/skills/memory-add/SKILL.md`",
        "- `templates/`",
        "- Existing sample entity files with the same entity type.",
        "",
        "Routing hints:",
        f"- Entity type: {entity_type}",
        f"- Entity id: `{entity_id}`",
        f"- Display name: {args.name}",
        f"- Target root: `{root_name}/{entity_id}/`",
        "",
        "Guardrails:",
        "- Create only the lightweight entity structure from templates.",
        f"- Required files/directories: `{root_name}/{entity_id}/profile.md`, `{root_name}/{entity_id}/sources.md`, `{root_name}/{entity_id}/states/current.md`, `{root_name}/{entity_id}/events/`.",
        "- Create one initial event that records why this entity was added and any safe initial context.",
        "- If profile/current are initialized from the initial event, set that event to `derived_status: applied` and cite it from `profile.md` / `states/current.md`.",
        "- Do not create `tasks.md`, `wiki/`, `outputs/`, monthly states, `state.md`, `states/00-current.md`, or entity-local `raw/`.",
        "- Do not update `company/` or hand-write `views/`.",
        "- Keep `sources.md` as a source registry; register only explicit URLs and keep unknown sources out.",
        "- Keep Japanese natural-language content in Japanese when the input is Japanese.",
        "- Finish by running `scripts/memory lint`.",
        "",
        "User input:",
    ]
    if text:
        lines.extend(["", "```text", text, "```"])
    if file_text:
        lines.extend(["", f"Source file: `{args.from_file}`", "", "```text", file_text, "```"])
    if not text and not file_text:
        lines.append("")
        lines.append("(No additional input text was provided. Create only a minimal initial entity with safe placeholders.)")

    print("\n".join(lines))
    return 0


def command_prompt_save(args: argparse.Namespace) -> int:
    text, file_text = read_prompt_input(args)
    digest = "not specified; run memory-digest only if there is enough context"
    if args.digest is True:
        digest = "requested after saving, if the event can be safely digested"
    elif args.digest is False:
        digest = "do not run digest; save only"

    lines = [
        "注意: `scripts/memory` v1 は dry-run / prompt 生成だけを行います。この command 自体は repository を更新していません。",
        "",
        "この依頼を repository 内の正本 skill に従って処理してください。",
        "",
        "Use skill: `memory-save`.",
        "",
        "Required reading:",
        "- `company/session-context.md`",
        "- `company/strategy.md`",
        "- `company/rules.md`",
        "- `.agentic/AGENT_CONTRACT.md`",
        "- `.agentic/skills/_shared/SCHEMA.md`",
        "- `.agentic/skills/_shared/GUARDRAILS.md`",
        "- `.agentic/skills/_shared/COLLABORATION.md`",
        "- `.agentic/skills/memory-save/SKILL.md`",
        "",
        "Routing hints:",
        *target_lines(args),
        f"- Event type hint: `{args.event_type}`" if args.event_type else "- Event type hint: not specified",
        f"- Digest handling: {digest}.",
        "",
        "Guardrails:",
        "- Do not add business logic outside the skill workflow.",
        "- Known client/internal business notes become entity events, even when lightweight.",
        "- Keep the original input as a visible top-level `raw/` note and cite it from each related event.",
        "- Keep event bodies thin: do not copy the raw transcript or long memo into the event.",
        "- Event bodies should be a structured index of key facts, decisions, tasks, risks, and open questions.",
        "- If multiple clients or projects are included, split into one event per entity.",
        "- Do not copy mixed raw material into client folders; events carry the entity-specific facts.",
        "- For monthly retrospectives, use a `monthly-review` event with `event_type: review`; do not create monthly state files.",
        "- Only truly unknown business notes go to `inbox/`; do not guess a target.",
        "- Do not auto-update `company/` during normal save/digest.",
        "- If no downstream update is needed, use `derived_targets: []`.",
        "- Keep Japanese natural-language content in Japanese when the input is Japanese.",
        "",
        "User input:",
    ]
    if text:
        lines.extend(["", "```text", text, "```"])
    if file_text:
        lines.extend(["", f"Source file: `{args.from_file}`", "", "```text", file_text, "```"])
    if not text and not file_text:
        lines.append("")
        lines.append("(No input text was provided. Ask the user for the note before saving.)")

    print("\n".join(lines))
    return 0


def command_prompt_review(args: argparse.Namespace) -> int:
    entity_type, entity_id, root_name = review_entity_target(args)
    bounds = month_bounds(args.month)
    if bounds is None:
        print("[memory] review: --month は YYYY-MM 形式で指定してください。例: 2026-05", file=sys.stderr)
        return 2
    month_start, month_end = bounds
    entity_root = ROOT / root_name / entity_id
    if not entity_root.exists():
        print(f"[memory] review: entity が見つかりません: {root_name}/{entity_id}", file=sys.stderr)
        return 1

    event_path = entity_root / "events" / f"{month_end.isoformat()}_monthly-review.md"
    existing_reviews = sorted((entity_root / "events").glob(f"{args.month}-*_monthly-review.md"))
    if existing_reviews:
        print(f"[memory] review: monthly-review event は既に存在します: {rel(existing_reviews[0])}", file=sys.stderr)
        print("[memory] review: 既存 event は上書きせず、必要なら correction event として保存してください。", file=sys.stderr)
        return 1

    text, file_text = read_prompt_input(args)
    lines = [
        "注意: `scripts/memory` v1 は dry-run / prompt 生成だけを行います。この command 自体は repository を更新していません。",
        "",
        "この依頼を repository 内の正本 skill に従って処理してください。",
        "",
        "Use skill: `memory-save`.",
        "",
        "Monthly review event flow:",
        "- 月次総括は `states/YYYY-MM.md` ではなく、同一 entity の event として保存する。",
        "- repository に月次 report / output file は保存しない。クライアント提出用 draft は `memory-output` でチャット上に作る。",
        "",
        "Required reading:",
        "- `company/session-context.md`",
        "- `company/strategy.md`",
        "- `company/rules.md`",
        "- `.agentic/AGENT_CONTRACT.md`",
        "- `.agentic/skills/_shared/SCHEMA.md`",
        "- `.agentic/skills/_shared/GUARDRAILS.md`",
        "- `.agentic/skills/_shared/COLLABORATION.md`",
        "- `.agentic/skills/memory-save/SKILL.md`",
        "- `.agentic/skills/memory-digest/SKILL.md`",
        "- `templates/monthly-review-event.md`",
        f"- `{root_name}/{entity_id}/profile.md`",
        f"- `{root_name}/{entity_id}/states/current.md`",
        f"- `{root_name}/{entity_id}/sources.md`",
        f"- Same-entity events from {month_start.isoformat()} through {month_end.isoformat()} only.",
        "",
        "Routing hints:",
        f"- Entity type: {entity_type}",
        f"- Entity id: `{entity_id}`",
        f"- Month: `{args.month}`",
        "- Event type: `review`",
        f"- Target event path: `{rel(event_path)}`",
        f"- Source event date range: `{month_start.isoformat()}` to `{month_end.isoformat()}`",
        "",
        "Guardrails:",
        "- Create exactly one `monthly-review` event for the target entity unless it already exists; never overwrite an existing review event.",
        "- Use `event_type: review` and keep the event body as a concise retrospective index.",
        "- Cite reviewed same-entity events in `source_refs`; do not cite or summarize cross-client files/events.",
        "- If the user supplied new retrospective notes, preserve them as a top-level `raw/` note and cite that raw note too. If not, no raw note is required.",
        "- Body sections: `要約`, `良かったこと`, `課題`, `決定事項`, `来月へ持ち越すこと`, `長期的な学び候補`, `参照イベント`.",
        "- Carry over only still-active tasks, risks, decisions, and next actions to `states/current.md`; merge duplicates and remove/close completed or obsolete items when the source is clear.",
        "- Put only durable knowledge, constraints, and advertising-operation learnings into `profile.md`; do not paste a whole monthly diary into profile.",
        "- Use `derived_targets: []` if no profile/current update is needed. Use `derived_targets: [state]` when current/profile was updated and cite this event there.",
        "- Do not create `states/YYYY-MM.md`, `tasks.md`, `wiki/`, `outputs/`, entity-local `raw/`, or monthly report files.",
        "- Finish by running `scripts/memory lint`.",
        "",
        "User input:",
    ]
    if text:
        lines.extend(["", "```text", text, "```"])
    if file_text:
        lines.extend(["", f"Source file: `{args.from_file}`", "", "```text", file_text, "```"])
    if not text and not file_text:
        lines.append("")
        lines.append("(No additional retrospective note was provided. Build the review from same-entity events in the month.)")

    print("\n".join(lines))
    return 0


def command_prompt_digest(args: argparse.Namespace) -> int:
    lines = [
        "注意: `scripts/memory` v1 は dry-run / prompt 生成だけを行います。この command 自体は repository を更新していません。",
        "",
        "この依頼を repository 内の正本 skill に従って処理してください。",
        "",
        "Use skill: `memory-digest`.",
        "",
        "Required reading:",
        "- `company/session-context.md`",
        "- `company/strategy.md`",
        "- `company/rules.md`",
        "- `.agentic/AGENT_CONTRACT.md`",
        "- `.agentic/skills/_shared/SCHEMA.md`",
        "- `.agentic/skills/_shared/GUARDRAILS.md`",
        "- `.agentic/skills/memory-digest/SKILL.md`",
        "",
        "Routing hints:",
        *target_lines(args),
    ]
    if args.all_pending:
        lines.append("- Scope hint: find pending events across all client/internal entities.")
    lines.extend(
        [
            "",
            "Guardrails:",
            "- Digest pending client/internal events only; do not create company events.",
            "- Update only `profile.md` and `states/current.md` incrementally.",
            "- Put long-term knowledge in `profile.md`; put current status, tasks, risks, decisions, and next actions in `states/current.md`.",
            "- Treat events as thin indexes; read raw only when needed and do not copy long raw text into derived files.",
            "- Keep `states/current.md` current: merge duplicate tasks and do not accumulate completed or obsolete tasks.",
            "- Within each profile/current section, order event-derived bullets by newest source event date when practical; keep stable context and manual sections in place.",
            "- Do not create monthly state files; monthly retrospectives belong in `monthly-review` events.",
            "- Preserve manual sections and existing history.",
            "- Add source event references to important derived claims.",
            "- After downstream updates, only status metadata may change on the event.",
            "- Do not auto-update `company/` during normal digest.",
        ]
    )
    print("\n".join(lines))
    return 0


def add_status_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("status", help="Show read-only vault status")
    parser.add_argument("--json", action="store_true", help="Print JSON")
    parser.add_argument("--with-lint", action="store_true", help="Run memory_lint.py and include its summary")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero for pending events, duplicate IDs, or failed lint")
    parser.set_defaults(func=command_status)


def add_entities_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("entities", help="List known client/internal entities")
    parser.add_argument("--json", action="store_true", help="Print JSON")
    parser.set_defaults(func=command_entities)


def add_prompt_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("prompt", help="Generate agent prompts without editing files")
    prompt_subparsers = parser.add_subparsers(dest="prompt_command", required=True)

    save = prompt_subparsers.add_parser("save", help="Generate a memory-save prompt")
    add_save_arguments(save)
    save.set_defaults(func=command_prompt_save)

    add_parser = prompt_subparsers.add_parser("add", help="Generate a memory-add prompt")
    add_add_arguments(add_parser)
    add_parser.set_defaults(func=command_prompt_add)

    digest_parser = prompt_subparsers.add_parser("digest", help="Generate a memory-digest prompt")
    add_digest_arguments(digest_parser)
    digest_parser.set_defaults(func=command_prompt_digest)

    review_parser = prompt_subparsers.add_parser("review", help="Generate a monthly-review event prompt")
    add_review_arguments(review_parser)
    review_parser.set_defaults(func=command_prompt_review)


def add_save_arguments(parser: argparse.ArgumentParser) -> None:
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--client", metavar="ID", help="Client entity id")
    target.add_argument("--internal", metavar="ID", help="Internal project id")
    target.add_argument("--unknown", action="store_true", help="Route safely, usually to inbox")
    parser.add_argument("--event-type", choices=ALLOWED_EVENT_TYPES, help="Event type hint")
    digest = parser.add_mutually_exclusive_group()
    digest.add_argument("--digest", dest="digest", action="store_true", help="Request digest after save")
    digest.add_argument("--no-digest", dest="digest", action="store_false", help="Request save only")
    parser.set_defaults(digest=None)
    parser.add_argument("--from-file", metavar="PATH", help="Read note text from a file")
    parser.add_argument("text", nargs="*", help="Natural language note text")


def add_add_arguments(parser: argparse.ArgumentParser) -> None:
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--client", metavar="ID", help="New client entity id")
    target.add_argument("--internal", metavar="ID", help="New internal project id")
    parser.add_argument("--name", required=True, help="Display name to use in profile/current/source templates")
    parser.add_argument("--from-file", metavar="PATH", help="Read initial context from a file")
    parser.add_argument("text", nargs="*", help="Initial natural-language context")


def add_digest_arguments(parser: argparse.ArgumentParser) -> None:
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--client", metavar="ID", help="Client entity id")
    target.add_argument("--internal", metavar="ID", help="Internal project id")
    target.add_argument("--all-pending", action="store_true", help="Digest all pending events")


def add_review_arguments(parser: argparse.ArgumentParser) -> None:
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--client", metavar="ID", help="Client entity id")
    target.add_argument("--internal", metavar="ID", help="Internal project id")
    parser.add_argument("--month", required=True, help="Review month in YYYY-MM format")
    parser.add_argument("--from-file", metavar="PATH", help="Read retrospective note text from a file")
    parser.add_argument("text", nargs="*", help="Optional retrospective note text")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="memory",
        description="Helper CLI for the memory vault. It does not implement memory business logic.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_status_parser(subparsers)
    add_entities_parser(subparsers)
    add_prompt_parser(subparsers)

    save_parser = subparsers.add_parser("save", help="Dry-run alias for prompt save; does not edit files")
    add_save_arguments(save_parser)
    save_parser.set_defaults(func=command_prompt_save)

    add_parser = subparsers.add_parser("add", help="Dry-run alias for prompt add; does not edit files")
    add_add_arguments(add_parser)
    add_parser.set_defaults(func=command_prompt_add)

    digest_parser = subparsers.add_parser("digest", help="Dry-run alias for prompt digest; does not edit files")
    add_digest_arguments(digest_parser)
    digest_parser.set_defaults(func=command_prompt_digest)

    review_parser = subparsers.add_parser("review", help="Dry-run alias for prompt review; does not edit files")
    add_review_arguments(review_parser)
    review_parser.set_defaults(func=command_prompt_review)

    lint_parser = subparsers.add_parser("lint", help="Run memory lint")
    lint_parser.add_argument("--fix", action="store_true", help="Fix mechanical issues in staged client/internal non-event files")
    lint_parser.add_argument("--staged", action="store_true", help="Run staged-only fix and event immutability checks")
    lint_parser.set_defaults(func=command_lint)

    smoke_parser = subparsers.add_parser("smoke", help="Run memory workflow smoke")
    smoke_parser.add_argument("--keep", action="store_true", help="Keep the temporary smoke vault")
    smoke_parser.set_defaults(func=command_smoke)

    qa_parser = subparsers.add_parser("qa", help="Run local-only memory QA checks")
    qa_parser.add_argument("--keep", action="store_true", help="Keep the temporary QA vaults")
    qa_parser.set_defaults(func=command_qa)

    memory_llm_qa.add_parser(subparsers)

    publish_parser = subparsers.add_parser("publish", help="現在の branch で変更を commit して push します")
    publish_parser.add_argument("--branch", help="互換用。公開テンプレートでは使用せず、現在の branch を push します")
    publish_parser.add_argument("--no-wait", action="store_true", help="互換用。公開テンプレートでは常に待機しません")
    publish_parser.add_argument(
        "--wait-timeout",
        type=int,
        default=PUBLISH_WAIT_TIMEOUT_SECONDS,
        help=f"互換用。公開テンプレートでは自動 merge 待機を行いません (default: {PUBLISH_WAIT_TIMEOUT_SECONDS})",
    )
    publish_parser.add_argument(
        "--wait-interval",
        type=int,
        default=PUBLISH_WAIT_INTERVAL_SECONDS,
        help=f"互換用。公開テンプレートでは自動 merge 待機を行いません (default: {PUBLISH_WAIT_INTERVAL_SECONDS})",
    )
    publish_parser.add_argument("message", nargs="*", help="コミットメッセージ。日本語を使ってください。")
    publish_parser.set_defaults(func=command_publish)

    sync_parser = subparsers.add_parser("sync", help="Return to main, fetch latest changes, and clean merged work branches")
    sync_parser.add_argument(
        "--prune-gone",
        action="store_true",
        help="Also delete local codex/* branches whose origin branch no longer exists",
    )
    sync_parser.set_defaults(func=command_sync)

    privacy_parser = subparsers.add_parser("privacy-scan", help="Reject unmasked email addresses and phone numbers")
    privacy_mode = privacy_parser.add_mutually_exclusive_group()
    privacy_mode.add_argument("--staged", action="store_true", help="Scan staged text files")
    privacy_mode.add_argument("--worktree", action="store_true", help="Scan changed worktree text files")
    privacy_parser.set_defaults(func=command_privacy_scan)

    role_guard_parser = subparsers.add_parser("role-guard", help="Run memory role guard")
    role_guard_mode = role_guard_parser.add_mutually_exclusive_group()
    role_guard_mode.add_argument("--staged", action="store_true", help="Check staged changes (default)")
    role_guard_mode.add_argument("--worktree", action="store_true", help="Check worktree changes")
    role_guard_parser.add_argument("--ci", action="store_true", help="Use .memory-roles.json and check a commit range")
    role_guard_parser.add_argument(
        "--actor",
        default=os.environ.get("GITHUB_ACTOR", ""),
        help="GitHub actor for --ci mode",
    )
    role_guard_parser.add_argument("--base", help="Base commit for --ci mode")
    role_guard_parser.add_argument("--head", default="HEAD", help="Head commit for --ci mode")
    role_guard_parser.set_defaults(func=command_role_guard)

    py_compile_parser = subparsers.add_parser("py-compile", help="Compile memory Python tools")
    py_compile_parser.set_defaults(func=command_py_compile)

    diff_check_parser = subparsers.add_parser("diff-check", help="Run git diff --cached --check")
    diff_check_parser.set_defaults(func=command_diff_check)

    commit_language_parser = subparsers.add_parser("commit-language", help="コミットメッセージが日本語か確認します")
    commit_language_parser.add_argument("--range", help="Git revision range to inspect, for example BASE..HEAD")
    commit_language_parser.add_argument("--base", help="Base commit for --base/--head mode")
    commit_language_parser.add_argument("--head", default="HEAD", help="Head commit for --base/--head mode")
    commit_language_parser.set_defaults(func=command_commit_language)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except BrokenPipeError:
        return 1


if __name__ == "__main__":
    sys.exit(main())
