# shellcheck shell=bash
# identity.sh - known commit identities.
#
# .neo/identity-map lists the identities that may author commits, one per
# line: "<email> <name> [agent]" (# comments allowed). A commit's author is
# known when its email is listed. A row ending in "agent" is an AI agent:
# its commits carry the model in the author name, "<name> (<Model>)", so
# blame tells which model wrote each line. A repository whose map lists nobody accepts
# any author with a real email (not empty, not a placeholder), so a fresh
# setup works before the team fills the map. A row that is a lone "*" keeps
# that openness for humans while the listed rows still apply: an open
# project can enforce its agents' model stamps without listing every human.
# A row ending in "owner" names the owner, who alone promotes dev to main
# (neo release, lib/policy.sh); owner rows alone keep the map open, and an
# email that also has an agent row is an agent, never an owner. A "*" row
# never admits an unlisted address at a domain an agent row uses, so an agent
# cannot pass as a human by inventing an address next to its own.

# With NEO_CONF_REV set (land: dev's tip; history: each merge's first
# parent) the map committed there rules, never a lane's own copy.
neo_identity_rows() {
  local f text
  # a caller that checks many commits against one map sets it once (history.sh)
  if [ "${NEO_ID_ROWS_SET:-}" = 1 ]; then printf '%s\n' "${NEO_ID_ROWS:-}" | sed '/^$/d'; return 0; fi
  if [ -n "${NEO_CONF_REV:-}" ]; then
    text=$(git show "$NEO_CONF_REV:.neo/identity-map" 2>/dev/null || true)
  else
    f="$(neo_ns)/identity-map"; [ -f "$f" ] || return 0
    text=$(cat "$f")
  fi
  grep -vE '^[[:space:]]*(#|$)' <<<"$text" || true
}

# neo_identity_known EMAIL: 0 when the email may author commits.
neo_identity_known() {
  local email="$1" rows
  case "$email" in ""|*example.com|*example.invalid|*@localhost|you@*) return 1 ;; esac
  rows=$(neo_identity_rows)
  # owner rows name who promotes; alone they do not close the map
  [ -n "$(awk '$NF != "owner"' <<<"$rows")" ] || return 0
  awk '{print $1}' <<<"$rows" | grep -Fx -e "$email" >/dev/null && return 0
  awk '{print $1}' <<<"$rows" | grep -Fx -e '*' >/dev/null || return 1
  # '*' admits any real human email, never an unlisted one at a domain an agent row uses
  [ -z "$(awk -v d="${email##*@}" '$NF == "agent" { n = split($1, p, "@"); if (n > 1 && p[n] == d) print }' <<<"$rows")" ]
}

# neo_identity_agent EMAIL: 0 when any row marks EMAIL as an agent.
neo_identity_agent() {
  [ -n "$1" ] || return 1
  [ -n "$(neo_identity_rows | awk -v e="$1" '$1 == e && $NF == "agent"')" ]
}

# neo_owner_emails: the emails marked owner, one per line; an email that also
# has an agent row is never an owner.
neo_owner_emails() {
  neo_identity_rows | awk '$NF == "owner" { o[$1] = 1 } $NF == "agent" { a[$1] = 1 }
    END { for (e in o) if (!(e in a)) print e }' | sort
}

# neo_identity_pair_problem AUTHOR_EMAIL COMMITTER_EMAIL: empty unless a
# human author sits under an agent committer (rule agent-author): an agent
# that writes a commit authors it as its own agent row, so a foreign
# --author never passes for a human's line.
neo_identity_pair_problem() {
  neo_rule_on agent-author || return 0
  if neo_identity_agent "$2" && ! neo_identity_agent "$1"; then
    echo "author '$1' is not an agent row but the committer '$2' is an agent; an agent authors as its own agent row"
  fi
}

# neo_identity_problem EMAIL NAME: empty when this author may commit, else
# the reason (unknown identity, or an agent commit without a model stamp).
neo_identity_problem() {
  local email="$1" name="$2" row
  neo_identity_known "$email" || { echo "author '$email' is not a known identity"; return 0; }
  # an email with an agent row anywhere in the map is an agent
  row=$(neo_identity_rows | awk -v e="$email" '$1 == e && $NF == "agent"' | sed -n 1p)
  if [ -n "$row" ]; then
    [[ "$name" =~ \ \([A-Za-z0-9][A-Za-z0-9\ ._-]*\)$ ]] \
      || echo "agent author '$name <$email>' carries no model stamp; author as '<name> (<Model>)'"
  fi
}
