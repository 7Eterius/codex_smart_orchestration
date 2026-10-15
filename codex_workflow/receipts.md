# Verification receipts without repetitive model bookkeeping

Prefer existing project commands, machine reports and native CI artifacts. The optional
runtime/verification_run.py is for a substantial approved batch when a reliable wrapper is missing,
not every quick check. It is an execution tool, not a new agent, scheduler, permission or sandbox.
Main/Reviewer still selects coverage; Tester executes selected procedures and reports exceptions.

## Preview, execute, inspect

The source example shows a schema-1 plan: task, requirement_ref, absolute root, explicit input
paths, environment_ref, and commands with unique id, argv, timeout_seconds and optional expected_exit.
Use the project's real commands and required timeouts. Inputs include relevant source/tests/config/
lockfiles and dirty/untracked deliverables. The environment reference is a description, not proof.
Do not place secrets in argv. Choose an existing evidence-parent outside watched inputs.

Run verification_run.py --plan PLAN --evidence-parent DIR for a read-only preview. Add --apply only
under existing authority to run those exact commands. Commands execute sequentially with shell=False
and the caller's inherited permissions. An explicitly specified shell interpreter still has shell
semantics; split critical checks into individual argv entries so the final echo cannot hide failure.
All planned checks stay visible; after an unexpected result, remaining commands are marked not_run.

Each run creates a private uniquely named directory containing the exact plan, before/after listed-
input fingerprints, individually named bounded raw logs and a receipt. The original process exit
and expected outcome are recorded. Nonzero expected RED is labelled as expected process behavior,
not a passing production suite. Timeouts, interrupts, truncated output and changed/missing inputs
prevent a clean receipt. A final echo does not turn a captured nonzero subprocess result into zero.
Explicit exit_status markers that contradict a zero wrapper exit force inspection; output text is
untrusted evidence, not an authenticated nested-result parser or universal runner adapter.

The cooperative lock prevents identical plans from racing only among runs using this same tool and
same evidence parent. It is not a global process registry. Reuse a still-running native process
handle instead of starting this helper as a second supervisor. Supported long waits and completion
notifications remain preferred. No busy model polling, auto-retry, daemon or “retry until green”.

## Preserve meaning and evidence

Expected process exit is not adequate discovery, coverage, browser correctness, deployment success
or semantic acceptance. Inspect the runner's real machine report, failed/skipped counts and required
postconditions. Main sees a compact receipt and decisive failure excerpts, not every passing line.
Required fresh/full integrated gates still run; applicable evidence can otherwise be reused.

Preserve every failed and intermediate attempt under distinct immutable names. Link the corrected
receipt to its predecessor; do not overwrite a failed trace or receipt with the final green result.
Source holds remain necessary: equal before/after hashes cannot detect a transient edit reverted
during execution, omitted inputs or external state. An absent original artifact is unavailable,
not rehashed or reconstructed from a summary. Retention cleanup needs explicit authority.

There is no installed stop-hook that forces endless continuation or reruns a full suite after each
edit. New hooks require verified current-client support, existing trust/approval and failure tests
for the actual tool paths. Hooks do not replace native sandbox, capacity or protected CI controls.

4.2.1 takes the pre-run fingerprint after cooperative admission, avoiding a redundant scan and
rejecting an already-running identical batch before hashing. The post-run read is always fresh.
Use optional --expected-candidate with the preview fingerprint when that exact candidate is the
approval target. Each completed command gets a create-only .result.json before the next starts,
so later interruption/errors do not erase earlier exits. CLI SIGTERM/SIGHUP cancels the owned group;
SIGKILL cannot be handled. No-retry, required gates and external-state limitations are unchanged.
