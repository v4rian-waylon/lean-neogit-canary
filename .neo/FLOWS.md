# neo flows

Every flow is the same for a human and an agent, online and offline. An
agent follows the steps literally; every refusal names the next command.
`neo` below is `.neo/neo` at the repository root.

## Start a repository

1. Vendor `.neo/` into the repository (copy it, or `neo setup --upgrade` from
   an existing one), set your gates in `.neo/conf` (setup refuses a gate
   that runs framework tests the vendor dropped), then `neo setup`: hooks active, identity checked, main
   and dev seeded (and pushed when origin is set). The root commit names the
   setup author as owner: main is production, and only the owner promotes.
2. List the team in `.neo/identity-map` (`<email> <name> [agent]`; a lone `*`
   row keeps it open to any human while agent rows are enforced) and set the
   gates in `.neo/conf`, on a first lane. From then on `commit-msg` refuses a
   commit whose author or committer the map on dev does not know.
3. Agents: `neo setup --agent` installs the guard for Claude Code and Codex.
   It is also the identity hook: an agent's commit, `neo land` and `neo sync`
   run under the agent row of `.neo/identity-map` stamped with the session's
   model, with nothing exported by hand (set `NEO_MODEL` when the session
   names no model, `NEO_AGENT_EMAIL` when the map lists several agents).
4. On a forge: `neo setup --remote` applies the rulesets (dev and main, the
   attic, the tags; with `land_pr=required` also GitHub's review rule and the
   neo-check status on dev) and writes the neo-check workflow; commit it on a
   lane. The workflow judges every candidate with dev's checker.

## Work on a change (one lane per concern)

1. `neo lane <kind> <slug> -r "<requirement and how its tests prove it>"`
   (or `--ticket CODE-123` to take the requirement from the tracker). Add
   `Pri:`, `Tests:`, `Code:` or `Status: intent` lines to
   `requirements/<slug>.md` when the defaults do not fit (RULES.md,
   Requirements register); `REQUIREMENTS.md` follows by itself on commit.
   The lane is `lane/<kind>/n<N>.<slug>`: its number is reserved on origin,
   or carries this clone's id when origin is unreachable, so it is never
   shared. Its fork point is anchored at `refs/safety/<kind>/n<N>.<slug>`
   for good; every push of the lane carries the anchor and the number.
2. Commit in atomic steps; a change and its test together. A test written
   first and red on purpose carries `Red: <test>` and the next commit turns it
   green. `commit-msg` runs the commit audit: a subject joined by `and`,
   `with`, `plus`, `+` or `,` is two commits; a `[FIX]` body says `Cause:`
   then `Fix:`; a commit stays under `max_commit_lines`; a behaviour change
   carries its test.
3. `neo check` (fast gate on the work tree) as often as you like;
   `neo check --each` (the commit audit, then the fast gate on every commit)
   or `neo check --audit` (the audit alone, instant) before landing. Pushing
   the lane to share it runs the same per-commit checks first, and a commit
   past `max_commits` is refused before it is written: land the lane and
   start the next.
4. `neo land`: policy, staleness, size, every commit's message and author,
   the fast gate on every commit, the merge built in a private worktree and
   both gates run on the merge tree, then one merge, one tag, one atomic push
   that also deletes the lane on origin.

## When dev moved under you

- `neo land` says the lane is behind dev: `neo sync` (the old tip is kept
  under `refs/neo/preflight/<slug>/...`), then `neo land`.
- `neo sync` stopped on a conflict: resolve, `git add`, `git rebase
  --continue`, `neo sync` again; or `git rebase --abort`.
- Two clones landing at once: the loser's atomic push is refused and nothing
  is half-published; `neo sync`, then `neo land` again.
- origin's dev holds a commit neo land did not make (someone pushed past the
  hooks): every verb that would take it refuses, names it, its author and
  the broken invariant, and leaves local dev alone. Tell the owner; once
  origin's dev is repaired, carry on.
- A coworker landed while you sat on dev: `neo lane` fast-forwards dev in
  every work tree that holds it, so the new lane starts clean on their work.
  If a work tree cannot follow (an untracked file in the way), `neo lane`
  refuses and names the catch-up command.
- The slug landed elsewhere first: `neo lane --rename <new-slug>`, then sync
  and land.

## Offline

- `neo land` with origin unreachable lands locally and says so.
- Back online: `neo sync --dev`. It fast-forwards to origin, publishes local
  lands in one push, or, when both sides moved, re-lands each local merge on
  top of origin dev through `neo land` (gates again, next version; the old
  merge keeps `superseded/<v>-<sha>`; a `Fixes:` naming a re-landed commit
  follows it to its new sha).
- A re-land stopped on a conflict: resolve, `git add`, `git cherry-pick
  --continue` (or `--skip`), then `neo sync --dev --continue`. The plan is
  kept in `.git/neo-reland` until every land is back; `neo doctor` reports a
  pending one. `neo sync --dev --abort` parks the remaining lands in the
  attic (`neo lane --restore` brings each back); nothing is lost.
- During a re-land never run `neo land` by hand: it is refused, because the
  plan lands each lane itself. Resolve, then `neo sync --dev --continue`.
- The link drops during a land's push: nothing changes locally (the tag is
  undone); rerun `neo land`.

## Prove the forge (framework source)

`bash .neo/tests/canary/live.sh` (gh signed in with the `repo`, `workflow`
and `delete_repo` scopes): one public throwaway repository runs the real
flows on GitHub and is deleted by exact name from the canary's ledger;
`--dry-run` shows the plan, `--cleanup` finishes an interrupted run. A
failing check names what the forge answered.

## Review on a forge

1. `neo land --pr`: the merge is built and published as the lane's head, and
   the PR is opened (or updated) with the merge subject and body. Reviewers
   approve that exact commit. Exit 3 means it waits.
2. It waits for `land_approvals` approvals given on the merge sha and, with
   `land_pr=required`, for the neo-check status on it (the forge reruns the
   gates and counts the approvals). A new lane commit makes a new merge, so
   earlier approvals stop counting.
3. `neo land --pr` again moves dev to exactly that merge, tags it and deletes
   the lane, in one push. Never use the merge button. With `land_pr=required`
   GitHub itself refuses dev moving to a commit without the approvals and the
   neo-check status.

## Release

main is production: publishing is a release reaching main, and only the
owner promotes dev to main. dev is integration; pushing dev, lanes or tags
is transport, never publishing.

`neo release`, run by the owner: the owner check (main's own policy), the
release gate on dev's exact tip, `release/<v>` (its message lists the lanes
still open, oldest first, and `Released-By:`), main fast-forwards, one
atomic push. The next land opens the next series.

- An agent never releases: it runs `neo release --dry-run` and reports that
  dev is ready; the agent guard denies a real `neo release`.
- Anyone else is refused with the owner's address. A new owner lands the
  row `<email> <name> owner` in `.neo/identity-map`; it takes effect once
  the current owner has released it to main.

- Changelog between two versions: `git log --first-parent
  --format='%s%n%n%b' vA..vB dev` (each merge's subject and body).
- The release a commit first shipped in: `git tag --contains <sha>
  --sort=v:refname 'release/*'`, first line.

## Find and undo a regression

- `neo bisect <good> <bad> -- <test command>`: first the landed lane, then the
  commit inside it; `Red:` commits are skipped, exit 125 skips a commit the
  command cannot test, and a skipped possible culprit is named.
- `git blame` names the author and, for agents, the model of every line;
  the merge's trailers name the requirement and the gates.
- Undo a landed lane: `neo lane fix revert-<slug>`, `git revert --no-commit -m 1
  <merge>`, restore `requirements/<slug>.md` (it is never deleted), commit with
  `[REVERT] ...` and `Fixes: <merge>`, land. Land the repaired work as a new
  lane with `Fixes: <revert commit>`.

## Recover and tidy

- Park a lane: `neo lane --close "<reason>"` (to `attic/`, reason as a git
  note); `neo lane --restore attic/<kind>/<slug>` brings it back.
- Every lane ever started, in creation order, landed, open or abandoned:
  `git for-each-ref --format='%(refname:lstrip=3) %(creatordate:iso)
  %(contents:subject)' refs/safety/numbers` (after `git fetch origin
  'refs/safety/*:refs/safety/*'`).
- Where did a lane start: `git rev-parse refs/safety/<kind>/<slug>^{commit}`
  (fetch the anchors first with `git fetch origin
  'refs/safety/*:refs/safety/*'`). Anchors are never deleted or moved.
- An agent's destructive git (reset --hard, branch -D, rebase, force push)
  needs `<hooks>/neo/git-preflight.sh <repo> "<reason>"` first; the guard's
  deny says exactly what to run.
- `neo status` (`--json` for tools): where you are, open lanes, last
  version, a pending re-land. `neo doctor`: the install (`--fix` repairs the
  hooks setting); `neo doctor --history [--since REV]`: I1 to I9;
  `neo doctor --prove [SINCE]`: every merge's gates rerun on its own tree.
- `neo <verb> -h` prints that verb's usage.
- A clone that never ran `neo setup`: `neo lane`, `land`, `sync` and
  `release` refuse and name it; `neo status` says what is missing; `check`,
  `bisect` and `doctor` work without it (the forge's runner has no hooks).
- `neo check --judge`: an advisory Claude review of the lane's commits
  (`--strict` fails on a finding); skipped without the claude CLI.

## Upgrade the framework

`neo lane chore upgrade-neo`, `neo setup --upgrade <framework repo> [rev]`,
review `git diff --cached`, commit, `neo land`. `.neo/conf`,
`.neo/identity-map` and `requirements/` are kept; going back is the same
with an older rev.
