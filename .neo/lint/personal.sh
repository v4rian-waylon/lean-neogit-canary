#!/usr/bin/env bash
# lint/personal.sh - no personal data in tracked files: no home or session
# path of a real person (a /Users/<name>/ or /home/<name>/ path, a mangled
# -Users-<name>- project path, a session temp path), and no email address
# outside the reserved and placeholder domains (*.test, *.example,
# *.invalid, *.localhost, example.com/.org/.net, users.noreply.github.com).
# Write <workspace>, <tmp> or a .test address instead. Prints file:line for
# each finding, exit 1 on any.  personal.sh [FILE...]
set -euo pipefail
u="Us""ers"; h="ho""me"
path_re="/$u/[A-Za-z][A-Za-z0-9._-]*/|/$h/[a-z][a-z0-9._-]*/|-$u-[A-Za-z][A-Za-z0-9._-]*-|/private/t""mp/claude-"
mail_re='[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}'
allow_re='@([A-Za-z0-9-]+\.)*(test|example|invalid|localhost)$|@example\.(com|org|net)$|@users\.noreply\.github\.com$'
files=("$@")
if [ ${#files[@]} -eq 0 ]; then
  while IFS= read -r -d '' f; do files+=("$f"); done < <(git ls-files -z)
fi
rc=0
for f in ${files[@]+"${files[@]}"}; do
  [ -f "$f" ] || continue
  grep -Iq . "$f" 2>/dev/null || continue
  while IFS= read -r hit; do
    [ -n "$hit" ] || continue
    echo "X personal path: $f:$hit"; rc=1
  done <<<"$(grep -nE "$path_re" "$f" || true)"
  while IFS= read -r hit; do
    [ -n "$hit" ] || continue
    ln=${hit%%:*}; addr=${hit#*:}
    grep -Eq "$allow_re" <<<"$addr" && continue
    echo "X personal email: $f:$ln: $addr"; rc=1
  done <<<"$(grep -noE "$mail_re" "$f" || true)"
done
exit "$rc"
