# Lens: commits

Enforced points are named once; the rest is yours to judge before `git commit`.

## Plan
- Plan the lanes before the first commit: kind, slug, the commit list, the
  landing order (dependencies land first).
- One concept per commit; two concepts, or unrelated subsystems with no
  connecting concept, split. Plan the split before staging, never after.
- Heuristics: a bug fix, a refactor pass, an adjacent tooling change is each
  its own commit; a change and the test that proves it share one; in doubt,
  split.
- A slug names the feature, never the mechanism: no `zip`, `bak`, `wip`,
  `snapshot`, `historical`, `preflight`, `recovered`, `reconstructed`,
  `from-zip`, `captured-in`, `temp`.
- A meaningful lane (subsystem, integration, operator workflow,
  architecture) carries a `[DOCS]` commit touching the README; internal
  refactors are exempt.

## Title
- Enforced (commit-msg, commit audit): tag set, capital, 12 to 72 chars, no
  final period, no em or en dash, no `Co-Authored-By`, no joiner (`and`,
  `with`, `plus`, `+`, `,`).
- `[NEW]` only for a new file, integration, subsystem, operator workflow or
  build dependency; a helper, token or adapter inside existing code is
  `[REFACTOR]` (reverting it removes a feature: NEW; only structure:
  REFACTOR). Cleanup is `[REFACTOR]`; there is no `[CLEANUP]`. `[MERGE]` is
  written by `neo land` only.
- No hyphens in English compounds in title or body prose; identifier
  hyphens stay.

## Body
- Opens with a 1 to 3 sentence paragraph at subsystem altitude: the title
  says what, the paragraph why and at what scope, the bullets how; never
  restate the title.
- `[FIX]`/`[HOTFIX]`: the paragraph, then `Cause:`, then `Fix:`, then the
  bullets (enforced). Other tags: bullets right after the paragraph; no
  `Changes:` header.
- Never in a message: `BAK`, `bak import`, `historical import`,
  `pre ATM role`, `captured in`, `from the zip`, `recovered from`,
  `reconstructed`, `WIP snapshot`, `in this zip`.

## Bullets
1. A top bullet leads with the class or module, not a path (unless the path
   is the story: a move, a contract config file).
2. Methods nest under their class; the class name is not repeated.
3. Name classes, functions and methods only: no fields, properties,
   constants or handlerless signals; no constructor bullets.
4. One short verb-led sentence per symbol; no parameters, return shapes or
   step walks; reuse the docstring's verb and noun.
5. Third person present (`Normalizes`), software verbs (`Creates`, `Deletes`,
   `Updates`, `Reads`, `Writes`, `Schedules`, `Dispatches`, `Returns`,
   `Throws`, `Adds`, `Exposes`, `Drops`); never `Stands up`, `Tears down`,
   `Spins up`, `Lights up`, `Stitches together`, `Kicks off`, `Gains`.
6. A new symbol reads declarative present; a modified one uses `now`.
7. Never fabricate a symbol: grep every name in a bullet in the committed
   tree (`git show <sha>:<path> | grep`).

## Receipts
- A body asserting observed behaviour (measured, verified, reproduces, a
  `Cause:` story, a `Fix:` outcome, a number) ends with a `Receipts:`
  section: per claim the command and its result, a log path, a green test or
  a benchmark id that existed before the message was written.
- An untested clean-looking fix fails; no behavioural claim (docs, pure
  refactor, rename) needs no section.

## Hygiene
- Stage by name (the guard refuses `git add -A`, `.`, `-u`, `commit -a`).
- Never stage `.DS_Store`, `.auth/`, `keys/`, certificates and profiles,
  `build/`, `build-*/`, `node_modules/`, `.env`, `exports/`, `*.zip`,
  `aqtinstall.log`, `runtime-smoke-notes.md`, `*.bak`, `*_old.qml`,
  `test_simple.qml`, or a file the workspace bans; keep them in `.gitignore`.
- The repository's gates carry its syntax check (`node --check` for JS).
- No em or en dash in staged prose; a regex or fixture that needs one writes
  the `–`/`—` escape with a comment saying why.
- Real-time commits set no date variables; rebuild dates: `rebuild.md`.

## Before `git commit`
Re-read this lens against `git diff --cached`, run the symbol greps, the
syntax check, and for a rebuild confirm the date variables. Before
`neo land`, review every lane commit again (`neo check --judge` gives an
advisory second read; `neo check --audit` the deterministic one) and rewrite
only your own unlanded commits, after the preflight.
