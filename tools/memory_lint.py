#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

# Legacy events may still contain tasks/entity_wiki in derived_targets, but new
# events use only the active target below.
ALLOWED_DERIVED_TARGETS = {"state", "tasks", "entity_wiki"}
ACTIVE_DERIVED_TARGETS = {"state"}
ALLOWED_SOURCE_TYPES = {"drive_folder", "drive_file", "spreadsheet", "document", "slide", "form", "other"}
ALLOWED_SOURCE_CONTEXT = {"yes", "no", "on_demand"}
ALLOWED_RAW_SCOPES = {"single_entity", "multi_entity", "unknown"}
RAW_ENTITY_REF_RE = re.compile(r"^(client|internal)/[A-Za-z0-9._-]+$")
SOURCE_TABLE_HEADER = "| 名称 | 種別 | URL | context | 備考 |"
MANUAL_START = "<!-- BEGIN MANUAL -->"
MANUAL_END = "<!-- END MANUAL -->"
MANUAL_HEADINGS = ("## Manual Notes", "## Do Not Share", "## 手動メモ", "## 共有しないメモ")
REQUIRED_DATAVIEW_VIEWS = {
    "views/updates.md": ("```dataview", "updated_at", "update_summary", "file.link", "update_source", "inbox"),
    "views/tasks.md": ("```dataview", "TASK"),
}
REQUIRED_COMPANY_CONTEXT_FILES = [
    "README.md",
    "session-context.md",
    "strategy.md",
    "rules.md",
]
REQUIRED_UPDATE_KEYS = [
    "updated_at",
    "update_summary",
    "update_source",
    "update_history",
]
TRACKED_UPDATE_PATTERNS = [
    "clients/**/*.md",
    "internal/**/*.md",
    "company/**/*.md",
    "raw/**/*.md",
    "inbox/**/*.md",
]

REQUIRED_EVENT_KEYS = [
    "type",
    "event_id",
    "event_date",
    "created_at",
    "author",
    "entity_type",
    "entity_id",
    "event_type",
    "derived_status",
    "derived_targets",
    "source_refs",
]

REQUIRED_SOURCE_INDEX_KEYS = [
    "type",
    "entity_type",
    "entity_id",
    "auto_generated",
    "owner",
]

REQUIRED_RAW_NOTE_KEYS = [
    "type",
    "raw_id",
    "scope",
    "entity_refs",
]

EVENT_MUTABLE_KEYS = {"derived_status"}

ALLOWED = {
    "entity_type": {"client", "internal"},
    "event_type": {"meeting", "note", "decision", "request", "proposal", "task", "risk", "source", "review"},
    "audience": {"internal", "client"},
    "share_status": {"internal", "draft"},
    "derived_status": {"pending", "applied"},
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def run_git(args: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def git_output(args: list[str]) -> str:
    result = run_git(args)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def git_lines(args: list[str]) -> list[str]:
    return [line for line in git_output(args).splitlines() if line.strip()]


def has_git_repo() -> bool:
    return run_git(["rev-parse", "--is-inside-work-tree"]).returncode == 0


def staged_paths() -> set[str]:
    if not has_git_repo():
        return set()
    return set(git_lines(["diff", "--name-only", "--cached"]))


def split_frontmatter_text(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    block = text[4:end].splitlines()
    body = text[end + len("\n---") :]
    if body.startswith("\n"):
        body = body[1:]
    data = {}
    current_key = None
    for line in block:
        if not line.strip():
            continue
        if line.startswith("  - ") and current_key:
            if not isinstance(data.get(current_key), list):
                data[current_key] = []
            data[current_key].append(line[4:].strip())
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            key, value = match.groups()
            current_key = key
            value = value.strip()
            if value == "[]":
                data[key] = []
            elif value == "":
                data[key] = ""
            else:
                data[key] = value.strip('"')
    return data, body


def split_frontmatter(path: Path) -> tuple[dict, str]:
    return split_frontmatter_text(path.read_text(encoding="utf-8"))


def parse_frontmatter(path: Path) -> dict:
    return split_frontmatter(path)[0]


def event_paths() -> list[Path]:
    paths = []
    for pattern in [
        "clients/*/events/*.md",
        "internal/*/events/*.md",
    ]:
        paths.extend(ROOT.glob(pattern))
    return sorted(paths)


def source_index_paths() -> list[Path]:
    paths = []
    for pattern in [
        "clients/*/sources.md",
        "internal/*/sources.md",
    ]:
        paths.extend(ROOT.glob(pattern))
    return sorted(paths)


def raw_note_paths() -> list[Path]:
    raw_root = ROOT / "raw"
    if not raw_root.exists():
        return []
    return sorted(path for path in raw_root.glob("**/*.md") if path.name != "README.md")


def update_tracked_paths() -> list[Path]:
    paths = set()
    for pattern in TRACKED_UPDATE_PATTERNS:
        paths.update(path for path in ROOT.glob(pattern) if path.is_file())
    return sorted(paths)


def expected_entity_from_path(path: Path) -> tuple[str | None, str | None]:
    parts = path.relative_to(ROOT).parts
    if len(parts) >= 4 and parts[0] == "clients" and parts[2] == "events":
        return "client", parts[1]
    if len(parts) >= 4 and parts[0] == "internal" and parts[2] == "events":
        return "internal", parts[1]
    return None, None


def expected_source_index_entity_from_path(path: Path) -> tuple[str | None, str | None]:
    parts = path.relative_to(ROOT).parts
    if len(parts) == 3 and parts[0] == "clients" and parts[2] == "sources.md":
        return "client", parts[1]
    if len(parts) == 3 and parts[0] == "internal" and parts[2] == "sources.md":
        return "internal", parts[1]
    return None, None


def entity_root(entity_type: str, entity_id: str) -> Path | None:
    if entity_type == "client":
        return ROOT / "clients" / entity_id
    if entity_type == "internal":
        return ROOT / "internal" / entity_id
    if entity_type == "company":
        return ROOT / "company"
    return None


def path_parts(path: Path) -> tuple[str, ...]:
    return path.relative_to(ROOT).parts


def client_id_from_path(path: Path) -> str | None:
    parts = path_parts(path)
    if len(parts) >= 2 and parts[0] == "clients":
        return parts[1]
    return None


def internal_id_from_path(path: Path) -> str | None:
    parts = path_parts(path)
    if len(parts) >= 2 and parts[0] == "internal":
        return parts[1]
    return None


def is_client_event_path(path: Path) -> bool:
    parts = path_parts(path)
    return len(parts) >= 4 and parts[0] == "clients" and parts[2] == "events" and path.suffix == ".md"


def is_raw_note_path(path: Path) -> bool:
    try:
        parts = path_parts(path)
    except ValueError:
        return False
    return len(parts) >= 2 and parts[0] == "raw" and path.suffix == ".md" and path.name != "README.md"


def is_client_manual_editable_path(path: Path) -> bool:
    try:
        parts = path_parts(path)
    except ValueError:
        return False
    if len(parts) < 3 or parts[0] != "clients" or path.suffix != ".md":
        return False
    if parts[2] == "events":
        return False
    if len(parts) == 3 and parts[2] in {"profile.md", "sources.md"}:
        return True
    if len(parts) == 4 and parts[2] == "states" and parts[3] == "current.md":
        return True
    return False


def is_internal_manual_editable_path(path: Path) -> bool:
    try:
        parts = path_parts(path)
    except ValueError:
        return False
    if len(parts) < 3 or parts[0] != "internal" or path.suffix != ".md":
        return False
    if parts[2] == "events":
        return False
    if len(parts) == 3 and parts[2] in {"profile.md", "sources.md"}:
        return True
    if len(parts) == 4 and parts[2] == "states" and parts[3] == "current.md":
        return True
    return False


def is_client_manual_source_path(path: Path) -> bool:
    try:
        parts = path_parts(path)
    except ValueError:
        return False
    if len(parts) < 3 or parts[0] != "clients" or path.suffix != ".md":
        return False
    if len(parts) == 3 and parts[2] in {"profile.md", "sources.md"}:
        return True
    if len(parts) == 4 and parts[2] == "states" and parts[3] == "current.md":
        return True
    return False


def event_tokens(event: dict) -> list[str]:
    path = event["path"]
    fm = event["frontmatter"]
    tokens = [
        fm.get("event_id", ""),
        rel(path),
        rel(path).removesuffix(".md"),
    ]
    return [token for token in tokens if token]


def wikilink_targets(text: str) -> list[str]:
    targets = []
    for match in re.finditer(r"\[\[([^\]]+)\]\]", text):
        target = match.group(1).split("|", 1)[0].split("#", 1)[0].strip()
        if target:
            targets.append(target)
    return targets


def source_ref_values(fm: dict) -> list[str]:
    refs = fm.get("source_refs", [])
    if refs in (None, "", []):
        return []
    if isinstance(refs, str):
        return [refs]
    if isinstance(refs, list):
        return [str(ref).strip() for ref in refs if str(ref).strip()]
    return []


def strip_ref_markup(ref: str) -> str:
    value = ref.strip().strip('"').strip("'")
    if value.startswith("[[") and value.endswith("]]"):
        value = value[2:-2]
    return value.split("|", 1)[0].split("#", 1)[0].strip()


def resolve_wikilink_target(target: str, current_path: Path) -> Path | None:
    if re.match(r"^[a-z]+://", target):
        return None
    target_path = Path(target)
    if target_path.suffix != ".md":
        target_path = target_path.with_suffix(".md")
    candidates = [
        current_path.parent / target_path,
        ROOT / target_path,
    ]
    for candidate in candidates:
        try:
            resolved = candidate.resolve().relative_to(ROOT.resolve())
        except ValueError:
            continue
        path = ROOT / resolved
        if path.exists():
            return path
    return None


def resolve_reference_target(ref: str, current_path: Path) -> Path | None:
    target = strip_ref_markup(ref)
    if not target or re.match(r"^[a-z]+://", target):
        return None
    target_path = Path(target)
    if target_path.suffix != ".md":
        target_path = target_path.with_suffix(".md")
    candidates = [
        current_path.parent / target_path,
        ROOT / target_path,
    ]
    for candidate in candidates:
        try:
            resolved = candidate.resolve().relative_to(ROOT.resolve())
        except ValueError:
            continue
        path = ROOT / resolved
        if path.exists():
            return path
    return None


def referenced_paths(text: str, current_path: Path) -> list[Path]:
    paths = []
    seen = set()
    for target in wikilink_targets(text):
        resolved = resolve_wikilink_target(target, current_path)
        if resolved is None:
            continue
        key = resolved.resolve()
        if key not in seen:
            paths.append(resolved)
            seen.add(key)
    return paths


def text_mentions_event(text: str, event: dict) -> bool:
    return any(token in text for token in event_tokens(event))


def referenced_events(text: str, events: list[dict], current_path: Path | None = None) -> list[dict]:
    refs = [event for event in events if text_mentions_event(text, event)]
    if current_path is None:
        return refs

    events_by_path = {event["path"].resolve(): event for event in events}
    seen = {event["path"].resolve() for event in refs}
    for target in wikilink_targets(text):
        resolved = resolve_wikilink_target(target, current_path)
        if resolved is None:
            continue
        event = events_by_path.get(resolved.resolve())
        if event and event["path"].resolve() not in seen:
            refs.append(event)
            seen.add(event["path"].resolve())
    return refs


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def check_events(findings: list[str]) -> list[dict]:
    events = []
    event_ids = {}
    for path in event_paths():
        fm, body = split_frontmatter(path)
        if not fm:
            findings.append(f"{rel(path)}: frontmatter がありません")
            continue
        missing = [key for key in REQUIRED_EVENT_KEYS if key not in fm or fm[key] == ""]
        if missing:
            findings.append(f"{rel(path)}: 必須キーがありません: {', '.join(missing)}")
        if fm.get("type") != "event":
            findings.append(f"{rel(path)}: type は event にしてください")
        for key, allowed in ALLOWED.items():
            value = fm.get(key)
            if value and value not in allowed:
                findings.append(f"{rel(path)}: 不正な {key}: {value}")

        expected_type, expected_id = expected_entity_from_path(path)
        if expected_type and fm.get("entity_type") != expected_type:
            findings.append(
                f"{rel(path)}: entity_type {fm.get('entity_type')} が path の entity_type {expected_type} と一致しません"
            )
        if expected_id and fm.get("entity_id") != expected_id:
            findings.append(
                f"{rel(path)}: entity_id {fm.get('entity_id')} が path の entity_id {expected_id} と一致しません"
            )

        event_id = fm.get("event_id")
        if event_id:
            if event_id in event_ids:
                findings.append(f"{rel(path)}: event_id が重複しています。使用済み: {rel(event_ids[event_id])}")
            event_ids[event_id] = path

        targets = fm.get("derived_targets")
        if not isinstance(targets, list):
            findings.append(f"{rel(path)}: derived_targets は YAML list にしてください")
        else:
            invalid_targets = [target for target in targets if target not in ALLOWED_DERIVED_TARGETS]
            if invalid_targets:
                findings.append(f"{rel(path)}: 不正な derived_targets: {', '.join(invalid_targets)}")
        events.append({"path": path, "frontmatter": fm, "body": body})
    return events


def check_pending_events(events: list[dict], findings: list[str]) -> None:
    for event in events:
        fm = event["frontmatter"]
        if fm.get("derived_status") == "pending":
            findings.append(f"{rel(event['path'])}: pending event です。memory-digest で反映してから lint を通してください")


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def check_source_indexes(findings: list[str]) -> None:
    for path in source_index_paths():
        fm, body = split_frontmatter(path)
        if not fm:
            findings.append(f"{rel(path)}: sources frontmatter がありません")
            continue

        missing = [key for key in REQUIRED_SOURCE_INDEX_KEYS if key not in fm or fm[key] == ""]
        if missing:
            findings.append(f"{rel(path)}: sources 必須キーがありません: {', '.join(missing)}")
        if fm.get("type") != "source_index":
            findings.append(f"{rel(path)}: type は source_index にしてください")
        if fm.get("auto_generated") == "true":
            findings.append(f"{rel(path)}: sources.md は人間が管理するため auto_generated にしないでください")

        expected_type, expected_id = expected_source_index_entity_from_path(path)
        if expected_type and fm.get("entity_type") != expected_type:
            findings.append(
                f"{rel(path)}: sources entity_type {fm.get('entity_type')} が path の entity_type {expected_type} と一致しません"
            )
        if expected_id and fm.get("entity_id") != expected_id:
            findings.append(
                f"{rel(path)}: sources entity_id {fm.get('entity_id')} が path の entity_id {expected_id} と一致しません"
            )

        if SOURCE_TABLE_HEADER not in body:
            findings.append(f"{rel(path)}: sources table header がありません: {SOURCE_TABLE_HEADER}")

        for line in body.splitlines():
            if not line.strip().startswith("|"):
                continue
            if line.strip() == SOURCE_TABLE_HEADER or re.match(r"^\|\s*-+\s*\|", line):
                continue
            cells = split_table_row(line)
            if len(cells) != 5:
                findings.append(f"{rel(path)}: sources table は 5 列にしてください: {line.strip()}")
                continue
            name, source_type, url, context, _notes = cells
            if not name:
                findings.append(f"{rel(path)}: source 名称が空です")
            if source_type not in ALLOWED_SOURCE_TYPES:
                findings.append(f"{rel(path)}: 不正な source 種別です: {source_type}")
            if context not in ALLOWED_SOURCE_CONTEXT:
                findings.append(f"{rel(path)}: context は yes/no/on_demand のいずれかにしてください: {context}")
            if url and url not in {"-", "_未登録_"} and not url.startswith("https://"):
                findings.append(f"{rel(path)}: source URL は https:// から始めてください: {url}")


def check_raw_notes(findings: list[str]) -> None:
    if not (ROOT / "raw").is_dir():
        findings.append("raw: raw/ がありません")
        return
    raw_ids = {}
    for path in raw_note_paths():
        fm, _body = split_frontmatter(path)
        if not fm:
            findings.append(f"{rel(path)}: raw note frontmatter がありません")
            continue
        missing = [key for key in REQUIRED_RAW_NOTE_KEYS if key not in fm or fm[key] == ""]
        if missing:
            findings.append(f"{rel(path)}: raw note 必須キーがありません: {', '.join(missing)}")
        if fm.get("type") != "raw_note":
            findings.append(f"{rel(path)}: type は raw_note にしてください")
        raw_id = fm.get("raw_id")
        if raw_id:
            if raw_id in raw_ids:
                findings.append(f"{rel(path)}: raw_id が重複しています。使用済み: {rel(raw_ids[raw_id])}")
            raw_ids[raw_id] = path
        scope = fm.get("scope")
        if scope and scope not in ALLOWED_RAW_SCOPES:
            findings.append(f"{rel(path)}: raw scope は single_entity / multi_entity / unknown のいずれかにしてください: {scope}")
        entity_refs = fm.get("entity_refs")
        if "entity_refs" in fm and not isinstance(entity_refs, list):
            findings.append(f"{rel(path)}: entity_refs は YAML list にしてください")
            continue
        refs = entity_refs if isinstance(entity_refs, list) else []
        if scope == "single_entity" and len(refs) != 1:
            findings.append(f"{rel(path)}: scope: single_entity の raw note は entity_refs を 1 件にしてください")
        if scope == "multi_entity" and len(refs) < 2:
            findings.append(f"{rel(path)}: scope: multi_entity の raw note は entity_refs を 2 件以上にしてください")
        for ref_value in refs:
            if not RAW_ENTITY_REF_RE.match(str(ref_value)):
                findings.append(f"{rel(path)}: entity_refs は client/{{id}} または internal/{{id}} 形式にしてください: {ref_value}")


def check_entities(findings: list[str]) -> None:
    for client in sorted((ROOT / "clients").glob("*")):
        if not client.is_dir():
            continue
        required = [
            "profile.md",
            "sources.md",
            "states/current.md",
        ]
        for item in required:
            if not (client / item).exists():
                findings.append(f"{rel(client)}: {item} がありません")
        current_state = client / "states" / "current.md"
        if current_state.exists() and parse_frontmatter(current_state).get("type") != "entity_state":
            findings.append(f"{rel(current_state)}: type は entity_state にしてください")

    for project in sorted((ROOT / "internal").glob("*")):
        if not project.is_dir():
            continue
        required = [
            "profile.md",
            "sources.md",
            "states/current.md",
        ]
        for item in required:
            if not (project / item).exists():
                findings.append(f"{rel(project)}: {item} がありません")
        current_state = project / "states" / "current.md"
        if current_state.exists() and parse_frontmatter(current_state).get("type") != "entity_state":
            findings.append(f"{rel(current_state)}: type は entity_state にしてください")


def check_retired_entity_paths(findings: list[str]) -> None:
    retired = []
    for pattern in [
        "clients/*/tasks.md",
        "internal/*/tasks.md",
        "clients/*/outputs",
        "internal/*/outputs",
        "clients/*/wiki",
        "internal/*/wiki",
        "clients/*/states/00-current.md",
        "clients/*/states/20??-??.md",
        "internal/*/state.md",
    ]:
        retired.extend(ROOT.glob(pattern))
    for path in sorted(set(retired)):
        findings.append(
            f"{rel(path)}: lite 構成では使いません。profile.md / sources.md / states/current.md / events/ に集約してください"
        )


def check_company_context(findings: list[str]) -> None:
    company = ROOT / "company"
    allowed_paths = {Path(item) for item in REQUIRED_COMPANY_CONTEXT_FILES}
    for item in REQUIRED_COMPANY_CONTEXT_FILES:
        path = company / item
        if not path.exists():
            findings.append(f"company: {item} がありません")
            continue
        fm = parse_frontmatter(path)
        if fm.get("owner") != "management":
            findings.append(f"{rel(path)}: owner は management にしてください")
        if fm.get("auto_generated") == "true":
            findings.append(f"{rel(path)}: company context は auto_generated にしないでください")

    for path in sorted(company.rglob("*.md")):
        relative = path.relative_to(company)
        if relative not in allowed_paths:
            findings.append(f"{rel(path)}: company 配下の不要な file です。README.md、session-context.md、strategy.md、rules.md のみにしてください")
            continue
        fm = parse_frontmatter(path)
        if not fm:
            continue
        if fm.get("owner") != "management":
            findings.append(f"{rel(path)}: company 配下の管理ファイルは owner を management にしてください")
        if fm.get("auto_generated") == "true":
            findings.append(f"{rel(path)}: company 配下の管理ファイルは auto_generated にしないでください")


def check_dataview_views(findings: list[str]) -> None:
    for rel_path, required_tokens in REQUIRED_DATAVIEW_VIEWS.items():
        path = ROOT / rel_path
        if not path.exists():
            findings.append(f"{rel_path}: Dataview view がありません")
            continue
        text = path.read_text(encoding="utf-8")
        for token in required_tokens:
            if token not in text:
                findings.append(f"{rel_path}: Dataview view に必要な token がありません: {token}")


def check_update_metadata(findings: list[str]) -> None:
    for path in update_tracked_paths():
        fm = parse_frontmatter(path)
        if not fm:
            findings.append(f"{rel(path)}: 更新メタデータ用 frontmatter がありません")
            continue
        missing = [key for key in REQUIRED_UPDATE_KEYS if key not in fm or fm[key] == ""]
        if missing:
            findings.append(f"{rel(path)}: 更新メタデータが不足しています: {', '.join(missing)}")
        if "updated_at" in fm and fm.get("updated_at") and not re.match(r"^\d{4}-\d{2}-\d{2}", fm["updated_at"]):
            findings.append(f"{rel(path)}: updated_at は YYYY-MM-DD 形式にしてください")
        history = fm.get("update_history")
        if "update_history" in fm and (not isinstance(history, list) or not history):
            findings.append(f"{rel(path)}: update_history は 1 件以上の YAML list にしてください")


def target_paths_for_event_target(event: dict, target: str) -> list[Path]:
    fm = event["frontmatter"]
    root = entity_root(fm.get("entity_type", ""), fm.get("entity_id", ""))
    if root is None:
        return []
    if target == "state":
        return [root / "states" / "current.md"]
    return []


def check_applied_target_evidence(events: list[dict], findings: list[str]) -> None:
    for event in events:
        fm = event["frontmatter"]
        if fm.get("derived_status") != "applied":
            continue
        targets = fm.get("derived_targets")
        if not isinstance(targets, list):
            continue
        for target in targets:
            if target not in ACTIVE_DERIVED_TARGETS:
                continue
            paths = target_paths_for_event_target(event, target)
            if not paths:
                findings.append(f"{rel(event['path'])}: target {target} の派生ファイルが見つかりません")
                continue
            found = False
            for path in paths:
                if not path.exists():
                    continue
                text = path.read_text(encoding="utf-8")
                if event in referenced_events(text, [event], path):
                    found = True
                    break
            if not found:
                findings.append(
                    f"{rel(event['path'])}: derived target {target} は applied ですが、source reference が見つかりません"
                )


def check_entity_source_boundaries(events: list[dict], findings: list[str]) -> None:
    scoped_patterns = [
        ("client", "clients/*", ["profile.md", "sources.md", "states/current.md"]),
        ("internal", "internal/*", ["profile.md", "sources.md", "states/current.md"]),
    ]
    for entity_type, entity_glob, file_patterns in scoped_patterns:
        for root in sorted(ROOT.glob(entity_glob)):
            if not root.is_dir():
                continue
            entity_id = root.name
            paths = []
            for pattern in file_patterns:
                paths.extend(root.glob(pattern))
            for path in paths:
                text = path.read_text(encoding="utf-8")
                for event in referenced_events(text, events, path):
                    fm = event["frontmatter"]
                    if fm.get("entity_type") == "company":
                        continue
                    if fm.get("entity_type") != entity_type or fm.get("entity_id") != entity_id:
                        findings.append(
                            f"{rel(path)}: 別 entity の event を参照しています: {fm.get('entity_type')}/{fm.get('entity_id')}: {rel(event['path'])}"
                        )


def check_entity_file_reference_boundaries(findings: list[str]) -> None:
    scoped_patterns = [
        ("client", "clients/*", ["profile.md", "sources.md", "states/current.md"]),
        ("internal", "internal/*", ["profile.md", "sources.md", "states/current.md"]),
    ]
    for entity_type, entity_glob, file_patterns in scoped_patterns:
        for root in sorted(ROOT.glob(entity_glob)):
            if not root.is_dir():
                continue
            entity_id = root.name
            paths = []
            for pattern in file_patterns:
                paths.extend(root.glob(pattern))
            for path in paths:
                text = path.read_text(encoding="utf-8")
                for resolved in referenced_paths(text, path):
                    if is_raw_note_path(resolved):
                        findings.append(
                            f"{rel(path)}: raw note を直接参照しています: {rel(resolved)}。raw は event の source_refs から参照してください"
                        )
                        continue
                    client_id = client_id_from_path(resolved)
                    internal_id = internal_id_from_path(resolved)
                    if entity_type == "client":
                        if client_id and client_id != entity_id:
                            findings.append(f"{rel(path)}: 別 client の file を参照しています: {rel(resolved)}")
                        if internal_id:
                            findings.append(f"{rel(path)}: client file が internal project を参照しています: {rel(resolved)}")
                    elif entity_type == "internal":
                        if internal_id and internal_id != entity_id:
                            findings.append(f"{rel(path)}: 別 internal project の file を参照しています: {rel(resolved)}")
                        if client_id:
                            findings.append(f"{rel(path)}: internal project file が client を参照しています: {rel(resolved)}")


def check_manual_markers(findings: list[str]) -> None:
    for path in sorted(ROOT.glob("**/*.md")):
        if ".git" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if not any(heading in text for heading in MANUAL_HEADINGS):
            continue
        start = text.find(MANUAL_START)
        end = text.find(MANUAL_END)
        if start == -1 or end == -1:
            findings.append(f"{rel(path)}: 手動セクションに BEGIN/END marker がありません")
        elif start > end:
            findings.append(f"{rel(path)}: 手動セクション marker の順序が逆です")


def format_frontmatter_value(key: str, value: object) -> list[str]:
    if isinstance(value, list):
        if not value:
            return [f"{key}: []"]
        lines = [f"{key}:"]
        lines.extend(f"  - {item}" for item in value)
        return lines
    return [f"{key}: {value}"]


def frontmatter_key_order(text: str) -> list[str]:
    if not text.startswith("---\n"):
        return []
    end = text.find("\n---", 4)
    if end == -1:
        return []
    order = []
    for line in text[4:end].splitlines():
        match = re.match(r"^([A-Za-z0-9_-]+):", line)
        if match and match.group(1) not in order:
            order.append(match.group(1))
    return order


def write_frontmatter(path: Path, fm: dict, body: str, order: list[str]) -> None:
    preferred = [
        "type",
        "raw_id",
        "scope",
        "entity_refs",
        "entity_type",
        "entity_id",
        "month",
        "output_type",
        "audience",
        "share_status",
        "auto_generated",
        "owner",
        "updated_at",
        "update_summary",
        "update_source",
        "update_history",
    ]
    keys = []
    for key in preferred + order + sorted(fm):
        if key in fm and key not in keys:
            keys.append(key)
    lines = ["---"]
    for key in keys:
        lines.extend(format_frontmatter_value(key, fm[key]))
    lines.append("---")
    lines.append("")
    path.write_text("\n".join(lines) + body.lstrip("\n"), encoding="utf-8")


def inferred_client_defaults(path: Path) -> dict:
    today = dt.date.today().isoformat()
    client_id = client_id_from_path(path) or ""
    defaults = {
        "entity_type": "client",
        "entity_id": client_id,
        "updated_at": today,
        "update_summary": "手動編集を反映。",
        "update_source": [],
        "update_history": [f"{today} 手動編集を反映。"],
    }
    parts = path_parts(path)
    leaf = parts[-1]
    section = parts[2] if len(parts) >= 3 else ""
    if len(parts) == 3 and leaf == "profile.md":
        defaults.update({"type": "client_profile", "auto_generated": "false", "owner": "human"})
    elif len(parts) == 3 and leaf == "sources.md":
        defaults.update({"type": "source_index", "auto_generated": "false", "owner": "human"})
    elif section == "states" and leaf == "current.md":
        defaults.update({"type": "entity_state", "auto_generated": "true", "owner": "memory-digest"})
    return defaults


def inferred_internal_defaults(path: Path) -> dict:
    today = dt.date.today().isoformat()
    internal_id = internal_id_from_path(path) or ""
    defaults = {
        "entity_type": "internal",
        "entity_id": internal_id,
        "updated_at": today,
        "update_summary": "手動編集を反映。",
        "update_source": [],
        "update_history": [f"{today} 手動編集を反映。"],
    }
    parts = path_parts(path)
    leaf = parts[-1]
    section = parts[2] if len(parts) >= 3 else ""
    if len(parts) == 3 and leaf == "profile.md":
        defaults.update({"type": "internal_profile", "auto_generated": "false", "owner": "human"})
    elif len(parts) == 3 and leaf == "sources.md":
        defaults.update({"type": "source_index", "auto_generated": "false", "owner": "human"})
    elif section == "states" and leaf == "current.md":
        defaults.update({"type": "entity_state", "auto_generated": "true", "owner": "memory-digest"})
    return defaults


def inferred_raw_defaults(path: Path) -> dict:
    today = dt.date.today().isoformat()
    return {
        "type": "raw_note",
        "raw_id": path.stem,
        "scope": "unknown",
        "entity_refs": [],
        "updated_at": today,
        "update_summary": "raw 原本を保存。",
        "update_source": [],
        "update_history": [f"{today} raw 原本を保存。"],
    }


def needs_value(value: object) -> bool:
    return value in (None, "", [])


def ensure_frontmatter_defaults(path: Path, defaults: dict) -> bool:
    text = path.read_text(encoding="utf-8")
    fm, body = split_frontmatter_text(text)
    order = frontmatter_key_order(text)
    changed = False
    for key, value in defaults.items():
        if key not in fm or needs_value(fm.get(key)):
            fm[key] = value
            if key not in order:
                order.append(key)
            changed = True
    if changed or not text.startswith("---\n"):
        write_frontmatter(path, fm, body, order)
    return changed or not text.startswith("---\n")


def ensure_manual_markers(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if MANUAL_START in text and MANUAL_END in text:
        return False
    for heading in MANUAL_HEADINGS:
        index = text.find(heading)
        if index == -1:
            continue
        line_end = text.find("\n", index)
        insert_at = len(text) if line_end == -1 else line_end + 1
        insert = "\n<!-- BEGIN MANUAL -->\n<!-- END MANUAL -->\n"
        path.write_text(text[:insert_at] + insert + text[insert_at:], encoding="utf-8")
        return True
    return False


def apply_staged_fixes() -> None:
    fixed = []
    for rel_path in sorted(staged_paths()):
        path = ROOT / rel_path
        if not path.exists():
            continue
        if is_client_manual_editable_path(path):
            defaults = inferred_client_defaults(path)
        elif is_internal_manual_editable_path(path):
            defaults = inferred_internal_defaults(path)
        elif is_raw_note_path(path):
            defaults = inferred_raw_defaults(path)
        else:
            continue
        changed = ensure_frontmatter_defaults(path, defaults)
        changed = ensure_manual_markers(path) or changed
        if changed:
            fixed.append(rel_path)
    for rel_path in fixed:
        run_git(["add", rel_path])
    if fixed:
        print("[memory] lint --fix: staged manual files を補正しました:")
        for rel_path in fixed:
            print(f"- {rel_path}")


def staged_event_paths_for_immutability() -> list[tuple[str, str]]:
    paths = []
    for line in git_lines(["diff", "--cached", "--name-status"]):
        fields = line.split("\t")
        if len(fields) < 2:
            continue
        status = fields[0]
        for path in fields[1:]:
            if re.match(r"^clients/[^/]+/events/.*\.md$", path) or re.match(r"^internal/[^/]+/events/.*\.md$", path):
                paths.append((status, path))
    return paths


def check_event_immutability(findings: list[str]) -> None:
    if not has_git_repo():
        return
    for status, rel_path in staged_event_paths_for_immutability():
        if status.startswith("A"):
            continue
        if status.startswith("D") or status.startswith("R"):
            findings.append(f"{rel_path}: 既存 event の削除・移動は禁止です。訂正は correction event を追加してください")
            continue

        old_result = run_git(["show", f"HEAD:{rel_path}"])
        new_result = run_git(["show", f":{rel_path}"])
        if old_result.returncode != 0 or new_result.returncode != 0:
            continue
        old_fm, old_body = split_frontmatter_text(old_result.stdout)
        new_fm, new_body = split_frontmatter_text(new_result.stdout)
        if old_body != new_body:
            findings.append(f"{rel_path}: 既存 event 本文の変更は禁止です。訂正は correction event を追加してください")
        for key in sorted(set(old_fm) | set(new_fm)):
            if key in EVENT_MUTABLE_KEYS:
                continue
            if old_fm.get(key) != new_fm.get(key):
                findings.append(f"{rel_path}: 既存 event の immutable frontmatter を変更しています: {key}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the memory vault.")
    parser.add_argument("--fix", action="store_true", help="Fix mechanical issues in staged client/internal non-event files and raw notes")
    parser.add_argument("--staged", action="store_true", help="Limit fix scope and event immutability checks to staged files")
    args = parser.parse_args(argv)

    if args.fix and not args.staged:
        print("Memory lint --fix は --staged と一緒に使ってください", file=sys.stderr)
        return 2

    if args.fix:
        apply_staged_fixes()

    if args.staged:
        findings = []
        check_event_immutability(findings)
        if findings:
            print("Memory lint で問題が見つかりました:")
            for item in findings:
                print(f"- {item}")
            return 1
        print("Memory lint staged 合格: staged fixes と event immutability を確認しました。")
        return 0

    findings = []
    events = check_events(findings)
    check_pending_events(events, findings)
    check_entities(findings)
    check_retired_entity_paths(findings)
    check_company_context(findings)
    check_dataview_views(findings)
    check_update_metadata(findings)
    check_source_indexes(findings)
    check_raw_notes(findings)
    check_applied_target_evidence(events, findings)
    check_entity_source_boundaries(events, findings)
    check_entity_file_reference_boundaries(findings)
    check_manual_markers(findings)

    if findings:
        print("Memory lint で問題が見つかりました:")
        for item in findings:
            print(f"- {item}")
        return 1

    print(f"Memory lint 合格: {len(events)} 件のイベントを確認しました。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
