# Rule map: every neo-git lens rule and its home in lean

neo-git carried 16 skills (lenses) of agent rules. lean keeps one skill: `SKILL.md`, which an agent loads,
and the lens files beside it, each read only for its task. This map lists every distinct rule of every
neo-git lens (ids `<lens>.<n>`, in the lens order) and where lean holds it: a lens file and section, the
skill itself, or the code that enforces it. "machinery gone" marks a rule about neo-git machinery the owner
removed (pool numbers, anchors, claim amend, modes); its intent, where it survives, is held elsewhere and
named. main is production: only the owner promotes dev to main. Not loaded for tasks; it is the audit trail
that no rule was lost (`lint/docs.sh` checks every home file exists).


## neo-git (loader)

| Rule | neo-git rule | Home in lean |
|---|---|---|
| neo-git.1 | Pick the one task row and read only its lenses; never load whole RUNBOOK/strategy docs | SKILL.md lens table |
| neo-git.2 | Canonical framework source is the framework repo dev; never edit a vendored copy | enforced: `agent/guard-write.sh`, S27; `.neo/FRAMEWORK` marker; AGENTS.md |
| neo-git.3 | Skill overrides from ~/.config/neo-git/skills, one copy per skill | machinery gone: user overrides cut, REPLAY row 136; one skill, intent irrelevant |
| neo-git.4 | Detect model: pool layout vs legacy feature/* | machinery gone: single lane model; intent irrelevant |
| neo-git.5 | Before any git write export GIT_AUTHOR_*/GIT_COMMITTER_* for the origin org's account; the user's own identity only for rebuilds of the user's ... | SKILL.md step 2; rebuild.md Common (identity) |
| neo-git.6 | A multi-row plan names every inventory lens with where it applies or why N/A | SKILL.md Always |
| neo-git.7 | Required checks green before merge; if the budget does not fit, it does not ship | enforced: `neo land`: check --each fast gate per commit, fast+full on merge tree; `neo release` release gate |
| neo-git.8 | Every claim in a commit (cause, fix, number) has a receipt gathered first; clean compile is not one; unverified changes wait uncommitted | SKILL.md Always; commit.md Receipts |
| neo-git.9 | Every change rides a branch, single commit included; dev/main take no direct commits | enforced: commit-msg dev/main refusal, pre-push, I1 |
| neo-git.10 | One defect, one pool: retries land on the same branch | SKILL.md Always |
| neo-git.11 | Merge only after the user ran the artifact and said it works, or a per-repo grant allows it | SKILL.md Always |
| neo-git.12 | No PR unless asked | SKILL.md Always |
| neo-git.13 | Merge body is the claim's PR paragraph + PR body verbatim; into main the release roster | machinery gone: claim |
| neo-git.14 | main moves only on the user's explicit instruction; automation never writes dev or main without a verbatim grant. main: | SKILL.md intro (main); SKILL.md Always (land) |
| neo-git.15 | Push right after each commit; push every ref you create plus tags; verify each push with `git ls-remote`; zsh-safe refspecs | SKILL.md Always; forge.md Pushes |
| neo-git.16 | Never pick nN, never push self-made pool/safety refs | machinery gone: allocator; slug uniqueness I7 ENFORCED at lane/sync/land |
| neo-git.17 | One pool = one feature area, ~20 commits max; bigger = sequence | enforced: `max_commits=20`, land refuses; S12 |
| neo-git.18 | Safety anchors stay forever; manual snapshots and bak zips go to Trash only on user direction, never hard-deleted. Anchors | history.md Recover (backups kept); attic never deleted (pre-push) |
| neo-git.19 | No empty commits | SKILL.md Always |
| neo-git.20 | Fresh repo fast-forwards main to dev | enforced: `neo setup` seeds main and dev at the root; main stays there until the owner releases, S47 |
| neo-git.21 | Intro commit: bare repo name title, README body, only .gitignore+README.md, source date when replanting | rebuild.md Common (dates) |
| neo-git.22 | Never invent a JIRA code | SKILL.md Always |
| neo-git.23 | Never touch user-authored commits without explicit authorization | SKILL.md Always; history.md Whose commit |
| neo-git.24 | Rewriting own commits keeps each original author; only the committer names your model | history.md How |
| neo-git.25 | After cherry-pick/replay/re-applied patch, diff against the baseline and grep every symbol the body claims; compare files by hash; "applied ... | history.md How |
| neo-git.26 | Commit dates keep the source's real offset; ref and zip names UTC Z; never asked | rebuild.md Common (dates) |
| neo-git.27 | Replay keeps author dates byte for byte, committer date = replay time | history.md How |
| neo-git.28 | A merge takes its source tip's committer date | rebuild.md Common (dates) |
| neo-git.29 | After a replay `git log --reverse --format=%ct base..tip / sort -c -n` passes and no commit is empty | history.md How |
| neo-git.30 | Merge body: 1-3 sentence paragraph, blank line, `- <Topic>.` bullets with indented ` - <label>: <summary>.` leaves, every list line ends with a ... | merge.md |
| neo-git.31 | Amend a merge only before the claim push; never amend/force main after tagging | machinery gone: merge written once; pre-push forward-only, tags immutable ENFORCED |
| neo-git.32 | Dash scrub in staged files, code included; a regex/fixture needing one writes `–`/`—` with a why comment. Messages | commit.md Hygiene |
| neo-git.33 | Message auto-fix and Co-Authored-By removal. Co-Authored-By | enforced: message.sh, guard rule 5 |
| neo-git.34 | Subject length enforced | enforced: 12-72, merge <=140 |
| neo-git.35 | Branch names enforced at push | enforced: pre-push lane/attic regex, core.sh slug regex |
| neo-git.36 | Version tags by the claim only | enforced: neo land tags; guard denies agent v-tag/--tags push; pre-push immutable tags |
| neo-git.37 | Rulesets when connected | enforced: `neo setup --remote` |

## how-dev (CI watch)

| Rule | neo-git rule | Home in lean |
|---|---|---|
| how-dev.1 | When a CI is connected, watch every run your push fires until completed | forge.md |
| how-dev.2 | Confirm the expected workflows fired on the head sha; a missing one is a signal to investigate | forge.md |
| how-dev.3 | Wait with `gh run watch` or an until-loop, never arbitrary sleeps | forge.md |
| how-dev.4 | Read failing logs (`gh run view --log-failed`), not just the conclusion | forge.md |
| how-dev.5 | Diagnose root cause; a failure unrelated to your change is named and fixed separately | forge.md |
| how-dev.6 | Report green or red as the closing artifact; never report done while runs are in flight | forge.md |
| how-dev.7 | Local green is not a substitute for CI | forge.md |
| how-dev.8 | After opening a PR, check mergeable and statusCheckRollup | forge.md Pushes; SKILL.md step 4 |
| how-dev.9 | Off-grid: run `bin/ci-local` before handing off; never `--allow-claim` before merge | machinery gone: ci-local/claims |
| how-dev.10 | Binding only when a CI is connected | forge.md |

## git-commit-audit

| Rule | neo-git rule | Home in lean |
|---|---|---|
| commit-audit.1 | One concept per commit; 2+ concepts or unrelated subsystems split | SKILL.md |
| commit-audit.2 | A title needing `+`, `,`, `and`, `with`, `plus` is a split smell | commit.md |
| commit-audit.3 | Soft cap ~800 lines per commit | commit.md |
| commit-audit.4 | Plan the split before staging | commit.md |
| commit-audit.5 | Every change rides a branch | enforced: dup neo-git.9 |
| commit-audit.6 | `[TAG] Title` sentence case; approved tags; no [CLEANUP] (cleanup = REFACTOR); [MERGE] tool-only | enforced: message.sh tag set, capital |
| commit-audit.7 | [NEW] only for a new file, integration, subsystem, operator workflow or build dependency; helpers/adapters inside existing code are REFACTOR; ... | commit.md |
| commit-audit.8 | Aim <=72 chars; hard limits by hook | enforced: 12-72 |
| commit-audit.9 | No hyphens in English compounds in title/body prose; identifier hyphens stay | commit.md |
| commit-audit.10 | No em/en dash, no word "plus", no Co-Authored-By: Claude (also on merges/amends). Dash + trailer | enforced: message.sh, guard |
| commit-audit.11 | Body opens with a 1-3 sentence paragraph at subsystem altitude: title = what, paragraph = why and scope, bullets = how; never restate the title | commit.md |
| commit-audit.12 | [FIX]/[HOTFIX]: `Cause:` then `Fix:` then bullets | commit.md |
| commit-audit.13 | Other tags: bullets directly after the paragraph; no `Changes:` header | commit.md |
| commit-audit.14 | [MERGE] body per merge-audit. See merge-audit. | commit.md |
| commit-audit.15 | Banned mechanism words anywhere: BAK, bak import, historical import, pre ATM role, captured in, from the zip, recovered from, reconstructed, WIP ... | commit.md |
| commit-audit.16 | V.1 top bullet leads with class/module name, not a path (unless the path is the story) | commit.md |
| commit-audit.17 | V.2 methods nest under their class; class name not repeated | commit.md |
| commit-audit.18 | V.3 bullets name classes/functions/methods only (no fields, properties, constants, handlerless signals) | commit.md |
| commit-audit.19 | V.4 no constructor bullets | commit.md |
| commit-audit.20 | V.5 one short verb-led sentence per symbol; no params, return shapes, step walks | commit.md |
| commit-audit.21 | V.6 reuse the docstring's verb and noun | commit.md |
| commit-audit.22 | V.7 third person present | commit.md |
| commit-audit.23 | V.8 standard verbs (Creates, Deletes, Updates, Reads, Writes, Schedules, Dispatches, Returns, Throws, Adds, Exposes, Drops); banned: Stands up, ... | commit.md |
| commit-audit.24 | V.9 new symbol declarative present; modified symbol uses "now" | commit.md |
| commit-audit.25 | V.10 never fabricate a symbol: grep each bullet name in the committed tree (`git show <sha>:<path>`) | commit.md |
| commit-audit.26 | No staged .DS_Store, .auth/, keys/, certs/profiles, build/, build-*/, node_modules/, .env, exports/, *.zip, aqtinstall.log, ... | commit.md Hygiene |
| commit-audit.27 | Stage by name; never `git add -A`/`.` | enforced: guard rule 5, also -u, :/, commit -a |
| commit-audit.28 | `node --check` passes for staged JS | commit.md Hygiene; verify.md Compile |
| commit-audit.29 | Dashes in staged files rewritten; fixtures use escapes with a comment | commit.md |
| commit-audit.30 | Real-time commits set no date vars; rebuild commits set both dates to the staged subset's latest mtime with real offset; a replayed commit keeps ... | rebuild.md Common (dates) |
| commit-audit.31 | Rebuild commits: author date == committer date, explicit offset, monotonic on the branch, <= now; copy with `cp -p`/`rsync -a` | rebuild.md Common (dates) |
| commit-audit.32 | Merge takes source tip committer date; closing [DOCS] takes the branch's latest content date | rebuild.md Common (dates) |
| commit-audit.33 | Only the brand-new repo root lands without a branch | enforced: neo setup root; commit-msg |
| commit-audit.34 | Branch name shape; never zipN/bak/wip/snapshot/historical in a branch name; ~20 commits per branch. Shape | enforced: slug regex |
| commit-audit.35 | `--no-ff` into dev; a meaningful branch carries a [DOCS] commit touching README. --no-ff | enforced: land, I1 |
| commit-audit.36 | Merge title `[MERGE] <source> into <target>: <version>`, version by tool; branches into dev, dev into main, no jumps | enforced: message.sh regex, neo land/release, I5 |
| commit-audit.37 | Merge bodies never mention rebuild, import, snapshot, recovered, reconstructed, WIP | commit.md |
| commit-audit.38 | Retroactive review: walk every commit, catalog offenses, plan corrective rewrite of your own commits only; siblings share defects | commit.md Before git commit |
| commit-audit.39 | A rewrite keeps author name/email/date; committer may name the model; committer date = replay time | history.md How |
| commit-audit.40 | A body asserting observed behavior (measured, verified, reproduces, Cause:, Fix: outcome, a number) carries a `Receipts:` section: per claim the ... | commit.md |
| commit-audit.41 | An untested clean-looking fix fails; reasoning + clean compile is not a receipt | commit.md |
| commit-audit.42 | No behavioral claim (docs, pure refactor, rename) needs no Receipts section | commit.md |
| commit-audit.43 | Before commit: re-read A-J vs staged diff, run the V.10 greps, node --check, confirm rebuild date vars | commit.md Before git commit |
| commit-audit.44 | A CI judge re-audits every push | commit.md Before git commit |

## git-merge-audit

| Rule | neo-git rule | Home in lean |
|---|---|---|
| merge-audit.1 | Title `[MERGE] <source> into <target>: <version>` | enforced: message.sh regex; land writes it |
| merge-audit.2 | No redundant "Merge" word | enforced: regex |
| merge-audit.3 | Merge subject length <=140 | enforced: see RULES.md |
| merge-audit.4 | No hyphens in prose, no em dash, no "plus" in merge text. Dash | enforced: see RULES.md |
| merge-audit.5 | Version mandatory, from the tool, never hand-typed | enforced: neo land computes vYYYY.S.N |
| merge-audit.6 | Body: 1-3 sentence paragraph, blank line, nested `- <Topic>.` / ` - <label>: <summary>.`, a period on every list line, no `Changes:`. Partly | enforced: paragraph then `- ` list, thin floor |
| merge-audit.7 | Failing shapes: paragraph only, bullets only, flat bullets, missing period, `Changes:` header, method names, comma-separated inline enumeration. ... | enforced: see RULES.md |
| merge-audit.8 | Reverts within the branch get their own `- Reverts within the branch.` topic | merge.md |
| merge-audit.9 | Altitude: lane merge topics group the lane's commits; release groups merges from the user's perspective. Lane: | merge.md |
| merge-audit.10 | The list is a literal recap of what merged, not a story; read-aloud test (neither signature prose nor marketing) | merge.md |
| merge-audit.11 | Forbidden (code pole): file/dir names, byte counts/timeouts, protocol/RFC refs, code-construct names, reviewer implementation verbs, token literals | merge.md |
| merge-audit.12 | Forbidden (manual pole): outcome pitch (actually works, just works, becomes usable), anthropomorphized assistant verbs, end-user benefit framing ... | merge.md |
| merge-audit.13 | This merge only: no reference to prior merges, siblings, future work; absolute terms | merge.md |
| merge-audit.14 | Forbidden in title/body: BAK, bak import, historical import, pre ATM role, captured in, from the zip, recovered from, reconstructed, WIP snapshot, ... | merge.md |
| merge-audit.15 | "rebuild" never as a noun; feature-led framing | merge.md |
| merge-audit.16 | No Co-Authored-By: Claude | enforced: see RULES.md |
| merge-audit.17 | `--no-ff` always | enforced: land, I1 |
| merge-audit.18 | Lane->dev merge dated at source tip %cI | rebuild.md Common (dates) |
| merge-audit.19 | dev->main merge dated at dev tip | machinery gone: main fast-forwards |
| merge-audit.20 | Only working branches merge into dev, under the canonical naming | enforced: land, pre-push, I1 |
| merge-audit.21 | dev merges into main at every release/zip close | SKILL.md intro; rebuild.md Common |
| merge-audit.22 | One tagged [MERGE] per branch; no untagged duplicates | enforced: I1, I2, I7 |
| merge-audit.23 | Never tag manually | enforced: land/release tag; guard; pre-push tag rules |
| merge-audit.24 | Amend a merge only before the claim push; never amend/force main | enforced: merge written once; dev/main forward-only |
| merge-audit.25 | Merge body minus PR paragraph equals PR body; patch both together; parity check script | machinery gone: land --pr uses the merge's own body as the PR body, ENFORCED |
| merge-audit.26 | Release merge appends open-pool roster | enforced: `neo release` lists open lanes in the release tag |
| merge-audit.27 | Connected-mode PR validator caveats (fix what validator changed) | machinery gone: cut by the owner |
| merge-audit.28 | Pre-push lens: title/version scan; body shape; macro-tone grep (file extensions, paths, byte counts, RFC, `[A-Z_]` tokens, impl verbs); ... | enforced: see RULES.md |
| merge-audit.29 | Legacy model specifics | machinery gone: cut by the owner |
| merge-audit.30 | Retroactive cleanup of bad merge titles via filter-branch/rebase exec | machinery gone: dev never rewritten; I3 machine-checks merges |

## git-history-preservation

| Rule | neo-git rule | Home in lean |
|---|---|---|
| preservation.1 | Never amend, retag, rebase, filter or rewrite a commit the user authored unless that commit is named and authorized; identical tree + new SHA is ... | history.md |
| preservation.2 | Heuristic: untagged prose titles are the user's; tagged are mine | history.md |
| preservation.3 | Heuristic: date boundary of the rebuild window (reflog). Superseded by model stamp; keep as fallback for pre-lean history | history.md |
| preservation.4 | Heuristic: author timezone shift. Superseded; | machinery gone: stamp decides |
| preservation.5 | Reflog comparison: original user SHA in reflog is canonical | history.md |
| preservation.6 | When in doubt, treat as the user's and do not touch | history.md |
| preservation.7 | Permitted on user commits: read, branch off, merge a new branch on top | history.md |
| preservation.8 | Forbidden: amend at their HEAD, rebase over them, filter-branch touching them, commit-tree reconstruction, force push over their ref. Partly | enforced: guard demands preflight for rebase/filter/amend-of-pushed/force; commit-tree under human author ... |
| preservation.9 | Recovery after accidental rewrite: stop; find originals via reflog/message; verify trees; pin originals to local refs; show the user the diff; ... | history.md |
| preservation.10 | Own session commits are fair game per rewrite lens; author line alone does not decide under neo-git | history.md |
| preservation.11 | Pre-rewrite checklist: list range, classify each, stop or narrow if any is the user's | history.md |

## git-history-rewrite

| Rule | neo-git rule | Home in lean |
|---|---|---|
| rewrite.1 | Consult preservation first; range holds no user commits | history.md |
| rewrite.2 | Rewrite preserves author name/email/date byte for byte; committer may carry `<Name> (<Model>)`; never `--reset-author`/`--author` on amend; ... | history.md |
| rewrite.3 | Replays keep author dates (never --ignore-date/--reset-author-date); committer date = replay time | history.md |
| rewrite.4 | After any replay: committer dates monotonic (`sort -c -n`) and no empty replayed commit | history.md |
| rewrite.5 | New-content commits take identity from the org export (or user for own snapshots), never git config/global | history.md |
| rewrite.6 | filter-branch: never `-- --all`; enumerate refs | enforced: guard denies filter-branch --all |
| rewrite.7 | After filter-branch, refresh remote-tracking refs, then force-with-lease | history.md |
| rewrite.8 | commit-tree walker when filter-branch is blocked, preserving all six identity/date fields and parents | history.md |
| rewrite.9 | Blank-repo wipe: orphan, empty tree, empty message, no tombstone; delete other branches | machinery gone: pre-push/rulesets forbid deleting or rewriting dev/main; guard denies push to main |
| rewrite.10 | Wipe proceeds without asking because a safety snapshot makes it reversible | machinery gone: safety snapshots |
| rewrite.11 | Force-push only with --force-with-lease on pushed branches | enforced: guard rule 3; neo sync uses a lease |
| rewrite.12 | Never include preflight-bak-* in a force push | enforced: F1: pre-push refuses any push of a non-lane branch; guard denies --no-verify |
| rewrite.13 | Deleting a default branch: change default first (admin) | machinery gone: dev/main never deleted, ENFORCED |
| rewrite.14 | Sandbox blocks filter-branch: use walker or `rebase -i` with exec | history.md |
| rewrite.15 | Origin is canonical for preflight refs; refresh local copies from origin | history.md |
| rewrite.16 | Snapshot affected branches as safety/<branch>-<ts>, push before rewriting; force back on rejection | history.md |

## git-snapshot-preflight

| Rule | neo-git rule | Home in lean |
|---|---|---|
| preflight.1 | One preflight per (zip x repo) | rebuild.md |
| preflight.2 | Name `preflight-bak-YYYY-MM-DD/NN`, NN from 01, global across repos for one zip. Name shape | enforced: git-preflight.sh |
| preflight.3 | Title `[NEW] WIP snapshot YYYY-MM-DD` | rebuild.md |
| preflight.4 | Author+committer date = zip mtime with real offset; names in UTC Z | rebuild.md |
| preflight.5 | Identity exported (org or user), never git config/global/hardcoded | rebuild.md |
| preflight.6 | Tree = the repo's full zip content minus sensitive files | rebuild.md |
| preflight.7 | Orphan commit, no parent | rebuild.md |
| preflight.8 | Push to origin first, before any rebuild commit | enforced: guard requires the ref on origin when one exists |
| preflight.9 | Never delete the preflight branch on origin | enforced: F1 |
| preflight.10 | Never rewrite its SHA or force-push against it | enforced: F1 |
| preflight.11 | Never filter-branch -- --all | enforced: guard |
| preflight.12 | Exclude .git, __MACOSX, .DS_Store, .auth/, keys/, certs/profiles, node_modules/, .env, build/, build-*/, exports/, *.zip, workspace bans. Mostly | rebuild.md Zip chains |
| preflight.13 | Build preflights in a scratch dir, never in the working repo | enforced: temp index, no checkout |
| preflight.14 | No hardcoded paths; scratch via mktemp -d honouring TMPDIR | rebuild.md |
| preflight.15 | Dispatch builds in parallel (10 workers) | rebuild.md |
| preflight.16 | Verify every affected repo's preflight on origin via ls-remote before any rebuild commit | rebuild.md |
| preflight.17 | Never `git push origin --all` | enforced: guard rule 3 treats --all/--mirror as a main push |
| preflight.18 | Never force-with-lease a preflight after the initial push | enforced: F1 |
| preflight.19 | Recovery: restore local preflight ref from origin; if origin lost, rebuild from zip | rebuild.md |

## git-snapshots

| Rule | neo-git rule | Home in lean |
|---|---|---|
| snapshots.1 | Establish scope first (workspace, bak dir, mirror, in-scope repos, identity): infer in order (user path, multi-repo cwd, baks/ dir, CLAUDE.md), ... | rebuild.md |
| snapshots.2 | Before any force/delete push, reset --hard, filter-branch, rebase: safety-snapshot each affected branch and push it first | history.md How (preflight) |
| snapshots.3 | On "stop/revert/undo/roll back" restore from the latest safety snapshot | history.md Recover |
| snapshots.4 | Keep safety snapshots until the user accepts the result | history.md Recover |
| snapshots.5 | Irreversible ops (repo delete, force push with no snapshot) need a genuine `Confirm IRREVERSIBLE` ask. Repo deletion | history.md Recover |
| snapshots.6 | Step 0: extract each zip to a mktemp scratch preserving mtimes; find touched repos; compute date/NN | rebuild.md |
| snapshots.7 | Step 1: safety + one preflight per affected repo, pushed before any rebuild commit | rebuild.md |
| snapshots.8 | Step 2: plan topics/branches via strategy audit before committing | rebuild.md |
| snapshots.9 | Step 3: commit-audit per commit; dates = staged subset latest mtime; paragraph opens body; [NEW] only for genuinely new | rebuild.md |
| snapshots.10 | Step 4: after every merge into dev run merge, coverage, compile, runtime audits; on failure reset to safety and investigate | rebuild.md Common; verify.md |
| snapshots.11 | Step 5: close each zip with dev->main and rerun audits on main | rebuild.md |
| snapshots.12 | Step 6: push force-with-lease only; never include preflights | rebuild.md |
| snapshots.13 | Step 7: archive the zip to mirror/baks/archived only after all checks; never delete the latest zip; keep safety until next acceptance | rebuild.md |
| snapshots.14 | Blank repo: orphan empty tree empty message | machinery gone (see rewrite.9) |
| snapshots.15 | Memory and skills are binding; read before committing or dispatching | rebuild.md |
| snapshots.16 | Apply every rule on the first pass; sub-agents get rules inline or a skill pointer | SKILL.md Always |
| snapshots.17 | Active-monitor background agents; watch their refs; intervene before push | history.md Recover |
| snapshots.18 | Never ask effort-saving questions | rebuild.md |
| snapshots.19 | Never touch user commits. Dup preservation.1. | rebuild.md |
| snapshots.20 | The resulting log reads as normal development: no zip/rebuild language, no fabrication | rebuild.md |
| snapshots.21 | Project scope (repos, build commands, init markers) lives in workspace CLAUDE.md, not the skill | rebuild.md |

## git-strategy-audit

| Rule | neo-git rule | Home in lean |
|---|---|---|
| strategy.1 | Decide strategy before the first commit | commit.md Plan |
| strategy.2 | Pick the model (pool layout or legacy), never mix | machinery gone: cut by the owner |
| strategy.3 | Layout main<-dev<-pool with paired safety anchor | machinery gone: lanes; attic |
| strategy.4 | main only from dev; dev only from pools | enforced: pre-push, I1, I5 |
| strategy.5 | Version vYYYY.main.dev with resets | enforced: vYYYY.S.N, I2, S31 |
| strategy.6 | Hotfixes follow dev->main, never a bypass | enforced: main only fast-forwards to a released dev commit, I5; HOTFIX is a lane |
| strategy.7 | Cut the branch off dev; merge --no-ff into dev | enforced: `neo lane` from dev; land |
| strategy.8 | Lay out atomic commits and name the branch first | SKILL.md |
| strategy.9 | Heuristics: one new file = one commit; one refactor pass = one; one bug fix = one; adjacent tooling = own commit; in doubt split | commit.md Plan |
| strategy.10 | Branch format regex | enforced: lane/<kind>/<slug>, kinds feature fix refactor docs test chore |
| strategy.11 | nN from the allocator | machinery gone: cut by the owner |
| strategy.12 | Paired safety anchor, never touched | machinery gone: cut by the owner |
| strategy.13 | Forbidden in branch names: zipN, bak, wip, snapshot, historical, preflight, recovered, reconstructed, from-zip, captured-in; uppercase. Uppercase | enforced: slug regex |
| strategy.14 | Names describe the feature, not the mechanism; no `temp` | commit.md Plan |
| strategy.15 | --no-ff always | enforced: see RULES.md |
| strategy.16 | One tagged merge per branch | enforced: see RULES.md |
| strategy.17 | dev into main per release | enforced: owner `neo release` |
| strategy.18 | Every meaningful branch (subsystem, integration, operator workflow, architecture) touches README via a [DOCS] commit (or a one-line delta in the ... | commit.md Plan |
| strategy.19 | Per-release/zip planning: diff vs previous, group topics (one per branch), commit list, README commit, single-commit topics still get a branch | commit.md Plan |
| strategy.20 | Merge order respects dependency layering (deps first) | commit.md Plan |
| strategy.21 | Plan the release boundary | commit.md Plan |
| strategy.22 | Strategy lens before merge/push (items 1-10). Mostly | enforced: see RULES.md |
| strategy.23 | Blank-main exception (`Initial`) | machinery gone: cut by the owner |
| strategy.24 | Banned: direct commit to dev/main ( | enforced: ENFORCED: lane cuts from dev |

## git-reconcile-intent

| Rule | neo-git rule | Home in lean |
|---|---|---|
| reconcile.1 | Reason at the diff layer (what each change adds/changes/removes), not the end state | history.md Conflicts |
| reconcile.2 | Decide per hunk, never per file/commit | history.md Conflicts |
| reconcile.3 | Per hunk: context present -> apply verbatim; absent -> `git log --all -S` to tell never-landed (insert at natural slot, flag as interpretation) ... | history.md Conflicts |
| reconcile.4 | Report a failed allocation (hunk, what it does, why it does not fit, options); never silently drop or reshape | history.md Conflicts |
| reconcile.5 | Detect conflicts canonically (`git diff --name-only --diff-filter=U`, `git ls-files -u`, `git status --porcelain`), never greedy marker greps | history.md Conflicts |
| reconcile.6 | Doc claims must match code; fix a wrong doc and surface the code concern; never copy prose across repos unverified | history.md Conflicts |
| reconcile.7 | Isolate the exact failure mode before retrying | history.md Conflicts |
| reconcile.8 | Recipe: cherry-pick --no-commit; reset conflicted file; apply hunks; sanity gate; commit preserving metadata | history.md Conflicts |
| reconcile.9 | Auto-rebase L1-L5 ladder, reconcile branches pushed as CREATE, original PR untouched | machinery gone: author runs `neo sync`; DESIGN table |
| reconcile.10 | Never reconcile across user commits without authorization. Dup preservation.1. | history.md Conflicts |

## git-compile-audit

| Rule | neo-git rule | Home in lean |
|---|---|---|
| compile.1 | Node: `npm install --silent --no-audit --no-fund` and `node --check` every JS outside node_modules/build | verify.md Compile |
| compile.2 | Qt lib: clean build dir, cmake configure + build; static lib and QML plugin lib emitted | verify.md Compile |
| compile.3 | Qt app: needs adjacent lib repos; for a historical point use each lib's latest preflight dated <= the zip date | verify.md Compile |
| compile.4 | Pass = .app emitted | verify.md Compile |
| compile.5 | Compile after each merge into dev and on main after release | enforced: land on every merge tree; gates_release |
| compile.6 | Save build logs to a per-run mktemp dir; the log is the audit trail | verify.md Compile |
| compile.7 | On failure diagnose by kind; fix in the atomic commit that introduced it | verify.md Compile |
| compile.8 | Run up to 4 compiles in parallel | verify.md Compile |
| compile.9 | Banned: Qt app without matching-date lib preflights; skipping npm install because node_modules exists; judging by cmake warnings (only the build ... | verify.md Compile |

## git-coverage-audit

| Rule | neo-git rule | Home in lean |
|---|---|---|
| coverage.1 | Preflight coverage: preflight tree byte-identical to the zip extract, no allowed diff | verify.md Coverage |
| coverage.2 | Merge coverage: after each dev merge and dev->main at zip close, tree byte-identical to the zip minus sensitive files, README.md and .gitignore | verify.md Coverage |
| coverage.3 | Use `diff -r --brief` with exactly the sensitive + README + .gitignore (+aqtinstall.log) excludes | verify.md Coverage |
| coverage.4 | Pass iff zero differ lines, zero only-in-repo (beyond allowed), zero only-in-zip | verify.md Coverage |
| coverage.5 | Differ: inspect with `diff -u`; whitespace-only is acceptable but documented; content -> amend the right commit | verify.md Coverage |
| coverage.6 | Only in zip -> add in the right atomic commit; only in repo -> gitignore+drop or document | verify.md Coverage |
| coverage.7 | Save a per-zip coverage ledger | verify.md Coverage |
| coverage.8 | Banned: skipping small zips; accepting a differ without `diff -u`; widening excludes | verify.md Coverage |

## git-runtime-audit

| Rule | neo-git rule | Home in lean |
|---|---|---|
| runtime.1 | Boot-check after every merge into dev, after release, and from a fresh clone of origin/main | verify.md Runtime |
| runtime.2 | Repo type: workspace CLAUDE.md authoritative; else file heuristics (package.json, CMakeLists, Cargo, go.mod, pyproject, Makefile); ask once only ... | verify.md Runtime |
| runtime.3 | Per-type check matrix (build, brief run, pass criterion) | verify.md Runtime |
| runtime.4 | Init markers from workspace CLAUDE.md; default pass = alive for the window and none of Error, EADDRINUSE, ENOMODULE, ImportError, Traceback, ... | verify.md Runtime |
| runtime.5 | Tolerable error markers must be declared in workspace CLAUDE.md; unreachable downstream = PENDING not FAIL | verify.md Runtime |
| runtime.6 | macOS: `open` returns immediately, confirm with pgrep; precise pkill; codesign sanity | verify.md Runtime |
| runtime.7 | Fresh-clone deployability check is mandatory, the final gate (catches untracked-but-used files, stale lock, absolute paths, submodules, LFS) | verify.md Runtime |
| runtime.8 | Save logs per (zip x repo) until the user accepts | verify.md Runtime |
| runtime.9 | A runtime failure blocks the push; roll back, fix or split, retry | enforced: land refuses, dev unchanged |
| runtime.10 | Parallel checks use distinct ports, temp dirs and kill patterns | verify.md Runtime |
| runtime.11 | Banned: skip runtime because compile passed; skip fresh clone; check after push; silence errors undeclared; working tree instead of fresh clone ... | enforced: land gates run before the merge exists |
| runtime.12 | Notarization is out of scope; flag separately | verify.md Runtime |

## git-token-discovery

| Rule | neo-git rule | Home in lean |
|---|---|---|
| token.1 | Get the GitHub token via `git credential fill` | forge.md Tokens |
| token.2 | Token is secret: never print, hold in a variable | enforced: guard rule 4 |
| token.3 | Never write the token to a file outside the session | forge.md Tokens |
| token.4 | Know token types by prefix (gho_, ghp_, github_pat_, ghs_, ghr_) | forge.md Tokens |
| token.5 | gho_ tokens usually lack delete_repo/admin; 403 or 404 on admin endpoints = scope failure | forge.md Tokens |
| token.6 | Fallbacks: repo delete -> orphan wipe or user UI; default-branch change -> push to main or user; protection -> admin or user | forge.md Tokens |
| token.7 | Probe scopes once (`x-oauth-scopes` / `gh auth status`), never trial-and-error | forge.md Tokens |
| token.8 | Per-operation scope cheatsheet | forge.md Tokens |
| token.9 | Never ask for delete_repo scope unless a repo delete was requested | forge.md Tokens |

## git-shuttle

| Rule | neo-git rule | Home in lean |
|---|---|---|
| shuttle.1 | Ask for every path, repo mapping and grant; assume none; identity and dates derived by rule | rebuild.md Folder snapshots |
| shuttle.2 | Every question offers "Other, tell me what I'm missing"; free-form answers recorded verbatim (`user_clarifications[]`) | rebuild.md Folder snapshots |
| shuttle.3 | The working tree is irreplaceable; default to surfacing and asking | rebuild.md Folder snapshots |
| shuttle.4 | Lossless: every byte of every snapshot ends reachable from a branch | rebuild.md Folder snapshots |
| shuttle.5 | A blob anywhere in related repos' `--all` history is integrated (skip); others are orphans needing a placement decision | rebuild.md Folder snapshots |
| shuttle.6 | Halts reach the user via the workspace channel; independent work continues | rebuild.md Folder snapshots |
| shuttle.7 | Step 1 scan ~4 levels, classify (bare, tree with/without .git, expanded zip, container), show the table, ask; unmapped folders asked about | rebuild.md Folder snapshots |
| shuttle.8 | Step 2 target repo per snapshot: surface candidates, never auto-pick; init (root on dev, main ff), clone (URL verbatim, destination confirmed, ... | rebuild.md Folder snapshots |
| shuttle.9 | Step 3 author as the user for the user's dropped work (manifest override, memory or CLAUDE.md), org account otherwise; ask only if none; export ... | rebuild.md Folder snapshots |
| shuttle.10 | Step 4 ask push policy; probe credentials non-hanging (gh auth status; credential fill only with timeout; ssh BatchMode) and halt until they work; ... | rebuild.md Folder snapshots |
| shuttle.11 | Step 5 writing existing dev/main needs the user's verbatim grant, recorded; no grant -> parallel branches | rebuild.md Folder snapshots |
| shuttle.12 | Step 6 confirm the full summary, wait for explicit yes; no questions after except irreversible steps | rebuild.md Folder snapshots |
| shuttle.13 | Step 7 also reach the user by voice before executing where voice-ask exists | rebuild.md Folder snapshots |
| shuttle.14 | Snapshots for one target run in chronological order, each against the previous one's commits | rebuild.md Folder snapshots |
| shuttle.15 | A backup: `cp -pR` snapshots, `git clone --mirror` targets, push a preflight-bak before any commit; never delete/force it | rebuild.md Folder snapshots |
| shuttle.16 | B scope: exclude .git, node_modules, dist, build*, lock files, *.log, .DS_Store, .session, *.bak, *_old.qml plus workspace bans; apply path ... | rebuild.md Folder snapshots |
| shuttle.17 | C parent commit via content-match: 100% skip; >=90% parent; <90% parent with note; ties earliest author date; <~30% run C.5 first, halt only if ... | rebuild.md Folder snapshots |
| shuttle.18 | C.5 cross-repo integration check over target, named siblings and declared lineage (ask if unknown); write integration.tsv/summary | rebuild.md Folder snapshots |
| shuttle.19 | D diff parent vs snapshot for orphans into NEW/MODIFIED/DELETED | rebuild.md Folder snapshots |
| shuttle.20 | D.5 one placement per run: P-1 parallel _2 branches (default), P-2 direct mainline only with grant and when named, P-3 archival branch only when ... | rebuild.md Folder snapshots |
| shuttle.21 | D.6 atomize: subsystem/import graph -> one feature; new dep + users -> one; docs alone -> DOCS; stray tweaks -> FIX/REFACTOR; cleanup -> REFACTOR ... | rebuild.md Folder snapshots |
| shuttle.22 | D.7 timestamps: raw = mtime, else birth time, else folder birth; render with real offset; orphan older than target HEAD -> HEAD + 1 day keeping ... | rebuild.md Folder snapshots |
| shuttle.23 | E commit in plan order: stage by name ( | enforced: no "era", "pre-X", "later refactored to" |
| shuttle.24 | F merge each branch --no-ff per merge-audit, date = latest content commit; P-1 ff main_2; P-2 dev->main; P-3 push archival alone | rebuild.md Folder snapshots |
| shuttle.25 | After commit-tree + update-ref replays run `git reset --hard` to the branch before file ops | rebuild.md Folder snapshots |
| shuttle.26 | Re-push with `--force-with-lease=<branch>:<sha from fresh ls-remote>` | rebuild.md Folder snapshots |
| shuttle.27 | Push each action within seconds; never batch | rebuild.md Folder snapshots |
| shuttle.28 | G verify coverage, compile, runtime; on failure halt, report, ask or roll back from the mirror; never skip | rebuild.md Folder snapshots |
| shuttle.29 | Output run dir (manifest with grants verbatim, BACKUP, per-snapshot artifacts, REPORT.md); deliver to the outbound shuttle | rebuild.md Folder snapshots |
| shuttle.30 | Banned: touching user commits; hardcoded paths/identities/grants; inferring a dev/main grant; force without lease; ever force-pushing main; ... | enforced: guard |
| shuttle.31 | Use git-snapshots for zip chains, git-shuttle for folders, both for mixed | rebuild.md Folder snapshots |

## git-reconstruct

| Rule | neo-git rule | Home in lean |
|---|---|---|
| reconstruct.1 | Never touch the originals; all output to a throwaway target | rebuild.md Old repositories |
| reconstruct.2 | Preflight every source before processing | rebuild.md Old repositories |
| reconstruct.3 | Replay real commits (author, dates, message) where history exists | rebuild.md Old repositories |
| reconstruct.4 | Derive dates from mtimes where there is no history | rebuild.md Old repositories |
| reconstruct.5 | Compile and test at every commit and merge | enforced: `neo check --each`, land gates |
| reconstruct.6 | One topic branch per module, `--no-ff` into dev, no PR | enforced: one lane per module, `neo land` |
| reconstruct.7 | Do not stop until done | rebuild.md Old repositories |
| reconstruct.8 | Catalog the target module map first; layout include/<ns>/<module>, src, third_party only for unmanaged deps, independently buildable CMake; ... | rebuild.md Old repositories |
| reconstruct.9 | Discover identities per source verbatim; never normalize; replayed commits carry the source identity, new work today's identity; never blend | rebuild.md Old repositories |
| reconstruct.10 | Rename only the identifier; port real logic; an unanswered rename question is resolved on evidence and flagged in the report | rebuild.md Old repositories |
| reconstruct.11 | Reusability filter: exclude classes hardcoding a single consumer's URL, UA, cookie; say why | rebuild.md Old repositories |
| reconstruct.12 | A historical bug is replayed faithfully, then fixed in a separate [FIX] dated today under today's identity | rebuild.md Old repositories |
| reconstruct.13 | Build gotchas: force_load/whole-archive INTERFACE for self-registering objects; ObjC++ outside C++ namespaces; -fobjc-arc per file; add widgets ... | rebuild.md Old repositories |
| reconstruct.14 | MWE per module: real calls, background + kill timer, never modal system UI, explicit cleanup; final integration CMake of all modules | rebuild.md Old repositories |
| reconstruct.15 | Document catalogue gaps; never invent a module or class | rebuild.md Old repositories |
| reconstruct.16 | Re-scope onto a fresh throwaway by copying refs verbatim | rebuild.md Old repositories |
| reconstruct.17 | Structural self-audit after every push from a fresh clone: every branch landed, every merge tagged, versions continuous, ... | rebuild.md Common (self-audit) |
| reconstruct.18 | Even single-commit steps get their own branch when the repo does | enforced: every change is a lane |
| reconstruct.19 | Remnant scrub over content, every path ever, messages, diffs, ref names, identities for codenames, personal paths, internal self-references, ... | enforced: `lint/personal.sh`: home paths and real emails in tracked files, every gate |
| reconstruct.20 | Fix a leak at the commit that introduced it, never a later patch | rebuild.md Old repositories |
| reconstruct.21 | A published defect: never a [FIX] after the merge; fix at origin, replay to a new throwaway, verify from an independent clone, publish via ... | history.md (fixed forward); SKILL.md Always |
| reconstruct.22 | Fix an original commit in isolation preserving all six identity/date fields | rebuild.md Old repositories |
| reconstruct.23 | Relocate a finished history into a subdirectory last (filter-repo), then re-audit | rebuild.md Old repositories |
| reconstruct.24 | Distribution: binaries via a separate dist repo; install EXPORT + Config; FetchContent SOURCE_SUBDIR for internal consumers; a dev tag is never a ... | enforced: owner-only |
| reconstruct.25 | Verify every artifact, not a sample; PUBLIC sibling links need find_dependency | rebuild.md Old repositories |
| reconstruct.26 | Split force_load with BUILD_INTERFACE/INSTALL_INTERFACE; prove with an external consumer's symbol table | rebuild.md Old repositories |
| reconstruct.27 | After a cross-layout cherry-pick, find stray prefixed paths; clean status is not proof | rebuild.md Old repositories |
| reconstruct.28 | Replays onto a fresh root keep merges (`--rebase-merges`); an empty merge after a path filter means cut before it | rebuild.md Old repositories |
| reconstruct.29 | In a repurposed clone check `git remote -v` before version math | rebuild.md Old repositories |
| reconstruct.30 | Anti-patterns: blended commit from two sources (replay deeper history); branch named after its source; compile/green as proof; content-only greps ... | rebuild.md Old repositories |
| reconstruct.31 | Fix unpushed history in place: preflight, reset to the bad commit, amend, replay later commits; keep backups until verified; retire them with the ... | rebuild.md Old repositories |
