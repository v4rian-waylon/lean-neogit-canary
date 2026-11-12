#!/usr/bin/env bash
# reqs-fix.sh - run by neo sync (git rebase -x) and the re-land after each
# replayed commit: regenerate REQUIREMENTS.md from that commit's requirement
# files and amend the commit when the register changed, so every rebased
# commit carries the register its own tree generates (lib/reqs.sh).
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$here/core.sh"; . "$here/reqs.sh"
git cat-file -e HEAD:REQUIREMENTS.md 2>/dev/null || [ -n "$(git ls-tree --name-only HEAD requirements/)" ] || exit 0
neo_reqs_write_index || { echo "X neo: the requirement files of $(git rev-parse --short HEAD) break the register model" >&2; exit 1; }
git diff --cached --quiet -- REQUIREMENTS.md || git -c core.hooksPath=/dev/null commit -q --amend --no-edit --no-verify
