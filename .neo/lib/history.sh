# shellcheck shell=bash
# history.sh - the history invariants I1 to I9, checked by doctor --history
# and, per landed merge, by pre-push. Each check prints "<Id> <sha> <why>"
# for every violation; empty output means the history holds.
#
#   I1 every first-parent commit on dev after the root is a two-parent merge
#      whose second-parent range is linear
#   I2 every such merge carries exactly one version tag, the next version
#      after the previous one (version.sh)
#   I3 the merge subject is "[MERGE] <kind>/<slug> into dev: <version>" and
#      its trailers Lane-Base, Gates, Tested-Tree and Requirement are present,
#      Tested-Tree equal to the merge's tree, Lane-Base equal to its first parent;
#      under the lane-number rule also Lane-Number, a lane number (core.sh)
#   I4 the lane holds 1 to max_commits commits, each with a ruled subject, a
#      known author and committer (model-stamped for agents; an agent committer
#      never carries a human author), no commit-audit smell (lib/audit.sh) and at most one
#      Red: trailer, on a [TEST] commit that neither ends the lane nor follows
#      another Red: commit, and each change commit with a body line (commit_body)
#   I5 main is an ancestor of dev and, past the root, carries release/<version>;
#      every release/<version> made under the owner rule is an annotated tag
#      whose tagger the policy at the previous release (or the root) allows
#   I6 every v* and release/* tag sits on dev's first-parent line
#   I7 lane slugs are unique across landed merges, open lanes and the attic,
#      and so are lane numbers: one number never names two lanes
#   I8 requirements/<slug>.md exists at every merge of that lane and at dev's tip,
#      and REQUIREMENTS.md at each merge is the register its requirement files
#      generate (lib/reqs.sh; merges made under rule reqs-register)
#   I9 every superseded merge is re-landed on dev or parked in the attic, and
#      no re-land is left half done

# neo_check_merge M PREV_VERSION PREV_RELEASED: I1-I4 and I8 for one merge;
# prints violations, and on success prints "OK <version>" as its last line.
neo_check_merge() {
  local m="$1" prev="$2" released="$3" n p1 p2 v vs subj slug want tt tree base req c reds f pb
  n=$(git rev-list --parents -n1 "$m" | wc -w | tr -d ' ')
  if [ "$n" != 3 ]; then echo "I1 $m is not a two-parent merge"; return 0; fi
  p1=$(git rev-parse "$m^1"); p2=$(git rev-parse "$m^2")
  if [ -n "$(git rev-list --merges "$p1..$p2")" ]; then echo "I1 $m lane range holds a merge commit"; fi
  vs=$(git tag --points-at "$m" -l 'v*' | grep -cE '^v[0-9]{4}\.[0-9]+\.[0-9]+$' || true)
  v=$(neo_version_of "$m")
  if [ "$vs" != 1 ]; then echo "I2 $m carries $vs version tags (want 1)"; fi
  subj=$(git log -1 --format=%s "$m")
  f=$(mktemp "${TMPDIR:-/tmp}/neo-msg.XXXXXX"); git log -1 --format=%B "$m" >"$f"
  while IFS= read -r line; do [ -n "$line" ] && echo "I3 $m $line"; done <<<"$(neo_msg_violations "$f" merge)"
  rm -f "$f"
  if [ -n "$v" ]; then
    want=$(neo_version_next "$prev" "$released" "${v:1:4}")
    [ "$v" = "$want" ] || echo "I2 $m is $v, expected $want after ${prev:-<none>}"
    case "$subj" in *": $v") ;; *) echo "I3 $m subject does not name its tag $v" ;; esac
  fi
  slug=$(sed -nE 's/^\[MERGE\] [a-z]+\/([a-z0-9-]+) into dev: .*/\1/p' <<<"$subj")
  local trs; trs=$(git log -1 --format=%B "$m" | git interpret-trailers --parse)
  base=$(sed -nE 's/^Lane-Base: (.*)$/\1/p' <<<"$trs" | sed -n 1p); tt=$(sed -nE 's/^Tested-Tree: (.*)$/\1/p' <<<"$trs" | sed -n 1p)
  req=$(sed -nE 's/^Requirement: (.*)$/\1/p' <<<"$trs" | sed -n 1p)
  grep -q '^Gates: ' <<<"$trs" || echo "I3 $m has no Gates: trailer"
  tree=$(git rev-parse "$m^{tree}")
  [ "$tt" = "$tree" ] || echo "I3 $m Tested-Tree ${tt:-<missing>} is not its tree $tree"
  [ -n "$base" ] && [ "$(git rev-parse -q --verify "$base^{commit}" 2>/dev/null)" = "$p1" ] \
    || echo "I3 $m Lane-Base ${base:-<missing>} is not its first parent"
  [ "$req" = "requirements/$slug.md" ] || echo "I3 $m Requirement ${req:-<missing>} is not requirements/$slug.md"
  [ -n "$slug" ] && git cat-file -e "$m:requirements/$slug.md" 2>/dev/null \
    || echo "I8 $m has no requirements/${slug:-?}.md"
  # the register at the merge is the one its requirement files generate (rule reqs-register, read at p1)
  if case " $(neo_rules_at "$p1") " in *" reqs-register "*) true ;; *) false ;; esac; then
    local rd; rd=$(neo_reqs_drift "$m"); [ -z "$rd" ] || echo "I8 $m $rd"
  fi
  n=$(git rev-list --count "$p1..$p2")
  local max; max=$(NEO_CONF_REV="$p1" neo_policy_max_commits)
  if [ "$n" -lt 1 ] || [ "$n" -gt "$max" ]; then echo "I4 $m lane holds $n commits (1 to $max)"; fi
  # the map committed at the merge's first parent judges its lane, read once
  local NEO_ID_ROWS NEO_ID_ROWS_SET=0 who ae an ce
  NEO_ID_ROWS=$(NEO_CONF_REV="$p1" neo_identity_rows); NEO_ID_ROWS_SET=1
  # the rules the framework at the first parent knew judge this lane
  local NEO_RULES_AT prevred=0 red ln
  NEO_RULES_AT=$(neo_rules_at "$p1")
  if neo_rule_on lane-number; then
    ln=$(sed -nE 's/^Lane-Number: (.*)$/\1/p' <<<"$trs" | sed -n 1p)
    [[ "$ln" =~ ^$NEO_NUM_RE$ ]] || echo "I3 $m Lane-Number ${ln:-<missing>} is not a lane number (n<N> or n<N>-<c>)"
  fi
  f=$(mktemp "${TMPDIR:-/tmp}/neo-msg.XXXXXX")
  for c in $(git rev-list --reverse "$p1..$p2"); do
    git log -1 --format=%B "$c" >"$f"
    while IFS= read -r line; do [ -n "$line" ] && echo "I4 $c $line"; done <<<"$(NEO_CONF_REV="$p1" neo_msg_violations "$f")"
    who=$(git log -1 --format='%ae%x09%an%x09%ce' "$c"); IFS=$'\t' read -r ae an ce <<<"$who"
    pb=$(NEO_ID_ROWS_SET=1 NEO_ID_ROWS="$NEO_ID_ROWS" neo_identity_problem "$ae" "$an"); [ -z "$pb" ] || echo "I4 $c $pb"
    NEO_ID_ROWS_SET=1 NEO_ID_ROWS="$NEO_ID_ROWS" neo_identity_known "$ce" || echo "I4 $c committer '$ce' is not a known identity"
    pb=$(NEO_ID_ROWS_SET=1 NEO_ID_ROWS="$NEO_ID_ROWS" neo_identity_pair_problem "$ae" "$ce"); [ -z "$pb" ] || echo "I4 $c $pb"
    while IFS= read -r line; do [ -n "$line" ] && echo "I4 $c $line"; done <<<"$(NEO_CONF_REV="$p1" neo_commit_smells "$c")"
    if neo_rule_on red-test; then
      red=$(grep -cE '^Red: .+' "$f" || true)
      if [ "${red:-0}" -ge 1 ]; then
        [ "$prevred" = 0 ] || echo "I4 $c a Red: commit follows a Red: commit"
        [ "$c" != "$p2" ] || echo "I4 $c a Red: commit is the lane tip"
        prevred=1
      else
        prevred=0
      fi
    fi
  done
  rm -f "$f"
  [ -n "$v" ] && echo "OK $v"
  return 0
}

# neo_history_check [DEV] [MAIN]: every invariant over the whole history.
neo_history_check() {
  local dev="${1:-dev}" main="${2:-main}" since="${NEO_HISTORY_SINCE:-}" checking=1 root c out prev="" released=0 v t tc slugs dup s r
  git rev-parse -q --verify "$dev^{commit}" >/dev/null || { echo "I1 - no $dev branch"; return 0; }
  root=$(git rev-list --first-parent --max-parents=0 "$dev" | tail -n 1)
  [ -z "$since" ] || { since=$(git rev-parse -q --verify "$since^{commit}") || { echo "I1 - unknown revision for --since"; return 0; }; checking=0; }
  [ "$since" != "$root" ] || checking=1
  for c in $(git rev-list --first-parent --reverse "$dev"); do
    [ "$c" = "$root" ] && continue
    if [ "$checking" = 0 ]; then
      # before SINCE: only the version chain, for the checks that follow
      v=$(neo_version_of "$c"); [ -z "$v" ] || { prev="$v"; if git rev-parse -q --verify "refs/tags/release/$v" >/dev/null; then released=1; else released=0; fi; }
      [ "$c" = "$since" ] && checking=1
      continue
    fi
    out=$(neo_check_merge "$c" "$prev" "$released")
    grep -v '^OK ' <<<"$out" | sed '/^$/d' || true
    v=$(sed -nE 's/^OK (.*)$/\1/p' <<<"$out")
    if [ -n "$v" ]; then
      prev="$v"
      if git rev-parse -q --verify "refs/tags/release/$v" >/dev/null; then released=1; else released=0; fi
    fi
  done
  # I5
  if git rev-parse -q --verify "$main^{commit}" >/dev/null; then
    git merge-base --is-ancestor "$main" "$dev" || echo "I5 - $main is not an ancestor of $dev"
    if [ "$(git rev-parse "$main")" != "$root" ]; then
      v=$(neo_version_of "$main")
      [ -n "$v" ] && git rev-parse -q --verify "refs/tags/release/$v" >/dev/null \
        || echo "I5 $(git rev-parse "$main") $main tip carries no release/<version> tag"
    fi
  fi
  # I5: main is production; each release was the owner's, by the policy at the release before it
  local gov="$root" rt rtag tagger why
  for c in $(git rev-list --first-parent --reverse "$dev"); do
    v=$(neo_version_of "$c"); [ -n "$v" ] || continue
    rt="refs/tags/release/$v"
    git rev-parse -q --verify "$rt" >/dev/null || continue
    # releases made before the framework knew the owner rule are not judged by it
    if git show "$c:.neo/lib/policy.sh" 2>/dev/null | grep -F 'release_who' >/dev/null; then
      rtag=$(git rev-parse "$rt")
      if [ "$(git cat-file -t "$rtag")" != tag ]; then
        echo "I5 $c release/$v is not an annotated tag"
      else
        tagger=$(git for-each-ref --format='%(taggeremail)' "$rt" | tr -d '<>')
        why=$(neo_policy_may_release "$gov" "$c" "$tagger") || echo "I5 $c release/$v tagged by '${tagger:-<none>}': $why"
      fi
    fi
    gov="$c"
  done
  # I6
  local fp; fp=$(git rev-list --first-parent "$dev")
  for t in $(git tag -l 'v*' 'release/*'); do
    tc=$(git rev-parse "$t^{commit}")
    grep -Fx -- "$tc" <<<"$fp" >/dev/null || echo "I6 $tc tag $t is off dev's first-parent line"
  done
  # I7
  slugs=$( { git log --first-parent --format=%s "$dev" | sed -nE 's/^\[MERGE\] [a-z]+\/([a-z0-9-]+) into dev: .*/\1/p'
             git for-each-ref --format='%(refname:short)' refs/heads/lane refs/heads/attic | sed -nE 's#^(lane|attic)/[a-z]+/##p' | sed -E "s/^$NEO_NUM_RE[.]//"; } )
  dup=$(sort <<<"$slugs" | uniq -d | sed '/^$/d' || true)
  for s in $dup; do
    # a lane still open after it landed is the one allowed repeat: land deletes it, a stale copy is reported
    echo "I7 - lane slug '$s' is used more than once"
  done
  # I7 for numbers: each "number slug" pair once; a number with two slugs is two lanes
  local pairs
  pairs=$( { git log --first-parent --format='%(trailers:key=Lane-Number,valueonly,separator=%x2C)%x09%s' "$dev" \
               | awk -F '\t' '$1 ~ /^n/ && $2 ~ /^\[MERGE\] [a-z]+\/[a-z0-9-]+ into dev: / { split($2, w, " "); sub(/^[a-z]+\//, "", w[2]); print $1, w[2] }'
             git for-each-ref --format='%(refname:short)' refs/heads/lane refs/heads/attic \
               | sed -nE "s#^(lane|attic)/[a-z]+/($NEO_NUM_RE)[.]([a-z0-9-]+)\$#\\2 \\4#p"; } | sort -u )
  for s in $(awk '{ print $1 }' <<<"$pairs" | sort | uniq -d); do
    echo "I7 - lane number '$s' names more than one lane"
  done
  # I8 at the tip
  for s in $(git log --first-parent --format=%s "$dev" | sed -nE 's/^\[MERGE\] [a-z]+\/([a-z0-9-]+) into dev: .*/\1/p'); do
    git cat-file -e "$dev:requirements/$s.md" 2>/dev/null || echo "I8 - requirements/$s.md was deleted after it landed"
  done
  # I9
  neo_reland_pending "$dev" | sed 's/^/I9 - re-land pending: /'
  [ ! -d "$(git rev-parse --git-path neo-reland)" ] || echo "I9 - a neo sync --dev re-land is half done; finish it with --continue or --abort"
  return 0
}

# neo_slug_landed SLUG [DEV]: 0 when DEV's first-parent line holds a merge of SLUG.
neo_slug_landed() {
  git log --first-parent --format=%s "${2:-dev}" 2>/dev/null | grep -E "^\[MERGE\] [a-z]+/$1 into dev: " >/dev/null
}

# neo_reland_pending [DEV]: the superseded merges whose lane is neither on DEV
# nor in the attic, one "tag kind/slug" per line (I9).
neo_reland_pending() {
  local dev="${1:-dev}" t m subj ks
  for t in $(git tag -l 'superseded/*'); do
    m=$(git rev-parse "$t^{commit}"); subj=$(git log -1 --format=%s "$m")
    ks=$(sed -nE 's/^\[MERGE\] ([a-z]+)\/([a-z0-9-]+) into dev: .*/\1 \2/p' <<<"$subj")
    [ -n "$ks" ] || continue
    set -- $ks
    neo_slug_landed "$2" "$dev" && continue
    git for-each-ref --format='%(refname)' refs/heads/attic | sed -E "s#.*/##; s/^$NEO_NUM_RE[.]//" | grep -Fx -- "$2" >/dev/null && continue
    printf '%s %s/%s\n' "$t" "$1" "$2"
  done
}

# neo_prove_merge M [GATES]: re-run the gates (default "fast full") the conf at M's first parent names on
# M's own tree and compare with M's Gates: receipt. Prints "P1 <m> <why>" per
# gate that fails (a receipt that claims a pass it cannot show is a lie).
neo_prove_merge() {
  local m="$1" gates="${2:-fast full}" p1 wt g r receipt claimed out=""
  p1=$(git rev-parse "$m^1"); receipt=$(neo_trailer "$m" Gates)
  wt=$(mktemp -d "${TMPDIR:-/tmp}/neo-prove.XXXXXX")
  git worktree add -q --detach "$wt" "$m" >/dev/null 2>&1 || { echo "P1 $m cannot check out its tree"; return 0; }
  for g in $gates; do
    claimed=$(sed -nE "s/(^|.*[[:space:]])$g=([a-z]+).*/\2/p" <<<"$receipt")
    r=$(NEO_CONF_REV="$p1" neo_gate "$g" "$wt" 2>/dev/null) || true
    if [ "$r" = fail ]; then
      out="$out
P1 $m gate $g fails on the merge tree (receipt says ${claimed:-nothing})"
    fi
  done
  git worktree remove --force "$wt" >/dev/null 2>&1 || true
  [ -z "$out" ] || printf '%s\n' "${out#?}"
  return 0
}

# neo_ungated_range SINCE DEV: the version (or sha) of each first-parent
# merge of DEV after SINCE whose Gates: receipt names no gate that ran.
neo_ungated_range() {
  local since="$1" dev="${2:-dev}" root m range g out=""
  root=$(git rev-list --first-parent --max-parents=0 "$dev" | tail -n 1)
  case "$since" in ""|0000000000000000000000000000000000000000) range="$dev" ;; *) range="$since..$dev" ;; esac
  for m in $(git rev-list --first-parent --reverse $range); do
    [ "$m" = "$root" ] && continue
    g=$(neo_trailer "$m" Gates)
    [[ "$g" == *=pass* ]] && continue
    out="$out $(neo_version_of "$m")"; [ -n "$(neo_version_of "$m")" ] || out="$out$(git rev-parse --short "$m")"
  done
  printf '%s' "${out# }"
}

# neo_prove_range SINCE DEV: neo_prove_merge on each first-parent merge of DEV
# after SINCE (SINCE empty or all zeros: every merge after the root).
neo_prove_range() {
  local since="$1" dev="${2:-dev}" root m range
  root=$(git rev-list --first-parent --max-parents=0 "$dev" | tail -n 1)
  case "$since" in ""|0000000000000000000000000000000000000000) range="$dev" ;; *) range="$since..$dev" ;; esac
  for m in $(git rev-list --first-parent --reverse $range); do
    [ "$m" = "$root" ] && continue
    neo_prove_merge "$m"
  done
}

