# Systematic debugging, not speculative repair

Use for a bug, failing test, build/integration failure, unexpected state or performance regression.
The same implementation owner can investigate; an extra Investigator is optional, not a mandatory
handoff. Scale the depth, not the obligation to inspect the actual failure.

## Observe, compare, discriminate, repair

1. Preserve the original error, complete relevant trace, failing command, candidate, environment
   and expected/observed behavior. Reproduce with the smallest real entry point. For intermittent
   failures record frequency and relevant conditions; do not call a passing rerun a root cause.
2. Locate the last known working case and recent relevant changes. Trace bad data/state backward
   through producers, consumers and component boundaries. Inspect actual references/contracts,
   configuration propagation and dependencies instead of reading the entire repository.
3. State one falsifiable hypothesis and the observation that would distinguish it from alternatives.
   Run the smallest safe probe; change one causal variable at a time. Keep diagnostic artifacts
   separate from fixes. Redact secrets and personal data; log presence/type or a safe digest rather
   than dumping environment variables, tokens, cookies or customer records.
4. Add the decisive regression test when practical, observe the intended failure, make the focused
   causal fix, rerun that test and affected checks, then refresh required integrated evidence.
   `testing.md` defines honest RED/GREEN and alternatives. Do not bundle unrelated refactoring.

An obvious parser error may satisfy these steps in a few lines. An unknown cross-system problem
may need bounded investigation. Unreproducible or external behavior requires instrumentation or
an explicitly labeled mitigation, not invented certainty. Authorized incident containment can
precede full diagnosis, but must be called a mitigation with its risks and follow-up unresolved.

For performance work, establish a comparable baseline and metric before optimizing. Keep workload,
config, cache state and environment comparable; separate model latency, tools, builds and tests.
Measure the changed path and functional regressions. Do not declare faster from fewer lines,
fewer agents or lower token prices. Avoid arbitrary sleeps; prefer bounded condition-based waits
or existing process completion notifications with a real timeout and preserved failure evidence.

## Fix-loop circuit breaker

Before another patch, ask what NEW evidence makes it worth trying. Keep the task/defect identity
and cumulative counts in the current note or long-task checkpoint, including attempts by Main.
One evidence-based same-defect correction without progress triggers an appropriate Sol/Main
handoff with original evidence and attempted approaches. `allocation.classify(previous_owner=...)`
can recommend a higher lane without repeating a known stalled preset.

Stop automatic patch dispatch after three failed causal fixes for one defect OR three complete
repair/re-review waves for the task. This is a review trigger, not proof that the architecture is
wrong, and not a target to exhaust. Model switches, new threads and renamed subtasks do not reset
it. Main inspects assumptions, coupling, plan validity and scope. Resume only with a recorded new
approach and bounded attempt budget under existing authority; protected changes need approval.

Classify blockers versus optional taste early. Verify review feedback against source and
requirements before changing code; reject a false positive with evidence, not deference or
confidence. Batch related justified fixes, then inspect the complete correction delta and affected
dependencies. A newly discovered real blocker stays visible even outside the original review diff.
At the cap or budget exhaustion, checkpoint BLOCKED/UNVERIFIED. Never relabel required failures as
optional, accept a dependent task on broken prerequisites, or mark a blocked task done to escape.

## Bounded resume after replanning

With delivery.py, Main records optional `replan`: task, defect, decision_ref, current cumulative
failed_fixes and repair_rounds, and attempt_limit (1-3). Identity must match. Lifetime counters
never decrease; the new window consumes their deltas and reports remaining_attempts. New evidence,
quota, authority and implementation ownership still bind. Only the exact new baseline acknowledges
a prior stall; later failures can stop again. Changing workers alone is not a replan.
