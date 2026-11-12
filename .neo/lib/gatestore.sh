# shellcheck shell=bash
# gatestore.sh - the gate result store and the merge train. Sourced, never executed.
#
# The store keeps one record per gate run, keyed by the tree the gate ran on
# and the gate configuration (gatecfg), under the main repository's git
# common dir, so every clone sharing it (linked work trees) and every agent
# reads the same results:
#   <git common dir>/neo/gated/<tree>-<gatecfg>/<gate>
# gatecfg is a hash of the gate keys of the conf in force (gates_fast,
# gates_full, gates_release, gates_commit, gate_paths) and of every file
# gate_paths names (a path inside the tree by its blob in the gated tree, an
# absolute path by its content on disk): a changed gate command or gate script
# changes it, so an old result never answers for a new gate. A record holds
# the gate's command, exit code, duration, log tail, tree and gatecfg; it
# also feeds the gate log notes of the merge it answers for.
# Only a record with exit 0 is ever reused; a red record is kept as a log and
# the gate runs again. The store is a cache: a miss always means gating, and
# correctness never depends on it (neo doctor --prove and pre-push rerun the
# gates without it).
#
# The merge train (<git common dir>/neo/train, one lane per line, in landing
# order): neo train predicts, for each queued lane on top of the predicted
# merges of the lanes before it, the exact commits neo sync would write and
# the merge tree neo land would write, and gates them all in parallel into the
# store. Each land in order then finds its gates green in the store and only
# re-verifies the tree, merges, tags and pushes.

# neo_store_root: the store directory (absolute), shared by every work tree.
neo_store_root() {
  local c; c=$(git rev-parse --git-common-dir)
  c=$(cd "$c" && pwd)
  printf '%s/neo/gated' "$c"
}

# neo_gatecfg TREE: the gate configuration hash for gates run on TREE, from
# the conf in force (NEO_CONF_REV: the conf land applies).
neo_gatecfg() {
  local tree="$1" k p ps
  {
    for k in gates_fast gates_full gates_release gates_commit gate_paths; do
      printf '%s=%s\n' "$k" "$(neo_conf "$k" "")"
    done
    IFS=, read -r -a ps <<<"$(neo_conf gate_paths "")"
    for p in ${ps[@]+"${ps[@]}"}; do
      p="${p#"${p%%[![:space:]]*}"}"; p="${p%"${p##*[![:space:]]}"}"
      [ -n "$p" ] || continue
      case "$p" in
        /*) if [ -f "$p" ]; then printf '%s %s\n' "$p" "$(git hash-object -- "$p")"; else printf '%s missing\n' "$p"; fi ;;
        *) printf '%s %s\n' "$p" "$(git rev-parse -q --verify "$tree:$p" 2>/dev/null || echo missing)" ;;
      esac
    done
  } | git hash-object --stdin
}

# neo_store_file GATE TREE: the record path of GATE on TREE under the gatecfg in force.
neo_store_file() {
  printf '%s/%s-%s/%s' "$(neo_store_root)" "$2" "$(neo_gatecfg "$2")" "$1"
}

# neo_store_green GATE TREE: 0 when the store holds a green run of GATE on
# TREE under the gatecfg in force, with the command the conf names now.
neo_store_green() {
  local f cmd; f=$(neo_store_file "$1" "$2")
  [ -f "$f" ] || return 1
  cmd=$(neo_conf "gates_$1" "")
  grep -Fx "exit=0" "$f" >/dev/null && grep -Fx "command=$cmd" "$f" >/dev/null
}

# neo_store_put GATE TREE CMD RC SECONDS LOGFILE: write one record, atomically
# (a temp file renamed in place), so parallel predictions never read half a record.
neo_store_put() {
  local f d t
  f=$(neo_store_file "$1" "$2"); d=$(dirname "$f")
  mkdir -p "$d" || return 0
  t=$(mktemp "$d/.$1.XXXXXX") || return 0
  {
    printf 'gate=%s\ncommand=%s\nexit=%s\nduration=%ss\ntree=%s\ngatecfg=%s\nat=%s\n' \
      "$1" "$3" "$4" "$5" "$2" "$(basename "$d" | sed "s/^$2-//")" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf -- '--- log tail\n'
    tail -n 25 "$6" 2>/dev/null || true
  } > "$t"
  mv -f "$t" "$f"
}

# neo_gate_stored GATE DIR TREE: GATE's result on TREE, checked out in DIR:
# "pass (stored)" from a green record, else the gate runs (neo_gate, which
# records the run). rc as neo_gate.
neo_gate_stored() {
  if neo_store_green "$1" "$3"; then echo "pass (stored)"; return 0; fi
  NEO_GATE_TREE="$3" neo_gate "$1" "$2"
}

# ---------------------------------------------------------------- train
neo_train_file() { printf '%s/train' "$(dirname "$(neo_store_root)")"; }

# neo_train_lanes: the queued lanes, in landing order, one per line.
neo_train_lanes() {
  local f; f=$(neo_train_file)
  [ -f "$f" ] && sed '/^[[:space:]]*$/d' "$f"
  return 0
}

# neo_train_edit add|drop LANE: queue LANE at the end, or take it out, under
# a short lock (mkdir), so two agents queueing at once both stay queued.
neo_train_edit() {
  local f l i=0 t
  f=$(neo_train_file); l="$f.lock"
  mkdir -p "$(dirname "$f")"
  until mkdir "$l" 2>/dev/null; do i=$((i + 1)); [ "$i" -lt 100 ] || neo_die "the train file is locked ($l); remove it if no neo train is running"; sleep 0.1; done
  t=$(mktemp "$f.XXXXXX")
  { neo_train_lanes | grep -Fxv -- "$2" || true; [ "$1" = drop ] || printf '%s\n' "$2"; } > "$t"
  mv -f "$t" "$f"; rmdir "$l"
}

# neo_predict LANE BASE: the commits neo sync would write for LANE on top of
# BASE (a commit), in a private work tree; no ref moves. Prints
# "<predicted tip> <predicted merge>" (the merge is a dangling commit with
# BASE and the tip as parents, the base for the next lane of the train).
# rc 1 when the rebase stops on a conflict.
neo_predict() {
  local lane="$1" base tip wt
  base=$(git rev-parse "$2^{commit}"); tip=$(git rev-parse "$lane^{commit}")
  if [ "$(git merge-base "$base" "$tip")" != "$base" ]; then
    wt=$(neo_tmpdir predict)
    git worktree add -q --detach "$wt" "$tip" >/dev/null 2>&1
    # neo sync's own rebase: the register regenerated after each replayed commit
    if ! git -C "$wt" -c core.hooksPath=/dev/null rebase -q -x "bash '$NEO_SELF/lib/reqs-fix.sh'" "$base" >/dev/null 2>&1; then
      git -C "$wt" rebase --abort >/dev/null 2>&1 || true
      git worktree remove --force "$wt" >/dev/null 2>&1 || true
      return 1
    fi
    tip=$(git -C "$wt" rev-parse HEAD)
    git worktree remove --force "$wt" >/dev/null 2>&1 || true
  fi
  printf '%s %s\n' "$tip" "$(git commit-tree "$tip^{tree}" -p "$base" -p "$tip" -m "neo train: predicted merge of $lane")"
}

# neo_pregate BASE TIP: the gates neo land runs, on what it would run them
# on, stored: the fast gate on every commit of BASE..TIP and the fast and
# full gates on the merge tree (TIP's tree: the lane contains BASE). The conf
# in force is BASE's, as land applies dev's. Prints one line per gate.
neo_pregate() {
  local base="$1" tip="$2" wt c t r rc=0
  export NEO_CONF_REV="$base"
  wt=$(neo_tmpdir pregate)
  git worktree add -q --detach "$wt" "$base" >/dev/null 2>&1
  for c in $(git rev-list --reverse "$base..$tip"); do
    git -C "$wt" checkout -q --detach "$c"
    r=$(neo_gate_stored fast "$wt" "$(git rev-parse "$c^{tree}")" 2>/dev/null) || true
    printf '  fast  %s %s: %s\n' "$(git rev-parse --short "$c")" "$(git log -1 --format=%s "$c")" "$r"
  done
  t=$(git rev-parse "$tip^{tree}")
  git -C "$wt" checkout -q --detach "$tip"
  for c in fast full; do
    r=$(neo_gate_stored "$c" "$wt" "$t" 2>/dev/null) || rc=1
    printf '  %-5s merge tree %s: %s\n' "$c" "$(git rev-parse --short "$t")" "$r"
  done
  git worktree remove --force "$wt" >/dev/null 2>&1 || true
  return "$rc"
}
