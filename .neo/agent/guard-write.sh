#!/usr/bin/env bash
# neo agent hook: PreToolUse(Write|Edit|NotebookEdit) guard for Claude Code (Codex reaches it
# through codex/codex-adapter.sh, one call per patched path). Denies any write under a vendored
# .neo/ copy (conf and identity-map excepted): consumers change the canonical framework repo and
# pull the change with 'neo setup --upgrade'. The path is resolved (relative to cwd, symlinks, case) before the check, and
# the framework source repo is recognised only by a .neo/FRAMEWORK marker committed in it. The check
# lives in guard_destructive.py (vendored()); without python3 or the module the write is refused.
here=$(cd "$(dirname "$0")" && pwd)
if ! command -v python3 >/dev/null 2>&1 || [ ! -f "$here/guard_destructive.py" ]; then
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"neo guard: python3 or guard_destructive.py is missing, so the write was not checked and is refused; reinstall with 'neo setup --agent'."}}'
  exit 0
fi
exec python3 "$here/guard_destructive.py" --write
