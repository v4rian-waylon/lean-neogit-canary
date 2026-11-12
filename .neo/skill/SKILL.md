---
name: neo
description: Work in a repository that vendors .neo (lean git flow). Load before any git commit, branch, merge, push, release, revert, rewrite, rebuild or history question in such a repository.
---

# neo for agents

You work through `.neo/neo` (shown as `neo`). Never land, release, tag or push
dev or main by hand.

main is production: publishing is a release reaching main, and only the owner
promotes dev to main. dev is integration; pushing dev, lanes or tags is
transport, never publishing. Never run `neo release`: when dev is ready, run
`neo release --dry-run` and report it to the owner.

1. Start every change with `neo lane <kind> <slug> -r "<requirement; how its
   tests prove it>"` (kinds: feature fix refactor docs test chore) and
   `--proof <test file or S<nn>>`; the requirement says eight words or more.
   Never edit `REQUIREMENTS.md`: it is generated from `requirements/` on
   commit; add `Pri:`, `Tests:`, `Code:` lines to your requirement file instead.
   The lane is `lane/<kind>/n<N>.<slug>`; never pick or edit a number by hand.
2. Commit one concern at a time; a change and its test in one commit. Subject
   `[NEW|FIX|REFACTOR|DOCS|TEST|REVERT|HOTFIX] Capitalised summary`, 12 to 72
   chars, no final period, blank second line, no em dash; a change commit
   has a body line of five words or more saying what and why. You author as
   `<name> (<Model>)` with your `agent` row's email: the guard supplies it
   to `git commit`, `neo land` and `neo sync` when your session sets no
   identity (set `NEO_MODEL` or `NEO_AGENT_EMAIL` if its deny asks), and
   denies any other identity, naming the prefix to use.
   One concern per commit, with its test: a subject that needs `and`,
   `with`, `plus`, `+` or `,` is two commits; a `[FIX]` body has a
   description, then a `Cause:` paragraph, then a `Fix:` paragraph; stay
   under 800 changed lines (commit-msg refuses each, naming the rule).
3. A test you write first and leave red is a `[TEST]` commit carrying
   `Red: <test>`; the very next commit turns it green. Never two reds in a
   row, never `Red:` on a commit whose gate passes or on any other tag.
4. `neo check --each`, then `neo land`. If it says the lane is behind dev:
   `neo sync`, then land again. Exit 3 from `neo land --pr` means waiting for
   approvals on the exact merge (or for neo-check and commit-audit): stop
   and report.
5. Before destructive git (reset --hard, branch -D, rebase, force push) run
   the preflight the guard names, in the same command with `&&`.
6. Offline: land anyway; when back, `neo sync --dev`. If it stops on a
   conflict: resolve, `git cherry-pick --continue`, `neo sync --dev --continue`
   (never a hand `neo land` while a re-land is pending).
7. To find a regression: `neo bisect <good> <bad> -- <test>`. To undo a lane:
   a revert lane with `Fixes: <merge>` (FLOWS.md).
8. Never delete or move a lane, the attic or a safety anchor
   (`refs/safety/...`, a lane's fork point, kept forever); park a lane
   with `neo lane --close "<reason>"`.
9. Every refusal names the fix. Run it; never work around a refusal with
   `--no-verify`, a hand-made merge, a moved tag or a hand-written proof note.

## Always

- Receipts first: a cause, a fix outcome or a number in a message names the
  run that proved it, gathered before you write; reasoning and a clean
  compile are not receipts; unverified work stays uncommitted.
- Land only after the owner ran the result and said it works, or under a
  standing grant for this repository; plain `neo land`, `--pr` only when
  asked or required.
- A retry of an unlanded fix stays on its lane; a fix to a landed lane is a
  new `fix` lane with `Fixes: <merge>`. dev is never rewritten.
- Push your lane after each commit when origin is reachable; nothing else
  by hand. No empty commit. Never invent a ticket id.
- A commit you did not author (no model stamp of yours) is not yours: never
  amend, rebase, filter or replay it unless the owner names it; in doubt,
  it is theirs.
- A plan spanning several flows names each lens row below and each rule it
  applies, or why it does not apply. A subagent doing git work gets this
  skill's path.

## Lenses: read only the row your task needs

| Task | Read |
|---|---|
| Write a commit message, stage, plan commits | `lenses/commit.md` |
| Write a merge body (`neo land -F`) | `lenses/merge.md` |
| Rewrite, replay, reconcile a conflict, recover | `lenses/history.md` |
| Push to a forge, PR, CI runs, tokens | `lenses/forge.md` |
| Compile, runtime or coverage checks, gates | `lenses/verify.md` |
| Rebuild history from zips, folders or old repos | `lenses/rebuild.md` |

Rules: `.neo/RULES.md`. Flows: `.neo/FLOWS.md`. Every neo-git lens rule and
its home here: `lenses/RULE-MAP.md` (for audits, not for tasks).
