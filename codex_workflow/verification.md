# Change-aware verification

Read for validation-bearing work. Main or lead supplies the relevant gates, not another
planning hierarchy. Coverage, independence and owner/repository obligations stay binding.

## One requirement map, appropriate boundaries

Reuse authoritative requirement IDs and their contract revision. Map each obligation to
acceptance level, expected behavior, evidence method, owner and disposition in the existing
checklist. Add missing obligations after an independent completeness check; do not invent
a parallel matrix for every reviewer. Source describes implementation, not the test oracle.
Do not repair a test by copying the implementation's defect into its expected result.

During edits run narrow decisive checks. At stable candidates independently verify affected
behavior where required. At authorized integration/release boundaries run their gates.
No full device/theme/locale matrix after every edit, but never omit an explicitly required
matrix or fresh independent execution. Validation-only gates need no implementation setup.

| Change | Decisive evidence |
| --- | --- |
| Internal documentation | Correct references and executable examples |
| Domain/backend | Unit/contracts; affected consumers of data/errors/state |
| Copy/localization | Keys/placeholders/plurals and wrapping/accessibility names |
| Layout/theme/components | Running screens, consumers, contrast/zoom/motion |
| Forms/focus/navigation | Keyboard/focus/back, labels/roles, screen-reader states |
| Auth/entitlements/schema/financial | Invariants, denied paths, persistence, regressions |

Preserve targeted accessibility and mandated manual checks. No disabled rules or excluded
violations for economy. Give browser smoke, contract tests and visual critique complementary
jobs, not three repetitions of every assertion. Operator evidence is not an independent
Tester verdict when that verdict is required. Main retains design/owner acceptance.

## Candidate hold and identity

Identify workspace, staged/unstaged/untracked inputs, harness/config/dependencies, build,
target, account/data and environment. HEAD or a URL alone is insufficient. Hold relevant
writer changes and target replacement during independent testing. During the hold write
only evidence/disposable test data, not source or candidate tests. Hold is an ownership
agreement, not a filesystem lock; outside edits remain possible.

On relevant drift or uncertain continuity, invalidate affected evidence, release before
repair, identify the new candidate, and revalidate affected plus required fresh checks.
Keep original failures. Different owners can work only in genuinely isolated scope.

Optional `runtime/candidate.py` snapshots selected files/directories, including untracked
additions inside them. Include relevant shared contracts, lockfiles and config. It proves
identity only for listed inputs, not test coverage, served-build provenance, external state,
or absence of intervening changes. A hash is not a dependency graph or authority.

Use `verify-many --manifest A --manifest B` for several existing evidence scopes in one
bounded call. Each result stays distinct; error dominates drift in the exit code. It
performs new reads, never a command-result cache or one atomic snapshot across candidates.
Do not create manifests solely to use batching or interpret a match as permission to skip
a gate. Keep existing trustworthy provenance rather than regenerating inventories.

## Reuse, repair and reporting

Reuse only when requirement revision, coverage, relevant inputs, dependencies, toolchain,
config, data/environment and viewport/theme/locale apply. New failures, shared changes or
unknown impact widen checks. Reopen affected dependent gates, not every successful test.
Mandatory fresh execution remains fresh. Unknown applicability requires checking; missing
logs never become PASS. Do not claim
independence from the writer's reasoning or verdict; independently check requirements.

Keep executed-pass, reused-pass, failed, blocked, unrun, deferred and not-applicable distinct.
A required gate cannot be waived by relabeling it not-applicable. Record its authorized
scope basis. A later OPEN release gate need not block legitimate local acceptance, but a
required local failure does. Test success, local acceptance, commit and integration differ.

Use `browser.md` for multi-step operation. Preserve a required rendered journey even when
API checks are cheaper. Reuse identified servers/builds; clean only for stale artifacts or
explicit gates. Preserve underlying exit status, timeout/cancellation and incomplete output.
Save private raw logs, inspect failures, and never rerun just to recover discarded output.

Main reviews decisive diffs in Normal; coordinated lead reviews substance and main checks
identity, full gate coverage and exceptions. A packet indexes evidence, not proof itself.
Persist acceptance basis before authorized consequential mutations and observed outcomes
afterward. On resume reconcile missing receipts with actual state, not repeated mutations.
