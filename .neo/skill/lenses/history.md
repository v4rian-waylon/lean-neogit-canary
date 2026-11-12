# Lens: rewrites, replays, conflicts, recovery

dev and main never move backwards (pre-push, rulesets, I1): everything here
applies to unlanded lane commits only; a landed defect is fixed forward by a
`fix` or revert lane with `Fixes: <merge>`.

## Whose commit
- A commit is yours when its author carries your model stamp and it has not
  landed. Anything else is not: never amend, rebase over, filter,
  commit-tree, cherry-pick-and-drop or force-push over it unless the owner
  names that commit. Identical tree plus a new sha is still a rewrite.
- Older history without stamps: untagged prose titles, the session's date
  window (reflog) and a timezone shift hint at the owner's work; in doubt,
  it is the owner's. Reading, branching off and landing on top are allowed.
- Before any rewrite list the range, classify every commit, and stop or
  narrow the range if one is not yours.

## How
- Run the preflight the guard names first, in the same command:
  `<hooks>/neo/git-preflight.sh <repo> "<reason>" && <git ...>`. `neo sync`
  keeps its own `refs/neo/preflight/<slug>/...` ref.
- A rewrite keeps each author name, email and date byte for byte; you are
  the committer (your agent row) and the committer date is the replay time;
  never `--reset-author`, `--author` on an amend, `--ignore-date`.
- After a replay: `git log --reverse --format=%ct base..tip | sort -c -n`
  passes, no replayed commit is empty, and you diffed the result against the
  baseline (hashes for files, a grep for every symbol a body claims);
  "applied cleanly" proves nothing.
- `--force-with-lease` only (enforced), never `filter-branch -- --all`
  (enforced), never a preflight ref in a push; `rebase -i` is unavailable:
  use a non-interactive rebase or a `commit-tree` walker that passes
  `%an %ae %aI` (the guard allows it only under your agent identity, so a
  walker over the owner's commits is the owner's to run).
- Origin holds the canonical preflight refs; refresh local copies from it.

## Conflicts (`neo sync`, `neo sync --dev`, cherry-pick)
- Find them canonically (`git diff --name-only --diff-filter=U`,
  `git ls-files -u`), never by grepping markers.
- Reason at the diff layer, hunk by hunk: what each side adds, changes,
  removes. Context present: apply the hunk verbatim. Context absent:
  `git log --all -S` tells never-landed (insert it at its natural slot,
  flagged as your interpretation) from dropped (skip it). Context evolved:
  surface it, never reshape a hunk or a file to fit.
- A hunk you cannot place is reported (the hunk, what it does, why it does
  not fit, the options), never dropped or rewritten silently.
- Isolate the exact failure before retrying. Then `git add`, `git rebase
  --continue` (or `git cherry-pick --continue`) and `neo sync` (or `neo sync
  --dev --continue`). A doc claim that disagrees with the code is fixed to
  the code and the code concern surfaced.

## Recover
- "Stop", "revert", "undo", "roll back": restore from the latest preflight
  (`preflight-bak-*` on origin, or `refs/neo/preflight/<slug>/*`), keep
  backups until the owner accepts the result, and ask before anything
  irreversible (repo deletion is refused outright by the guard).
- After an accidental rewrite: stop, find the originals (reflog, messages),
  verify their trees, pin them to local refs, show the owner the diff, and
  restore only on the owner's word.
- Watch the refs of background agents doing git work and step in before
  they push.
