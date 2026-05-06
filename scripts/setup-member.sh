#!/usr/bin/env bash
set -euo pipefail

REPO_HTTPS_URL="https://github.com/tsutomutomizawa/btob-project-memory-template.git"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=10

info() {
  printf '[setup-member] %s\n' "$1"
}

warn() {
  printf '[setup-member] 注意: %s\n' "$1" >&2
}

fail() {
  printf '[setup-member] エラー: %s\n' "$1" >&2
  exit 1
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

require_command() {
  local command_name="$1"
  local install_hint="$2"

  if ! command_exists "$command_name"; then
    printf '[setup-member] %s が見つかりません。\n' "$command_name" >&2
    printf '%s\n' "$install_hint" >&2
    exit 1
  fi
}

is_interactive() {
  [[ -t 0 && -t 1 ]]
}

ensure_python_version() {
  local version
  if ! version="$("${BASH:-bash}" scripts/memory-python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"; then
    fail "Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR} 以上が必要です。Windows では Git Bash から python / python3 / py -3 のいずれかを使える状態にしてください。"
  fi

  local major="${version%%.*}"
  local minor="${version#*.}"

  if (( major < MIN_PYTHON_MAJOR )) || { (( major == MIN_PYTHON_MAJOR )) && (( minor < MIN_PYTHON_MINOR )); }; then
    fail "Python ${version} が見つかりました。Python 3.10 以上が必要です。"
  fi

  info "Python ${version} を確認しました。"
}

detect_shell_environment() {
  local uname_value
  uname_value="$(uname -s 2>/dev/null || true)"
  case "$uname_value" in
    MINGW*|MSYS*|CYGWIN*)
      info "Windows Git Bash 環境を確認しました。"
      ;;
    Darwin*)
      info "macOS 環境を確認しました。"
      ;;
    Linux*)
      info "Linux 環境を確認しました。"
      ;;
  esac
}

ensure_git_identity_value() {
  local key="$1"
  local label="$2"
  local current

  current="$(git config --get "$key" || true)"
  if [[ -n "$current" ]]; then
    if [[ "$key" == "user.email" ]]; then
      info "${key} は設定済みです。"
    else
      info "${key}=${current}"
    fi
    return
  fi

  if ! is_interactive; then
    fail "${key} が未設定です。git config --local ${key} \"${label}\" を設定してから再実行してください。"
  fi

  local value=""
  while [[ -z "$value" ]]; do
    printf '%s: ' "$label"
    read -r value
    if [[ -z "$value" ]]; then
      warn "${label} は空にできません。"
    fi
  done

  git config --local "$key" "$value"
  info "${key} を repo local に設定しました。"
}

ensure_https_remote() {
  local current_remote
  current_remote="$(git remote get-url origin 2>/dev/null || true)"

  if [[ -z "$current_remote" ]]; then
    git remote add origin "$REPO_HTTPS_URL"
    info "origin を HTTPS remote として追加しました。"
    return
  fi

  if [[ "$current_remote" == "$REPO_HTTPS_URL" ]]; then
    info "origin は HTTPS remote です。"
    return
  fi

  warn "origin が標準 HTTPS remote ではありません: ${current_remote}"
  git remote set-url origin "$REPO_HTTPS_URL"
  info "origin を ${REPO_HTTPS_URL} に変更しました。"
}

check_gws() {
  if command_exists "gws"; then
    if gws auth status >/dev/null 2>&1; then
      info "gws CLI を確認しました。Google Workspace 資料を読む場合は manual/GWS.md も確認してください。"
    else
      warn "gws CLI はありますが、認証状態を確認できませんでした。Google Workspace 資料を読む担当者は manual/GWS.md を見て設定してください。"
    fi
  else
    warn "gws CLI は見つかりませんでした。Google Workspace 資料を読む担当者だけ、manual/GWS.md を見て必要になった時点で設定してください。"
  fi
}

check_github_access() {
  info "GitHub への HTTPS 接続を確認します。"
  if GIT_TERMINAL_PROMPT=0 git ls-remote --exit-code origin HEAD >/dev/null 2>&1; then
    info "GitHub への接続を確認しました。"
    return
  fi

  cat >&2 <<'EOF'
[setup-member] GitHub への接続を確認できませんでした。

以下を確認してください。
- GitHub アカウントで tsutomutomizawa/btob-project-memory-template にアクセスできる
- HTTPS 認証が完了している
- ネットワークに接続している

認証をやり直す場合は、以下を実行して GitHub のログインを完了してから、setup を再実行してください。

  git pull
EOF
  exit 1
}

main() {
  require_command "git" "macOS では xcode-select --install、Windows では Git for Windows をインストールして Git Bash から実行してください。"

  local repo_root
  repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  if [[ -z "$repo_root" ]]; then
    fail "Git repository の中で実行してください。先に git clone してから cd してください。"
  fi
  cd "$repo_root"

  info "repository: ${repo_root}"
  detect_shell_environment
  ensure_python_version
  ensure_https_remote
  check_github_access

  info "Git の user.name / user.email を確認します。"
  ensure_git_identity_value "user.name" "GitHub username"
  ensure_git_identity_value "user.email" "Git commit email"

  info "pre-commit / commit-msg hook を有効化します。"
  ./scripts/install-hooks.sh

  check_gws

  info "memory vault の状態を確認します。"
  scripts/memory status --strict --with-lint

  cat <<'EOF'

[setup-member] セットアップ完了です。

普段の流れ:
  1. 作業前に「最新化してください」とエージェントに依頼
  2. Obsidian / Codex / Claude Code で作業
  3. 共有するときに「プッシュしてください」とエージェントに依頼

エージェントは scripts/memory publish / sync を使います。main への直接 push はせず、作業ブランチ push 後に GitHub Actions が PR を自動作成し、CI が通ると main に取り込まれ、ローカルも main 最新へ戻ります。
EOF
}

main "$@"
