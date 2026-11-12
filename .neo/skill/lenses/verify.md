# Lens: compile, runtime and coverage checks

`neo land` runs `gates_fast` on every lane commit and both `gates_fast` and
`gates_full` on the merge tree before the merge exists; `neo release` runs
`gates_release`. These rules say what those gates must hold; a check the
gates lack is run by hand and its log kept.

## Compile
- The gates compile the project: Node runs `npm install --silent --no-audit
  --no-fund` (always, even when `node_modules` exists) and `node --check`
  on every JS file outside `node_modules` and build output; a Qt library
  configures and builds into a clean build directory (the static and QML
  plugin libraries emitted); a Qt app builds against its adjacent libraries
  (for a historical point, each library at its latest preflight dated at or
  before that point) and passes when the `.app` is emitted. Use the
  workspace's build tool when it has one.
- Only the build's exit code counts, never the warnings. Logs go to a
  per-run `mktemp -d` directory: the log is the audit trail. Up to four
  compiles run in parallel.
- A failure is diagnosed by kind and fixed in the commit that introduced it
  (unlanded, after the preflight) or by a `fix` lane (landed).

## Runtime
- The full and release gates boot what they build, and the release is also
  booted from a fresh clone of origin (catches untracked files, stale locks,
  absolute paths, submodules, LFS); the forge's neo-linux job is a clean
  checkout too.
- The repository type comes from the workspace instructions first, else
  from its files (`package.json`, `CMakeLists.txt`, `Cargo.toml`, `go.mod`,
  `pyproject.toml`, `Makefile`); ask once only when several are unknown,
  else check compile only; remember the answer for the session.
- Pass: the process stays alive for the window, prints the workspace's init
  markers, and none of `Error`, `EADDRINUSE`, `ENOMODULE`, `ImportError`,
  `Traceback`, `panic:`, `Segmentation fault`, `Killed`. Tolerable markers
  are declared in the workspace instructions; an unreachable downstream is
  PENDING, not FAIL. Never silence an undeclared error.
- macOS: `open` returns at once, confirm with `pgrep`, stop with a precise
  `pkill`; signing and notarisation are out of scope and never the
  explanation of a failure.
- Parallel checks use distinct ports, temp dirs and kill patterns. Logs are
  kept until the owner accepts. A runtime failure blocks the land: roll
  back, fix or split, retry. Never skip it because the compile passed, never
  check after the push.

## Coverage (rebuilds from snapshots)
- A preflight tree is byte-identical to its snapshot; after each lane lands,
  dev's tree equals the snapshot minus the sensitive files, `README.md` and
  `.gitignore` (and `aqtinstall.log`), by `diff -r --brief` with exactly
  those excludes, never wider.
- Pass: zero differing files, zero only in the repository beyond the
  allowed, zero only in the snapshot. A differing file is read with
  `diff -u` (whitespace-only is accepted and documented; content is fixed
  in the commit that carries it); a file only in the snapshot is added in
  its atomic commit; a file only in the repository is ignored and dropped,
  or documented.
- Keep one coverage ledger per snapshot; never skip a small snapshot.
