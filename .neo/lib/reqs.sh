# shellcheck shell=bash
# reqs.sh - the REQUIREMENTS.md register, generated from requirements/<slug>.md.
#
# The register is the project-reqs model (Hard Requirements, Units of Intent,
# Scrapped) rendered from the requirement files of one tree, so it is a view,
# never a second database and never edited by hand: pre-commit regenerates
# and stages it on every lane commit, neo sync regenerates it in every
# rebased commit, neo land refuses a tree whose register differs from the one
# its requirement files generate, and I8 checks it at every merge made under
# rule reqs-register.
#
# A requirement file is "# <kind>/<slug>", a blank line, the requirement (one
# paragraph), then optional "Key: value" lines, any order:
#   Status: done|in-progress|blocked|intent   (default done: the lane delivers it)
#   Pri: P0|P1|P2|P3                           (default by kind: fix P0, feature P1, else P2)
#   Tests: <path> [<path>...]                  (default: the scenarios S<nn> the text names)
#   Source: internal|jira-<KEY>                (default: jira-<Ticket> with a ticket, else internal)
#   Code: <path> [<path>...]                   (the code it maps to; Trace also names the lane)
#   Sprint: backlog|<sprint>                   (intents; default backlog)
#   Notes: <text>                              (intents)
#   Scraps: <slug>: <why>                      (moves <slug> to Scrapped; terminal)
#   Promotes: <slug>                           (retires intent <slug>; this row carries the crumb)
#   Completes: <slug>                          (an in-progress or blocked <slug> is done)
# Landed files are never edited (I8), so a later state is written by the lane
# that changes it, in its own file. IDs are <reqs_id>-R-<slug> (Hard) and
# <reqs_id>-I-<slug> (intent): the slug is unique for the life of the
# repository (I7) and chosen offline with no counter, so two clones never mint
# the same ID. Every Hard Requirement is protected: a test it names must exist
# in the tree, else the register cannot be generated and the commit or land
# is refused until the row is scrapped with a reason.

# neo_reqs_render DIR: print the register for the tree gathered in DIR: its
# requirement files (DIR/requirements/*.md), its .neo/conf (DIR/conf) and the
# list of every path in it (DIR/paths). Exit 1 with the reasons on stderr when
# a requirement breaks the model.
neo_reqs_render() {
  local d="$1" id scen files
  id=$(sed -nE 's/^[[:space:]]*reqs_id[[:space:]]*=[[:space:]]*([A-Za-z0-9]+)[[:space:]]*$/\1/p' "$d/conf" 2>/dev/null | sed -n 1p)
  scen=$(sed -nE 's#^\.neo/tests/scenarios/([0-9]+-[a-z0-9-]+\.sh)$#\1#p' "$d/paths" | tr '\n' ' ')
  files=$(find "$d/requirements" -maxdepth 1 -type f -name '*.md' 2>/dev/null | LC_ALL=C sort)
  if [ -z "$files" ]; then printf '# %s Requirements\n\nNo requirements yet.\n' "${id:-REQ}"; return 0; fi
  # shellcheck disable=SC2016,SC2086
  awk -v ID="${id:-REQ}" -v SCEN=" $scen " -v PATHS="$d/paths" '
    function trim(s) { sub(/^[[:space:]]+/, "", s); sub(/[[:space:]]+$/, "", s); return s }
    function cell(s) { gsub(/\|/, "\\|", s); return s }
    function err(m) { print "X requirements: " m > "/dev/stderr"; bad = 1 }
    function exists(p) { return (p in tree) }
    BEGIN { while ((getline l < PATHS) > 0) tree[l] = 1; close(PATHS) }
    FNR == 1 {
      n++; f = FILENAME; sub(/.*\//, "", f); sub(/\.md$/, "", f); slug[n] = f; text[n] = ""; inbody = 0
      if ($0 ~ /^# [a-z]+\/[a-z0-9-]+$/) { split(substr($0, 3), ks, "/"); kind[n] = ks[1] } else { kind[n] = ""; err("requirements/" f ".md does not start with # <kind>/<slug>") }
      next
    }
    # the requirement is the first paragraph after the header; Key: value lines follow it
    trim($0) == "" { if (text[n] != "") inbody = 1; next }
    inbody && /^(Status|Pri|Tests|Source|Code|Sprint|Notes|Scraps|Promotes|Completes|Ticket): / {
      k = $0; sub(/:.*/, "", k); v = trim(substr($0, length(k) + 3))
      if (k == "Scraps") { t = v; sub(/:.*/, "", t); w = v; sub(/^[^:]*:[[:space:]]*/, "", w); if (t == v) w = ""
        if (t in scrapby) err("requirement " t " is scrapped twice"); scrapby[t] = n; scrapwhy[t] = w; next }
      if (k == "Promotes") { if (v in promby) err("intent " v " is promoted twice"); promby[v] = n; next }
      if (k == "Completes") { if (v in compby) err("requirement " v " is completed twice"); compby[v] = n; next }
      fld[n, k] = v; next
    }
    !inbody { l = trim($0); text[n] = (text[n] == "" ? l : text[n] " " l) }
    END {
      for (i = 1; i <= n; i++) { idx[slug[i]] = i }
      for (s in scrapby) if (!(s in idx)) err("Scraps names " s ", which has no requirements/" s ".md")
      for (s in promby) if (!(s in idx)) err("Promotes names " s ", which has no requirements/" s ".md")
      for (s in compby) if (!(s in idx)) err("Completes names " s ", which has no requirements/" s ".md")
      hard = 0; intent = 0; scrapped = 0; done_ = 0; prog = 0; blk = 0; gap = 0
      for (i = 1; i <= n; i++) {
        s = slug[i]; st = ((i, "Status") in fld) ? fld[i, "Status"] : "done"
        if (st !~ /^(done|in-progress|blocked|intent)$/) err(s ": Status " st " is not done, in-progress, blocked or intent")
        if (s in compby) { if (st != "in-progress" && st != "blocked") err(s ": Completes needs an in-progress or blocked requirement"); st = "done" }
        if (s in promby) { if (st != "intent") err(s ": Promotes needs an intent"); st = "promoted" }
        if (s in scrapby) st = "scrapped"
        state[i] = st
        pri = ((i, "Pri") in fld) ? fld[i, "Pri"] : (kind[i] == "fix" ? "P0" : (kind[i] == "feature" ? "P1" : "P2"))
        if (pri !~ /^P[0-3]$/) err(s ": Pri " pri " is not P0 to P3")
        prio[i] = pri
        src = ((i, "Source") in fld) ? fld[i, "Source"] : (((i, "Ticket") in fld) ? "jira-" fld[i, "Ticket"] : "internal")
        source[i] = src
        tests = ""
        if ((i, "Tests") in fld) {
          m = split(fld[i, "Tests"], tp, /[ ,]+/)
          for (j = 1; j <= m; j++) if (tp[j] != "") {
            if (!exists(tp[j])) { if (st != "scrapped" && st != "intent" && st != "promoted") err(s ": names test " tp[j] ", which the tree lacks; a protected requirement keeps its test (scrap it with a reason to drop it)") }
            tests = tests (tests == "" ? "" : " ") "`" tp[j] "`"
          }
        } else {
          rest = text[i]; delete seen
          while (match(rest, /S[0-9][0-9]/)) {
            num = substr(rest, RSTART + 1, 2); rest = substr(rest, RSTART + RLENGTH)
            if (num in seen) continue; seen[num] = 1
            if (match(SCEN, " " num "-[a-z0-9-]+\\.sh ")) { p = substr(SCEN, RSTART + 1, RLENGTH - 2); tests = tests (tests == "" ? "" : " ") "`.neo/tests/scenarios/" p "`"; rest = rest }
          }
        }
        if (tests == "" && (st == "done" || st == "in-progress" || st == "blocked")) gap++
        tcell[i] = tests == "" ? "⚠️ needs units" : "✅ " tests
        trace = "`" kind[i] "/" s "`"
        if ((i, "Code") in fld) { m = split(fld[i, "Code"], cp, /[ ,]+/); for (j = 1; j <= m; j++) if (cp[j] != "") trace = trace " · `" cp[j] "`" }
        trc[i] = trace
      }
      for (s in promby) { j = promby[s]; trc[j] = trc[j] " · promoted from " ID "-I-" s }
      for (i = 1; i <= n; i++) {
        if (state[i] == "done") done_++; else if (state[i] == "in-progress") prog++; else if (state[i] == "blocked") blk++
        if (state[i] == "done" || state[i] == "in-progress" || state[i] == "blocked") hard++
        else if (state[i] == "intent") intent++
        else if (state[i] == "scrapped") scrapped++
      }
      if (bad) exit 1
      printf "# %s Requirements\n\n", ID
      print "> Single-doc requirements register (project-reqs skill)."
      print "> Lifecycle: intent → in-progress → done   (off-ramps: blocked, scrapped)"
      print "> Protection: every Hard Requirement is protected until explicitly scrapped."
      print "> JIRA: a ticket is a Unit of Intent until its sprint is active, then it promotes."
      print "> Generated from requirements/<slug>.md by neo (.neo/lib/reqs.sh); never edit it by hand:"
      print "> pre-commit regenerates it, and neo land refuses a register that differs from its tree."
      print ""
      print "## Hard Requirements"
      print "<!-- Committed + protected. A regression against any row here is a release-blocker. -->"
      print ""
      print "| ID | Requirement | Pri | Status | Tests | Source | Trace |"
      print "|----|-------------|-----|--------|-------|--------|-------|"
      for (i = 1; i <= n; i++) if (state[i] == "done" || state[i] == "in-progress" || state[i] == "blocked")
        printf "| %s-R-%s | %s | %s | %s | %s | %s | %s |\n", ID, slug[i], cell(text[i]), prio[i],
          (state[i] == "done" ? "✅ done" : (state[i] == "blocked" ? "🚫 blocked" : "in-progress")), tcell[i], source[i], trc[i]
      print ""
      print "## Units of Intent"
      print "<!-- NOT binding, NOT protected. Promotes to a Hard Requirement through a lane whose file says Promotes: <slug>. -->"
      print ""
      print "| ID | Intent | Pri | Source | Sprint | Notes |"
      print "|----|--------|-----|--------|--------|-------|"
      for (i = 1; i <= n; i++) if (state[i] == "intent")
        printf "| %s-I-%s | %s | %s | %s | %s | %s |\n", ID, slug[i], cell(text[i]), prio[i], source[i],
          (((i, "Sprint") in fld) ? fld[i, "Sprint"] : "backlog"), cell(((i, "Notes") in fld) ? fld[i, "Notes"] : "")
      print ""
      print "## Scrapped"
      print "<!-- Graveyard. Kept for traceability. Never deleted. -->"
      print ""
      print "| ID | Requirement | Scrapped | Why |"
      print "|----|-------------|----------|-----|"
      for (i = 1; i <= n; i++) if (state[i] == "scrapped") {
        j = scrapby[slug[i]]
        printf "| %s-%s-%s | %s | `%s/%s` | %s |\n", ID, (((i, "Status") in fld) && fld[i, "Status"] == "intent" ? "I" : "R"), slug[i], cell(text[i]), kind[j], slug[j], cell(scrapwhy[slug[i]])
      }
    }' $files
}

# neo_reqs_gather_rev REV DIR: fill DIR (see neo_reqs_render) from revision REV.
neo_reqs_gather_rev() {
  local rev="$1" d="$2"
  git ls-tree -r --name-only "$rev" > "$d/paths"
  git show "$rev:.neo/conf" > "$d/conf" 2>/dev/null || : > "$d/conf"
  mkdir -p "$d/requirements"
  if git cat-file -e "$rev:requirements" 2>/dev/null; then git archive "$rev" requirements | tar -x -C "$d"; fi
}

# neo_reqs_gather_index DIR: fill DIR from the index (GIT_INDEX_FILE when set).
neo_reqs_gather_index() {
  local d="$1"
  git ls-files > "$d/paths"
  git show ":.neo/conf" > "$d/conf" 2>/dev/null || : > "$d/conf"
  mkdir -p "$d/requirements"
  git ls-files -z -- 'requirements/*.md' | xargs -0 git checkout-index --prefix="$d/" -- 2>/dev/null || true
}

# neo_reqs_gen_rev REV: the register REV's requirement files generate (stdout).
neo_reqs_gen_rev() {
  local d rc=0
  d=$(neo_tmpdir reqs)
  neo_reqs_gather_rev "$1" "$d"
  neo_reqs_render "$d" || rc=$?
  rm -rf "$d"
  return "$rc"
}

# neo_reqs_drift REV: empty when REV's REQUIREMENTS.md is the register its
# requirement files generate, else one line saying why.
neo_reqs_drift() {
  local rev="$1" want have err
  err=$(mktemp "${TMPDIR:-/tmp}/neo-reqs.XXXXXX")
  if ! want=$(neo_reqs_gen_rev "$rev" 2>"$err"); then
    echo "the requirement files break the register model: $(tr '\n' ';' < "$err")"; rm -f "$err"; return 0
  fi
  rm -f "$err"
  # a tree with no requirement file needs no register
  [ "$want" != "$(printf '%s\n\nNo requirements yet.' "$(sed -n 1p <<<"$want")")" ] || git cat-file -e "$rev:REQUIREMENTS.md" 2>/dev/null || return 0
  have=$(git show "$rev:REQUIREMENTS.md" 2>/dev/null) || { echo "REQUIREMENTS.md is missing; it is generated from requirements/"; return 0; }
  [ "$have" = "$want" ] || echo "REQUIREMENTS.md differs from the register requirements/ generates"
}

# neo_reqs_write_index: regenerate REQUIREMENTS.md from the index and stage it
# when it changed (pre-commit, neo sync, neo check --reqs --write). Prints the
# model errors and returns 1 when the requirement files break the model.
neo_reqs_write_index() {
  local d top out rc=0
  top=$(git rev-parse --show-toplevel)
  [ -n "$(git ls-files -- 'requirements/*.md')" ] || [ -n "$(git ls-files -- REQUIREMENTS.md)" ] || return 0
  d=$(neo_tmpdir reqs)
  neo_reqs_gather_index "$d"
  out=$(neo_reqs_render "$d") || rc=$?
  rm -rf "$d"
  [ "$rc" = 0 ] || return 1
  if [ "$out" != "$(git show :REQUIREMENTS.md 2>/dev/null || true)" ]; then
    printf '%s\n' "$out" > "$top/REQUIREMENTS.md"
    git add -- "$top/REQUIREMENTS.md"
  fi
}
