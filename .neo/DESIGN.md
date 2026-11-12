# lean-neogit design record

lean-neogit distils neo-git into one flow: lanes in, one merge out, and the
history as the only database. The specification is the distillation spec of
the lean design audit (principles, invariants, verbs, scenario matrix);
this file records the decisions taken while building it. The code now holds
nine verbs and invariants I1 to I9, and `.neo/lint/docs.sh` keeps every
count and name in these docs equal to the code.

## Principles

1. Merge once. `neo land` writes the merge commit with its final message,
   version tag and receipts; nothing on dev or main is amended or
   force-pushed.
2. History is the database. Versions, lane uniqueness and requirements are
   answered by walking dev's first-parent line; no counter, anchor or vault
   ref stores them (a safety anchor keeps a lane's fork point, nothing
   more).
3. One flow. A remote is a transport, not a mode: the same commands work
   with and without one, and land pushes atomically when there is one.
4. Every guarantee has one enforcement point and one history check
   (`neo doctor --history`, invariants I1 to I9 in `.neo/lib/history.sh`).
5. Land applies the conf committed on dev, never the lane's own copy, so a
   lane cannot relax the gates it is judged by.

## Decisions

- Versions are `vYYYY.S.N`. N starts at 1 in every series; after a
  `release/<v>` tag the next land opens series S+1 at 1, and the first land
  of a new year is `vYYYY.0.1` (the spec's ".0 after a release" reads
  `.1` here, so the first land of every series has the same number).
- The landing year comes from the clock, or from `NEO_YEAR` in tests and
  replays, so version math is deterministic under test.
- A lane must contain dev's tip to land (no stale merges): the merge tree is
  then the lane tip's tree, and the gates run on that exact tree in a
  private worktree before the merge commit exists. `Tested-Tree` records it.
- A test-first commit that fails its test on purpose carries `Red: <test>`
  and cannot be a lane tip; `neo check --each` runs the fast gate on every
  lane commit and names any unmarked red commit.
- Landing is only through `neo land`, never a forge merge button, because a
  forge-written merge cannot carry the receipts and would bring back the
  amend this design removes.
- Offline is a state, not a mode: with origin configured but unreachable,
  `neo land` lands locally and says so; `neo sync --dev` later publishes the
  local lands (fast-forward) or re-lands them onto a moved origin dev through
  `neo land`, so a re-landed merge passes the gates again and takes the next
  version. The old merge keeps its old version as
  `superseded/<version>-<sha>` (the sha keeps two clones from colliding); no
  commit is lost and I6 only judges `v*` and `release/*` tags. The re-land
  plan lives in `.git/neo-reland`, so a conflict stops it without dropping
  the remaining lands: `--continue` resumes and `--abort` parks the rest in
  the attic. doctor reports a half-done re-land and any superseded merge
  that is neither re-landed nor parked (I9). While a re-land is in progress a
  hand `neo land` is refused with the `--continue`/`--abort` instruction (the
  plan lands each lane itself), a plan head whose slug is already on dev is
  dropped from the plan, and `--abort` never parks a landed slug, so the
  attic never repeats a slug (I7). A `Fixes:` trailer that names a
  re-landed commit is rewritten to the commit's new sha.
- A clone never builds on an unverified dev: before local dev takes origin's
  (in `neo lane`, `neo land`, `neo sync`, `neo release` and `neo sync
  --dev`), every incoming first-parent commit is checked as pre-push checks
  a landed merge (I1 to I4 and I8). A commit neo land did not make, pushed
  past the hooks onto a remote without rulesets, is refused there by name,
  author and invariant, and local dev stays where it was; plain `neo
  doctor` names it too, from origin's dev as last fetched.
- Detection runs as early as the facts exist: the commit that would push a
  lane past `max_commits` is refused before it is written
  (`prepare-commit-msg`), a placeholder requirement at the lane's first
  commit and, with `gates_commit`, a staged tree that fails it are refused
  at commit (`pre-commit`), and a lane push runs the per-commit fast gate
  (`neo_check_each`, shared with `neo check --each` and land), so a red
  commit never reaches a shared remote unnamed. Land still reruns every
  commit's fast gate itself.
- No gate is ever silent. `neo setup` and `neo doctor` name a gate whose
  command runs a `.neo/tests` or `.neo/lint` script the repository lacks (a
  fresh vendor drops the framework's tests); land refuses a lane whose own
  conf leaves `gates_full` unset, lands an explicit `gates_full=none` with a
  warning (and, once, a lane that sets it on a dev that has none), and
  `doctor --prove` counts the merges that carry no gate instead of calling
  every gate passed. README's quick start sets the gates before setup and
  runs as written (S84).
- A clone that never ran `neo setup` has no hooks: the verbs that write
  (lane, land, sync, release) refuse with `neo setup` instead of working
  unguarded, and `neo status` says what is missing; `check`, `bisect` and
  `doctor` stay usable, since the forge workflow runs them on a runner with
  no hooks.
- A push that fails while origin is reachable (refused, or the link drops
  mid-push) undoes the local tag and leaves dev unmoved, so the next land
  resumes from the same state.
- Safety anchors stay forever (the owner's rule, kept from neo-git). `neo
  lane` writes `refs/safety/<kind>/<slug>` at the fork point as an annotated
  tag object, so it records who forked and when. It rides with the lane: pre-push pushes it before a lane
  or attic push when the remote lacks it, land and close put it in their
  atomic push, and `neo sync --dev` publishes those of offline lands. A
  sync, a close, a rename (which adds the new name's anchor) and a land never
  touch it. pre-push and the agent guard refuse deleting, moving or forging
  one. The namespace is outside `refs/heads` and `refs/tags`, as the owner
  named it, so the forge rulesets cannot cover it: on a forge only a push
  past the hooks can delete one.
- Lane numbers are back from neo-git (the owner refused their removal), in
  lean's shape: `neo lane` takes the number itself, no allocator workflow and
  no extra command. neo-git's allocator could not serialize two clones
  offline (its RUNBOOK says a clone that allocates before fetching another's
  push can pick the same number). Here origin serializes online numbers by
  a create-only atomic push of `refs/safety/numbers/n<N>` with the anchor,
  retried on a loss, and an offline clone never needs serializing: its
  numbers carry its own id, `n<N>-<c>`, so a collision needs two clones with
  the same id prefix, and even that is refused at their first push rather
  than shared. N is a Lamport count (one more than the highest number
  known), so a lane started after another was seen always numbers after it,
  and the reservation's tagger date orders the rest; reservations are kept
  forever, so abandoned lanes keep their place. The number rides in the
  branch name, the anchor and the merge's `Lane-Number:` trailer; the slug
  stays the requirement file's name and the merge subject's, so I7 and I8
  read as before. A merge is judged by the rule its first parent's
  framework knew, so history landed before numbers stays lawful.
- Banned files and kept branches hold for humans too (neo-git's
  "developers never delete branches" ruleset and its banned list, which lean
  had left to the agent guard). `pre-commit` refuses a staged banned file
  on every branch, and land and a lane push refuse a lane commit that adds
  one past the hook, so a `--no-verify` commit still never reaches dev or
  a shared remote. pre-push refuses a hand deletion of a lane on the remote
  and lets through only neo's own moves, recognised in the same push (dev's
  new tip holds the lane, or the attic takes its tip); the agent guard
  denies deleting or renaming dev, main, a lane or the attic outright. No
  forge ruleset can say "no deletion except a land", so lanes carry none on
  the forge; landed work survives anyway as the merge's second parent and
  every fork point as its anchor.
- A slug that lands elsewhere first is refused at sync (I7). `neo lane
  --rename` rewrites the lane so its requirement file always carried the
  new slug, never deleting the file the other lane landed.
- dev moves by fast-forward inside whichever work tree holds it, so a land
  from a linked worktree leaves the main checkout current. The same holds
  when `neo lane`, `neo land`, `neo sync` or `neo release` take origin's
  newer dev: a work tree with dev checked out follows it, so a lane started
  from a stale dev checkout never stages the reversal of a coworker's land,
  and `neo lane` refuses to start when the work tree it stands in could not
  follow.
- main is production. Publishing is a release reaching main, and only the
  owner promotes dev to main; dev is integration, and pushing dev, lanes or
  tags to a remote is transport, never publishing. The owner is the
  identity-map row marked `owner` (`neo setup` writes the setup author as
  owner in the root commit), or `release_list` under `release_who=list`.
  Who may release is read as committed at main's tip, so a lane landed on
  dev never grants itself the right, and a change of owner takes effect
  only through a release the current owner makes; while main's map names
  no owner (a repository first released under this rule), dev's owner rows
  rule. An agent row never releases, and an author name with a model stamp
  is an agent. `neo release` refuses anyone else before its gate, the tag
  records `Released-By:`, pre-push refuses main moving to a release tagged
  by anyone else (or to a lightweight tag), I5 judges every release tag's
  tagger against the policy at the release before it, the agent guard
  denies `neo release` (its `--dry-run` stays allowed), and on a forge the
  `neo-main` ruleset lets only the repository's admins update main.
- A release is `neo release`: the release gate runs on dev's exact tip,
  `release/<version>` tags it and main fast-forwards to it in one atomic
  push. main never takes a commit dev does not hold (I5), and the next land
  opens the next series, so every version says which release precedes it.
- Finding a regression is `neo bisect GOOD BAD -- CMD`: a binary search over
  dev's first-parent merges finds the lane that broke CMD, then a search over
  that lane's commits finds the culprit, skipping commits marked `Red:`. It
  works because every first-parent commit is a gated merge and every lane
  commit is atomic and passes the fast gate unless marked red.
- Client hooks are a guard rail. On a forge, server rulesets on dev, main,
  the attic and tags are the authority, and with `land_pr=required` GitHub's
  own review rule on dev is what a hostile change meets.
- `neo bisect` treats a command exit of 125 as "cannot test this commit", as
  git bisect does: the commit is skipped, and when a skipped commit could be
  the culprit the report names it instead of guessing.
- The agent guard and preflight come from neo-git with their parser and rules,
  renamed to the `.neo` layout. neo-git's identity hook (n206) is folded into
  the guard rather than kept as a second PreToolUse hook: Claude Code runs a
  tool's hooks side by side and a deny outranks a rewrite, so a separate
  rewrite hook could never win against the guard's identity rule. When the
  only fault is an identity that git config alone supplies, the guard answers
  with `updatedInput`, the command prefixed by `export` of the missing fields
  from the agent row of dev's map stamped with the session's model, and
  checks the rewritten command against every rule again. Claude Code gets
  `ask` (the user sees the rewrite, no permission widened) unless the session
  is in bypass mode; Codex rewrites only through `allow`, so an allowed
  rewrite outside bypass mode must be a line of plain git, neo, cd and export
  commands. An explicit wrong identity, two repositories, an unmapped one in
  the same line, an unknown model or an unpicked row keep the deny. The guard is a best-effort
  guard against agent accidents, not a security boundary: it matches known
  command shapes and allows unknown ones; a hostile agent needs an OS sandbox
  and the server rulesets. `.neo/FRAMEWORK` marks this repository as the
  framework source, the one place `.neo` may be edited; `conf` and
  `identity-map` are the consumer's own files and stay editable everywhere.
- `neo setup --remote` applies four rulesets (dev and main: no deletion, no
  force push; `neo-main`: main takes no update at all except from the
  repository's admins, since main is production and only the owner promotes;
  `attic/**`: no deletion, no force push; `v*` and `release/*`
  tags: no update, no deletion) and writes a read-only `neo-check` workflow.
  The workflow never runs the candidate's checker: it extracts `.neo` from
  dev (for a dev push, from dev as it was before the push) and runs that
  copy against the candidate, so a lane that replaces `.neo/neo` is judged by
  the checker it tried to replace. With `land_pr=required` the dev ruleset
  also carries GitHub's own `pull_request` rule (`land_approvals` approvals,
  stale approvals dismissed on a push, the last push approved by someone
  else) and the neo-check status: `neo land --pr` publishes the merge as the
  lane's head, reviewers approve that exact commit, the workflow proves it
  (`neo check --merge`: shape, both gates on its tree, approvals on its sha),
  and dev then moves to it by a push of that head. Two limits are stated, not
  hidden: a candidate's gates are its own tests, and a candidate can edit the
  workflow file, so a status alone can be produced by the change it judges;
  the review rule is the authority, the status a second line. With
  `land_pr=optional` a land is a plain push and the workflow proves each new
  dev merge after the push (`neo doctor --prove`); a receipt that does not
  hold fails it. A second job, `neo-linux`, runs the full gate on ubuntu
  (bash 5, GNU tools) for every lane and dev push. The workflow checks the
  full invariants only for merges after its base (`--since`); the version
  chain and the invariants that span history still run on every push.
- A receipt is never only trusted: pre-push reruns the fast gate on any merge
  this clone did not gate (land leaves a local proof note naming the merge's
  tree and this clone's private id, so a fetched or copied note never
  counts; the agent guard denies writing it by hand), and a dev push must
  carry each new merge's version tag.
- `neo setup --upgrade SOURCE [REV]` runs on a lane, so a framework upgrade or
  downgrade lands, gates and versions like any change; it keeps `conf`,
  `identity-map` and `requirements/` and never vendors the framework's tests, bench
  or source marker.
- `neo land --pr` publishes the merge itself as the lane's head and opens or
  updates its PR with the exact merge subject and body. It counts only
  approvals given on that merge sha (an approval of an earlier head never
  counts, so a new commit dismisses it) and, with `land_pr=required`, waits
  for the neo-check status on it; then dev moves to exactly the approved
  commit. The forge's merge button is never a landing path.
- `neo land` deletes the lane on origin only with a lease on the sha it
  landed, and refuses while origin's lane holds commits the lander lacks,
  so a coworker's push to a shared lane is never discarded.
- The identity map and conf that judge a lane are the ones committed on dev;
  per merge, history uses the ones at its first parent.
- The requirements register (`REQUIREMENTS.md`, the project-reqs model with
  protected rows and a graveyard) comes back as a view, not a database:
  `lib/reqs.sh` renders it from the requirement files of one tree, so the
  gate can prove it on the exact tree it lands. Fields live in the
  requirement file, and since a landed file is never edited, a later state
  is written by the lane that causes it (`Promotes:`, `Completes:`,
  `Scraps:`); the tree alone decides every row, with no history walk. IDs
  are the slug, the one name unique offline. Rows are sorted by slug and the
  register carries no totals line; a row merge driver (`lib/reqs-merge.sh`,
  declared by `neo setup` and `neo lane` in the clone's config and
  `info/attributes`, never in a tracked file) merges two lanes' rows, so no
  rebase, merge or cherry-pick stops on it, and `neo sync` and the re-land
  also regenerate it in every replayed commit. Defaults keep every older requirement file valid: done, a
  priority by kind, tests from the scenario ids its text names; rows with
  none say `needs units`, the visible test backlog.
- A ticket id travels from `neo lane --ticket` into the requirement file and
  the merge's `Ticket:` trailer with no tracker at all. A command tracker runs
  an executable, so it is honoured only from operator settings
  (`NEO_TRACKER`, `git config neo.tracker`), never from the committed conf and
  never when the adapter is a file the repository tracks. A failed link or
  transition is reported and never undoes a lane or a land.
- An identity-map row ending in `agent` is an AI agent: its commits author as
  `<name> (<Model>)`, checked at commit (`commit-msg`, against dev's map), at
  land, at push and by I4, so blame names the model of every line and an
  agent learns of a missing stamp before its lane is written. Committers are
  checked at the same points. A lone `*` row keeps the map open to any real
  human email while its agent rows are enforced; this repository's own map
  uses it for its agent account. The hooks cannot tell an agent from a
  human, so the agent guard, which runs only in an agent session, closes
  that gap: it resolves the identity git would use (env prefix, exports
  earlier in the line, the session's environment, `git -c user.*`,
  `--author`, git config) and denies a commit-writing command unless it is
  a stamped agent row of dev's map, naming the exact prefix, or supplies that
  identity itself when the session sets none (the identity hook above). A `*`
  row never admits an unlisted address at an agent row's domain. An agent
  committer never carries a human author (rule `agent-author`: commit-msg,
  land, pre-push and I4), so the guard's deny of a foreign `--author` has a
  hook behind it.
- `neo release` writes the lanes still open into the release tag, oldest
  first with their first and last commit dates (origin's lanes when there is
  a remote): open lanes are refs that move, so the release is where the
  snapshot of work in flight stays.
- `Fixes: <sha>` must name a commit on dev; a revert is a lane of its own that
  keeps the reverted lane's requirement file (I8) and links the merge it
  undoes, and the repaired work lands as a new lane linking the revert.

## Bootstrap of this repository

The root commit seeds the repository with a README. The foundation lane
(the replay of neo-git's first pool) was landed by a finished `neo` run from
outside the tree, because no `neo` existed in the repository yet; its merge
satisfies I1 to I4 and I8 like every later one, under the bootstrap conf's
gates (`true`), since the scenario harness arrives with the next lane. From
the test-harness lane on, every lane is landed by the `neo` committed on dev
and gated by the scenarios present at that point.

## What lean-neogit gives up, and why each guarantee holds anyway

| neo-git machinery | lean-neogit | The guarantee, and where it lives now |
|---|---|---|
| Merge first, then a separate claim amends, re-pushes, tags and vaults | `neo land` writes the final merge once | Version, receipts and requirement are in the merge commit itself (I2, I3); nothing on dev is ever rewritten |
| Server-allocated pool numbers `nN` and the allocator workflow | `neo lane` numbers every lane `n<N>`, reserved on origin, or `n<N>-<c>` offline | Every lane, landed or abandoned, keeps its creation order and a number no other lane has, offline included (I7); landed order is also the version sequence (I2) |
| `safety/*` anchors and `vault/*` archive refs | `refs/safety/<kind>/<slug>` anchors, kept forever; no vault | Every lane's fork point survives a sync, a rename, a close and a land in its anchor, pushed with the lane; a landed lane's commits are reachable through its merge's second parent forever; `neo sync` keeps a preflight ref before every rebase |
| Machine-authored reconcile branches and the auto-rebase ladder | `neo sync` by the lane's author; `neo sync --dev` re-lands offline work | Every re-landed merge passes the gates again and takes the next version; the old one keeps `superseded/<v>-<sha>`; a conflict stops a resumable plan, never drops a land (I9) |
| GitHub merge button, PR validation workflows, claim workflows | `neo land` (and `--pr` for review) | Gates run on the exact merge tree before the merge exists (`Tested-Tree`). Under `land_pr=required` dev's ruleset carries GitHub's review rule (approvals after the last push) and the neo-check status, computed by dev's checker on the exact merge; under `optional` the forge reruns every new merge's gates after the push |
| Off-grid and connected modes | one flow; a remote is a transport | The same checks run with and without origin; offline is a state handled by `neo sync --dev` |
| CI matrix and the required.* audit scripts | `gates_fast`, `gates_full`, `gates_release` in `.neo/conf`; the `neo-linux` job | Every lane commit passes the fast gate or is marked `Red:`; every merge passes both gates; a release passes the release gate; the full gate also runs on ubuntu for every lane and dev push |
| Sixteen agent skills (lenses), user overrides and a lazy loader | one skill, `skill/SKILL.md`, whose task table loads one lens file from `skill/lenses/` per task | Every rule of every neo-git lens has a home, listed rule by rule in `skill/lenses/RULE-MAP.md`: the skill, a lens file section, or the code that enforces it; the docs lint proves the loader and the map resolve. About a fifth of neo-git's bytes; user overrides stay cut (one skill to override) |
| Doc-freshness gate and protocol lint over skills and docs | `.neo/lint/docs.sh` in every gate | Verbs and flags, invariant ids, conf keys, kinds and tags, scenario ids and counts in the docs are read from the code and must match it |
| CHANGELOG file, `changelog` and `release-of` tools | none; history answers both | A changelog is `git log --first-parent --format='%s%n%n%b' vA..vB` on dev (each merge's body is its entry); a commit's release is `git tag --contains <sha> --sort=v:refname 'release/*'`, first line. A file would be a second database (principle 2) |
| Live canaries on public throwaway repositories | `tests/canary/live.sh` in one persistent public canary repository, run by hand | Forge behaviour is driven through a `gh` stub on every land (S20, S28, S40) and the workflow's own step scripts are executed locally (S40); the live canary proves it on GitHub itself (Live canary, below): rulesets refusing a forced dev, a deleted dev, a moved tag and a deleted attic branch past the hooks, the workflow's jobs, a release, review under `land_pr=required`; it never deletes a repository (S87 proves its safety against a stub) |
| Reconstruct, shuttle, snapshot and rewrite tooling | out of the core | Not needed by the flow; history quality is enforced at land, not repaired afterwards; the rebuild rules live in the skill's `rebuild.md` lens |
| Bench harness, agent runner and loadbytes | `bench/speed.sh` and `bench/loadbytes.py`, framework-only | Lean's speed and read budget are measured against neo-git, not claimed (Measured, above); the model-run agent bench stays out: no model is called |

Kept as they were: the message rules, the identity map, the protected-ref and
tag rules of pre-push, the agent guard and preflight, the tracker contract's
operator-only command adapter, and a thorough scenario matrix (S01 to S90)
that runs on every land.

The agent skill is one loader with lazy lenses, as neo-git's lean loader
was: `skill/SKILL.md` holds what every task needs (the eight steps and the
rules that bind always: receipts, landing only on the owner's word or a
grant, fix forward, never someone else's commit) and a task table; each
lens file (commit, merge, history, forge, verify, rebuild) holds one task's
rules and is read only for that task. The rules were folded, not dropped:
`skill/lenses/RULE-MAP.md` lists each of the 322 rules of neo-git's 16
lenses with its home, so an audit can prove none was lost. Where a rule
meets a lean guarantee it is restated in lean's terms (lanes, `neo land`,
the owner's release, fix forward on dev); where it needs neo-git machinery
the owner cut, the map says so and names where the intent survives.

neo-git's commit audit is split as neo-git split it: the deterministic
smells of how-git's commit lens (subject joiners, Cause and Fix on a fix,
the 800-line soft cap made a conf key, a behaviour change carrying its test)
are rule `commit-audit` in `lib/audit.sh` and `lib/message.sh`, checked at
every point a commit passes (commit-msg, `check --each` and `--audit`,
land, pre-push, I4) and, on a forge, by a `commit-audit` job that runs dev's
checker and is a required status under `land_pr=required`, as neo-git's
`required.commit-audit` was. History landed before the rule is judged by
the rules its own framework knew. The joiners are matched as words, so a
true single concern phrased with "with" is reworded, never waved through;
an attic push parks work as it was and is not audited. The scenario repos
set `test_paths=*` so the test smell stays out of scenarios about other
rules (S54 sets real paths).

neo-git's advisory Claude commit judge is `neo check --judge`: a review of
the lane's commits against the conventions the hooks cannot check (one
concern per commit, a body that matches the diff), in a scrubbed
environment with file tools only and verdicts bound to a nonce. It never
blocks a land; `--strict` makes it fail for teams that want it as a gate.

## Live canary

`tests/canary/live.sh` restores neo-git's live canaries and public
throwaways (n207, n209) in lean's shape: one script, no CI minutes, run by
hand, and no repository is ever deleted. It works in one persistent public
repository (`<gh user>/lean-neogit-canary`, created once when missing): every
run lands run-scoped lanes (slugs ending in the run id) onto that
repository's own dev, so its dev, main, version and release tags and
rulesets keep each run's record, as neo's rules require; the framework under
test arrives through an upgrade lane when it differs. The checks: C1 setup
or upgrade and the four rulesets; C2 dev refused a force push and a deletion
past the hooks; C3 a version tag refused a move and a deletion; C4 an attic
branch refused a deletion; C5 the neo-check, commit-audit and neo-linux jobs
green on a pushed lane; C6 the owner's release; C7 `land --pr` through
review and C8 a release under `land_pr=required` (hole M1); C0 and C9 put the
canary back to optional review, lifting the review rule as the owner's admin
step first. Cleanup removes only the run's unlanded lanes by name; tags, the
attic, dev and main stay by rule. It needs gh's `repo` and `workflow` scopes,
never `delete_repo` (S87 proves the safety against a stub).

Live runs, 2026-11-12 (receipts in the restoration progress record): run
261112104430 passed C0 to C6 and C9 and failed C7 and C8. C4 failed in the
run before it: GitHub matches ruleset patterns with fnmatch, so
`refs/heads/attic/**` protected one level only and a parked lane was
deleted; the ruleset now includes `refs/heads/attic/**/*` and C4 passes. C7
and C8 are open defects of the forge flow: with `land_pr=required`, dev's
ruleset carries GitHub's pull_request rule, and GitHub refuses the push that
`neo land --pr` makes to move dev to the approved merge ("atomic transaction
failed" on the lane, the tag refused) and the push of main by `neo release`
("push declined due to repository rule violations"), since neo-protected
also covers main. Hole M1 is confirmed live; how review should move dev and
main on GitHub is the owner's decision.

## Measured: speed and read budget

The bench (`.neo/bench/`, framework-only like the tests) measures lean against
neo-git instead of claiming. `bench/speed.sh [--runs N] [--neo-git PATH]`
times each flow on scratch repositories with gates that pass at once, so only
the framework is timed; neo-git's flows run off-grid through neo-git's own
bench fixtures. `bench/loadbytes.py [--neo-git PATH]` counts the bytes an
agent is told to read for each of neo-git's 13 tasks, with neo-git's own
loadbytes module for its two arms. Measured on 2026-11-12, lean at f3278af
(the four restoration lanes before this one), neo-git at 3618b0f
(v2026.0.209), Darwin arm64, bash 3.2, a loaded machine (load average about
10; three runs, the median):

| Flow | lean | neo-git | lean vs neo-git |
|---|---:|---:|---:|
| setup | 993 | 2995 | -67 % |
| lane | 272 | 1361 | -80 % |
| commit | 523 | 429 | +22 % |
| land | 3072 | 1763 | +74 % |
| sync | 1445 | 643 | +125 % |
| release | 775 | 1720 | -55 % |
| doctor | 491 | 118 | +316 % |
| history | 2324 | n/a | n/a |
| **flows both run** | 7571 | 9029 | -16 % |

lean is faster where neo-git did machine work (setup, a lane, a release) and
slower where lean does more per call: its land runs the commit audit and the
fast gate on every commit, builds and gates the merge in a private worktree
and pushes atomically, where neo-git's off-grid merge claimed and pushed with
no gate; its sync verifies incoming dev before rebasing; its doctor checks
more of the install. A gate's own time (the project's tests) is not in these
numbers and dominates a real land.

| Task | how-git B | neo-git B | lean B | lean vs neo-git | lean vs how-git |
|---|---:|---:|---:|---:|---:|
| Compose a commit | 230297 | 19664 | 8746 | -56 % | -96 % |
| Create a working branch | 230297 | 22692 | 4391 | -81 % | -98 % |
| Merge a pool into dev | 230297 | 26399 | 6723 | -75 % | -97 % |
| Release dev to main | 230297 | 35101 | 4391 | -87 % | -98 % |
| Rewrite my own history | 234370 | 22038 | 7858 | -64 % | -97 % |
| Rebuild from bak zips | 230297 | 24412 | 20113 | -18 % | -91 % |
| Rebuild from working-tree folders | 230297 | 24870 | 20113 | -19 % | -91 % |
| Replay or rebase across diverged history | 230297 | 14230 | 7858 | -45 % | -97 % |
| Verify compile, coverage or runtime | 230297 | 16019 | 7640 | -52 % | -97 % |
| After a push | 230297 | 16410 | 6317 | -62 % | -97 % |
| GitHub API call needing credentials | 230297 | 11501 | 6317 | -45 % | -97 % |
| Bootstrap a new repo | 249109 | 27292 | 8746 | -68 % | -96 % |
| Adopt or migrate the framework | 230297 | 12641 | 4391 | -65 % | -98 % |
| **All 13 tasks** | 3016746 | 273269 | 113604 | -58 % | -96 % |

The read budget is where the token claim lives: an agent reading lean's skill
and one lens reads 58 % fewer bytes than with neo-git's lean loader, 96 %
fewer than with how-git. Bytes are not tokens and no model run was made, so
this is the budget an agent is told to read, not a measured token bill.

## Build history

This repository replays neo-git's pool history in distilled form. neo-git's
209 pool merges are walked in order: a pool whose concern lean keeps is a
lane here (REPLAY), a pool whose effect another lane carries is named in that
lane's `Replays:` trailer (FOLD), and a pool with no lean counterpart is
recorded with the reason (CUT). `.neo/REPLAY.md` lists every pool with its
verdict and its lane and version; 86 pools became lanes, and six lean-only
lanes (bisect, Red:, Fixes:, the resumable re-land, land integrity and the
parity docs) close the history. Each lane keeps its pool's author and date.

A lane's tree is the lean code for the capabilities introduced so far, never
a weaker intermediate copy: where lean already carried a hardening whole, the
lane records in its requirement file where lean enforces the guarantee and
which scenario proves it (a trace lane). Two neo-git guarantees the first lean
design lacked are kept: no pipe into a quiet grep (lane of neo-git's
here-string pool) and no personal data in tracked files (lane of its
personal-path pool), both run by every gate. The scenario harness stopped
inheriting the caller's commit dates at the agent-guard lane, where S27
exposed it.
