#!/usr/bin/env bash
# neo agent hook adapter for Codex CLI PreToolUse. Codex sends the same hook envelope as
# Claude Code (tool_name, tool_input, cwd) and honours the same deny output
# (hookSpecificOutput.permissionDecision "deny"), but two inputs differ, so this adapter
# reshapes them and hands off to the shared guards next to it:
#   bash   tool_input.command may arrive as an argv array; ["bash","-lc","<script>"] (or sh/zsh,
#          -c) becomes "<script>", any other array is joined with spaces. -> guard-destructive.sh
#   patch  apply_patch carries the patch text in tool_input.command; every "*** Add File:",
#          "*** Update File:", "*** Delete File:" and "*** Move to:" path (relative ones resolved
#          against cwd) is checked by guard-write.sh, the first deny wins. Edit/Write inputs with
#          tool_input.file_path pass straight through.
# The guard learns it runs for Codex (NEO_GUARD_AGENT=codex): Codex rewrites a Bash call only through
# "allow" + updatedInput, so the identity hook (guard rule 8) answers allow with the command that
# exports the mapped agent identity, for a line of plain git, neo, cd and export commands only.
# A missing guard fails closed (deny with the reinstall command).
# Failure: Claude Code entries set onFailure "block" so a hook timeout or crash blocks the call;
# Codex hooks.json has no onFailure equivalent, so whether Codex blocks on a hook timeout is up to
# the Codex host. The timeouts in codex/hooks.json are the only knob.
# Usage (from hooks.json): codex-adapter.sh bash|patch   < hook JSON on stdin
set -u
here="$(cd "$(dirname "$0")" && pwd)"
# installed: the guards sit next to this adapter; in the framework tree they are in ..
[ -x "$here/guard-destructive.sh" ] || here="$(cd "$here/.." 2>/dev/null && pwd)"
input=$(cat)
if [ ! -x "$here/guard-destructive.sh" ] || [ ! -x "$here/guard-write.sh" ]; then
  jq -nc '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:"neo: the guards are missing next to codex-adapter.sh; re-run neo setup --agent codex."}}'
  exit 0
fi
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null)
case "${1:-}" in
  bash)
    # argv -> one shell string: a shell with any -...c... flag cluster (-c,
    # -lc, -lec, -xc) hands over its script; any other array is shell-quoted
    # word by word, so an argument never becomes a command.
    printf '%s' "$input" | jq -c '.tool_input.command |= (if type == "array" then
        (if length == 3 and (.[0] | test("(^|/)(ba|z|da)?sh$")) and (.[1] | test("^-[A-Za-z]*c[A-Za-z]*$")) then .[2] else (map(@sh) | join(" ")) end)
      else . end)' 2>/dev/null | NEO_GUARD_AGENT=codex "$here/guard-destructive.sh" ;;
  patch)
    fp=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
    if [ -n "$fp" ]; then printf '%s' "$input" | "$here/guard-write.sh"; exit 0; fi
    printf '%s' "$input" | jq -r '.tool_input.command // .tool_input.input // empty | if type == "array" then join("\n") else . end' 2>/dev/null \
      | sed -n -E 's/^\*\*\* (Add File|Update File|Delete File|Move to): +//p' \
      | while IFS= read -r p; do
          [ -z "$p" ] && continue
          case "$p" in /*) ;; *) p="${cwd:-$PWD}/$p" ;; esac
          out=$(jq -nc --arg f "$p" '{tool_name:"Write",tool_input:{file_path:$f}}' | "$here/guard-write.sh")
          if [ -n "$out" ]; then printf '%s\n' "$out"; break; fi
        done ;;
  *) echo "codex-adapter.sh: usage: codex-adapter.sh bash|patch" >&2; exit 0 ;;
esac
exit 0
