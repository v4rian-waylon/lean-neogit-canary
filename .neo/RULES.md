# neo rules

Each rule below is either enforced, with its enforcement point named, or a
convention, marked as one. The enforcement points are the `pre-commit`,
`prepare-commit-msg`, `commit-msg` and `pre-push` hooks, `neo land` and
`neo release`; the history checks are
`neo doctor --history` (invariants I1 to I9 in `.neo/lib/history.sh`) and
`neo doctor --prove` (every merge's gates rerun on its own tree). Client
hooks are a guard rail for honest work: anyone with a clone can skip them
(`--no-verify`, a hand-written proof note), and the agent guard denies both
to agents. On a forge the authority is the server: the rulesets from
`neo setup --remote` (no deletion or rewrite of dev, main and the attic, no
moved or deleted tag, no update of main except by the repository's admins) and, with `land_pr=required`, GitHub's own review rule
on dev (`land_approvals` approvals given after the last push) plus the
neo-check and commit-audit statuses, which the workflow computes with dev's checker, never the
candidate's. A candidate's gates are its own tests and it can edit the
workflow file, so review, not the status, is what a hostile change meets.

## Branches

| Branch | Moves by | Never |
|---|---|---|
| `dev` | `neo land` only: one merge per lane | a direct commit, a rewrite, a deletion |
| `main` | `neo release` by the owner only: fast-forward to a released dev commit | a commit dev lacks, a rewrite, a deletion, a release by anyone but the owner |
| `lane/<kind>/<number>.<slug>` | your commits; `neo sync` rebases it onto dev | landing without `neo land` |
| `attic/<kind>/<slug>` | `neo lane --close` / `--restore` | deletion: pre-push and the `neo-attic` ruleset refuse it (the reason is a git note) |
| `refs/safety/<kind>/<slug>` | written once by `neo lane` at the fork point | deletion, a move, a hand-written anchor: pre-push and the agent guard refuse them |

Kinds: `feature fix refactor docs test chore`. Slugs: `a-z`, `0-9`, `-`, 2 to
48 chars, unique for the life of the repository (I7). The attic and the
anchor keep the lane's full name, number included.

## Lane numbers

Every lane gets a number in its name, `lane/<kind>/<number>.<slug>`, from
`neo lane`, with no extra step. Numbers follow creation order and one
number never names two lanes (I7), online or offline:

- Online, the number is `n<N>`: N is one more than the highest number the
  clone knows of (and never below the count of merges on dev, since every
  lane landed before numbers spent one). `neo lane` reserves it on origin
  with one create-only atomic push of `refs/safety/numbers/n<N>` and the
  lane's anchor; when another clone took that number first it counts again,
  so origin serializes every online number.
- With origin unreachable, the number is `n<N>-<c>`: `c` is the first six
  hex digits of the clone's private id, so two machines offline at once may
  count the same N but never write the same number; the clone's own work
  trees reserve it create-only in the refs they share. The lane keeps that
  number for good; its first push publishes the reservation, and pre-push
  refuses a push that would meet another lane's reservation of it.
- With no origin at all (a single clone) it is `n<N>`, reserved locally.
- `refs/safety/numbers/<number>` names the lane's anchor, so it stays
  forever like one; with the anchor's tagger date it orders every lane ever
  started, landed, open or abandoned in the attic. `git for-each-ref
  --format='%(refname:lstrip=3) %(creatordate:iso) %(contents:subject)'
  refs/safety/numbers` lists them.
- A landed merge carries its number as `Lane-Number:` (land, I3). A lane
  made by hand or before numbers takes the next number when it lands; a
  hand-made name with a number the clone did not reserve for it is refused
  at land.

## Developers never delete branches

dev, main, lanes, the attic and safety anchors are never deleted or renamed
by hand, by a human or an agent: a lane leaves only as neo moves it.

- `neo land` retires a landed lane (its commits live on as the merge's
  second parent, its fork point in its anchor); `neo lane --close` moves a
  lane to the attic; `neo lane --rename` renames one, keeping the old
  anchor.
- pre-push refuses deleting a lane on the remote unless the same push is
  neo's move: dev's new tip holds the lane (land) or `attic/<same name>`
  takes its tip (close). It refuses deleting an attic branch, dev, main or
  an anchor outright.
- The agent guard denies `git branch -d/-D/-m/-M`, `update-ref -d` and a
  deleting push of dev, main, a lane or an attic branch, preflight or not.
- Convention for humans in their own clone: git has no hook on a local
  branch deletion, so a local `git branch -D` of a lane is not caught; its
  anchor stays, and once pushed origin keeps the lane. On a forge the
  rulesets keep dev, main and the attic; a lane cannot carry a deletion
  rule, since `neo land` retires it in its atomic push.

## Safety anchors

Safety anchors stay forever. `neo lane` writes `refs/safety/<kind>/<slug>`,
an annotated tag object on the commit the lane forked from (who forked it
and when), and nothing ever deletes or moves it: the lane may be synced,
renamed, closed to the attic or landed and deleted, and its fork point is
still there.

- Every push that carries a lane carries its anchor: pre-push pushes it
  first when the remote lacks it (and a clone sharing a coworker's lane
  takes origin's anchor, never a second one), `neo land` and `neo lane --close` put it
  in their atomic push, and `neo sync --dev` publishes the anchors of lanes
  landed offline. A lane made by hand or before anchors existed gets one
  where it leaves dev, at its first push or land.
- `neo lane --rename` writes the new name's anchor at the same fork point;
  the old name's anchor stays.
- pre-push refuses deleting an anchor, moving one, and creating one that is
  not an annotated tag on a commit; the agent guard denies `update-ref` on
  `refs/safety/`, a push that deletes, forces or sends anything but the
  anchor itself there, and a pruning or forced fetch into it, preflight or
  not. A forge ruleset can only name branches and tags, so on a forge a
  push past the hooks (`--no-verify`) is the one way left to delete one.
- Anchors are not fetched by default: `git fetch origin
  'refs/safety/*:refs/safety/*'` brings them.

## Production

main is production. Publishing is a release reaching main, and only the owner
promotes dev to main. dev is integration; pushing dev, lanes or tags to a
remote is transport, never publishing.

- The owner is the `.neo/identity-map` row ending in `owner` (`<email> <name>
  owner`); `neo setup` writes the setup author as owner in the root commit.
  With `release_who=list` the owner is instead every email in
  `release_list`. An email that also has an `agent` row, and an author name
  carrying a model stamp, is an agent, and an agent never releases.
- Who may release is read as committed at main's tip, never at dev's: a lane
  landed on dev cannot grant itself the right, and a new owner takes effect
  only through a release the current owner makes. While main's map names no
  owner (a repository first released under this rule), dev's owner rows
  rule.
- Enforced by `neo release` (before its gate; the release tag records
  `Released-By:`), pre-push (main moves only to an annotated `release/<v>`
  whose tagger the policy at the old main allows), I5 (each release tag's
  tagger against the policy at the release before it), the agent guard (an
  agent's `neo release` is denied; `--dry-run` is allowed) and, on a forge,
  the `neo-main` ruleset (only the repository's admins update main).

## Commits

- Subject: `[NEW|FIX|REFACTOR|DOCS|TEST|REVERT|HOTFIX] Capitalised summary`,
  12 to 72 chars, no final period; second line blank; no em or en dash.
- One concern per commit, and a change and the test that proves it share a
  commit. The deterministic part is enforced as the commit audit (rule
  `commit-audit`, `lib/audit.sh`): a subject whose text needs `and`,
  `with`, `plus`, `+` or `,` joins two concerns; a `[FIX]` or `[HOTFIX]`
  body carries a `Cause:` paragraph, then a `Fix:` paragraph; a commit
  changes at most `max_commit_lines` lines (default 800, added plus
  deleted); a `[NEW]`, `[FIX]` or `[HOTFIX]` commit that changes behaviour
  (a path that is not prose, a test, a requirement file or the policy files)
  touches a `test_paths` path, unless the commit before it carries `Red:`.
  Checked at commit (`commit-msg`), by `neo check --each` and `--audit`, at
  land, at a lane push (`pre-push`), by I4, and on a forge by the required
  `commit-audit` status. The rest (one concept, a body true to the diff) is
  convention: `neo check --judge` gives an advisory review of it; review on
  a forge is the authority.
- A test-first commit that fails its test on purpose carries one trailer
  `Red: <test name>` and is followed in the same lane by the commit that
  turns it green; it can never be a lane tip. `neo check --each` runs the
  fast gate on every lane commit and fails on an unmarked red one.
- `Red:` cannot hide broken work: it marks a `[TEST]` commit only
  (`commit-msg`, land, pre-push, I4); the commit after a `Red:` commit must
  pass the fast gate and carry no `Red:` (no chain of reds; `neo check
  --each`, land, and I4 for the chain); a `Red:` commit whose fast gate
  passes is a stale marker and is refused (`neo check --each`, land).
- `Fixes: <sha>` names the commit (usually a landed merge) a fix or revert
  repairs; `neo land` refuses one that names no commit on dev.
- A change commit says what it does: with `commit_body` at its default
  `required`, a `[NEW]`, `[FIX]`, `[REFACTOR]`, `[REVERT]` or `[HOTFIX]`
  commit carries a body line of five words or more that is not the subject
  again (`commit-msg`, land, pre-push, I4).
- Authors and committers come from `.neo/identity-map` (`<email> <name>
  [agent]`), the map committed on dev (a lane cannot relax it), checked at
  commit (`commit-msg`), at land, at push and by I4. An `agent` row authors
  as `<name> (<Model>)`, so blame names the model. A map with no rows accepts
  any real email; a lone `*` row keeps that for humans while the listed
  agent rows are still enforced, and never admits an unlisted address at a
  domain an agent row uses. In an agent session the agent guard denies a
  commit-writing git command (commit, merge, cherry-pick, revert, rebase,
  am, commit-tree) unless its resolved identity is a stamped agent row of
  dev's map, so an agent never lands as a human; `neo land`, `neo sync` and
  `neo lane --rename`/`--close` are held to the same rule. The guard is also
  the identity hook: when only git config supplies the identity (an agent
  session sets none), it rewrites the command to export the agent row of
  dev's map stamped with the session's model (`NEO_MODEL`, `ANTHROPIC_MODEL`
  or the hook input's model; `NEO_AGENT_EMAIL` picks among several rows), so
  an agent commits as itself without exporting anything; Claude Code asks
  before running the rewrite except in bypass mode. A human author under an
  agent committer (an agent's foreign `--author`) is refused at commit, land,
  push and by I4. No `Co-Authored-By: Claude` trailer.
- A lane holds 1 to `max_commits` commits (default 20) and no merge commit.
- Banned files never enter history, for humans as for agents: secrets and
  keys (`.env` and `.env.*` but templates such as `.env.example`, `.auth/`,
  `keys/`, `*.p8`, `*.p12`, `*.pem`, `*.cer`, `*.provisionprofile`,
  `*.mobileprovision`), build output (`build/`, `build-*/`), `node_modules/`,
  `*.zip`, `*.bak` and `.DS_Store`. `pre-commit` refuses them in the staged
  set on every branch; a lane push and `neo land` refuse a lane commit
  that adds one past the hook; the agent guard denies staging one. Deleting
  one is always allowed; a lane that ever added one is rebuilt without it.
- Caught at the earliest point: the commit that would make a lane
  `max_commits + 1` is refused before it is written (`prepare-commit-msg`;
  an amend passes); a lane's first commit never carries the placeholder
  requirement, and with `gates_commit` set the staged tree must pass it
  (`pre-commit`); a lane push is refused above `max_commits` or when a
  commit fails the fast gate without a valid `Red:` (`pre-push`, the same
  check as `neo check --each`).

## Merges (written by `neo land`, never by hand)

```
[MERGE] <kind>/<slug> into dev: vYYYY.S.N

<body: a paragraph saying what the lane does, then a '- ' list>

Lane-Base: <dev tip the lane contained>
Requirement: requirements/<slug>.md
Gates: fast=<pass|none> full=<pass|none>
Tested-Tree: <tree the gates passed on, equal to the merge's tree>
Lane-Number: <the lane's number, n<N> or n<N>-<c>>
Ticket: <CODE-123>              (when the lane has one)
Proof: <test file or S<nn>>     (the requirement's proof, requirement_proof=required)
```

The lane must contain dev's tip (else `neo sync` first), so the gated tree is
exactly the merged tree. The body is a paragraph, then a `- ` list (land,
pre-push and I3); land also refuses a body too thin to say anything (a
paragraph under three words, no list item of two words) and a requirement
under three words. Shape and a floor are machine-checked; whether the words
are true is review's job. A `-F` body whose last paragraph is only
`Key: value` lines (`Replays:`, `Fixes:`) has them moved into the trailer
block, so `git log --format='%(trailers:key=...)'` finds them. `requirements/<slug>.md` is committed on the lane, states a
real requirement (land refuses the placeholder; with `requirement_proof`
at its default `required`, eight words or more and a `Proof: <test file or
S<nn>>` line naming what the lane tip holds, or `Untested: <reason>`; land
copies it as a `Proof:` trailer) and is never edited or
deleted by a later lane (land and I8).

A `Gates:` receipt is re-proven, never only trusted: pre-push reruns the fast
gate on any merge this clone did not gate itself (land leaves a local
`neo-proof` note naming the tree and this clone's private id, so a note
fetched from elsewhere never counts), `neo doctor --prove` reruns both gates
on every merge's tree, and the neo-check workflow does so for each new dev
merge. A dev push must carry each new merge's version tag. A human can still
hand-write the note in their own clone, as they can skip any hook; the forge
proof is what catches it.

## Requirements register

`REQUIREMENTS.md` at the root is the project-reqs register (Hard
Requirements, Units of Intent, Scrapped), generated from
`requirements/<slug>.md` by `lib/reqs.sh`; nobody edits it by hand.

- A requirement file is `# <kind>/<slug>`, a blank line, the requirement as
  one paragraph, then optional `Key: value` lines: `Status:`
  (`done`, the default, `in-progress`, `blocked` or `intent`), `Pri:` (`P0`
  to `P3`; default `P0` for a fix, `P1` for a feature, else `P2`), `Tests:`
  (paths; default the scenarios `S<nn>` the text names, else the row says
  `needs units`), `Source:` (default `jira-<Ticket>` with a ticket, else
  `internal`), `Code:` (paths), and for intents `Sprint:` and `Notes:`.
- A landed file never changes (I8), so a later lane changes a row from its
  own file: `Promotes: <slug>` retires an intent, `Completes: <slug>` marks
  an in-progress or blocked row done, `Scraps: <slug>: <why>` moves a row to
  Scrapped, the graveyard that keeps it.
- IDs are `<reqs_id>-R-<slug>` and `<reqs_id>-I-<slug>`: a slug is unique
  for the life of the repository (I7) and taken without a counter, so two
  offline clones never mint the same ID.
- Every Hard Requirement is protected: a test it names must exist in the
  tree, or the register cannot be generated and the commit and the land are
  refused, until a lane scraps the row with its reason.
- Enforced by `pre-commit` (regenerates and stages it with every lane
  commit), `neo sync`, the re-land and `neo lane --rename` (regenerate it in
  every rewritten commit; a row merge driver, `lib/reqs-merge.sh`, declared
  by `neo setup` and `neo lane`, lets even a plain `git rebase` combine two
  lanes' rows),
  `neo land` (refuses a register its tree does not generate) and I8 (rule
  `reqs-register`). `neo check --reqs` compares, `--write` regenerates.

## Versions and tags

- `vYYYY.S.N`: year, series (releases so far that year), land number in the
  series starting at 1. After `release/<v>` the next land opens series S+1;
  a new year starts at `vYYYY.0.1`. Computed from dev's first-parent line;
  no counter is stored.
- Each landed merge carries exactly one annotated `v*` tag naming it (I2,
  I3). `release/<v>` sits on a released dev commit that main points at (I5).
- Version and release tags are created once and never moved or deleted;
  every one sits on dev's first-parent line (I6). A merge re-landed by
  `neo sync --dev` keeps its old version as `superseded/<v>-<sha>`.
- `release/<v>` records the release gate result, the tested tree and the
  lanes still open at release, oldest first, with their first and last
  commit dates.

## Invariants (`neo doctor --history`)

| Id | Holds when |
|---|---|
| I1 | every first-parent commit on dev after the root is a two-parent merge whose lane range is linear |
| I2 | each carries exactly one version tag, the next version after the previous one |
| I3 | its subject is the merge subject naming that tag, with Lane-Base, Requirement, Gates and Tested-Tree trailers (and Lane-Number for merges made under the lane-number rule); Tested-Tree equals the merge's tree, Lane-Base its first parent |
| I4 | the lane holds 1 to max_commits commits, each with a ruled subject, a known author (model-stamped for agents; never a human under an agent committer), no commit-audit smell, a known committer and at most one Red: trailer, on a [TEST] commit that neither ends the lane nor follows another Red: commit, and each change commit with a body line (commit_body) |
| I5 | main is an ancestor of dev and, past the root, carries release/<version>; every release tag made under the owner rule is annotated and tagged by an owner, by the policy at the release before it |
| I6 | every v* and release/* tag sits on dev's first-parent line |
| I7 | lane slugs are unique across landed merges, open lanes and the attic, and so are lane numbers: one number never names two lanes |
| I8 | requirements/<slug>.md exists at every merge of that lane and at dev's tip, and REQUIREMENTS.md at each merge is the register its requirement files generate |
| I9 | every superseded merge is re-landed on dev or parked in the attic, and no re-land is left half done |

## Policy (`.neo/conf`, one `key=value` per line, a key set twice is refused)

| Key | Meaning | Default |
|---|---|---|
| `land_who` | `anyone` or `list` | anyone |
| `land_list` | emails allowed to land when `land_who=list` | empty |
| `max_commits` | most commits one lane may carry | 20 |
| `gates_commit` | command the `pre-commit` hook runs on the staged tree of every lane commit | none |
| `max_commit_lines` | most lines one lane commit may change, added plus deleted (commit audit) | 800 |
| `commit_body` | `required`: a change commit carries a body line of five words or more; `optional` drops the rule | required |
| `requirement_proof` | `required`: a requirement states eight words or more and a `Proof:` line naming a file in the lane tip (or `S<nn>`), or `Untested:`; `optional` drops the rule | required |
| `test_paths` | shell patterns of test paths, space separated; a behaviour change touches one (commit audit) | `test/* tests/* */test/* */tests/* spec/* */spec/* *_test.* *.test.* *_spec.* test_*` |
| `gates_fast` | command run on every lane commit and on the merge tree | none |
| `gates_full` | command run on the merge tree before the merge exists; a lane's own conf must set it (`none` lands without one, with a warning), and a dev without it lands only a lane that sets it | none |
| `gates_release` | command run on dev's tip before a release | none |
| `land_pr` | `required` makes review mandatory (`neo land --pr`); on a forge `neo setup --remote` then adds GitHub's review rule and the neo-check status to dev's ruleset | optional |
| `land_approvals` | approvals given on the exact merge commit that `neo land --pr` waits for, and the forge's review rule requires (0 to 10) | 1 |
| `forge_repo` | OWNER/REPO when origin's URL does not name it | from origin |
| `tracker` | may only be `none`; a command tracker is operator-only | none |
| `reqs_id` | the project token of the register's IDs, `<reqs_id>-R-<slug>` and `<reqs_id>-I-<slug>` (lib/reqs.sh) | REQ |
| `release_who` | `owner` (the identity-map rows marked `owner`) or `list`; read at main's tip, never dev's | owner |
| `release_list` | emails allowed to release when `release_who=list`; an agent row never releases | empty |

Land always reads the conf committed on dev, never the lane's copy, so a lane
cannot relax the gates it is judged by; a conf change lands through a lane
like any other change.

## Lint: quiet grep

Under `set -o pipefail` a pipeline ending in a quiet grep (`-q`, `--quiet`, `--silent`) turns a hit into a
miss once its input outgrows the pipe buffer. Feed grep a here-string (`grep -q x <<<"$v"`), or let it read
all of its input with its output sent to `/dev/null` (BSD grep, GNU grep 2.27 or later). `.neo/lint/quiet-grep.py`
fails the gates on any such pipe in a tracked shell file, in every spelling; its `--self-check` proves each one.

## Lint: personal data

No tracked file holds a real person's home or session path or an email address outside the reserved domains
(`*.test`, `*.example`, `*.invalid`, `*.localhost`, `example.com`, `users.noreply.github.com`). Write
`<workspace>`, `<tmp>` or a `.test` address. `.neo/lint/personal.sh` fails the gates on any finding.

## Lint: docs against code

The docs state only what the code holds: the verbs and their flags (README's
command table), the invariant ids, the conf keys, the kinds and commit tags,
and the scenario ids and counts are read from the code and checked against
the docs by `.neo/lint/docs.sh`, run by every gate.
