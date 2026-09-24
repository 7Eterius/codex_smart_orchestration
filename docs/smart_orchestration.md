# Smart Orchestration engineering notes

## Single adaptive loop

2.3 preserves the single-owner architecture introduced in 2.2. Main retains consequential
judgment and final acceptance. Routine/Default own implementation, self-checks and repairs.
Tester covers actual-diff/contract review and required behavior verification. There is
no dedicated lead reviewing the same ordinary change again.

Answers/trivial already-known operations can stay direct. Multi-step mechanical work
goes to Simple, settled implementation to Routine, deep work to Default. These are
responsibilities, not modes. No classifier guarantees a globally cheapest correct choice.
Main re-entry is for decisions, authority, genuine blockers or acceptance. Corrections
carry failed requirements, evidence, allowed deltas and fresh gates, not full rediscovery.

## Capability and lifecycle

Routine/Default may dispatch one Tester under explicit authority with applicable observed
nested mechanics and an available slot. Otherwise Main dispatches the same named reviewer.
The intended unit uses two Smart-owned open threads, with serialization for additional
mandatory reviewers. The configured cap remains a ceiling including other work.

Completion, correction retention, closing, observed closure and resource handoff are
separate. Only observed native release frees a slot. Parents close eligible direct
children before themselves. No blind retries, unrelated closures or cap increases.

`runtime/allocation.py` checks supplied observations; it does not authenticate them or
call native tools. 2.3 applies writer exclusion to reuse as well as spawn, separates
readback/cleanup from work, and validates primary/caller identity, same-unit review and
explicit authority. Cleanup can release eligible children of completed/retired owners
without granting new dispatch. See [input contracts](../codex_workflow/boundary.md).

## Evidence boundaries

The optional `runtime/boundary.py` checks an existing capsule at review, repair and
acceptance boundaries. A separate Tester verdict must match unit, attempt, contract,
candidate, target and reviewer, with the exact authoritative gate map. Required fresh
checks cannot be satisfied by reused results. Holds prevent a permitted write transition
in the supplied record, not at the filesystem or native tool layer.

`runtime/candidate.py` fingerprints explicit source inputs, not behavioral coverage or
runtime provenance. Batch errors preserve later results; directory aliases and hard links
cannot inflate matched-manifest counts. Equal bytes in different files are still not
proof of independent review. There is no automatic hash cache or new telemetry store.

## Installation and verification

The installer fingerprints the new guide/helper along with the existing package. It
continues to protect owner edits, unrelated configuration and projects. Migration tests
run real historical installers and verify idempotence and exact rollback, including
v2.2 -> v2.3. CI requires full Git history rather than skipping unavailable migrations.

See [2.3 release notes](v2.3.md), [2.2 rationale](v2.2.md),
[targeted runtime checks](../codex_workflow/runtime_check.md) and
[optional evaluation](evaluation.md). Source tests do not qualify native thread turnover
or establish allowance savings. The earlier three-thread trial remains evidence for
its first loop, not proof of repeatable reclamation or of the exact failure cause.
