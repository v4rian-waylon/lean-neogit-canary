# neo

A lean git flow for humans and AI agents prototyping fast without giving up
quality, control or traceability.

- **Lanes in, one merge out.** Work happens on `lane/<kind>/n<N>.<slug>`
  (`n<N>`: the lane's number, in creation order, never shared, online or
  offline); `neo
  land` merges it into dev once, with its version tag, its requirement and the
  receipts of the gates that passed on the exact merged tree.
- **One requirements register.** `REQUIREMENTS.md` traces every requirement
  (status, priority, tests, source, code, protected rows, a graveyard) and is
  generated from `requirements/<slug>.md`, so it cannot drift.
- **Fork points stay forever.** `neo lane` anchors every lane at the commit
  it forked from (the branch `safety/<kind>/<slug>`) and `neo land` records where
  it ended (`vault/<kind>/<slug>`); every push of the lane carries its
  anchor, and nothing deletes or moves either.
- **Nothing is lost, nothing leaks.** Lanes, the attic, dev and main are
  never deleted by hand, and no secret, key, build output or archive is ever
  committed (`pre-commit`, land, pre-push, the agent guard).
- **History is the database.** Versions, lane names and requirements are read
  from dev's first-parent line; nothing else stores them. Every point of
  progress can be rebuilt, blamed and bisected per commit and per concern.
- **One flow.** The same commands work alone or in a team, online or offline,
  with or without a forge.
- **main is production.** Publishing is a release reaching main, and only the
  owner promotes dev to main (`neo release`; the identity-map row marked
  `owner`). dev is integration; pushing dev, lanes or tags to a remote is
  transport, never publishing. An agent never releases: it reports that dev
  is ready.

## Quick start

```sh
cp -R path/to/lean-neogit/.neo .   # vendor the framework, then drop its own
rm -rf .neo/tests .neo/bench .neo/FRAMEWORK   # tests, bench, source marker (setup --upgrade does this)
grep '^#' .neo/identity-map > m && mv m .neo/identity-map   # your team, not the framework's
cat > .neo/conf <<'CONF'            # your gates first: one shell command each, exit 0 passes
gates_fast=sh .neo/lint/run.sh && sh login_test.sh
gates_full=sh .neo/lint/run.sh && sh login_test.sh
gates_release=sh .neo/lint/run.sh && sh login_test.sh
CONF
printf 'test -f login.sh\n' > login_test.sh # your project's own test
.neo/neo setup                      # hooks, identity, the owner, main and dev
.neo/neo lane feature login -r "Users sign in with a passkey; login_test.sh proves the entry point exists." --proof login_test.sh
echo 'echo signed in' > login.sh    # commit in atomic steps, a change and its test together
git add login.sh login_test.sh && git commit -q -m "[NEW] Add the login entry point" -m "Users sign in through login.sh; login_test.sh checks that it exists."
.neo/neo land                       # gated, versioned, pushed atomically
.neo/neo doctor --history           # invariants I1 to I9 hold
```

Set your gates in `.neo/conf` first (`gates_fast`, `gates_full`,
`gates_release`: one shell command each, exit 0 passes), as the block does
before `neo setup`: setup refuses a conf whose gates run framework tests the
vendor dropped, land refuses an unset `gates_full` (`gates_full=none` lands
without one, said out loud), and S84 runs this block as written. The
personal-data lint in those gates refuses a personal email in any tracked
file, the identity map included: list the team under
`users.noreply.github.com` addresses, or leave the lint out of your gates.

## Commands

| Command | Does |
|---|---|
| `neo setup` | hooks, identity, seed main and dev; `--agent` guard (`--uninstall`, `--prefix`); `--remote` rulesets and CI (`--repo`, `--dry-run`); `--upgrade` the vendored `.neo` |
| `neo lane` | start a lane (`-r`, `--proof`, `--ticket`); `--close`, `--restore`, `--rename`, `--retire` |
| `neo check` | a gate on the work tree (`--gate`); `--each` the commit audit and the fast gate on every lane commit; `--audit` the deterministic commit audit on the lane or a merge's lane; `--reqs` REQUIREMENTS.md against the register `requirements/` generates (`--write` regenerates it); `--merge` the forge's proof of a `land --pr` candidate; `--judge` an advisory review (`--strict` fails on a finding) |
| `neo land` | merge once into dev, gated, tagged, pushed atomically (`-F` body, `--dry-run`); `--pr` through review; `--predict` gates ahead the exact merge a land on a given base would write |
| `neo train` | the merge train: the queued lanes in landing order; `add` queues a lane and `predict` gates every queued lane in parallel on its predecessors' predicted merges, so each land in order reuses its stored gates |
| `neo sync` | rebase the lane onto dev; `--dev` reconcile dev with origin after offline work (`--continue`, `--abort` a stopped re-land) |
| `neo release` | the owner only (main is production): release gate, `release/<v>` listing the lanes still open, main fast-forwards (`--dry-run`) |
| `neo bisect` | find the lane, then the commit, that broke a command |
| `neo status`, `neo doctor` | where you are (`--json`); the install (`--fix`), the history invariants (`--history`, `--since`, `--history-only`), every merge's gates rerun (`--prove`) |

Ten verbs, one CLI. The docs are checked against the code by `.neo/lint/docs.sh`.

## Read next

- [RULES.md](RULES.md): branches, commits, merges, versions, invariants, policy.
- [FLOWS.md](FLOWS.md): every flow as steps, for humans and agents.
- [DESIGN.md](DESIGN.md): why it is built this way and what it gives up.
- [tests/SCENARIOS.md](tests/SCENARIOS.md): the scenario matrix that proves it.
- `bench/` (framework source only): `speed.sh` and `loadbytes.py` measure
  lean's speed and read budget against neo-git (DESIGN.md, Measured).
- [skill/SKILL.md](skill/SKILL.md): the loader for AI agents, with its lens
  files (`skill/lenses/`) read one per task, and the map of every neo-git
  lens rule to its home (`skill/lenses/RULE-MAP.md`).
