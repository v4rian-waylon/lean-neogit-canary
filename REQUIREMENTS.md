# REQ Requirements

> Single-doc requirements register (project-reqs skill).
> Lifecycle: intent → in-progress → done   (off-ramps: blocked, scrapped)
> Protection: every Hard Requirement is protected until explicitly scrapped.
> JIRA: a ticket is a Unit of Intent until its sprint is active, then it promotes.
> Generated from requirements/<slug>.md by neo (.neo/lib/reqs.sh); never edit it by hand:
> pre-commit regenerates it, and neo land refuses a register that differs from its tree.

## Hard Requirements
<!-- Committed + protected. A regression against any row here is a release-blocker. -->

| ID | Requirement | Pri | Status | Tests | Source | Trace |
|----|-------------|-----|--------|-------|--------|-------|
| REQ-R-forge-261112103904 | The canary keeps the rulesets and the neo-check workflow of run 261112103904 on the forge. | P2 | ✅ done | ⚠️ needs units | internal | `chore/forge-261112103904` |
| REQ-R-forge-261112104037 | The canary keeps the rulesets and the neo-check workflow of run 261112104037 on the forge. | P2 | ✅ done | ⚠️ needs units | internal | `chore/forge-261112104037` |
| REQ-R-forge-261112104430 | The canary keeps the rulesets and the neo-check workflow of run 261112104430 on the forge. | P2 | ✅ done | ⚠️ needs units | internal | `chore/forge-261112104430` |
| REQ-R-forge-261112112049 | The canary keeps the rulesets and the neo-check workflow of run 261112112049 on the forge. | P2 | ✅ done | ⚠️ needs units | internal | `chore/forge-261112112049` |
| REQ-R-forge-261112112547 | The canary keeps the rulesets and the neo-check workflow of run 261112112547 on the forge. | P2 | ✅ done | ⚠️ needs units | internal | `chore/forge-261112112547` |
| REQ-R-forge-261112154555 | The canary keeps the rulesets and the neo-check workflow of run 261112154555 on the forge. | P2 | ✅ done | ⚠️ needs units | internal | `chore/forge-261112154555` |
| REQ-R-gadget-261112112547 | A gadget lane of run 261112112547 lands through its pull request. | P1 | ✅ done | ⚠️ needs units | internal | `feature/gadget-261112112547` |
| REQ-R-review-261112104037 | Lands of run 261112104037 go through review on the forge. | P2 | ✅ done | ⚠️ needs units | internal | `chore/review-261112104037` |
| REQ-R-review-261112104430 | Lands of run 261112104430 go through review on the forge. | P2 | ✅ done | ⚠️ needs units | internal | `chore/review-261112104430` |
| REQ-R-review-261112112049 | Lands of run 261112112049 go through review on the forge. | P2 | ✅ done | ⚠️ needs units | internal | `chore/review-261112112049` |
| REQ-R-review-261112112547 | Lands of run 261112112547 go through review on the forge. | P2 | ✅ done | ⚠️ needs units | internal | `chore/review-261112112547` |
| REQ-R-unreview-261112104430 | Run 261112104430 puts lands back to optional review. | P2 | ✅ done | ⚠️ needs units | internal | `chore/unreview-261112104430` |
| REQ-R-unreview-261112112049 | Run 261112112049 puts lands back to optional review. | P2 | ✅ done | ⚠️ needs units | internal | `chore/unreview-261112112049` |
| REQ-R-unreview-261112112547 | Run 261112112547 puts lands back to optional review. | P2 | ✅ done | ⚠️ needs units | internal | `chore/unreview-261112112547` |
| REQ-R-unreview0-261112104430 | Run 261112104430 puts lands back to optional review left by an earlier run. | P2 | ✅ done | ⚠️ needs units | internal | `chore/unreview0-261112104430` |
| REQ-R-upgrade-261112104430 | The canary takes the framework under test for run 261112104430. | P2 | ✅ done | ⚠️ needs units | internal | `chore/upgrade-261112104430` |
| REQ-R-upgrade-261112112049 | The canary takes the framework under test for run 261112112049. | P2 | ✅ done | ⚠️ needs units | internal | `chore/upgrade-261112112049` |
| REQ-R-upgrade-261112112547 | The canary takes the framework under test for run 261112112547. | P2 | ✅ done | ⚠️ needs units | internal | `chore/upgrade-261112112547` |
| REQ-R-upgrade-261112154555 | The canary takes the framework under test for run 261112154555. | P2 | ✅ done | ⚠️ needs units | internal | `chore/upgrade-261112154555` |
| REQ-R-upgrade-policy-261112154555 | Run 261112154555 lets a framework upgrade land as one commit on the canary. | P2 | ✅ done | ⚠️ needs units | internal | `chore/upgrade-policy-261112154555` |
| REQ-R-widget-261112104037 | A widget lane of run 261112104037 runs the forge jobs green. | P1 | ✅ done | ⚠️ needs units | internal | `feature/widget-261112104037` |
| REQ-R-widget-261112104430 | A widget lane of run 261112104430 runs the forge jobs green. | P1 | ✅ done | ⚠️ needs units | internal | `feature/widget-261112104430` |
| REQ-R-widget-261112112049 | A widget lane of run 261112112049 runs the forge jobs green. | P1 | ✅ done | ⚠️ needs units | internal | `feature/widget-261112112049` |
| REQ-R-widget-261112112547 | A widget lane of run 261112112547 runs the forge jobs green. | P1 | ✅ done | ⚠️ needs units | internal | `feature/widget-261112112547` |

## Units of Intent
<!-- NOT binding, NOT protected. Promotes to a Hard Requirement through a lane whose file says Promotes: <slug>. -->

| ID | Intent | Pri | Source | Sprint | Notes |
|----|--------|-----|--------|--------|-------|

## Scrapped
<!-- Graveyard. Kept for traceability. Never deleted. -->

| ID | Requirement | Scrapped | Why |
|----|-------------|----------|-----|
