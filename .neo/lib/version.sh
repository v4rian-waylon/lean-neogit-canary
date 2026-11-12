# shellcheck shell=bash
# version.sh - version math, a pure function of dev's first-parent history.
#
# Versions are vYYYY.S.N: YYYY the landing year, S the series (releases so
# far that year), N the land within the series, starting at 1. After a
# release/<v> tag the next land opens series S+1 at N=1; in a new year the
# next land is vYYYY.0.1. No counter is stored anywhere: the last version
# tag on dev's first-parent line and whether it carries a release tag
# answer everything (principle 2, "history is the database").

# neo_version_next PREV RELEASED YEAR -> the version the next land takes.
# PREV is the last vYYYY.S.N on dev's first-parent line (empty: none yet),
# RELEASED is 1 when that commit also carries release/<PREV>.
neo_version_next() {
  local prev="$1" released="$2" year="$3" y s n
  [ "$prev" = - ] && prev=""
  if [ -z "$prev" ]; then printf 'v%s.0.1\n' "$year"; return 0; fi
  [[ "$prev" =~ ^v([0-9]{4})\.([0-9]+)\.([0-9]+)$ ]] || { echo "bad version $prev" >&2; return 2; }
  y=${BASH_REMATCH[1]}; s=${BASH_REMATCH[2]}; n=${BASH_REMATCH[3]}
  if [ "$year" -gt "$y" ]; then printf 'v%s.0.1\n' "$year"; return 0; fi
  if [ "$released" = 1 ]; then printf 'v%s.%s.1\n' "$y" $((s + 1)); return 0; fi
  printf 'v%s.%s.%s\n' "$y" "$s" $((n + 1))
}

# neo_version_of COMMIT -> its vYYYY.S.N tag (annotated), empty when none.
neo_version_of() {
  git tag --points-at "$1" -l 'v*' 2>/dev/null | grep -E '^v[0-9]{4}\.[0-9]+\.[0-9]+$' | sed -n 1p || true
}

# neo_version_last [REF] -> "<version> <released 0|1>" for the newest
# version tag on REF's first-parent line (REF defaults to dev); the version
# is "-" when there is none yet. Read it with: read -r v rel; [ "$v" = - ] && v=""
neo_version_last() {
  local ref="${1:-dev}" v
  v=$(git describe --first-parent --tags --abbrev=0 --match 'v[0-9][0-9][0-9][0-9].*' "$ref" 2>/dev/null || true)
  if [[ "$v" =~ ^v[0-9]{4}\.[0-9]+\.[0-9]+$ ]]; then
    if git rev-parse -q --verify "refs/tags/release/$v" >/dev/null; then echo "$v 1"; else echo "$v 0"; fi
    return 0
  fi
  echo "- 0"
}

# neo_year: the landing year (UTC). NEO_YEAR overrides it for tests and
# for replays, so version math never depends on a wall clock in a test.
neo_year() { printf '%s' "${NEO_YEAR:-$(date -u +%Y)}"; }
