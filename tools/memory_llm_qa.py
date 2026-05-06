#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

import memory_lint
import memory_workflow_smoke as smoke


PRIMARY_CLIENT = smoke.PRIMARY_CLIENT
SECONDARY_CLIENT = smoke.SECONDARY_CLIENT
INTERNAL_PROJECT = smoke.INTERNAL_PROJECT

SINGLE_MARKER = "LLMQA-A1-FORM"
MULTI_ALPHA_MARKER = "LLMQA-MULTI-ALPHA"
MULTI_BETA_MARKER = "LLMQA-MULTI-BETA"
MULTI_INTERNAL_MARKER = "LLMQA-MULTI-INTERNAL"
UNKNOWN_MARKER = "LLMQA-UNKNOWN-INBOX"
MANUAL_MARKER = "LLMQA-MANUAL-CURRENT"
MANUAL_PROFILE_MARKER = "LLMQA-MANUAL-PROFILE"
INTERNAL_SINGLE_MARKER = "LLMQA-INTERNAL-SINGLE"
SOURCE_MARKER = "LLMQA-SOURCE-REGISTER"
CORRECTION_MARKER = "LLMQA-CORRECTION-EVENT"
NO_DIGEST_MARKER = "LLMQA-NO-DIGEST"
MONTHLY_REVIEW_MARKER = "LLMQA-MONTHLY-REVIEW"
ADD_CLIENT_ID = "llmqa-new-client"
ADD_INTERNAL_ID = "llmqa-new-internal"
ADD_CLIENT_MARKER = "LLMQA-ADD-CLIENT"
ADD_INTERNAL_MARKER = "LLMQA-ADD-INTERNAL"
THIN_EVENT_MAX_CHARS = 2400

IGNORED_CHECK_PARTS = {".git", "__pycache__", "llm-qa"}


def today() -> str:
    return dt.date.today().isoformat()


def rel(vault: Path, path: Path) -> str:
    return str(path.relative_to(vault))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def md_paths_under(root: Path) -> list[Path]:
    if not root.exists():
        return []
    paths = []
    for path in sorted(root.rglob("*.md")):
        if any(part in IGNORED_CHECK_PARTS for part in path.parts):
            continue
        paths.append(path)
    return paths


def non_readme_raw_paths(vault: Path) -> list[Path]:
    raw_root = vault / "raw"
    if not raw_root.exists():
        return []
    return sorted(path for path in raw_root.glob("**/*.md") if path.name != "README.md")


def paths_containing(paths: list[Path], marker: str) -> list[Path]:
    return [path for path in paths if marker in read_text(path)]


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_marker_present(paths: list[Path], marker: str, label: str, vault: Path) -> list[Path]:
    matches = paths_containing(paths, marker)
    if not matches:
        searched = "\n".join(f"- {rel(vault, path)}" for path in paths[:20])
        raise AssertionError(f"{label}: {marker} が見つかりません\nsearched:\n{searched}")
    return matches


def assert_marker_absent(paths: list[Path], marker: str, label: str, vault: Path) -> None:
    matches = paths_containing(paths, marker)
    if matches:
        listed = "\n".join(f"- {rel(vault, path)}" for path in matches)
        raise AssertionError(f"{label}: {marker} が混入しています\n{listed}")


def frontmatter(path: Path) -> dict:
    fm, _body = memory_lint.split_frontmatter(path)
    return fm


def body_text(path: Path) -> str:
    _fm, body = memory_lint.split_frontmatter(path)
    return body


def source_refs_include_raw(path: Path) -> bool:
    refs = frontmatter(path).get("source_refs", [])
    if isinstance(refs, str):
        refs = [refs]
    return any("raw/" in ref for ref in refs)


def assert_event_applied_with_raw_source(path: Path, label: str) -> None:
    fm = frontmatter(path)
    assert_condition(fm.get("type") == "event", f"{label}: type: event ではありません: {path}")
    assert_condition(fm.get("derived_status") == "applied", f"{label}: derived_status: applied ではありません: {path}")
    assert_condition(source_refs_include_raw(path), f"{label}: source_refs に raw note 参照がありません: {path}")
    body = body_text(path)
    assert_condition(
        len(body) <= THIN_EVENT_MAX_CHARS,
        f"{label}: event 本文が長すぎます。raw 原文を再掲せず thin index にしてください: {path} ({len(body)} chars)",
    )


def client_paths(vault: Path, client_id: str) -> list[Path]:
    return md_paths_under(vault / "clients" / client_id)


def internal_paths(vault: Path, project_id: str) -> list[Path]:
    return md_paths_under(vault / "internal" / project_id)


def client_event_paths(vault: Path, client_id: str) -> list[Path]:
    return sorted((vault / "clients" / client_id / "events").glob("*.md"))


def internal_event_paths(vault: Path, project_id: str) -> list[Path]:
    return sorted((vault / "internal" / project_id / "events").glob("*.md"))


def client_digest_paths(vault: Path, client_id: str) -> list[Path]:
    root = vault / "clients" / client_id
    return [root / "profile.md", root / "states" / "current.md"]


def internal_digest_paths(vault: Path, project_id: str) -> list[Path]:
    root = vault / "internal" / project_id
    return [root / "profile.md", root / "states" / "current.md"]


def create_manual_current_note(vault: Path) -> None:
    path = vault / "clients" / PRIMARY_CLIENT / "states" / "current.md"
    text = read_text(path)
    text += f"\n## LLM QA 手動追記\n\n{MANUAL_MARKER}: Obsidian で手動追記された、導入前FAQを優先するメモ。\n"
    path.write_text(text, encoding="utf-8")


def create_manual_profile_note(vault: Path) -> None:
    path = vault / "clients" / PRIMARY_CLIENT / "profile.md"
    text = read_text(path)
    text += f"\n## LLM QA 手動 profile 追記\n\n{MANUAL_PROFILE_MARKER}: Obsidian で手動追記された、導入前FAQを長期知識として残すメモ。\n"
    path.write_text(text, encoding="utf-8")


def runbook_text(vault: Path) -> str:
    return f"""# LLM QA Runbook

この directory は使い捨ての QA vault です。

Vault path:

```text
{vault}
```

## 目的

この QA は、機械的 fixture ではなく、Codex / Claude などの LLM agent が実際に repository skill を読んで save / digest を実行できるかを見るためのものです。

## 必須ルール

- この一時 vault の中だけを更新してください。
- 最初に `AGENTS.md` と関連 skill を読んでください。
- 保存では必ず `scripts/memory save ...` で agent 向け prompt を生成し、その prompt と `memory-save` skill に従ってください。
- 新規 client / internal project 作成では必ず `scripts/memory add ...` で agent 向け prompt を生成し、その prompt と `memory-add` skill に従ってください。
- digest では必ず `scripts/memory digest ...` で agent 向け prompt を生成し、その prompt と `memory-digest` skill に従ってください。
- 月次総括では必ず `scripts/memory review ...` で agent 向け prompt を生成し、`monthly-review` event として保存してください。
- QA marker は検証に使うので、raw / event / profile / states/current.md の該当箇所にそのまま残してください。
- 複数 client / internal のメモでは、top-level `raw/` に原本を 1 つ保存し、entity ごとの event と digest に分けてください。
- raw note は厚く、event は薄くしてください。長文議事録や発言録を event に再コピーせず、event は要点・決定事項・タスク・リスク・未解決事項の index にします。
- digest 後の `profile.md` / `states/current.md` では、event 由来の箇条書きを各 section 内でできるだけ新しい source event 順に並べてください。基本説明と手動メモは無理に並べ替えないでください。
- `clients/*/raw/` は作らないでください。
- `tasks.md`、`wiki/`、`outputs/`、月次 state は作らないでください。
- 月次総括は `event_type: review` の `monthly-review` event にし、来月へ持ち越す active item だけ `states/current.md` に残してください。
- 既存 event を直接編集せず、必要なら新規 event / correction event にしてください。
- 最後に `scripts/memory lint` を通してください。

## シナリオ

### 1. Single client save + digest

次のメモを `{PRIMARY_CLIENT}` に保存し、digest まで実行してください。

```text
{SINGLE_MARKER}: Alpha の次回定例では、問い合わせフォームで費用不安が強く、導入初日の流れ説明が不足している点を扱う。次回までに導入前FAQ案を1つ作る。
```

期待:

- top-level `raw/` に raw note ができる。
- `{PRIMARY_CLIENT}` の event が raw note を `source_refs` に持つ。
- event は raw 全文をコピーせず、薄い index になっている。
- event は digest 後に `derived_status: applied` になる。
- `{PRIMARY_CLIENT}` の `profile.md` または `states/current.md` に `{SINGLE_MARKER}` が残る。

### 2. Multi entity split

次の複数 entity 混在メモを保存し、entity ごとに event と digest を分けてください。

```text
{MULTI_ALPHA_MARKER}: Alpha だけの情報。問い合わせフォームのFAQでは、費用不安の回答を先頭に置く。
{MULTI_BETA_MARKER}: Beta だけの情報。初回購入アンケートでは、配送日指定の不安を選択肢に追加する。
{MULTI_INTERNAL_MARKER}: Internal だけの情報。BtoB事業チームの営業提案では、商談成果だけでなく提案資料更新と計測整備をセットで話す。
```

期待:

- top-level `raw/` の同じ raw note に3つの marker が残る。
- `{PRIMARY_CLIENT}` 配下には `{MULTI_ALPHA_MARKER}` だけが入り、他 marker は入らない。
- `{SECONDARY_CLIENT}` 配下には `{MULTI_BETA_MARKER}` だけが入り、他 marker は入らない。
- `{INTERNAL_PROJECT}` 配下には `{MULTI_INTERNAL_MARKER}` だけが入り、client marker は入らない。
- 各 event は raw note を `source_refs` に持ち、digest 後に `derived_status: applied` になる。
- 各 event は raw 全文をコピーせず、entity ごとの薄い index になっている。

### 3. Unknown target inbox

次の対象不明メモは client / internal に推定せず、`inbox/` に残してください。

```text
{UNKNOWN_MARKER}: 商談レポートのクリック率が落ちたらしいが、本文から client / internal が特定できない。
```

期待:

- `inbox/` に note ができる。
- client / internal event は作らない。
- raw note にも client / internal memory にも混ぜない。

### 4. Manual current/profile note preservation

既に `{PRIMARY_CLIENT}` の `states/current.md` に `{MANUAL_MARKER}` を含む手動メモがあります。
また `profile.md` に `{MANUAL_PROFILE_MARKER}` を含む手動メモがあります。
digest 追加時にこれらの手動メモを消さず、`profile.md` と `states/current.md` のどちらかに新しい学びを追記してください。

### 5. Internal project save + digest

次のメモを `{INTERNAL_PROJECT}` に保存し、digest まで実行してください。

```text
{INTERNAL_SINGLE_MARKER}: Internal の営業提案テンプレートでは、CRM・商談管理の施策だけでなく、提案資料更新、計測整備、月次報告の型を1ページで説明する。
```

期待:

- top-level `raw/` に raw note ができる。
- `{INTERNAL_PROJECT}` の event が raw note を `source_refs` に持つ。
- event は raw 全文をコピーせず、薄い index になっている。
- event は digest 後に `derived_status: applied` になる。
- `{INTERNAL_PROJECT}` の `profile.md` または `states/current.md` に `{INTERNAL_SINGLE_MARKER}` が残る。

### 6. Source registration

`{PRIMARY_CLIENT}` の継続利用資料として、次の URL を `sources.md` に登録してください。event にはしません。

```text
名称: {SOURCE_MARKER} 問い合わせフォーム改善シート
種別: spreadsheet
URL: https://example.com/llmqa-alpha-form-sheet
context: on_demand
備考: LLM QA 用。必要なときだけ gws で取得する。
```

期待:

- `{PRIMARY_CLIENT}` の `sources.md` に `{SOURCE_MARKER}` が残る。
- URL は `https://` で、context は `on_demand`。
- 別 client / internal の `sources.md` には混ざらない。

### 7. Correction event

`{PRIMARY_CLIENT}` について、既存 event を直接編集せず、次の訂正を新規 event として保存し、digest してください。

```text
{CORRECTION_MARKER}: 導入前FAQ案の優先順位は「導入初日の流れ」ではなく「費用不安」を先頭にする、という訂正を記録する。
```

期待:

- 既存 event を直接書き換えず、新規 event が作られる。
- event は raw note を `source_refs` に持つ。
- event は raw 全文をコピーせず、薄い index になっている。
- event は digest 後に `derived_status: applied` になる。
- `{PRIMARY_CLIENT}` の `profile.md` または `states/current.md` に `{CORRECTION_MARKER}` が残る。

### 8. No-digest event

`{SECONDARY_CLIENT}` に、派生更新不要の軽い記録として次を保存してください。

```text
{NO_DIGEST_MARKER}: Beta の雑メモ。今日はCRM画面の表示確認だけで、profile や current に反映するほどの判断はない。
```

期待:

- `{SECONDARY_CLIENT}` の event に `{NO_DIGEST_MARKER}` が残る。
- event は raw note を `source_refs` に持つ。
- event は raw 全文をコピーせず、薄い index になっている。
- `derived_targets: []` にする。
- `profile.md` / `states/current.md` には `{NO_DIGEST_MARKER}` を入れない。

### 9. Monthly review event

`{PRIMARY_CLIENT}` の月次総括を保存してください。

```bash
scripts/memory review --client {PRIMARY_CLIENT} --month 2026-05 "{MONTHLY_REVIEW_MARKER}: Alpha の5月総括。問い合わせフォームの費用不安対応、問い合わせ分類、導入前FAQ案を振り返り、来月へ持ち越す active item だけ current に残す。"
```

期待:

- `{PRIMARY_CLIENT}` の `events/` に `monthly-review` を含む event ができる。
- event の `event_type` は `review`。
- source_refs には同じ client の月内 event と、必要なら raw note が入る。
- `states/current.md` に `{MONTHLY_REVIEW_MARKER}` と review event への参照が残る。
- `states/2026-05.md`、`outputs/`、`tasks.md`、`wiki/` は作らない。
- 別 client / internal に `{MONTHLY_REVIEW_MARKER}` を混ぜない。

### 10. New client creation

次の新規 client を `memory-add` で作成してください。

```bash
scripts/memory add --client {ADD_CLIENT_ID} --name "LLM QA New Client" "{ADD_CLIENT_MARKER}: Google商談・プロジェクト運用を新しく受ける client。初期課題は問い合わせ計測の整備と商談フォローの構成確認。"
```

期待:

- `clients/{ADD_CLIENT_ID}/profile.md`、`sources.md`、`states/current.md`、`events/` ができる。
- 初期 event が作成され、`derived_status: applied` になる。
- `states/current.md` が初期 event を参照する。
- `{ADD_CLIENT_MARKER}` が初期 event、`profile.md`、`states/current.md` に残る。
- `raw/` には `{ADD_CLIENT_MARKER}` を入れない。
- `clients/{ADD_CLIENT_ID}/raw/`、`tasks.md`、`wiki/`、`outputs/`、月次 state は作らない。

### 11. New internal project creation

次の新規 internal project を `memory-add` で作成してください。

```bash
scripts/memory add --internal {ADD_INTERNAL_ID} --name "LLM QA New Internal" "{ADD_INTERNAL_MARKER}: BtoB事業チームの提案テンプレートを整える社内 project。CRM・商談管理、提案資料更新、計測整備を1枚で説明する型を作る。"
```

期待:

- `internal/{ADD_INTERNAL_ID}/profile.md`、`sources.md`、`states/current.md`、`events/` ができる。
- 初期 event が作成され、`derived_status: applied` になる。
- `states/current.md` が初期 event を参照する。
- `{ADD_INTERNAL_MARKER}` が初期 event、`profile.md`、`states/current.md` に残る。
- `raw/` には `{ADD_INTERNAL_MARKER}` を入れない。
- `internal/{ADD_INTERNAL_ID}/raw/`、`tasks.md`、`wiki/`、`outputs/`、月次 state、`state.md` は作らない。

## 検証

LLM agent が作業した後、この repository の外側または一時 vault 内で次を実行します。

```bash
scripts/memory qa-llm check {vault}
```

通ったら一時 vault を削除できます。

```bash
scripts/memory qa-llm cleanup {vault}
```
"""


def expected_json(vault: Path) -> str:
    data = {
        "vault": str(vault),
        "clients": [PRIMARY_CLIENT, SECONDARY_CLIENT, ADD_CLIENT_ID],
        "internal": [INTERNAL_PROJECT, ADD_INTERNAL_ID],
        "markers": {
            "single": SINGLE_MARKER,
            "multi_alpha": MULTI_ALPHA_MARKER,
            "multi_beta": MULTI_BETA_MARKER,
            "multi_internal": MULTI_INTERNAL_MARKER,
            "unknown": UNKNOWN_MARKER,
            "manual": MANUAL_MARKER,
            "manual_profile": MANUAL_PROFILE_MARKER,
            "internal_single": INTERNAL_SINGLE_MARKER,
            "source": SOURCE_MARKER,
            "correction": CORRECTION_MARKER,
            "no_digest": NO_DIGEST_MARKER,
            "monthly_review": MONTHLY_REVIEW_MARKER,
            "add_client": ADD_CLIENT_MARKER,
            "add_internal": ADD_INTERNAL_MARKER,
        },
        "thin_event_max_chars": THIN_EVENT_MAX_CHARS,
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def prepare_vault() -> Path:
    vault = smoke.copy_vault(prefix="memory-llm-qa-")
    smoke.create_client_fixture(vault, PRIMARY_CLIENT, "Example Client Alpha")
    smoke.create_client_fixture(vault, SECONDARY_CLIENT, "Example Client Beta")
    smoke.create_internal_fixture(vault, INTERNAL_PROJECT, "Example Internal Project")
    create_manual_current_note(vault)
    create_manual_profile_note(vault)
    write_text(vault / "llm-qa" / "RUNBOOK.md", runbook_text(vault))
    write_text(vault / "llm-qa" / "expected.json", expected_json(vault))
    return vault


def run_lint(vault: Path) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, "tools/memory_lint.py"],
        cwd=vault,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return result.returncode, result.stdout


def assert_lint_passes(vault: Path) -> None:
    code, output = run_lint(vault)
    if code != 0:
        raise AssertionError(f"scripts/memory lint 相当が失敗しました\n{output}")
    print("成功: LLM QA vault の lint が通過")


def assert_no_retired_paths(vault: Path) -> None:
    patterns = [
        "clients/*/tasks.md",
        "internal/*/tasks.md",
        "clients/*/wiki",
        "internal/*/wiki",
        "clients/*/outputs",
        "internal/*/outputs",
        "clients/*/states/00-current.md",
        "clients/*/states/20??-??.md",
        "internal/*/states/20??-??.md",
        "internal/*/state.md",
        "clients/*/raw",
        "internal/*/raw",
    ]
    paths = []
    for pattern in patterns:
        paths.extend(vault.glob(pattern))
    if paths:
        listed = "\n".join(f"- {rel(vault, path)}" for path in paths)
        raise AssertionError(f"lite 構成で使わない path が作られています\n{listed}")
    print("成功: retired paths は作られていない")


def assert_single_client_flow(vault: Path) -> None:
    raw_matches = assert_marker_present(non_readme_raw_paths(vault), SINGLE_MARKER, "single client raw", vault)
    event_matches = assert_marker_present(client_event_paths(vault, PRIMARY_CLIENT), SINGLE_MARKER, "single client event", vault)
    digest_matches = assert_marker_present(client_digest_paths(vault, PRIMARY_CLIENT), SINGLE_MARKER, "single client digest", vault)
    assert_marker_absent(client_paths(vault, SECONDARY_CLIENT), SINGLE_MARKER, "single client marker cross-client check", vault)
    for path in event_matches:
        assert_event_applied_with_raw_source(path, f"single client event {rel(vault, path)}")
    print(
        "成功: single client save + digest "
        f"(raw={rel(vault, raw_matches[0])}, event={rel(vault, event_matches[0])}, digest={rel(vault, digest_matches[0])})"
    )


def assert_multi_entity_split(vault: Path) -> None:
    raw_alpha = set(paths_containing(non_readme_raw_paths(vault), MULTI_ALPHA_MARKER))
    raw_beta = set(paths_containing(non_readme_raw_paths(vault), MULTI_BETA_MARKER))
    raw_internal = set(paths_containing(non_readme_raw_paths(vault), MULTI_INTERNAL_MARKER))
    shared_raw = sorted(raw_alpha.intersection(raw_beta).intersection(raw_internal))
    assert_condition(bool(shared_raw), "multi entity marker が同じ top-level raw note に残っていません")

    alpha_events = assert_marker_present(client_event_paths(vault, PRIMARY_CLIENT), MULTI_ALPHA_MARKER, "multi alpha event", vault)
    beta_events = assert_marker_present(client_event_paths(vault, SECONDARY_CLIENT), MULTI_BETA_MARKER, "multi beta event", vault)
    internal_events = assert_marker_present(internal_event_paths(vault, INTERNAL_PROJECT), MULTI_INTERNAL_MARKER, "multi internal event", vault)
    assert_marker_present(client_digest_paths(vault, PRIMARY_CLIENT), MULTI_ALPHA_MARKER, "multi alpha digest", vault)
    assert_marker_present(client_digest_paths(vault, SECONDARY_CLIENT), MULTI_BETA_MARKER, "multi beta digest", vault)
    assert_marker_present(internal_digest_paths(vault, INTERNAL_PROJECT), MULTI_INTERNAL_MARKER, "multi internal digest", vault)

    assert_marker_absent(client_paths(vault, PRIMARY_CLIENT), MULTI_BETA_MARKER, "multi split alpha beta contamination", vault)
    assert_marker_absent(client_paths(vault, PRIMARY_CLIENT), MULTI_INTERNAL_MARKER, "multi split alpha internal contamination", vault)
    assert_marker_absent(client_paths(vault, SECONDARY_CLIENT), MULTI_ALPHA_MARKER, "multi split beta alpha contamination", vault)
    assert_marker_absent(client_paths(vault, SECONDARY_CLIENT), MULTI_INTERNAL_MARKER, "multi split beta internal contamination", vault)
    assert_marker_absent(internal_paths(vault, INTERNAL_PROJECT), MULTI_ALPHA_MARKER, "multi split internal alpha contamination", vault)
    assert_marker_absent(internal_paths(vault, INTERNAL_PROJECT), MULTI_BETA_MARKER, "multi split internal beta contamination", vault)

    for path in [*alpha_events, *beta_events, *internal_events]:
        assert_event_applied_with_raw_source(path, f"multi entity event {rel(vault, path)}")
    print(f"成功: multi entity raw + entity 別 event/digest 分離 (raw={rel(vault, shared_raw[0])})")


def assert_unknown_inbox(vault: Path) -> None:
    inbox_matches = assert_marker_present(md_paths_under(vault / "inbox"), UNKNOWN_MARKER, "unknown inbox", vault)
    assert_marker_absent(md_paths_under(vault / "clients"), UNKNOWN_MARKER, "unknown marker client contamination", vault)
    assert_marker_absent(md_paths_under(vault / "internal"), UNKNOWN_MARKER, "unknown marker internal contamination", vault)
    assert_marker_absent(non_readme_raw_paths(vault), UNKNOWN_MARKER, "unknown marker raw contamination", vault)
    print(f"成功: 対象不明メモは inbox に残っている ({rel(vault, inbox_matches[0])})")


def assert_manual_note_preserved(vault: Path) -> None:
    current_path = vault / "clients" / PRIMARY_CLIENT / "states" / "current.md"
    profile_path = vault / "clients" / PRIMARY_CLIENT / "profile.md"
    assert_condition(MANUAL_MARKER in read_text(current_path), f"手動 current marker が消えています: {current_path}")
    assert_condition(MANUAL_PROFILE_MARKER in read_text(profile_path), f"手動 profile marker が消えています: {profile_path}")
    print("成功: 手動 current/profile note は保持されている")


def assert_internal_single_flow(vault: Path) -> None:
    raw_matches = assert_marker_present(non_readme_raw_paths(vault), INTERNAL_SINGLE_MARKER, "internal single raw", vault)
    event_matches = assert_marker_present(
        internal_event_paths(vault, INTERNAL_PROJECT),
        INTERNAL_SINGLE_MARKER,
        "internal single event",
        vault,
    )
    digest_matches = assert_marker_present(
        internal_digest_paths(vault, INTERNAL_PROJECT),
        INTERNAL_SINGLE_MARKER,
        "internal single digest",
        vault,
    )
    assert_marker_absent(md_paths_under(vault / "clients"), INTERNAL_SINGLE_MARKER, "internal marker client contamination", vault)
    for path in event_matches:
        assert_event_applied_with_raw_source(path, f"internal single event {rel(vault, path)}")
    print(
        "成功: internal project save + digest "
        f"(raw={rel(vault, raw_matches[0])}, event={rel(vault, event_matches[0])}, digest={rel(vault, digest_matches[0])})"
    )


def assert_source_registration(vault: Path) -> None:
    source_path = vault / "clients" / PRIMARY_CLIENT / "sources.md"
    text = read_text(source_path)
    assert_condition(SOURCE_MARKER in text, f"sources.md に {SOURCE_MARKER} がありません")
    assert_condition("https://example.com/llmqa-alpha-form-sheet" in text, "sources.md に QA URL がありません")
    assert_condition("on_demand" in text, "sources.md に context: on_demand がありません")
    assert_marker_absent([vault / "clients" / SECONDARY_CLIENT / "sources.md"], SOURCE_MARKER, "source marker beta contamination", vault)
    assert_marker_absent([vault / "internal" / INTERNAL_PROJECT / "sources.md"], SOURCE_MARKER, "source marker internal contamination", vault)
    print("成功: source registration は対象 client の sources.md のみ")


def assert_correction_event(vault: Path) -> None:
    raw_matches = assert_marker_present(non_readme_raw_paths(vault), CORRECTION_MARKER, "correction raw", vault)
    event_matches = assert_marker_present(client_event_paths(vault, PRIMARY_CLIENT), CORRECTION_MARKER, "correction event", vault)
    digest_matches = assert_marker_present(client_digest_paths(vault, PRIMARY_CLIENT), CORRECTION_MARKER, "correction digest", vault)
    assert_marker_absent(client_paths(vault, SECONDARY_CLIENT), CORRECTION_MARKER, "correction marker beta contamination", vault)
    for path in event_matches:
        assert_event_applied_with_raw_source(path, f"correction event {rel(vault, path)}")
    print(
        "成功: correction event + digest "
        f"(raw={rel(vault, raw_matches[0])}, event={rel(vault, event_matches[0])}, digest={rel(vault, digest_matches[0])})"
    )


def assert_no_digest_event(vault: Path) -> None:
    raw_matches = assert_marker_present(non_readme_raw_paths(vault), NO_DIGEST_MARKER, "no-digest raw", vault)
    event_matches = assert_marker_present(client_event_paths(vault, SECONDARY_CLIENT), NO_DIGEST_MARKER, "no-digest event", vault)
    assert_marker_absent(client_digest_paths(vault, SECONDARY_CLIENT), NO_DIGEST_MARKER, "no-digest derived contamination", vault)
    for path in event_matches:
        fm = frontmatter(path)
        assert_event_applied_with_raw_source(path, f"no-digest event {rel(vault, path)}")
        assert_condition(fm.get("derived_targets") == [], f"no-digest event は derived_targets: [] の想定です: {path}")
    print(f"成功: 派生更新不要 event (raw={rel(vault, raw_matches[0])}, event={rel(vault, event_matches[0])})")


def assert_monthly_review_flow(vault: Path) -> None:
    event_matches = assert_marker_present(
        client_event_paths(vault, PRIMARY_CLIENT),
        MONTHLY_REVIEW_MARKER,
        "monthly review event",
        vault,
    )
    review_events = [path for path in event_matches if "monthly-review" in path.stem]
    assert_condition(bool(review_events), "monthly review event の file 名に monthly-review がありません")
    review_event = review_events[0]
    fm = frontmatter(review_event)
    assert_condition(fm.get("type") == "event", f"monthly review: type が event ではありません: {review_event}")
    assert_condition(fm.get("event_type") == "review", f"monthly review: event_type が review ではありません: {review_event}")
    assert_condition(fm.get("derived_status") == "applied", f"monthly review: derived_status: applied ではありません: {review_event}")
    refs = fm.get("source_refs") or []
    if isinstance(refs, str):
        refs = [refs]
    assert_condition(bool(refs), f"monthly review: source_refs がありません: {review_event}")
    assert_condition(
        any("raw/" not in str(ref) for ref in refs),
        f"monthly review: 月内 event への source_refs が見つかりません: {review_event}",
    )
    body = body_text(review_event)
    assert_condition(
        len(body) <= THIN_EVENT_MAX_CHARS,
        f"monthly review: event 本文が長すぎます。総括も thin index にしてください: {review_event} ({len(body)} chars)",
    )
    current_path = vault / "clients" / PRIMARY_CLIENT / "states" / "current.md"
    current_text = read_text(current_path)
    assert_condition(MONTHLY_REVIEW_MARKER in current_text, f"monthly review: current に marker がありません: {current_path}")
    assert_condition(
        review_event.stem in current_text or rel(vault, review_event).removesuffix(".md") in current_text,
        f"monthly review: current が review event を参照していません: {current_path}",
    )
    assert_marker_absent(client_paths(vault, SECONDARY_CLIENT), MONTHLY_REVIEW_MARKER, "monthly review beta contamination", vault)
    assert_marker_absent(internal_paths(vault, INTERNAL_PROJECT), MONTHLY_REVIEW_MARKER, "monthly review internal contamination", vault)
    print(f"成功: monthly-review event + current carry-over (event={rel(vault, review_event)})")


def entity_required_paths(vault: Path, entity_type: str, entity_id: str) -> tuple[Path, list[Path]]:
    root = vault / ("clients" if entity_type == "client" else "internal") / entity_id
    return root, [root / "profile.md", root / "sources.md", root / "states" / "current.md", root / "events"]


def entity_event_paths(vault: Path, entity_type: str, entity_id: str) -> list[Path]:
    if entity_type == "client":
        return client_event_paths(vault, entity_id)
    return internal_event_paths(vault, entity_id)


def entity_digest_paths(vault: Path, entity_type: str, entity_id: str) -> list[Path]:
    if entity_type == "client":
        return client_digest_paths(vault, entity_id)
    return internal_digest_paths(vault, entity_id)


def assert_added_entity(vault: Path, entity_type: str, entity_id: str, marker: str, label: str) -> None:
    root, required_paths = entity_required_paths(vault, entity_type, entity_id)
    assert_condition(root.exists(), f"{label}: root がありません: {root}")
    for path in required_paths:
        assert_condition(path.exists(), f"{label}: required path がありません: {path}")

    profile_path = root / "profile.md"
    sources_path = root / "sources.md"
    current_path = root / "states" / "current.md"
    profile_type = "client_profile" if entity_type == "client" else "internal_profile"
    assert_condition(frontmatter(profile_path).get("type") == profile_type, f"{label}: profile type が不正です")
    assert_condition(frontmatter(sources_path).get("type") == "source_index", f"{label}: sources type が不正です")
    assert_condition(frontmatter(current_path).get("type") == "entity_state", f"{label}: current type が不正です")
    for path in [profile_path, sources_path, current_path]:
        fm = frontmatter(path)
        assert_condition(fm.get("entity_type") == entity_type, f"{label}: entity_type が不正です: {path}")
        assert_condition(fm.get("entity_id") == entity_id, f"{label}: entity_id が不正です: {path}")

    event_matches = assert_marker_present(entity_event_paths(vault, entity_type, entity_id), marker, f"{label} event", vault)
    assert_condition(marker in read_text(profile_path), f"{label}: profile.md に {marker} がありません")
    assert_condition(marker in read_text(current_path), f"{label}: states/current.md に {marker} がありません")
    assert_marker_absent(non_readme_raw_paths(vault), marker, f"{label} raw contamination", vault)

    other_entity_paths = [
        path
        for path in [*md_paths_under(vault / "clients"), *md_paths_under(vault / "internal")]
        if root not in path.parents and path != root
    ]
    assert_marker_absent(other_entity_paths, marker, f"{label} other entity contamination", vault)

    for path in event_matches:
        fm = frontmatter(path)
        assert_condition(fm.get("type") == "event", f"{label}: event type が不正です: {path}")
        assert_condition(fm.get("entity_type") == entity_type, f"{label}: event entity_type が不正です: {path}")
        assert_condition(fm.get("entity_id") == entity_id, f"{label}: event entity_id が不正です: {path}")
        assert_condition(fm.get("derived_status") == "applied", f"{label}: initial event は applied の想定です: {path}")
        assert_condition("state" in (fm.get("derived_targets") or []), f"{label}: initial event の derived_targets に state がありません: {path}")
        current_text = read_text(current_path)
        event_stem = rel(vault, path).removesuffix(".md")
        assert_condition(
            event_stem in current_text or path.stem in current_text or fm.get("event_id", "") in current_text,
            f"{label}: states/current.md が initial event を参照していません: {path}",
        )
    print(f"成功: {label} は memory-add の軽量構成で作成されている")


def check_vault(vault: Path) -> None:
    assert_condition(vault.exists(), f"vault が存在しません: {vault}")
    assert_condition((vault / "tools" / "memory_lint.py").exists(), f"memory vault に見えません: {vault}")
    assert_lint_passes(vault)
    assert_no_retired_paths(vault)
    assert_single_client_flow(vault)
    assert_multi_entity_split(vault)
    assert_unknown_inbox(vault)
    assert_manual_note_preserved(vault)
    assert_internal_single_flow(vault)
    assert_source_registration(vault)
    assert_correction_event(vault)
    assert_no_digest_event(vault)
    assert_monthly_review_flow(vault)
    assert_added_entity(vault, "client", ADD_CLIENT_ID, ADD_CLIENT_MARKER, "new client creation")
    assert_added_entity(vault, "internal", ADD_INTERNAL_ID, ADD_INTERNAL_MARKER, "new internal project creation")


def cleanup_vault(vault: Path) -> None:
    resolved = vault.resolve()
    assert_condition(resolved.name == "vault", f"cleanup 対象は .../vault の path にしてください: {resolved}")
    assert_condition(
        resolved.parent.name.startswith("memory-llm-qa-"),
        f"cleanup 対象は memory-llm-qa-* の一時 directory にしてください: {resolved}",
    )
    shutil.rmtree(resolved.parent)


def command_prepare(_args: argparse.Namespace) -> int:
    vault = prepare_vault()
    print(f"LLM QA vault: {vault}")
    print(f"Runbook: {vault / 'llm-qa' / 'RUNBOOK.md'}")
    print()
    print("次に Codex / Claude に、この runbook のシナリオを実際に処理させてください。")
    print()
    print(runbook_text(vault))
    return 0


def command_check(args: argparse.Namespace) -> int:
    vault = Path(args.vault).expanduser().resolve()
    try:
        check_vault(vault)
    except AssertionError as exc:
        print(f"失敗: {exc}")
        return 1
    print("成功: LLM QA の全シナリオが通過")
    if args.cleanup:
        cleanup_vault(vault)
        print(f"削除: {vault.parent}")
    return 0


def command_cleanup(args: argparse.Namespace) -> int:
    vault = Path(args.vault).expanduser().resolve()
    try:
        cleanup_vault(vault)
    except AssertionError as exc:
        print(f"失敗: {exc}")
        return 1
    print(f"削除: {vault.parent}")
    return 0


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("qa-llm", help="Prepare/check manual LLM memory QA")
    qa_subparsers = parser.add_subparsers(dest="qa_llm_command", required=True)

    prepare = qa_subparsers.add_parser("prepare", help="Create a disposable vault and LLM QA runbook")
    prepare.set_defaults(func=command_prepare)

    check = qa_subparsers.add_parser("check", help="Check a disposable vault after an LLM agent updated it")
    check.add_argument("vault", help="Path to the disposable vault created by qa-llm prepare")
    check.add_argument("--cleanup", action="store_true", help="Delete the disposable vault after a successful check")
    check.set_defaults(func=command_check)

    cleanup = qa_subparsers.add_parser("cleanup", help="Delete a disposable LLM QA vault")
    cleanup.add_argument("vault", help="Path to the disposable vault created by qa-llm prepare")
    cleanup.set_defaults(func=command_cleanup)
