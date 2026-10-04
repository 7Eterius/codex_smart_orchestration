# Risk-based verification with intelligent review

Every writer, including Main, self-checks. Independent review is required by project/owner
gates and meaningful behavior, integration, security, payment, schema or data-integrity risk.
A reversible established copy/style change with decisive checks does not automatically acquire
a reviewer. Default now means normal Sol implementation, not a reason by itself for a full suite.
Do not mistake a small diff for low risk. Main cannot self-certify a required independent gate.

## Evidence and acceptance

Use original requirements and controlling code for expected behavior, never assertions copied
from current output. Actual state and executed tests outrank summaries. Preserve complete logs,
exit codes and failure blocks. Missing proof is UNVERIFIED; affected dependency drift is STALE.
Unrelated notes do not invalidate tests. Mandatory fresh checks remain fresh; an old green run
cannot establish a current deployment, browser state or repaired finding.

Optional challenge.py/boundary.py use existing records only; no mandatory ledger or per-tool
preflight. CLEAR is not acceptance or authentic evidence. Handoff is distinct from acceptance:
later checks stay pending, current known failures return for repair, addressed findings await
independent resolution. Honest BLOCKED does not require a fake pass. Main alone accepts the
result, separately from owner approval, commit or deployment authority.

## One thorough first review, bounded corrections

Tester is GPT-6.1 Sol Medium: use intelligence to identify controlling behavior and a small
reproduction, not a large checklist of speculative concerns. Initially read the original task,
complete actual bounded diff and each requested deliverable. Review without writer history.
Read definitions, returned values, guards and affected consumers before asserting defects.
Inspect sibling cases. Ground a counterexample; do not invent faults to look adversarial.

For corrections use the same suitable reviewer and a recorded reviewed candidate. Read every
hunk of the correction delta, affected dependencies and original findings. Preserve only
applicable prior coverage. Include Main fixes and concurrent mutations. Missing baseline,
changed contract, unknown impact or a new reviewer requires full bounded review. Record this
in the existing verdict, not a second database. Execute required independent gates even when
no defect is suspected. Mandatory fresh/full checks override delta optimization.

New critical checks should exercise real entry points and meaningful negative controls where
practical. A disposable known-bad input must fail the intended assertion, not only setup or
syntax. Never mutate live work to plant defects or alter observers to fabricate success.
BLOCKING includes correctness, completeness and violations of the accepted design. Optional
taste or cleanup is nonblocking. A worker repairs; reviewer/Main resolves from fresh evidence.

## Holds, parallel tests and integration

Hold the reviewed source, test/config/lock inputs and build/target stable. Disjoint isolated
work can proceed only when it cannot alter those inputs or shared resources. Whole-tree checks
and mutable live-preview review must not run against active conflicting writers. An immutable
preview can overlap later implementation. Temporary test outputs and accounts need ownership.

Release the hold before repair, identify the repaired candidate, re-hold and refresh affected
plus mandated fresh gates. Tester never changes candidate code/tests. Main-authored repairs
retain independent requirements. Failed independent review cannot be overwritten by writer
self-checks. Unknown named questions go to Main, not guessed answers.

Main directly inspects required design evidence and consequential risks without duplicating
the complete technical investigation. Established tweaks can use one final visual check;
new compositions need an early frame where it reduces rework. Tests, rendered journeys and
screenshots answer different questions; preserve required complementary evidence.

Reuse the narrowest decisive local checks while editing. Run the complete product gate at
integration/release when required, not after every typo. Helpers establish consistency or
identity only for listed inputs, not test coverage, runtime provenance, authority or savings.
