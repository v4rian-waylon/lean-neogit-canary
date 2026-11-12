# shellcheck shell=bash
# policy.sh - who may land, how big a lane may be, which gates run.
#
# conf keys (all optional):
#   land_who=anyone|list     who may land a lane (default anyone)
#   land_list=a@x,b@x        allowed lander emails when land_who=list
#   max_commits=N            most commits one lane may carry (default 20)
#   commit_body=required|optional  required: a NEW, FIX, REFACTOR, REVERT or HOTFIX commit carries a body
#                            line of five words or more (default required)
#   requirement_proof=required|optional  required: a lane's requirement states eight words or more and a
#                            Proof: <path or S<nn>> line naming what proves it in the lane tip (default required)
#   docs_rules=c=d,c2=d2     pairs <code glob>=<doc glob>: a lane changing code matching c changes a doc matching
#                            d, or its requirement says Docs: none (<reason>); the merge records which (default unset)
#   land_pr=optional|required  required: a land goes through review (neo land --pr)
#   land_approvals=N         approving reviews land --pr waits for (default 1)
#   forge_repo=OWNER/REPO    the forge repository when origin's URL does not name it
#   tracker=none             the committed conf may only say none (lib/tracker.sh)
#   reqs_id=TOKEN            the project token of REQUIREMENTS.md IDs, <TOKEN>-R-<slug> (default REQ; lib/reqs.sh)
#   release_who=owner|list   who may promote dev to main (default owner: the identity-map rows marked owner)
#   release_list=a@x,b@x     allowed releaser emails when release_who=list (an agent row never releases)
#   gates_commit=<command>   run by the pre-commit hook on the staged tree of every lane commit (default none)
#   max_commit_lines=N       most lines one lane commit may change, added plus deleted (default 800; lib/audit.sh)
#   test_paths=<patterns>    shell patterns of test paths, space separated (default lib/audit.sh's list); a
#                            [NEW], [FIX] or [HOTFIX] commit that changes behaviour touches one of them
#   gates_fast=<command>     run on every lane commit by check --each
#   gates_full=<command>     run on the merge tree before a land
#   gates_release=<command>  run on dev before a release
#   gate_paths=p1,p2         files the gates read besides the tree's own (an absolute path, or a path in the
#                            tree): their content joins the gatecfg key of stored gate results (default unset;
#                            lib/gatestore.sh)
# A gate is one shell command run from the tree's root; exit 0 passes.
# An empty gate passes and is reported as "none"; so does the explicit value
# "none", which land requires for gates_full instead of an unset key.

# the defaults, named once: lint/docs.sh checks RULES' policy table against them
NEO_MAX_COMMITS_DEFAULT=20

neo_policy_may_land() {
  local who email list
  who=$(neo_conf land_who anyone)
  email=$(git var GIT_AUTHOR_IDENT 2>/dev/null | sed -E 's/.*<([^>]*)>.*/\1/')
  case "$who" in
    anyone) return 0 ;;
    list)
      list=$(neo_conf land_list "")
      if [ -n "$email" ] && tr ',' '\n' <<<"$list" | grep -Fx -- "$email" >/dev/null; then return 0; fi
      echo "'${email:-<no identity>}' is not in land_list (land_who=list)"; return 1 ;;
    *) echo "land_who='$who' is not anyone or list"; return 1 ;;
  esac
}

# neo_policy_may_release MAIN DEV EMAIL...: 0 when every EMAIL may promote
# dev to main, else prints why. main is production: release_who,
# release_list and the owner rows are read as committed at MAIN (main's tip,
# or for a push the main it moves from), so a lane landed on dev never grants
# itself the right. While MAIN's map names no owner (a repository not yet
# released under this rule) the owner rows at DEV rule; neo setup writes the
# setup author as owner in the root commit, so a new repository starts with
# one. An agent row, at MAIN or at DEV, never releases.
neo_policy_may_release() {
  local main="$1" dev="$2" who list e
  shift 2
  who=$(NEO_CONF_REV="$main" neo_conf release_who owner)
  case "$who" in
    owner)
      list=$(NEO_CONF_REV="$main" neo_owner_emails | tr '\n' ',')
      [ -n "$list" ] || list=$(NEO_CONF_REV="$dev" neo_owner_emails | tr '\n' ',')
      if [ -z "$list" ]; then
        echo "main is production and no .neo/identity-map row is marked owner; the owner lands the row '<email> <name> owner' through a lane"; return 1
      fi ;;
    list)
      list=$(NEO_CONF_REV="$main" neo_conf release_list "")
      if [ -z "$list" ]; then echo "main is production and release_list is empty at main (release_who=list); the owner sets it"; return 1; fi ;;
    *) echo "release_who='$who' is not owner or list"; return 1 ;;
  esac
  list="${list%,}"
  for e in "$@"; do
    if NEO_CONF_REV="$main" neo_identity_agent "$e" || NEO_CONF_REV="$dev" neo_identity_agent "$e"; then
      echo "main is production; '$e' is an agent row and an agent never promotes dev to main: report that dev is ready"; return 1
    fi
    if [ -z "$e" ] || ! tr ',' '\n' <<<"$list" | grep -Fx -- "$e" >/dev/null; then
      echo "main is production; only $list promotes dev to main ('${e:-<no identity>}' may not)"; return 1
    fi
  done
  return 0
}

neo_policy_max_commits() {
  local m; m=$(neo_conf max_commits "$NEO_MAX_COMMITS_DEFAULT")
  [[ "$m" =~ ^[0-9]{1,4}$ ]] && [ "$m" -ge 1 ] || NEO_RC=2 neo_die "max_commits='$m' must be 1 to 9999"
  printf '%s' "$m"
}

# neo_gate_missing [DIR]: one line per gate whose command names a .neo/tests
# or .neo/lint script DIR (default the work tree root) does not have, as a
# fresh vendor that dropped the framework's own tests would.
neo_gate_missing() {
  local dir="${1:-.}" g cmd p
  for g in fast full release; do
    cmd=$(neo_conf "gates_$g" "")
    for p in $(grep -oE '\.neo/(tests|lint)/[A-Za-z0-9._/-]+' <<<"$cmd" || true); do
      [ -e "$dir/$p" ] || echo "gates_$g runs $p, which this repository does not have"
    done
  done
}

# neo_path_in GLOBS PATH: 0 when PATH matches one of the comma-separated GLOBS.
neo_path_in() {
  local g gs
  # split on commas only: a glob is never expanded against the work tree
  IFS=, read -r -a gs <<<"$1"
  for g in ${gs[@]+"${gs[@]}"}; do
    g="${g#"${g%%[![:space:]]*}"}"; g="${g%"${g##*[![:space:]]}"}"
    [ -n "$g" ] || continue
    # shellcheck disable=SC2053
    [[ "$2" == $g ]] && return 0
  done
  return 1
}

# neo_docs_named BASE TIP REQFILE: with docs_rules set, a lane that changes
# code matching a rule's code glob changes a doc matching its doc glob, or
# its requirement says "Docs: none (<reason>)". Prints the merge trailer
# ("Docs: <doc>, ..." or "Docs: none (<reason>)"), or on rc 1 the reason.
neo_docs_named() {
  local rules files r code doc hit need="" got="" why p rs
  rules=$(neo_conf docs_rules "")
  [ -n "$rules" ] || return 0
  files=$(git diff --name-only --no-renames "$1" "$2" || true)
  IFS=, read -r -a rs <<<"$rules"
  for r in ${rs[@]+"${rs[@]}"}; do
    code="${r%%=*}"; doc="${r#*=}"; [ -n "$code" ] && [ -n "$doc" ] && [ "$code" != "$r" ] || continue
    hit=""; while IFS= read -r p; do [ -n "$p" ] && neo_path_in "$code" "$p" && hit=1; done <<<"$files"
    [ -n "$hit" ] || continue
    hit=""; while IFS= read -r p; do [ -n "$p" ] && neo_path_in "$doc" "$p" && { hit="$p"; break; }; done <<<"$files"
    if [ -n "$hit" ]; then got="$got, $hit"; else need="$need $code=$doc"; fi
  done
  if [ -n "$need" ]; then
    why=$(sed -nE 's/^Docs: none \((.+)\)$/\1/p' "$3" | sed -n 1p)
    [ -n "$why" ] && { echo "Docs: none ($why)"; return 0; }
    echo "the lane changes code its docs describe and no doc:$need; change the doc, or say 'Docs: none (<reason>)' in the requirement"; return 1
  fi
  [ -z "$got" ] || echo "Docs: ${got#, }"
}

# neo_gate NAME DIR: run gates_NAME in DIR; prints pass|fail|none, rc 0 unless fail.
# With NEO_GATE_TREE set (DIR holds that tree), the run, green or red, is
# recorded in the gate result store (lib/gatestore.sh).
neo_gate() {
  local name="$1" dir="$2" cmd rc=0 log t0
  cmd=$(neo_conf "gates_$name" "")
  if [ -z "$cmd" ] || [ "$cmd" = none ]; then echo none; return 0; fi
  log=$(mktemp "${TMPDIR:-/tmp}/neo-gate-$name.XXXXXX"); t0=$(date +%s)
  # The gate is the project's own command: it runs without neo's internal
  # state (NEO_CONF_REV names a revision of this repository, which a test
  # suite driving other repositories must not inherit).
  ( cd "$dir" && unset NEO_CONF_REV NEO_OFFLINE NEO_RELAND_STEP NEO_GATE_TREE NEO_GATE_STORE && sh -c "$cmd" ) >"$log" 2>&1 || rc=$?
  [ -z "${NEO_GATE_TREE:-}" ] || neo_store_put "$name" "$NEO_GATE_TREE" "$cmd" "$rc" "$(( $(date +%s) - t0 ))" "$log"
  if [ "$rc" = 0 ]; then rm -f "$log"; echo pass; return 0; fi
  # the end of the log: a test runner prints its failures and counts last
  tail -n 25 "$log" | sed 's/^/    | /' >&2; rm -f "$log"
  echo fail; return 1
}

# neo_check_each BASE TIP: the fast gate on every commit of BASE..TIP, in order.
# A failing commit passes only with a Red: trailer and a later green commit:
# the commit right after it must pass and carry no Red: (no chain of reds),
# and a Red: commit whose gate passes is a stale marker, refused. Shared by
# neo check --each, neo land and the pre-push hook (a lane push).
neo_check_each() {
  local base="$1" tip="$2" wt c r subj red last fails=0 prev_red=0
  last=$(git rev-parse "$tip")
  if [ -z "$(neo_conf gates_fast "")" ]; then neo_info "check --each: no fast gate configured"; return 0; fi
  wt=$(neo_tmpdir each)
  git worktree add -q --detach "$wt" "$base" >/dev/null 2>&1
  for c in $(git rev-list --reverse "$base..$tip"); do
    git -C "$wt" checkout -q --detach "$c"
    subj=$(git log -1 --format=%s "$c"); red=$(neo_trailer "$c" Red)
    # land and the train read and fill the gate result store (NEO_GATE_STORE=1);
    # check --each and pre-push run every gate themselves
    if r=$(if [ "${NEO_GATE_STORE:-}" = 1 ] && declare -F neo_gate_stored >/dev/null; then neo_gate_stored fast "$wt" "$(git rev-parse "$c^{tree}")"; else neo_gate fast "$wt"; fi 2>/dev/null); then
      if [ -n "$red" ]; then
        neo_info "  FAIL  $(git rev-parse --short "$c") $subj: stale Red: marker, the fast gate passes (Red: $red)"; fails=1
      else
        neo_info "  pass  $(git rev-parse --short "$c") $subj"
      fi
      prev_red=0
    elif [ -n "$red" ] && [ "$prev_red" = 1 ]; then
      neo_info "  FAIL  $(git rev-parse --short "$c") $subj: a Red: commit follows a Red: commit; the commit after a red one turns it green"; fails=1
    elif [ -n "$red" ] && [ "$c" != "$last" ]; then
      neo_info "  red   $(git rev-parse --short "$c") $subj (marked: Red: $red)"; prev_red=1
    elif [ -n "$red" ]; then
      neo_info "  FAIL  $(git rev-parse --short "$c") $subj: a Red: commit cannot be the lane tip"; fails=1
    else
      neo_info "  FAIL  $(git rev-parse --short "$c") $subj: fast gate fails and no Red: trailer marks it"; fails=1
    fi
  done
  git worktree remove --force "$wt" >/dev/null 2>&1 || true
  return "$fails"
}
