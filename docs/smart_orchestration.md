# Smart Orchestration engineering notes

## 2.6: judgment stays expensive, contradictions get cheap

Smart 2.6 keeps the single-loop/eight-role architecture from 2.5. Main recommends GPT-6.1
Sol Medium; Senior remains GPT-6.1 Sol xhigh; Luna role models/efforts stay unchanged.
Main owns product/architecture/design judgment and acceptance; named workers execute settled
work and repairs.

2.6 borrows lightweight mechanisms from Kiborgik/BlaBla without adopting its DSL or task
database. The shared theme is that durable project/evidence state should outrank an agent's
story, and that a bounded worker should stop at a protected decision instead of silently
redesigning the system.

## Progressive context disclosure

Assignments point workers toward the narrowest authoritative routing surface first:
project instructions, status/index/architecture map, then relevant identity/rule/file.
Projects may provide queryable status/explain/index commands; Smart does not require one.
Retrieving a rule is not applying it. This avoids replacing a large parent transcript with
a large project-memory dump.

## Deterministic preflight

`runtime/challenge.py` accepts one bounded structured record and returns CLEAR or one
grounded contradiction. It covers supplied scope/attribution, protected decisions,
deliverables, blocking findings and evidence freshness/disposition. It performs no model
call, source scan, test run or mutation. CLEAR is deliberately weak: it means no supported
contradiction in supplied facts, not semantic correctness, authenticity, coverage,
authority or acceptance.

The helper is progressive enhancement. Do not create a persistent ledger solely to feed it.
Mechanical challenges return to the current worker; DECISION_NEEDED returns to Main.

## Evidence and review

Implementation claims now use an explicit precedence: actual repository/target state,
deterministic readback, current executed checks, independent review, then worker narrative.
STALE and UNVERIFIED are first-class states.

Tester is falsification-first: original task, complete diff, every deliverable, controlling
code before semantic findings, sibling cases around changed branches and the smallest
concrete counterexample. BLOCKING is correctness/completeness/truth, not taste. Tester
still never edits candidate source and does not replace Main's visual judgment.

Workers use DECISION_NEEDED only for protected product/design/architecture/contract/scope/
authority choices. Smart intentionally avoids numeric confidence thresholds.

## Preserved safeguards

The run-wide two-thread target, meaningful wake conditions, no-timeout-polling rule,
candidate holds, independent verdict ownership, same-writer correction loop, progressive
milestone handoff, native-release observation, permissions and exact rollback protections
remain. `allocation.py`, `candidate.py`, `boundary.py` and `challenge.py` are advisory
bounded helpers, not native enforcement.

CI includes exact archived 2.5 -> 2.6 -> no-op reapply -> rollback plus all historical
migrations. Tests prove shipped contracts and helper behavior, not live Codex compliance
or measured savings. See [2.6 notes](v2.6.md), [2.5 history](v2.5.md) and
[optional evaluation](evaluation.md).
