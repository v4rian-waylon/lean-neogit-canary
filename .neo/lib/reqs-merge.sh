#!/usr/bin/env bash
# reqs-merge.sh BASE OURS THEIRS - the merge driver of REQUIREMENTS.md (git
# config merge.neo-reqs.driver, set by neo setup, neo sync and neo doctor
# --fix; .git/info/attributes names the file). The register is generated, one
# table row per requirement, so two lanes that each add or change rows merge
# by rows, never by lines: per section, a row one side added is kept, a row
# one side changed takes that side, a row one side removed is dropped, and the
# rows are written in the generator's order (by slug). The result is written
# to OURS (git's %A); exit 0. neo sync and the re-land regenerate the register
# after each replayed commit anyway; this keeps a plain git rebase or merge
# from stopping on it.
set -euo pipefail
base="$1" ours="$2" theirs="$3"
# the frame (title, notes, section headers) comes from the side that has sections, ours first
frame="$ours"; grep -q '^## ' "$ours" || { frame="$theirs"; grep -q '^## ' "$theirs" || frame="$base"; }
awk -v B="$base" -v O="$ours" -v T="$theirs" -v F="$frame" '
  function rows(f, tag,   l, sec, id) {
    sec = ""
    while ((getline l < f) > 0) {
      if (l ~ /^## /) { sec = l; continue }
      if (sec != "" && l ~ /^\| [A-Za-z0-9]+-[RI]-[a-z0-9-]+ \|/) {
        id = l; sub(/^\| /, "", id); sub(/ \|.*/, "", id)
        R[tag, sec, id] = l; ids[sec, id] = 1
      }
    }
    close(f)
  }
  BEGIN {
    rows(O, "o"); rows(B, "b"); rows(T, "t")
    # the frame: lines before the first section, then each section up to its table separator
    sec = ""; insep = 0
    while ((getline l < F) > 0) {
      if (l ~ /^## /) { sec = l; order[++ns] = sec; insep = 0; continue }
      if (sec == "") { head[++nh] = l; continue }
      if (!insep) { n = ++hn[sec]; H[sec, n] = l; if (l ~ /^\|-/) insep = 1 }
    }
    close(F)
    for (i = 1; i <= nh; i++) print head[i]
    for (s = 1; s <= ns; s++) {
      sec = order[s]; print sec
      for (i = 1; i <= hn[sec]; i++) print H[sec, i]
      m = 0
      for (k in ids) {
        split(k, p, SUBSEP); if (p[1] != sec) continue
        id = p[2]; o = ((("o", sec, id) in R) ? R["o", sec, id] : ""); b = ((("b", sec, id) in R) ? R["b", sec, id] : "")
        t = ((("t", sec, id) in R) ? R["t", sec, id] : "")
        if (o == t) v = o; else if (o == b) v = t; else if (t == b) v = o; else v = o
        if (v == "") continue
        slug = id; sub(/^[A-Za-z0-9]+-[RI]-/, "", slug)
        out[++m] = slug ".md\t" v
      }
      if (m > 0) {
        cmd = "LC_ALL=C sort -t \"\t\" -k1,1 | cut -f2-"
        for (i = 1; i <= m; i++) print out[i] | cmd
        close(cmd)
      }
      if (s < ns) print ""
    }
  }' > "$ours.neo-merged"
mv "$ours.neo-merged" "$ours"
