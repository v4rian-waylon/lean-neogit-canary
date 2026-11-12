# Lens: rebuilding history (zip chains, folder snapshots, old repositories)

Read `history.md` and `verify.md` too. Never touch the originals: every
output goes to the target repository or a throwaway, and the sources are
read only.

## Common
- The workspace's instructions and memories bind: read them before
  committing or dispatching, and apply every rule on the first pass.
- Scope first (workspace, backup directory, mirror, repositories in scope,
  identity), inferred in order: the path given, a multi-repo working
  directory, a backups directory, the workspace instructions; ask once,
  never again mid-flow. Every question offers "something else"; free answers
  are recorded verbatim; never infer a grant.
- Identity: replayed commits keep their source identity verbatim (never
  normalised); the owner's own dropped work is authored as the owner; new
  work today is your agent row. Never blend two sources in one commit. The
  guard refuses a human author in an agent session (rule 8), so commits
  authored as the owner are run by the owner from the plan you prepare.
- Dates, derived never asked: a commit's author and committer dates are the
  latest file mtime of what it stages (else birth time, else the folder's),
  rendered with the offset real at that instant (`date -r EPOCH
  +%Y-%m-%dT%H:%M:%S%z`, GNU `date -d @EPOCH`), equal to each other,
  ascending on the lane, never after now; a replayed commit keeps its own
  `%aI`; ref and zip names use UTC `Z`. Copy with `cp -p` / `rsync -a`. A
  replayed lane lands with `GIT_AUTHOR_DATE`/`GIT_COMMITTER_DATE` set to its
  tip's `%cI`; a closing `[DOCS]` commit takes the lane's latest content
  date. An orphan older than the target's HEAD takes HEAD plus one day at
  its own time of day; a blob already in history takes its first
  occurrence's date.
- Write in the moment: no "era", "pre-X", "later refactored to"; the log
  reads as normal development, no rebuild language, nothing invented.
- A historical bug is replayed faithfully, then fixed in a separate `[FIX]`
  dated today under your agent row.
- Preflight every affected repository first (`git-preflight.sh`), pushed to
  origin and verified with `git ls-remote` before any rebuild commit; never
  delete, rewrite or force a preflight; keep them until the owner accepts.
- Every byte of every snapshot ends reachable from a branch: a lane, the
  attic (`neo lane --close`) or a preflight.
- Push each action within seconds and check the remote tip equals local;
  halt on a mismatch.
- Landing on an existing dev needs the owner's verbatim grant, recorded;
  without it the work stays on unlanded lanes. A release (dev to main) is
  the owner's `neo release`; when a snapshot closes, run `neo release
  --dry-run` and hand over.
- After each landed lane run the compile, runtime and coverage checks
  (`verify.md`); on a failure roll back to the preflight and investigate.
- Self-audit from a fresh clone after every push: `neo doctor --history`,
  every lane landed and tagged, versions continuous, required paths present,
  local equals origin.
- Deliver a run directory: the manifest with every grant verbatim, the
  backup, per-snapshot artifacts, a report.

## Zip chains
- One preflight per (zip x repository), `preflight-bak-YYYY-MM-DD/NN` with
  NN from 01 shared across the repositories of one zip, titled
  `[NEW] WIP snapshot YYYY-MM-DD`, an orphan commit of the repository's full
  zip content minus `.git`, `__MACOSX`, `.DS_Store`, `.auth/`, `keys/`,
  certificates, `node_modules/`, `.env`, `build/`, `build-*/`, `exports/`,
  `*.zip` and workspace bans, dated at the zip's mtime, built in a scratch
  `mktemp -d`, never in the working repository; builds may run ten wide.
- Per zip: extract to a scratch directory keeping mtimes, find the touched
  repositories, plan the lanes (`commit.md`), commit with the date rules,
  land, check, then hand the release to the owner. Archive the zip to the
  backups only after every check passes; never delete the latest zip.
- Lost local preflight ref: restore it from origin; origin lost: rebuild it
  from the zip.

## Folder snapshots
- The working tree is irreplaceable: surface and ask by default. Scan about
  four levels, classify each folder (bare repo, tree with or without `.git`,
  expanded zip, container), show the table, ask about unmapped folders.
- Target per snapshot: surface candidates, never auto-pick; a new target is
  `neo setup`; a clone keeps the URL verbatim, confirms the destination and
  uses the credential account the owner chose; probe credentials without
  hanging (`gh auth status`, ssh `BatchMode`) and halt until they work;
  never push before the probe.
- Confirm the full summary and wait for an explicit yes; after it, ask only
  before irreversible steps (reach the owner by voice where the workspace
  provides it).
- Snapshots of one target run in chronological order, each against the
  previous one's commits. Back up first: `cp -pR` the snapshots, `git clone
  --mirror` the targets, push a preflight.
- Scope excludes `.git`, `node_modules`, `dist`, `build*`, lock files,
  `*.log`, `.DS_Store`, `.session`, `*.bak`, `*_old.qml` and workspace bans,
  applies the path prefix, writes `coverage.txt`.
- Parent by content match: 100 % skip, 90 % and up is the parent, below with
  a note, ties to the earliest author date; under about 30 % first check the
  cross-repository integration (target, named siblings, declared lineage;
  ask when unknown) and halt only if unexplained. A blob already anywhere in
  related history is integrated; the rest are orphans: diff them into new,
  modified, deleted.
- Placement, one per run: unlanded lanes (default), landing on dev only with
  the grant and when named, the attic only when the owner names it.
- Atomize: a subsystem or import graph is one feature, a new dependency with
  its users one, docs alone `[DOCS]`, stray tweaks `[FIX]`/`[REFACTOR]`,
  cleanup `[REFACTOR]` last; each cluster its own lane named for the
  feature; an earlier orphan from a later cluster commits first.
- After a `commit-tree`/`update-ref` replay, reset the work tree to the
  branch (after the preflight) before touching files; re-push only with
  `--force-with-lease=<branch>:<sha from a fresh ls-remote>`.

## Old repositories into one (reconstruct)
- Catalog the target module map first; never invent a module or class and
  document the gaps. C++ layout: `include/<ns>/<module>`, `src`,
  `third_party` only for unmanaged dependencies, each module independently
  buildable with CMake, sub-namespaces past three or four concerns.
- Replay real commits where history exists (keep merges with
  `--rebase-merges`; an empty merge after a path filter means cut before it;
  never replay a topic the source later removed); derive dates from mtimes
  where there is none. One lane per module; even a single commit gets its
  lane.
- Rename only the identifier and port the real logic; an unanswered rename
  question is decided on evidence and flagged. Drop classes that hard-code a
  single consumer's URL, user agent or cookie, saying why.
- Compile and test at every commit and merge; an MWE per module makes real
  calls, runs in the background under a kill timer, never opens modal system
  UI, cleans up; a final integration build links every module.
- Build traps: force_load or whole-archive as INTERFACE for self-registering
  objects, split by BUILD_INTERFACE/INSTALL_INTERFACE and proved by an
  external consumer's symbol table; Objective-C++ outside C++ namespaces;
  `-fobjc-arc` per file; the widgets component; PUBLIC dependencies for
  header-only inlines with `find_dependency` for PUBLIC sibling links;
  non-recursive per-target header globs; `__has_include` directories
  PRIVATE.
- Distribution: binaries through a separate dist repository, install EXPORT
  and Config files, FetchContent `SOURCE_SUBDIR` for internal consumers;
  verify every artifact, not a sample; a dev tag is never a release, and a
  release needs the owner's word and a throwaway consumer link test.
- Scrub remnants across content, every path ever, messages, diffs, ref
  names and identities (codenames, personal paths, self-references,
  hard-coded self identity); fix a leak at the commit that introduced it
  while unlanded (landed: a `fix` lane). Relocating a finished history into
  a subdirectory is done last, then re-audited; check for stray prefixed
  paths after a cross-layout cherry-pick (a clean status proves nothing).
- In a repurposed clone check `git remote -v` before any version math; fetch
  objects with `--no-tags`; no custom `IFS` over a loop body; never try an
  untested flag combination on the real target; compile or green alone is
  never proof; grep messages too, not only content; describe a class by what
  it is, not by its old consumer; never name a lane after its source.
- Re-scope onto a fresh throwaway by copying refs verbatim (dev, main,
  lanes, attic, `v*` and `release/*` tags). Do not stop until done.
