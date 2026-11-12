# Replay record

lean-neogit replays neo-git's pool history in distilled form. Each neo-git pool merge is listed in order
with its verdict: REPLAY (its own lean lane), FOLD (carried by another row's lane, named in that lane's
Replays: trailer) or CUT (no lean counterpart, with the reason). Generated from REPLAY-MAP; the version
tag of each lane resolves to its merge (git rev-parse <version>^{commit}).

| # | neo-git pool | sha | verdict | lean lane / reason |
|---|---|---|---|---|
| 1 | pool/n1.feature.template-skeleton | a19b32e | REPLAY | lane/feature/foundation, v2026.0.1 |
| 2 | pool/n2.feature.in-repo-audit-skills-and-hooks | b69006c | REPLAY | lane/feature/test-harness, v2026.0.2 |
| 3 | pool/n4.feature.auto-pair-safety-on-pool-create | 5a3ee38 | CUT | safety anchors dropped: DESIGN 'What lean-neogit gives up' row 3 (landed lanes stay reachable through the merge's second parent; sync keeps a preflight ref) |
| 4 | pool/n8.feature.auto-rebase-pools-after-dev-merge | 3c784ad | REPLAY | lane/feature/sync, v2026.0.3 |
| 5 | pool/n12.feature.rebase-onto-detect-plus-reconcile-conflict-flow | 6cac99d | REPLAY | lane/feature/sync-conflict, v2026.0.4 |
| 6 | pool/n24.fix.claim-merge-ci-permissions-plus-stdin-and-fstring | c74a849 | CUT | claim CI workflow permissions: the claim workflow is gone; landing is local (DESIGN row 'GitHub merge button, PR validation workflows, claim workflows') |
| 7 | pool/n15.feature.iterative-reconcile-retry-until-resolved | b1b3f90 | FOLD | carried by row 5 |
| 8 | pool/n3.feature.vault-archive-pool-on-merge | a0c0398 | CUT | vault archive dropped: DESIGN row 3 |
| 9 | pool/n5.feature.heal-ensures-dev-branch-exists | 5439950 | REPLAY | lane/feature/setup-seed-dev, v2026.0.5 |
| 10 | pool/n9.refactor.streamline-version-format-to-year-main-dev | 0baf12f | REPLAY | lane/feature/version-format, v2026.0.6 |
| 11 | pool/n6.feature.seed-dev-on-main-create | dc6fa2c | FOLD | carried by row 9 |
| 12 | pool/n7.fix.enforce-hyphens-in-branch-naming-regex | b091569 | REPLAY | lane/fix/slug-hyphens, v2026.0.7 |
| 13 | pool/n10.refactor.tags-as-version-seal-plus-version-bin | 36870d5 | REPLAY | lane/feature/tags-as-seal, v2026.0.8 |
| 14 | pool/n14.fix.release-reuses-dev-tag-no-cycle-bump | 183d62f | REPLAY | lane/feature/release, v2026.0.9 |
| 15 | pool/n11.feature.build-on-tag-plus-dual-channel-distribution | a65f653 | REPLAY | lane/feature/release-gate, v2026.0.10 |
| 16 | pool/n20.feature.real-world-e2e-consumer-conflict-rollover | 6c2af90 | REPLAY | lane/test/series-rollover, v2026.0.11 |
| 17 | pool/n13.feature.freeze-vault-branches-via-ruleset | 59f7c97 | FOLD | carried by row 37 |
| 18 | pool/n19.feature.ops-bins-status-ship-release-of | 41d8eda | REPLAY | lane/feature/status, v2026.0.12 |
| 19 | pool/n16.refactor.delete-dead-bump-and-init-version-scripts | 7314c26 | CUT | dead bump/init-version scripts never existed in lean |
| 20 | pool/n21.refactor.doc-alignment-to-current-spec | cdd1c0f | REPLAY | lane/docs/readme-quickstart, v2026.0.13 |
| 21 | pool/n22.feature.maximum-score-push-ops-bins-tests-docs | c4b0302 | REPLAY | lane/feature/doctor-install, v2026.0.14 |
| 22 | pool/n23.refactor.contributing-doc-template-consumers-and-hackers | f04f4be | REPLAY | lane/docs/flows, v2026.0.15 |
| 23 | pool/n25.fix.cycle-counter-starts-at-zero | 804e62e | REPLAY | lane/fix/series-start, v2026.0.16 |
| 24 | pool/n26.fix.test-fixtures-plus-restore-ci-test-workflow | dd91b4a | FOLD | carried by row 2 |
| 25 | pool/n27.refactor.root-readme-changelog-plus-template-readme-truth | f84acf8 | REPLAY | lane/docs/root-readme, v2026.0.17 |
| 26 | pool/n28.feature.ci-bootstrap-tool-plus-tagger-only-architecture | 06ce90c | REPLAY | lane/feature/remote-check, v2026.0.18 |
| 27 | pool/n29.fix.tag-drift-sanity-empty-input-bug | ef8b49d | FOLD | carried by row 21 |
| 28 | pool/n30.refactor.template-docs-into-namespace-dir | 1546145 | REPLAY | lane/docs/rules, v2026.0.19 |
| 29 | pool/n32.feature.pool-allocator-via-gh-actions | 6cbeb85 | CUT | pool allocator dropped: DESIGN row 2 (lane slugs, versions at land, I7) |
| 30 | pool/n33.refactor.commit-stage-pre-commit-and-async-ci | f5ed6a3 | REPLAY | lane/feature/check, v2026.0.20 |
| 31 | pool/n37.feature.build-on-tag-canonical-script | 9f04427 | FOLD | carried by row 15 |
| 32 | pool/n35.feature.pr-open-validate-and-init-cli | d3e6eda | REPLAY | lane/feature/land-pr, v2026.0.21 |
| 33 | pool/n36.refactor.claim-flow-bin-version-and-admin-trigger | 613ba41 | REPLAY | lane/feature/land-policy, v2026.0.22 |
| 34 | pool/n38.feature.bootstrap-ci-repo-config-defaults | 5229d08 | REPLAY | lane/feature/remote-protected, v2026.0.23 |
| 35 | Merge pull request #36 from joelquatro/pool/n39.feature.off-grid-mode-and-claim-amends-title | 5a874ab | REPLAY | lane/feature/land-offline, v2026.0.24 |
| 36 | pool/n40.refactor.bootstrap-ci-enables-workflows | a67764d | FOLD | carried by row 26 |
| 37 | pool/n41.feature.governance-lockdown-script | 07658fb | REPLAY | lane/feature/remote-tags, v2026.0.25 |
| 38 | pool/n42.fix.audit-retry-loop-and-branch-protection-gate | 2727843 | REPLAY | lane/fix/gate-failure, v2026.0.26 |
| 39 | pool/n43.refactor.auto-rebase-reconcile-only-no-rewrite | a4d2690 | REPLAY | lane/fix/sync-no-rewrite, v2026.0.27 |
| 40 | pool/n44.refactor.vault-major-prefix-classification | 092dcc8 | CUT | vault prefixes dropped: DESIGN row 3 |
| 41 | pool/n45.refactor.harness-in-one-dir-no-leak-to-consumers | caef4b5 | REPLAY | lane/feature/framework-marker, v2026.0.28 |
| 42 | pool/n46.feature.e2e-test-rigor-and-commitment-mandate | 2d30635 | REPLAY | lane/test/scenario-contract, v2026.0.29 |
| 43 | pool/n47.feature.doctor-deep-uses-framework-tests-as-diagnostic | 2ff0748 | FOLD | carried by row 21 |
| 44 | pool/n48.feature.safety-branches-archive-under-major-prefix | 28989b5 | CUT | safety archive dropped: DESIGN row 3 |
| 45 | pool/n49.refactor.framework-files-stay-inside-namespace | c6be08f | FOLD | carried by row 41 |
| 46 | pool/n50.refactor.consolidate-claude-skills-into-namespace | 5f72b45 | REPLAY | lane/feature/skill, v2026.0.30 |
| 47 | pool/n51.refactor.pool-and-safety-allocation-major-prefix | 7ba78f1 | CUT | allocation prefixes dropped with the allocator |
| 48 | pool/n52.refactor.rename-namespace-directory-to-dotted-form | 5320302 | FOLD | carried by row 41 |
| 49 | pool/n53.feature.claude-driven-smart-commit-tool | 07b2f55 | CUT | smart-commit dropped: agents write messages under the commit-msg rules and the skill |
| 50 | pool/n54.feature.active-requirement-on-pool-branch | 8e21f78 | REPLAY | lane/feature/requirements, v2026.0.31 |
| 51 | Merge pull request #55 from joelquatro/pool/v2026.0/n55.feature.layered-ci-tests-audits-dispatcher | 422fde8 | FOLD | carried by row 30 |
| 52 | Merge pull request #56 from joelquatro/pool/v2026.0/n56.fix.ci-dispatch-head-commit-yaml-expansion | 3ac5d04 | FOLD | carried by row 26 |
| 53 | Merge pull request #57 from joelquatro/pool/v2026.0/n57.fix.ci-dispatch-on-block-removes-fake-push-tag-event | ff9d731 | FOLD | carried by row 26 |
| 54 | pool/v2026.0/n58.fix.ci-dispatch-python-heredoc-indentation | 218d14b | FOLD | carried by row 26 |
| 55 | pool/v2026.0/n59.feature.doc-freshness-gate-on-dev-to-main-pr | 515e428 | REPLAY | lane/test/scenario-matrix, v2026.0.32 |
| 56 | Merge pull request #60 from joelquatro/pool/v2026.0/n60.refactor.ci-dispatch-drops-pull-request-trigger-to-end-duplication | 6668924 | FOLD | carried by row 26 |
| 57 | pool/v2026.0/n61.fix.commit-msg-allows-longer-merge-subjects | 0bba400 | REPLAY | lane/fix/merge-subject-length, v2026.0.33 |
| 58 | pool/v2026.0/n62.feature.off-grid-throwaway-repo-e2e-runner | 3907966 | REPLAY | lane/test/land-remote, v2026.0.34 |
| 59 | pool/v2026.0/n64.refactor.add-doc-kind-to-pool-branch-regex | 655224f | REPLAY | lane/fix/docs-kind, v2026.0.35 |
| 60 | pool/v2026.0/n65.fix.claim-flow-merge-body-recap-restore | e83c379 | REPLAY | lane/feature/merge-body, v2026.0.36 |
| 61 | pool/v2026.0/n66.refactor.move-pr-reference-to-body-header | 647dc33 | FOLD | carried by row 32 |
| 62 | pool/v2026.0/n67.refactor.pr-reference-appends-github-url | ecc1631 | FOLD | carried by row 32 |
| 63 | pool/v2026.0/n68.doc.distribute-scripts-inline-design-headers | 682898d | CUT | distribution scripts are out of the core (release gate commands) |
| 64 | pool/v2026.0/n69.feature.commit-audit-push-gate | 6498314 | REPLAY | lane/feature/check-each, v2026.0.37 |
| 65 | pool/v2026.0/n72.fix.hardlinks-derived-from-origin | a156a5e | REPLAY | lane/feature/forge-repo, v2026.0.38 |
| 66 | pool/v2026.0/n70.fix.allocator-off-grid-local-refs | f8b89ce | CUT | allocator dropped |
| 67 | pool/v2026.0/n71.fix.off-grid-e2e-uses-allocator-and-trusts-post-merge-hook | adc6cfb | CUT | allocator dropped |
| 68 | pool/v2026.0/n73.fix.safety-anchors-stay-forever-remove-gc | 0f08f96 | CUT | safety anchors dropped |
| 69 | pool/v2026.0/n77.fix.ci-dispatch-drops-lifecycle-test-mode-leak | 78bfd18 | CUT | no test-mode switch in production code; scenarios isolate through tests/lib.sh |
| 70 | pool/v2026.0/n78.fix.claim-dev-merge-source-resolution-and-tag-push-app-token | a77b6bd | CUT | claim and App token dropped |
| 71 | pool/v2026.0/n83.fix.template-bootstrap-ux-seed-dev-marker-prune | 7805124 | FOLD | carried by row 9 |
| 72 | pool/v2026.0/n82.fix.post-checkout-hook-marker-gate-and-audit-retry-classifies-transient | a17fb7f | CUT | no post-checkout hook in lean |
| 73 | Merge pull request #77 from v4rian-io/pool/v2026.0/n74.fix.off-grid-e2e-seeds-from-dev-plus-stderr-separation | a9222e3 | FOLD | carried by row 58 |
| 74 | Merge pull request #78 from v4rian-io/pool/v2026.0/n80.fix.validate-pr-open-amends-dev-to-main-title | dfef30d | CUT | release has no PR to amend |
| 75 | Merge pull request #81 from v4rian-io/pool/v2026.0/n76.reconcile.apply-repo-rules-self-contained-3 | 8d038e5 | FOLD | carried by row 37 |
| 76 | pool/v2026.0/n81.fix.init-pool-merge-and-create-pool-branch-and-hook-mode-aware | a54d92c | FOLD | carried by row 1 |
| 77 | Merge pull request #86 from v4rian-io/pool/v2026.0/n84.reconcile.canary-tests-parallel-pr-auto-heal | e449867 | REPLAY | lane/test/concurrent-clones, v2026.0.39 |
| 78 | pool/v2026.0/n85.feature.auto-rebase-comments-on-reconcile-start | e86b36a | CUT | machine reconcile dropped: DESIGN row 4 |
| 79 | pool/v2026.0/n88.fix.relands-n76-self-contained-code | c44fa2c | FOLD | carried by row 37 |
| 80 | pool/v2026.0/n86.reconcile.auto-rebase-ladder-wires-real-claude-for-semantic-resolution | 1662c05 | CUT | machine conflict resolution dropped: the author resolves in neo sync |
| 81 | pool/v2026.0/n87.feature.canaries-fire-on-push-trigger | 659b663 | FOLD | carried by row 26 |
| 82 | pool/v2026.0/n89.reconcile.scripts-print-every-failure-no-silent-stderr-suppression | 6e42bd0 | REPLAY | lane/fix/visible-failures, v2026.0.40 |
| 83 | pool/v2026.0/n92.feature.reconcile-merge-vaults-original-pool-branch-too | e7a5f9d | CUT | vault dropped |
| 84 | Merge pull request #94 from v4rian-io/pool/v2026.0/n90.feature.jira-ingress-tooling | 4bdea46 | REPLAY | lane/feature/tracker, v2026.0.41 |
| 85 | pool/v2026.0/n91.feature.claim-main-release-appends-open-pool-branches-report | 1b14f99 | FOLD | carried by row 18 |
| 86 | pool/v2026.0/n94.fix.pre-commit-is-text-file-bug-and-commit-audit-em-dash-gate | 352c41f | REPLAY | lane/fix/dash-rule, v2026.0.42 |
| 87 | pool/v2026.0/n97.fix.silence-is-success-in-sh-land | dc45663 | FOLD | carried by row 82 |
| 88 | pool/v2026.0/n93.reconcile.e2e-coverage-matrix-for-every-sprint-task | 2267839 | REPLAY | lane/test/matrix-axes, v2026.0.43 |
| 89 | Merge pull request #103 from v4rian-io/pool/v2026.0/n98.fix.auto-rebase-uses-merge-base-not-head-1 | 79f6f14 | REPLAY | lane/fix/sync-merge-base, v2026.0.44 |
| 90 | pool/v2026.0/n95.reconcile.commit-audit-runs-claude-judgment-not-just-structural-lens-2 | 86cf57f | REPLAY | lane/feature/judge, v2026.0.45 |
| 91 | pool/v2026.0/n101.fix.auto-rebase-no-force-push | c23fd17 | FOLD | carried by row 39 |
| 92 | pool/v2026.0/n100.fix.allocator-jira-optional | 39a3ea0 | FOLD | carried by row 84 |
| 93 | pool/v2026.0/n102.fix.bootstrap-ci-seeds-trigger-only-workflows | c02e53a | FOLD | carried by row 26 |
| 94 | pool/v2026.0/n103.fix.derive-allocator-app-id-from-pool-creations-ruleset | 0db733c | CUT | allocator App dropped |
| 95 | pool/v2026.0/n104.fix.bootstrap-ci-is-repo-ci-only-allocator-self-bootstraps | 6cfe0f2 | FOLD | carried by row 26 |
| 96 | pool/v2026.0/n107.fix.ruleset-bypass-adds-repository-role-admin-fallback | 7f76210 | FOLD | carried by row 37 |
| 97 | pool/v2026.0/n108.feature.claude-code-oauth-token-as-default-auth | 3a6cc5b | FOLD | carried by row 90 |
| 98 | pool/v2026.0/n115.reconcile.claude-in-ci-via-oauth-token | 52bdd3d | CUT | no Claude in CI: the judge is local and advisory |
| 99 | pool/v2026.0/n120.feature.bootstrap-installs-allocator-app | b6638d7 | CUT | allocator App dropped |
| 100 | pool/v2026.0/n122.fix.apply-rules-retry-without-integration-bypass | bd52a22 | FOLD | carried by row 37 |
| 101 | pool/v2026.0/n96.feature.abandoned-pool-branches-helper | ff29cee | REPLAY | lane/feature/attic, v2026.0.46 |
| 102 | pool/v2026.0/n123.fix.claim-no-orphan-tag-restore-dev-force-push | 0b65c67 | REPLAY | lane/fix/atomic-publish, v2026.0.47 |
| 103 | pool/v2026.0/n125.feature.full-ci-test-coverage | c2ccdd9 | FOLD | carried by row 2 |
| 104 | pool/v2026.0/n126.refactor.release-cleanup | 5826eb5 | FOLD | carried by row 20 |
| 105 | pool/v2026.0/n127.fix.archive-verifies-pool-deletion | 77a6457 | REPLAY | lane/fix/lane-delete-lease, v2026.0.48 |
| 106 | pool/v2026.0/n130.fix.consumer-hardening | 5ddac41 | FOLD | carried by row 105 |
| 107 | pool/v2026.0/n131.fix.reconcile-linkage | 0e57d44 | CUT | reconcile linkage dropped |
| 108 | pool/v2026.0/n132.fix.lifecycle-identity | 31cadcc | REPLAY | lane/feature/identity, v2026.0.49 |
| 109 | pool/v2026.0/n134.fix.production-fixes | 2cedd49 | REPLAY | lane/fix/ruleset-update, v2026.0.50 |
| 110 | pool/v2026.0/n135.fix.verify-lifecycle-key | b1770c6 | CUT | deploy keys dropped |
| 111 | pool/v2026.0/n135.fix.verify-lifecycle-key | cbba7a6 | FOLD | carried by row 34 |
| 112 | pool/v2026.0/n137.refactor.admin-session-lifecycle | 61fccd2 | CUT | admin session lifecycle dropped |
| 113 | pool/v2026.0/n137.refactor.admin-session-lifecycle | ec5477d | CUT | CI bot App dropped: landers push with their own credentials |
| 114 | pool/v2026.0/n138.fix.honest-mergeable | 9d56007 | REPLAY | lane/feature/stale-lane, v2026.0.51 |
| 115 | pool/v2026.0/n139.fix.reconcile-semantics | 0c0a84f | CUT | reconcile semantics dropped |
| 116 | pool/v2026.0/n140.fix.framework-gap-recovery | 3cd9fb4 | FOLD | carried by row 21 |
| 117 | pool/v2026.0/n141.fix.reconcile-delete-recreate | 02bdaed | CUT | reconcile dropped |
| 118 | pool/v2026.0/n142.fix.reconcile-rolling-pointer | e5b83a0 | CUT | reconcile dropped |
| 119 | pool/v2026.0/n143.fix.reconcile-pr-pointer | 4caabc8 | CUT | reconcile dropped |
| 120 | pool/v2026.0/n144.fix.verify-template-tags-as-seal | 55dd045 | FOLD | carried by row 13 |
| 121 | pool/v2026.0/n145.feature.reconcile-inherit-status | 58ea397 | CUT | reconcile dropped |
| 122 | pool/v2026.0/n150.feature.doctor-consumer-checks | 072a8db | REPLAY | lane/feature/doctor-consumer, v2026.0.52 |
| 123 | pool/v2026.0/n151.feature.local-ci-runner | feecb34 | REPLAY | lane/feature/check-gate, v2026.0.53 |
| 124 | pool/v2026.0/n152.feature.attach-existing-repo | e622d08 | REPLAY | lane/feature/adopt, v2026.0.54 |
| 125 | pool/v2026.0/n153.feature.sync-framework-migration | b984a04 | REPLAY | lane/feature/upgrade, v2026.0.55 |
| 126 | pool/v2026.0/n154.feature.doc-freshness-autofix-worker | dc88a00 | CUT | doc autofix dropped: docs change through lanes |
| 127 | pool/v2026.0/n155.fix.lifecycle-scaffold-connected-mode | edbccfd | FOLD | carried by row 2 |
| 128 | pool/v2026.0/n156.fix.finalize-prefixed-pool-resolution | 33fbc9c | CUT | prefixed pools dropped |
| 129 | pool/v2026.0/n157.feature.design-rationale-doc | d798273 | REPLAY | lane/docs/design, v2026.0.56 |
| 130 | pool/v2026.0/n158.feature.release-integrity-gates | 7938f15 | FOLD | carried by row 15 |
| 131 | pool/v2026.0/n159.feature.new-path-suite-coverage | 29822bf | FOLD | carried by row 125 |
| 132 | pool/v2026.0/n160.feature.suite-depth-and-register | 68e1893 | FOLD | carried by row 32 |
| 133 | pool/v2026.0/n161.feature.commit-receipts-gate | 7f88fa2 | REPLAY | lane/feature/receipts, v2026.0.57 |
| 134 | pool/v2026.0/n162.feature.artifact-sha-labeling | f3c78f2 | FOLD | carried by row 133 |
| 135 | pool/v2026.0/n163.feature.ci-log-archive-ref | 2ef9134 | CUT | CI log archive dropped: the merge carries its Gates receipt |
| 136 | pool/v2026.0/n164.feature.user-skill-overrides | 5028b58 | CUT | user skill overrides dropped: one skill; the lenses' rules restored by the owner into skill/lenses by lane/docs/skill-lenses |
| 137 | pool/v2026.0/n165.fix.off-grid-allocator-clone-refs-p1 | f28bef5 | REPLAY | lane/fix/slug-unique, v2026.0.58 |
| 138 | pool/v2026.0/n166.fix.off-grid-allocator-clone-refs-p2 | 69d17c5 | FOLD | carried by row 137 |
| 139 | pool/v2026.0/n167.fix.parallel-safe-framework-tests | cbab4be | REPLAY | lane/test/parallel-suites, v2026.0.59 |
| 140 | pool/v2026.0/n168.feature.ghost-tools-and-workflows | a8610d5 | CUT | ghost tools dropped |
| 141 | pool/v2026.0/n169.feature.benchmark-harness | 276532d | CUT | bench out of the core; speed and read budget restored by the owner in lane/feature/bench (no model runs) |
| 142 | pool/v2026.0/n170.fix.claim-data-safety-p1 | ad0a3d6 | REPLAY | lane/feature/offline-land, v2026.0.60 |
| 143 | pool/v2026.0/n171.fix.claim-data-safety-p2 | efed31b | REPLAY | lane/fix/link-drop, v2026.0.61 |
| 144 | pool/v2026.0/n172.fix.claim-data-safety-p3 | d13d9e6 | REPLAY | lane/fix/version-contiguous, v2026.0.62 |
| 145 | pool/v2026.0/n173.fix.contiguous-pool-ids | 75553c4 | FOLD | carried by row 144 |
| 146 | pool/v2026.0/n174.fix.hook-correctness-p1 | d079f9d | REPLAY | lane/feature/pre-push, v2026.0.63 |
| 147 | pool/v2026.0/n175.fix.hook-correctness-p2 | 3eff095 | REPLAY | lane/fix/pre-push-messages, v2026.0.64 |
| 148 | pool/v2026.0/n176.fix.hook-correctness-p3 | 1d0b237 | FOLD | carried by row 146 |
| 149 | pool/v2026.0/n177.fix.hook-correctness-p4 | 58ccb2d | FOLD | carried by row 146 |
| 150 | pool/v2026.0/n178.feature.reconstruct-tool-p1 | 284c5d1 | CUT | reconstruct out of the core |
| 151 | pool/v2026.0/n179.feature.reconstruct-tool-p2 | 6c1a45a | CUT | reconstruct out of the core |
| 152 | pool/v2026.0/n180.doc.resolve-spec-contradictions | ffe7aa8 | REPLAY | lane/docs/rules-one-way, v2026.0.65 |
| 153 | pool/v2026.0/n181.refactor.lean-skills | 7f1814d | FOLD | carried by row 46 |
| 154 | pool/v2026.0/n182.feature.lazy-loader | 1c5e792 | FOLD | carried by row 46 |
| 155 | pool/v2026.0/n183.fix.bench-loader-and-loadbytes | c49c63d | CUT | bench out of the core; loadbytes restored by the owner in lane/feature/bench |
| 156 | pool/v2026.0/n184.fix.herestring-test-greps | a5056d8 | REPLAY | lane/feature/lint-quiet-grep, v2026.0.66 |
| 157 | pool/v2026.0/n185.feature.identity-and-time-from-source | 2917b66 | REPLAY | lane/feature/model-stamp, v2026.0.67 |
| 158 | pool/v2026.0/n186.fix.linked-worktrees-and-bash32 | f43a23f | REPLAY | lane/fix/linked-worktree, v2026.0.68 |
| 159 | pool/v2026.0/n187.feature.self-documenting-tools | 10fb058 | REPLAY | lane/feature/help, v2026.0.69 |
| 160 | pool/v2026.0/n188.feature.consistency-lint | 66c563a | FOLD | carried by row 159 |
| 161 | pool/v2026.0/n189.fix.identity-gate-ignores-backups | 862ee3b | FOLD | carried by row 157 |
| 162 | pool/v2026.0/n190.feature.merge-policy-and-warp-mode | 2337781 | REPLAY | lane/feature/policy-conf, v2026.0.70 |
| 163 | pool/v2026.0/n191.feature.merge-body-in-hook | 3ed6646 | REPLAY | lane/feature/merge-body-rules, v2026.0.71 |
| 164 | pool/v2026.0/n192.fix.restore-backup-exclusion | b13fa19 | FOLD | carried by row 146 |
| 165 | pool/v2026.0/n193.fix.bench-agent-runner | 02da78a | CUT | bench out of the core |
| 166 | pool/v2026.0/n194.fix.benchmark-found-protocol-bugs | 7272e3d | FOLD | carried by row 14 |
| 167 | pool/v2026.0/n195.fix.friction-points-repo-side | a28aaea | REPLAY | lane/feature/lane-size, v2026.0.72 |
| 168 | pool/v2026.0/n196.fix.identity-and-commit-rule-leftovers | c46aa93 | FOLD | carried by row 157 |
| 169 | pool/v2026.0/n197.fix.rewrite-check-shared-patches | 4150305 | FOLD | carried by row 146 |
| 170 | pool/v2026.0/n198.fix.shared-patch-test-placement | fe70a95 | FOLD | carried by row 42 |
| 171 | pool/v2026.0/n199.feature.agent-hooks-and-installer | 4df131f | REPLAY | lane/feature/agent-guard, v2026.0.73 |
| 172 | pool/v2026.0/n200.doc.neo-git-development-history | b8d1bc1 | REPLAY | lane/docs/build-history, v2026.0.74 |
| 173 | pool/v2026.0/n201.doc.compliance-records-and-changelog | 01b591b | FOLD | carried by row 172 |
| 174 | pool/v2026.0/n202.fix.deterministic-lifecycle-suite | 8cd7588 | FOLD | carried by row 139 |
| 175 | pool/v2026.0/n203.fix.help-outside-a-repo | 2350cf5 | FOLD | carried by row 159 |
| 176 | pool/v2026.0/n204.doc.history-records-final | 4df71ea | FOLD | carried by row 172 |
| 177 | pool/v2026.0/n205.feature.personal-path-lint | 8de2dcf | REPLAY | lane/feature/lint-personal, v2026.0.75 |
| 178 | pool/v2026.0/n206.feature.agent-identity-hook | f754f07 | CUT | agent identity rewrite hook: DESIGN keeps identity map and model stamp instead; restored by the owner, folded into the guard by lane/fix/agent-identity-hook |
| 179 | pool/v2026.0/n207.fix.live-canaries | 694bae8 | FOLD | carried by row 58; the live canary restored by the owner in lane/feature/live-canaries |
| 180 | pool/v2026.0/n208.fix.allocator-lock-contention | 28d1ca4 | CUT | allocator dropped |
| 181 | pool/v2026.0/n209.feature.public-throwaways | 63cff4d | CUT | public throwaways dropped: scenarios use bare local remotes; restored by the owner in lane/feature/live-canaries |
| 182 | pool/v2026.0/n210.fix.connected-claim-live | 8ad0cec | CUT | connected claim dropped |
| 183 | pool/v2026.0/n211.fix.ci-secret-exposure | 08aecb5 | REPLAY | lane/fix/check-readonly, v2026.0.76 |
| 184 | pool/v2026.0/n212.fix.agent-guard-parser | b936a08 | FOLD | carried by row 171 |
| 185 | pool/v2026.0/n214.refactor.neo-git-rebrand | 6261d0e | FOLD | carried by row 1 |
| 186 | pool/v2026.0/n213.fix.claim-release-correctness | 074a3e2 | REPLAY | lane/fix/release-ff, v2026.0.77 |
| 187 | pool/v2026.0/n216.fix.template-onboarding | 9f40dd1 | FOLD | carried by row 20 |
| 188 | pool/v2026.0/n215.fix.personal-data-scrub | 3d11188 | FOLD | carried by row 177 (the personal-data lint covers the scrub) |
| 189 | pool/v2026.0/n217.fix.dev-protection | 0f6edb2 | REPLAY | lane/feature/forge-review, v2026.0.78 |
| 190 | pool/v2026.0/n218.fix.ai-gate-hardening | ab0d27e | REPLAY | lane/fix/judge-isolation, v2026.0.79 |
| 191 | pool/v2026.0/n219.fix.medium-hardening | 3f60f51 | FOLD | carried by row 137 |
| 192 | pool/v2026.0/n220.fix.low-claim-flow | 2717f5a | FOLD | carried by row 102 |
| 193 | pool/v2026.0/n221.fix.low-tooling | b68996f | FOLD | carried by row 139 |
| 194 | pool/v2026.0/n222.feature.tracker-agnostic | 6aa8c63 | REPLAY | lane/feature/tracker-contract, v2026.0.80 |
| 195 | pool/v2026.0/n223.fix.ci-trust-tags | 84092b6 | REPLAY | lane/fix/tags-immutable, v2026.0.81 |
| 196 | pool/v2026.0/n224.fix.guard-bypasses | 498e2ee | FOLD | carried by row 171 |
| 197 | pool/v2026.0/n225.fix.agent-confinement | 1296a28 | FOLD | carried by row 190 |
| 198 | pool/v2026.0/n226.fix.claim-policy-correctness | 6666fc6 | REPLAY | lane/fix/policy-fail-closed, v2026.0.82 |
| 199 | pool/v2026.0/n227.fix.hygiene-residuals | 8b7dc32 | FOLD | carried by row 183 |
| 200 | pool/v2026.0/n228.fix.guard-round2 | bafe375 | FOLD | carried by row 171 |
| 201 | pool/v2026.0/n229.fix.policy-claim-round2 | 27f62d6 | REPLAY | lane/fix/pre-push-merges, v2026.0.83 |
| 202 | pool/v2026.0/n230.fix.agents-docs-round2 | ec34657 | FOLD | carried by row 190 |
| 203 | pool/v2026.0/n231.fix.guard-default-deny | 999d4b7 | REPLAY | lane/docs/guard-scope, v2026.0.84 |
| 204 | pool/v2026.0/n232.fix.claim-tags-residuals | 46299fb | REPLAY | lane/fix/stray-tags, v2026.0.85 |
| 205 | pool/v2026.0/n233.fix.final-round4 | 41e8cc3 | REPLAY | lane/feature/gate-proof, v2026.0.86 |
| 206 | pool/v2026.0/n234.fix.final-round5 | 7c7e843 | FOLD | carried by row 204 |
| 207 | pool/v2026.0/n235.fix.final-lows | dbe65e1 | FOLD | carried by row 156 (the quiet-grep lint ships complete there) |
| 208 | pool/v2026.0/n236.fix.pipefail-complete | 583a5c4 | FOLD | carried by row 156 (the quiet-grep lint ships complete there) |
| 209 | pool/v2026.0/n237.fix.quiet-grep-lint | 3618b0f | FOLD | carried by row 156 (the quiet-grep lint ships complete there) |

Lean-only lanes (no neo-git origin):

| id | lean lane |
|---|---|
| L1 | lane/feature/bisect, v2026.0.87 |
| L2 | lane/feature/red-trailer, v2026.0.88 |
| L3 | lane/feature/fixes-trailer, v2026.0.89 |
| L4 | lane/fix/reland-resume, v2026.0.90 |
| L5 | lane/fix/land-integrity, v2026.0.91 |
| L6 | lane/docs/parity, this lane |
