# shellcheck shell=bash
# tracker.sh - one contract for any ticket tracker.
#
# The tracker comes from operator settings first: $NEO_TRACKER, then git
# config neo.tracker; the committed .neo/conf key tracker may only say none.
# A command tracker runs an executable, so a lane can never pick one by
# committing it: command:<path> is honoured only from operator settings, and
# never when the path is a file the repository tracks.
#
# Values: none (default), command:<path> (absolute, or relative to the root).
# Adapter contract: <adapter> <op> [args], one JSON object on stdout, exit 0.
#   get <ID>                              {"key": "<ID>", "title": "...", ...}
#   link <ID> --branch <lane>             {"ok": true}
#   transition <ID> --to done --ref <v>   {"ok": true}
# Ticket ids look like CODE-123. A failed link or transition is reported and
# never undoes a lane or a land.

neo_ticket_ok() { [[ "$1" =~ ^[A-Z][A-Z0-9]*-[0-9]+$ ]]; }

# neo_tracker: the adapter path, empty for none.
neo_tracker() {
  local v src=operator p root
  v="${NEO_TRACKER:-}"
  [ -n "$v" ] || v=$(git config --get neo.tracker 2>/dev/null || true)
  if [ -z "$v" ]; then v=$(neo_conf tracker none); src=conf; fi
  case "$v" in
    none) return 0 ;;
    command:?*)
      [ "$src" = operator ] || NEO_RC=2 neo_die "the committed conf names tracker '$v'; a command tracker runs an executable, so set it in NEO_TRACKER or git config neo.tracker"
      root=$(neo_root); p="${v#command:}"
      case "$p" in /*) ;; *) p="$root/$p" ;; esac
      if git -C "$root" ls-files --error-unmatch -- "$p" >/dev/null 2>&1; then
        neo_die "tracker command $p is a file this repository tracks; keep the adapter outside the repository"
      fi
      [ -x "$p" ] || neo_die "tracker command $p is missing or not executable"
      printf '%s' "$p" ;;
    *) NEO_RC=2 neo_die "tracker '$v' is not none or command:<path>" ;;
  esac
}

# neo_tracker_call OP ARGS...: run the adapter (if any); print its JSON object.
neo_tracker_call() {
  local a out
  a=$(neo_tracker)
  if [ -z "$a" ]; then printf '{}'; return 0; fi
  out=$("$a" "$@") || { neo_warn "tracker $1 failed (exit $?)"; return 1; }
  case "$out" in "{"*"}") ;; *) neo_warn "tracker $1 did not answer one JSON object"; return 1 ;; esac
  printf '%s' "$out"
}

# neo_json_str JSON KEY: one top-level string field (no nesting needed here).
neo_json_str() { sed -nE 's/.*"'"$2"'"[[:space:]]*:[[:space:]]*"(([^"\\]|\\.)*)".*/\1/p' <<<"$1" | sed -n 1p; }
