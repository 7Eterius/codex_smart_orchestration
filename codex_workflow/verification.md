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
remain pending at their own level, not falsely failed locally or silently satisfied.

Check coverage independently using original requirement IDs and expected behavior. Do not
derive assertions from implementation output. Preserve failures and full logs. Read the exit
code first, failure blocks next, summary last; a green count in partial output is not PASS.
Inspect retained failures before rerunning. Standalone validation has no implementer or manager.

## Falsification without omitted gates

Tester gets the original bounded task, complete actual diff, deliverables and must-answer
questions in a context independent of the writer's investigation. Account for every deliverable:
implemented, intentionally unchanged with evidence, or missing. Before a semantic/blocking
finding, read controlling definitions, possible values, guards and supporting helpers. Inspect
sibling branches for stale assumptions and seek the smallest concrete counterexample.

Execute required independent gates even when no defect is suspected. Additional optional probes
must answer concrete concerns. For new critical tests, exercise the real entry point and a
meaningful negative control where practical: known-bad input or a disposable mutation that
fails for the intended assertion, not syntax/setup failure. Never seed a defect in live work.
An observer must report actual failure, not be changed to fabricate success.

BLOCKING means wrong, incomplete or untrue, including an unmet accepted UI/design criterion.
Optional taste, cleanup and out-of-scope polish are NON-BLOCKING. No grounded defect means
say so, not proof of correctness. Tester never repairs candidate code/tests or rewrites the
writer's requirements. Main inspects decisive risks and actual visuals without duplicating
complete source investigation. Technical approval is not visual acceptance or owner sign-off.

## Candidate holds and repaired findings

Identify staged/unstaged/untracked source, relevant tests/config/lockfiles, contract revision,
actual build/target/account and environment. Freeze relevant writer changes and target
replacement during independent review. Tester writes only evidence or disposable data.
Release before same-writer repairs, identify the new candidate, re-hold and rerun affected
plus required fresh checks. Preserve original failures and unrelated applicable evidence.

Workers mark a repair addressed with fresh evidence; Main/reviewer resolves it after recheck.
A handoff is not acceptance. Never require an independent approval before dispatching its
reviewer. At acceptance, all required gates and blocking findings must actually be settled.
Named unknown questions require Main's decision, not a fabricated answer.

Use `challenge.md` only with existing structured facts. Its handoff/accept preflight and optional
fresh manifest check do not authenticate observations or grant approval. `candidate.py` proves
identity only for listed inputs, not test coverage, external state or runtime provenance.
`boundary.py` checks supplied transition records. None is a lock or a mandatory per-edit ledger.

## Complementary checks

Use focused checks during editing and required product gates at integration/release. Preserve
mandated device/theme/locale and manual accessibility coverage without replaying full matrices
after every tweak. Tests prove hidden behavior, browser journeys interaction, screenshots
appearance. Main directly inspects required design evidence. Return candidate/reviewer identity,
deliverable and question dispositions, exact gate evidence, findings and authority/lifecycle
obligations. No commit, deployment, owner sign-off or savings follows from a test pass.
