# shellcheck shell=bash
# audit.sh - the deterministic commit-audit smells (how-git's git-commit-audit
# lens, sections A and C, neo-git's required commit-audit check), one
# implementation for commit-msg, neo check --each and --audit, neo land,
# pre-push and I4. They run under rule commit-audit (lib/core.sh), so history
# landed before the rule is never judged by it.
#
#   joiner    a subject whose text needs '+', ',', 'and', 'with' or 'plus'
#             joins two concerns: split the commit
#   cause-fix a [FIX] or [HOTFIX] body carries a 'Cause:' paragraph, then a
#             'Fix:' paragraph
#   size      a commit changes at most max_commit_lines lines (default 800,
#             added plus deleted, binary files not counted)
#   test      a [NEW], [FIX] or [HOTFIX] commit that changes behaviour (a
#             path that is not a doc, a test, a requirement file, the register
#             or .neo/conf or .neo/identity-map) also touches a test path
#             (test_paths, shell patterns); the commit right after a Red:
#             commit is exempt, its test is the Red: commit's
# Message smells live in neo_msg_violations (lib/message.sh); this file holds
# the two that read the diff.

# the size cap's default, named once: lint/docs.sh checks RULES' policy table against it
NEO_MAX_COMMIT_LINES_DEFAULT=800
NEO_TEST_PATHS_DEFAULT='test/* tests/* */test/* */tests/* spec/* */spec/* *_test.* *.test.* *_spec.* test_*'

# neo_path_is_test PATH: 0 when PATH matches test_paths (dev's conf).
neo_path_is_test() {
  local p="$1" pat
  set -f
  for pat in $(neo_conf test_paths "$NEO_TEST_PATHS_DEFAULT"); do
    # shellcheck disable=SC2254
    case "$p" in $pat) set +f; return 0 ;; esac
  done
  set +f
  return 1
}

# neo_path_is_doc PATH: 0 for prose, requirements and the policy files.
neo_path_is_doc() {
  case "$1" in
    *.md|*.txt|*.rst|*.adoc|docs/*|*/docs/*|LICENSE*|requirements/*|.neo/conf|.neo/identity-map) return 0 ;;
  esac
  return 1
}

# neo_diff_smells SUBJECT NUMSTAT PREV_RED: the diff smells of one commit,
# one line each. NUMSTAT is 'git diff --numstat' output for the commit;
# PREV_RED is 1 when the commit right before it carries Red:.
neo_diff_smells() {
  local subj="$1" stat="$2" prev_red="${3:-0}" max lines=0 a d p behav=0 tested=0 tag
  neo_rule_on commit-audit || return 0
  max=$(neo_conf max_commit_lines "$NEO_MAX_COMMIT_LINES_DEFAULT")
  [[ "$max" =~ ^[0-9]{1,6}$ ]] && [ "$max" -ge 1 ] || NEO_RC=2 neo_die "max_commit_lines='$max' must be 1 to 999999"
  while IFS=$'\t' read -r a d p; do
    [ -n "${p:-}" ] || continue
    [ "$a" = - ] || lines=$((lines + a))
    [ "$d" = - ] || lines=$((lines + d))
    # a rename reads 'old => new'; judge the new path
    case "$p" in *" => "*) p=$(sed -E 's/\{[^{}]* => ([^{}]*)\}/\1/; s/^.* => //' <<<"$p" | sed 's#//*#/#g') ;; esac
    if neo_path_is_test "$p"; then tested=1
    elif ! neo_path_is_doc "$p"; then behav=1; fi
  done <<<"$stat"
  [ "$lines" -le "$max" ] || echo "changes $lines lines (max_commit_lines=$max); split it into atomic commits"
  tag=$(sed -nE 's/^\[([A-Z]+)\] .*/\1/p' <<<"$subj")
  case "$tag" in
    NEW|FIX|HOTFIX)
      if [ "$behav" = 1 ] && [ "$tested" = 0 ] && [ "$prev_red" != 1 ]; then
        echo "a [$tag] commit changes behaviour and touches no test path (test_paths); commit the change with its test, or tag it [REFACTOR] or [DOCS] if it changes no behaviour"
      fi ;;
  esac
}

# neo_commit_smells C: neo_diff_smells for commit C (its first parent is the base).
neo_commit_smells() {
  local c="$1" prev_red=0 base
  neo_rule_on commit-audit || return 0
  base=$(git rev-parse -q --verify "$c^1" 2>/dev/null || git hash-object -t tree /dev/null)
  [ -z "$(neo_trailer "$c^1" Red 2>/dev/null || true)" ] || prev_red=1
  neo_diff_smells "$(git log -1 --format=%s "$c")" "$(git diff --numstat -M "$base" "$c")" "$prev_red"
}
