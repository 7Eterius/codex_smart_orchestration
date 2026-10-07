# Risk-based verification: execution is not judgment

Every writer, including Main, self-checks. Independent semantic review is required by explicit
project/owner gates and meaningful behavior, integration, security, payment, schema or data-integrity
risk. A reversible established copy/style change with decisive checks does not automatically need
a reviewer. Role names alone do not mandate a full suite. Small diffs can have large consequences.
Main cannot self-certify a required independent gate.

## Separate roles and evidence

Tester/Luna Medium runs approved tests and supplies receipts. Reviewer/Luna Max independently
examines behavior and completeness. Senior Reviewer/Sol High handles deep, critical-risk or
stalled semantic review. Test strategy or causal diagnosis is not procedural Tester work.
A green suite, a confident writer and a process exit code are not semantic sign-off.

Use original requirements and controlling code for expected behavior, not assertions copied
from current output. Original results outrank summaries. Preserve raw logs, real exit codes and
failure blocks. Missing proof is UNVERIFIED; affected dependency drift is STALE. Unrelated notes
do not invalidate tests. An old green run cannot establish current deployment/browser state.
Read `testing.md` for discovery, shard completeness, run ownership, reuse and reporting.

Optional challenge.py/boundary.py check supplied records; no mandatory ledger or per-tool preflight.
CLEAR is not acceptance, authenticated evidence or release approval. Handoff is not acceptance;
known failures return for repair and addressed findings await independent resolution. Honest
BLOCKED does not require a fake pass. Main alone accepts, separately from commit/deploy authority.

## Independent first review, bounded corrections

Read the original task, complete actual bounded diff and every deliverable in an independent
context without writer reasoning/history. Find controlling behavior and concrete counterexamples.
Inspect definitions, returned values, guards, affected consumers and sibling cases. Do not invent
speculative faults to look adversarial. Critical checks should use real entry points and meaningful
negative controls where practical, without mutating live work or altering observers to fake success.

A correction may reuse the same suitable reviewer and a recorded reviewed candidate. Read every
hunk of the correction delta, affected dependencies and original findings. Include Main-authored
and concurrent changes. Missing baseline, changed contract, unknown impact or a new reviewer
requires full bounded review. Preserve only applicable prior coverage. Reuse valid test receipts;
do not rerun a suite merely because a second role now reads its result. All mandated fresh/full
gates still execute, regardless of whether an optional adversarial probe found a suspected defect.

BLOCKING means correctness, completeness or accepted-design violations. Optional taste/cleanup
is nonblocking. A worker repairs; the independent reviewer resolves findings from current proof.
Main directly inspects required visuals and consequential risks without duplicating the entire
technical investigation. Tests, rendered journeys and screenshots answer complementary questions.

## Holds and acceptance

Hold source, test/config/lock inputs, build and target stable. Isolated disjoint work may proceed
only when it cannot alter those inputs or shared resources. Whole-tree checks cannot race writers.
Temporary outputs and test accounts require ownership. Verifiers never change candidate source,
tests or assertions; their writable output scopes must not overlap candidate inputs.

Release the hold before repair, identify and re-hold the repaired candidate, then refresh affected
and mandated fresh gates. Main-authored repairs retain independent requirements. Failed review
cannot be overwritten by writer self-checks or a procedural Tester. Preserve separate test and
semantic verdicts. Unknown questions go to Main rather than guessed answers. Acceptance requires
all applicable evidence and authority, not only the cheapest or most recent passing result.

## Completion claims and integrated review

Report spec compliance and technical quality in one independent pass. Bind every completion claim
to the actual candidate, fulfilled requirements and decisive evidence; a test pass is not deployment
or live installation proof. Large features need integrated contract review, not duplicate suites.
The debugging.md circuit breaker stops repair dispatch, never accepts unresolved required findings.
Keep material new blockers visible even outside a correction diff.
