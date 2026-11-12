# Lens: forge, CI and tokens

## Pushes and runs
- `neo land`, `neo land --pr` and `neo release` push atomically and undo
  locally when a push fails; verify the result with `git ls-remote origin`
  when it matters. Push your lane after each commit.
- When the repository has a forge with the neo-check workflow, a push is not
  done until its runs are: confirm that neo-check, commit-audit and
  neo-linux fired on the pushed sha (a missing run is a finding), wait with
  `gh run watch` or an until-loop on `gh run list`, never a fixed sleep,
  read a failure with `gh run view --log-failed`, find its root cause (a
  failure your change did not cause is named and fixed in its own lane), and
  report green or red; never report done while a run is in flight. Local
  gates do not replace them.
- `neo land --pr` exit 3 is waiting (approvals on the exact merge, or a
  status): stop and report. A PR's `mergeable` and `statusCheckRollup` are
  read, never assumed. Never use the forge's merge button.

- In the framework source, forge behaviour is proven live by
  `tests/canary/live.sh` in one persistent canary repository (DESIGN.md,
  Live canary); it needs `repo` and `workflow`, never `delete_repo`, and
  removes only its run's unlanded lanes.

## Tokens
- gh holds the credential: use `gh api` and `gh auth status`; never extract
  a token into the transcript (`git credential fill` is refused by the
  guard), never print, log or write one to a file.
- Know the prefixes (`gho_` OAuth, `ghp_` classic, `github_pat_` fine
  grained, `ghs_` app installation, `ghr_` refresh). An OAuth token usually
  lacks `delete_repo` and admin; a 403 or 404 on an admin endpoint is a
  scope failure.
- Probe scopes once (`gh auth status`, or the `x-oauth-scopes` header),
  never by trial and error. Per operation: contents and PRs need `repo`,
  workflows `workflow`, rulesets admin rights on the repository,
  deletion `delete_repo`. Never ask for `delete_repo` unless a deletion was
  requested.
- Admin-only steps (`neo setup --remote`, a default branch change, rules on
  a plan without them) go to the owner; there is no fallback that writes
  main or deletes a repository.
