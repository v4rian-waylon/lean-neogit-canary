# shellcheck shell=bash
# core.sh - shared helpers for every neo verb. Sourced, never executed.
# Bash 3.2 compatible; callers run under set -euo pipefail.

NEO_KINDS="feature fix refactor docs test chore"
NEO_PROTECTED="dev main"
# the requirement a new lane starts with; land refuses it until it is replaced
NEO_REQ_PLACEHOLDER="State the requirement this lane meets, and how its tests prove it."

# Named rules added to the framework after its first history. The history
# audit judges each merge by the rules the framework at its first parent knew
# (NEO_RULES_AT, set by neo_check_merge), so an upgrade never turns history
# that was lawful when it landed red; commit-msg, land and pre-push apply
# every rule the running framework knows.
NEO_RULES="red-test agent-author commit-audit reqs-register commit-body lane-number"
# neo_rule_on NAME: 0 when rule NAME applies here.
neo_rule_on() { case " ${NEO_RULES_AT-$NEO_RULES} " in *" $1 "*) return 0 ;; esac; return 1; }
# neo_rules_at REV: the named rules of the framework committed at REV.
neo_rules_at() { git show "$1:.neo/lib/core.sh" 2>/dev/null | sed -nE 's/^NEO_RULES="(.*)"$/\1/p'; }

neo_die() { printf 'X neo: %s\n' "$*" >&2; exit "${NEO_RC:-1}"; }
neo_info() { printf '%s\n' "$*"; }
neo_warn() { printf '! neo: %s\n' "$*" >&2; }

# neo_root: the work tree root of the repository the caller stands in.
neo_root() { git rev-parse --show-toplevel 2>/dev/null || neo_die "not inside a git repository"; }

# neo_ns: the vendored .neo directory of that repository.
neo_ns() { printf '%s/.neo' "$(neo_root)"; }

# neo_conf KEY [DEFAULT]: one value from .neo/conf (key=value, spaces
# around = ignored). With NEO_CONF_REV set, the conf committed at that
# revision is read instead of the work tree's, so land applies dev's policy
# and a lane can never relax its own gates. A key set twice is an error, so
# a merge residue never changes policy silently.
neo_conf_text() {
  if [ -n "${NEO_CONF_REV:-}" ]; then
    git show "$NEO_CONF_REV:.neo/conf" 2>/dev/null || true
  elif [ -f "$(neo_ns)/conf" ]; then
    cat "$(neo_ns)/conf"
  fi
}
neo_conf() {
  local key="$1" def="${2-}" text n v
  text=$(neo_conf_text)
  n=$(grep -cE "^[[:space:]]*${key}[[:space:]]*=" <<<"$text" || true)
  case "$n" in
    0) printf '%s' "$def"; return 0 ;;
    1) ;;
    *) NEO_RC=2 neo_die "conf sets $key more than once; keep one line" ;;
  esac
  v=$(sed -nE "s/^[[:space:]]*${key}[[:space:]]*=[[:space:]]*//p" <<<"$text" | sed -E 's/[[:space:]]+$//')
  if [ -z "$v" ]; then printf '%s' "$def"; else printf '%s' "$v"; fi
}

# neo_has_remote: 0 when an origin remote is configured.
neo_has_remote() { git remote get-url origin >/dev/null 2>&1; }

# neo_branch: the current branch name, empty when detached.
neo_branch() { git symbolic-ref --short -q HEAD 2>/dev/null || true; }

# neo_tmpdir NAME: a private temp directory honouring TMPDIR.
neo_tmpdir() { mktemp -d "${TMPDIR:-/tmp}/neo-$1.XXXXXX"; }

# neo_clone_id: this clone's private random id (in the git dir, never pushed).
# land's proof note carries it, so pre-push trusts only notes this clone wrote.
neo_clone_id() {
  local f; f="$(git rev-parse --git-common-dir)/neo-clone-id"
  [ -s "$f" ] || od -An -N8 -tx1 /dev/urandom | tr -d ' \n' > "$f"
  cat "$f"
}

# neo_lane_parse REF -> "kind slug" for lane/<kind>/<number>.<slug> or
# attic/<kind>/<number>.<slug> (and the unnumbered lane/<kind>/<slug> of a
# lane made before numbers or by hand); the slug comes without its number.
neo_lane_parse() {
  local r="${1#refs/heads/}" k s n
  case "$r" in
    lane/*/*|attic/*/*) ;;
    *) return 1 ;;
  esac
  k=$(printf '%s' "$r" | cut -d/ -f2); s=$(printf '%s' "$r" | cut -d/ -f3-)
  case "$s" in
    *.*) n="${s%%.*}"; s="${s#*.}"; [[ "$n" =~ ^$NEO_NUM_RE$ ]] || return 1 ;;
  esac
  neo_kind_ok "$k" && neo_slug_ok "$s" || return 1
  printf '%s %s\n' "$k" "$s"
}

# Lane numbers. A lane is named lane/<kind>/<number>.<slug>: the number
# orders lanes by creation and is never handed out twice, online or offline.
#   - online it is n<N>, N one more than the highest number this clone knows
#     of (never below the count of merges on dev), reserved on origin by one
#     atomic, create-only push of refs/safety/numbers/n<N> with the lane's
#     anchor; when another clone took it first, neo counts again and retries,
#     so origin serializes every online number;
#   - with origin unreachable it is n<N>-<c>, c the first six hex digits of
#     this clone's private id: two offline machines may count the same N but
#     never write the same number, and the clone's own work trees reserve it
#     create-only in the refs they share;
#   - with no origin at all (a single clone) it is n<N>, reserved locally.
# refs/safety/numbers/<number> names the lane's anchor, so it is kept like an
# anchor (never deleted or moved) and its tagger date is the creation time:
# by number, then by that date, every lane ever started, landed, open or
# abandoned, keeps its creation order. A landed merge carries its number in
# the Lane-Number: trailer.
NEO_NUM_RE='n[0-9]+(-[0-9a-f]{6})?'
# neo_lane_number REF: the number in REF's name (empty for an unnumbered lane).
neo_lane_number() {
  local n="${1#refs/heads/}"; n="${n##*/}"
  case "$n" in *.*) n="${n%%.*}"; [[ "$n" =~ ^$NEO_NUM_RE$ ]] && printf '%s' "$n" ;; esac
  return 0
}

neo_kind_ok() { case " $NEO_KINDS " in *" $1 "*) return 0 ;; esac; return 1; }
neo_slug_ok() { [[ "$1" =~ ^[a-z0-9][a-z0-9-]{1,47}$ ]]; }

# neo_trailer COMMIT KEY: the value of trailer KEY in COMMIT's message.
neo_trailer() {
  git log -1 --format=%B "$1" | git interpret-trailers --parse | sed -nE "s/^$2: (.*)$/\1/p" | sed -n 1p
}

# Safety anchors ("safety anchors stay forever"). Every lane keeps the commit
# it forked from under refs/safety/<kind>/<name> for the life of the
# repository: neo lane writes it at the fork point, every push that carries
# the lane carries it (pre-push, land, lane --close), and nothing deletes or
# moves it (pre-push, the agent guard). The ref names an annotated tag
# object, so it records who forked when. A lane made by hand or before
# anchors existed gets one at the point it leaves dev when it is first pushed
# or landed.
NEO_ZERO=0000000000000000000000000000000000000000
# neo_anchor_ref REF -> refs/safety/<kind>/<name> for lane/<kind>/<name> or attic/<kind>/<name>.
neo_anchor_ref() {
  local r="${1#refs/heads/}"
  r="${r#lane/}"; r="${r#attic/}"
  printf 'refs/safety/%s' "$r"
}
# neo_anchor_make REF FORK [REMOTE]: write REF's anchor at FORK unless one
# exists; prints the anchor ref. With REMOTE, an anchor the remote already
# holds (a lane shared from another clone) is fetched instead of written.
neo_anchor_make() {
  local ref obj fork name
  ref=$(neo_anchor_ref "$1"); name="${ref#refs/safety/}"
  if [ -n "${3:-}" ] && ! git rev-parse -q --verify "$ref" >/dev/null \
     && [ -n "$(git ls-remote "$3" "$ref" 2>/dev/null || true)" ]; then
    git fetch -q --no-tags "$3" "$ref:$ref" 2>/dev/null || true
  fi
  if ! git rev-parse -q --verify "$ref" >/dev/null; then
    obj=$(neo_anchor_object "$name" "$2")
    # create only: when another work tree wrote it a moment ago, that one stands
    git update-ref "$ref" "$obj" "$NEO_ZERO" 2>/dev/null || true
  fi
  printf '%s' "$ref"
}
# neo_anchor_object NAME FORK: a new anchor tag object for <kind>/<name> on FORK (no ref written).
neo_anchor_object() {
  local fork; fork=$(git rev-parse "$2^{commit}")
  printf 'object %s\ntype commit\ntag safety/%s\ntagger %s\n\nneo lane %s: fork point %s\n' \
    "$fork" "$1" "$(git var GIT_COMMITTER_IDENT)" "$1" "$fork" | git mktag
}
# neo_anchor_refs REF: the refs that travel with lane REF: its anchor and,
# when it is numbered and reserved here, refs/safety/numbers/<number>.
neo_anchor_refs() {
  local n; neo_anchor_ref "$1"; printf '\n'
  n=$(neo_lane_number "$1")
  if [ -n "$n" ] && git rev-parse -q --verify "refs/safety/numbers/$n" >/dev/null; then printf 'refs/safety/numbers/%s\n' "$n"; fi
  return 0
}
