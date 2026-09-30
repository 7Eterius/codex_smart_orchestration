# Verification proportional to residual risk

Every owner self-checks. Add independent Tester for project/owner requirements or meaningful
behavior/state/integration risk, shared contracts, accessibility uncertainty, security,
payments, schema and financial invariants. Default/transferred Senior implementation needs
review by default. Established reversible copy/style changes with decisive checks do not
need another reviewer merely because they touch UI. Existing obligations cannot be waived.

## Evidence and honest completion

Agent narratives point to evidence, not authoritative state. Match claims to repository/target
readback and current test/browser evidence. Owner intent defines expected behavior. A tool
result proves only what it checked; source hashes cannot prove a served deployment or visuals.

Keep executed-pass, reused-pass, failed, blocked, unrun, deferred, authorized not-applicable,
STALE and UNVERIFIED distinct. Change in actual candidate/contract/target dependencies makes
affected evidence STALE. Missing proof is UNVERIFIED. Unrelated notes/files do not force reruns;
unknown impact widens checks. Required local failures block local acceptance. Later gates
remain pending, not falsely failed locally or silently satisfied.

Check coverage independently using original requirement IDs, never implementation output.
Preserve failures and full logs. Read exit status, failure blocks, then summary; a green count
in partial output is not PASS. Inspect retained failures before rerunning.

## Initial review and correction deltas

Initially, Tester gets the original bounded task, complete actual diff, deliverables and
must-answer questions without writer reasoning/history. Account for every deliverable:
implemented, intentionally unchanged with evidence, or missing. Read controlling definitions,
possible values, guards and helpers before semantic findings. Inspect sibling cases and
seek the smallest concrete counterexample.

For corrections, reuse the same suitable reviewer and its recorded reviewed candidate.
Read every hunk of the correction delta, affected callers/dependencies and original findings;
retain only demonstrably applicable prior coverage. Do not restart the complete investigation
merely because a new candidate exists. Missing review baseline, changed contract, unknown
impact or a new reviewer requires the full bounded review. Explicit full-review requirements
and mandated fresh gates always override this optimization. Record the baseline and delta
in the existing verdict, not another ledger.

Execute required independent gates even when no defect is suspected. Optional probes address concrete
concerns. New critical tests exercise real entry points and meaningful negative controls
where practical: known-bad input or a disposable mutation failing the intended assertion,
not syntax/setup failure. Never mutate live work or alter observers to fabricate success.

BLOCKING means wrong, incomplete or untrue, including an unmet accepted UI/design criterion. Optional
taste/cleanup is NON-BLOCKING. No grounded defect is not proof of correctness. Tester never
repairs candidate code/tests. Main examines decisive risks and actual visuals without repeating
the whole technical review. Technical approval is not visual acceptance or owner sign-off.

## Candidate holds and repaired findings

Identify staged/unstaged/untracked source, tests/config/lockfiles, contract, build/target/account
and environment. Freeze relevant writer changes and target replacement during review. Tester
writes only evidence/disposable data. Release before same-writer repair, identify the new
candidate, re-hold and rerun affected plus required fresh checks. Preserve failures and
unrelated applicable evidence.

Workers mark repairs addressed with fresh evidence; Main/reviewer resolves after recheck.
A handoff is not acceptance. Never require independent approval before dispatching its reviewer.
All required gates and blocking findings must be settled at acceptance. Named unknown questions require Main's decision, not a fabricated answer.

Use `challenge.md` only with existing structured facts. Its optional manifest check and
`candidate.py` establish identity only for listed inputs, not test coverage, provenance or authority.
`boundary.py` checks supplied transitions. Both gate helpers share `runtime/evidence.py`:
STALE/UNVERIFIED are valid unsatisfied states, not protocol errors. None authenticates evidence,
locks the workspace or requires a per-edit ledger.

## Complementary checks

Use focused editing checks and required integration/release gates. Preserve mandated device,
theme, locale and manual accessibility coverage without replaying full matrices after each tweak.
Tests prove hidden behavior, browser journeys interaction, screenshots appearance. Main directly
inspects required design evidence. Return candidate/reviewer, deliverable/question dispositions,
gate evidence, findings and authority/lifecycle obligations. No commit, deployment, owner sign-off
or savings follows from a test pass. Standalone validation has no implementer or manager.
