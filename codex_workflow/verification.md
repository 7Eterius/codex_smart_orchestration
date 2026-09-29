# Verification proportional to residual risk

Every owner self-checks. Add independent Tester when project/owner rules require it or
meaningful risk remains: behavior/state/integration, shared contracts, uncertain
accessibility, security, payments, schema or financial invariants. Default and transferred
Senior implementation require review by default. Reversible established copy/style edits
with decisive checks do not gain a reviewer merely because they touch UI.

## Evidence order and states

For implementation claims prefer actual repository/target state, deterministic readback,
executed test/browser evidence tied to the current candidate, independent Tester findings,
then worker narrative. Requirements/owner intent decide what should be built. A tool result
proves only what it checked.

Use executed-pass, reused-pass, failed, blocked, unrun, deferred, authorized not-applicable,
STALE and UNVERIFIED. Candidate/contract/target drift makes affected earlier evidence STALE.
Missing evidence is UNVERIFIED. Required fresh checks accept executed-pass only; reused-pass
needs explicit applicability and only satisfies non-fresh gates. Required local failures block
local acceptance. Missing/blocked/unrun/deferred/not-applicable never silently become PASS.

Check coverage independently against canonical requirement IDs and expected behavior; do not
derive assertions from implementation output. Preserve original failures. Changing tests to
agree with a bug is not repair. Standalone validation has no implementer or manager.

When structured handoff facts already exist, `runtime/challenge.py` may cheaply expose one
grounded contradiction before review. CLEAR means no supported contradiction in supplied
facts, not correctness, coverage or acceptance. Do not create a mandatory ledger just to run it.

## Independent review by falsification

Tester starts from the original bounded task and stable candidate, not the writer's summary.
Read the complete actual diff and account for every requested deliverable: implemented,
intentionally unchanged with evidence, or missing. Before making a semantic/blocking finding,
read the controlling code: relevant definitions, possible return/value set, guards/branches
and parser/classifier/helper behind the claim. Inspect sibling cases where one branch/case
changed for stale assumptions or contradictions.

Assume the patch may be wrong and seek the smallest concrete counterexample. Run focused
checks only where they can falsify a concrete concern. BLOCKING means wrong, incomplete or
claiming something untrue; stylistic preference or optional cleanup is NON-BLOCKING.
A finding needs exact code/tool evidence. A review with no grounded defect says so; tool-call
volume is not a quality metric. Tester never edits candidate source/tests.

Main retains consequential product/architecture/visual/final judgment. Tester approval is
not main's visual acceptance or owner sign-off. A writer cannot self-certify an independent
gate.

## Candidate hold and repair

Identify staged/unstaged/untracked source, relevant test/config/lockfiles, contract revision,
actual build/target/account and environment. Freeze relevant writer changes and target
replacement during independent review. Tester writes only evidence/disposable data.
Release before repair, identify the new candidate, re-hold and rerun affected plus required
fresh checks. Preserve original failures and unrelated applicable evidence.

The optional `runtime/candidate.py` fingerprints explicit selected inputs; `verify-many`
batches manifests. These prove identity only for listed inputs, not test coverage, runtime
provenance, external data, absence of intervening changes or authority. `boundary.py` checks
supplied review transitions. Neither helper authenticates observations.

## Useful non-duplicative evidence

| Change | Focus |
| --- | --- |
| Docs/copy | References, examples, keys/placeholders, wrapping |
| Domain/backend | Invariants, consumers, contracts, denied/error paths |
| UI behavior | Real interaction, keyboard/focus/labels, accessibility |
| Layout/theme | Running screens, viewports, contrast/zoom/motion |
| Auth/billing/schema/financial | Security, persistence, migration, regression |

Use the narrowest decisive checks while editing; complete integration/release gates at that
level. Do not repeat full matrices after every repair. Tests prove hidden behavior, browser
journeys interaction and screenshots appearance; do not substitute one for a required
complementary channel. Main directly inspects required design evidence.

Return exact candidate/reviewer identity, deliverable disposition, gate states, failures/
resolutions, evidence and remaining authority/lifecycle obligations. Main checks applicability
and decisive risk without routinely repeating the full investigation. No implied commit,
integration, release, owner sign-off or savings follows from a pass.
