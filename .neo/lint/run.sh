#!/usr/bin/env bash
# lint/run.sh - run every lint in .neo/lint on the tracked files of the tree
# it is run from; any finding fails the gate. The gates run it before the
# scenario matrix (gates_fast, gates_full and gates_release in conf).
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rc=0
for l in "$here"/*; do
  case "$(basename "$l")" in
    run.sh) continue ;;
    *.sh) bash "$l" || rc=1 ;;
    *.py) python3 "$l" || rc=1 ;;
  esac
done
exit "$rc"
