# Appropriate RED/GREEN and efficient test execution

Main/Reviewer chooses sufficient gates. Tester/Luna Medium executes approved commands, owns waits
and reports evidence; it is not coverage judgment, test design or causal debugging. Those belong
to the implementation owner, Luna Max or suitable Sol. Existing owner/project TDD requirements bind.

## Choose evidence by the change

Use RED/GREEN for new or changed deterministic behavior and reproducible bugs where a meaningful
test is practical. Test a requirement through a real entry point, not copied implementation output.
Observe failure for the intended missing/wrong behavior before the fix, then observe the same test
pass after a minimal fix. Import, syntax or environment errors alone do not establish a useful RED.
Do not manufacture a meaningless failure just to satisfy a ritual. Refactor after green and rerun
affected checks. Pure refactoring usually starts with passing characterization tests protecting
existing behavior; deliberately breaking it is not required.

Copy/style/docs, generated transformations, exploratory prototypes and untestable external states
may use concrete alternative evidence: rendered journeys, diffs, schema/build checks or bounded
manual reproduction. Record a material exception and its evidence, not a fake TDD claim. Explicit
required TDD cannot be silently waived; resolve an unavailable test strategy. Existing valuable
code is not deleted because it preceded tests. Validate a later regression test against a safe
isolated known-bad baseline or negative control when practical, labeled retrospective rather than
pretending it was test-first. Never plant defects in a live/shared tree.

## Run once on identified stable inputs

Read project scripts/CI before choosing commands. During edits use focused decisive checks;
at integration execute every required complete suite on the stable integrated candidate.
Do not run all 1,000+ tests after each edit or repeat one applicable run across Main/writer/reviewer.
Mandatory fresh/full gates override reuse. Baseline, focused tests, full suite, build, browser
journey and visual assessment prove different things; do not substitute one for another.

Identify relevant dirty/untracked source, tests/config/lockfiles, toolchain/environment, target/build,
command/options and suite scope. HEAD alone is insufficient for a dirty tree. Hold all relevant
inputs or use authorized isolation. Outputs, accounts, ports, caches and browser state need ownership.
Prefer runner parallelism within CPU/RAM limits; shard only with isolated resources and complete
expected-shard aggregation. Five agents do not mean five full-suite processes.

One owner keeps the process handle and supported long waits. A wait timeout while the command
continues is not failure or permission to restart. Cancellation, truncation or a still-running
suite is not PASS. Preserve complete original logs/reports and real exit status; pipefail or the
original process status is required when piping output. Do not paste passing streams into Main.

## Honest results and reuse

Verify discovery and expected scope. Zero tests, collection errors, missing shards, unexplained
skips, weakened coverage or incomplete execution cannot establish a valid passing gate. Report
available passed/failed/skipped/expected-failure totals; do not invent unknown counts. Preserve
first failures and rerun outcomes. A passing retry does not erase unresolved flakiness.

Tester never changes source/assertions/dependencies, accepts snapshots or disables tests. Return
original failures for diagnosis; `debugging.md` bounds repair loops. Missing proof is UNVERIFIED,
affected drift STALE. Reuse results only for applicable source/test/config/environment/target and
command scope; mandatory fresh evidence wins. Verify integrated changes independently of branch
passes. At low capacity, preserve receipts and observe native closure before semantic review.

Return candidate/scope; command/cwd/environment; completion/exit; duration; exposed totals/shards;
log/report locations; failures/skips/flakiness; freshness and remaining gates. Keep secrets private.
Main inspects the receipt and decisive evidence. Semantic correctness and acceptance stay separate.
