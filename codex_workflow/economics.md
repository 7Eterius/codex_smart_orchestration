# Quota-aware delivery without invented accounting

Keep the 3.1.1 named model/effort map. Main stays owner-selected; Sol Medium is a recommendation,
not a setting silently imposed by installation. Luna Max handles ordinary coherent implementation,
investigation and ordinary semantic review. Sol Low/Medium/High handle moderate/deep/serious work.
Tester/Luna Medium executes approved commands. Never switch to an unavailable or cheaper model
silently, raise effort by ritual, or buy credits/enable Fast to finish without authorization.

## Spend on accepted outcomes

Measure total accepted work including context, tool turns, repairs, tests and review. Delegate
coherent outcomes instead of pre-solving in Main, duplicating investigations or spawning a worker
per click. Reuse suitable same-task correction context; fresh unrelated work gets a bounded brief.
Large logs/review packets belong in authorized artifacts with concise pointers and decisive
excerpts, not repeated transcript dumps. Independently review original requirements and actual
diff, not the writer's persuasive narrative. Keep true reviewer independence.

Use supported completion notifications or long interruptible waits. A returned wait is not a reason
for a new model turn, repeated progress SEND, duplicate test, or whole-tree scan. After actual
context loss or a real stalled process, reconcile once. Do not confuse closing an agent with
terminating its tools: preserve results, settle writes and observe native resource/thread release.

At a substantial phase boundary, use available native usage/status evidence or an explicit owner
budget. Record only what is exposed; never derive Codex allowance from API token prices or raw
session totals. A meter may be account-wide and include other tasks. Keep input/cached/output/
reasoning totals distinct and avoid double-counting nested cumulative counters. No automatic
usage-log crawl, daemon, telemetry or per-command accounting. Missing quota is UNKNOWN, not free.

For an explicit budget, use one declared unit and a current observation. Account for spent work,
committed/in-flight work and the ENTIRE next batch including verification. Estimates are uncertain,
not enforced caps. Without the information to demonstrate fit, narrow/replan or ask for the
necessary decision rather than certify the budget. Preserve enough room for required validation;
if it cannot fit, checkpoint instead of lowering acceptance standards.

Low observed quota favors one useful worker, no speculative branches and no optional polish.
Unknown usage favors a conservative start, without blocking ordinary work for an expensive audit.
Exhaustion or an explicit spent budget stops new discretionary work; retain evidence/remaining
gates and use only already-authorized safe checkpoint/cleanup. It does not permit fake PASS.
Concurrent machines and work are outside these helpers' enforcement capability.

## Two budgets, not five machines

Five is the Smart open-worker ceiling, excluding Main, not a target. Actual lower owner/client
caps, unrelated threads and semantic-review reservations still bind. Main may work on a disjoint
critical path. CPU/RAM/test processes have their own budget: prefer one Tester coordinating a
runner's supported parallelism over five competing full suites. Whole-tree tests hold all relevant
inputs. Separate worktrees do not isolate external resources. Low-capacity testing then semantic
review is serial, preserving Main's gate after each native closure.

The optional `runtime/delivery.py` adviser handles practice selection, a next-batch budget and
cumulative repair limits from small supplied facts. `allocation.py` still handles model routing,
scopes and capacity. Neither spawns workers, reads live quota, locks files or accepts results.
No helper input/ledger is required merely to do work. See `docs/v4.0.md` in the source for the
protocol and evaluation cases; the installed policy is self-contained for ordinary operation.
