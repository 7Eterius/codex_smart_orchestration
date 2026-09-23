# Change-aware verification

Consult once while planning validation-bearing work. Main sends workers only the
relevant scope/checkpoint and gates. No extra planning agent or mandatory report.
Preserve explicit repository/owner gates. This guide narrows redundant timing,
not required coverage, independent testing, security or accessibility obligations.
A globally installed policy cannot silently amend a project's stricter test plan.

## Choose the checkpoint

- Edit loop: fastest checks that can invalidate this edit; no full matrix per worker.
- Stable candidate: independent Tester verifies the combined change and affected
  journeys; main audits decisive source and final running-product visual evidence.
- Merge/release: complete applicable gates when that phase is actually authorized.
  A candidate proof may stop with release gates explicitly OPEN, never called done.

Batch closely related edits under one acceptance contract. Repaired behavior gets
fresh affected checks. Shared dependencies, unknown impact or failures widen scope.
An executed check is not an obligation to repeat it at every handoff. Conversely,
Executor self-checks do not replace an owner-required independent execution.

## Trigger checks by what changed

| Change | Needed evidence |
| --- | --- |
| Internal docs only | Document/link correctness; no UI audit unless behavior or executable config changed |
| Pure domain/backend logic | Relevant unit/contracts; inspect UI consumers when data shape, errors or state behavior changed |
| UI copy/localization | Required key/placeholder/plural integrity and affected text wrapping/accessibility names |
| Layout/type/color/animation | Running changed screens, relevant contrast/target size/Dynamic Type or zoom/reduced motion |
| Menus/forms/focus/navigation | Keyboard and focus/back continuity, labels/roles, relevant screen-reader state and targeted automated scan |
| Shared theme/component/router | Broaden representative consuming journeys, both affected themes, inherited semantics |
| Auth/entitlements/migration/financial truth | Boundary/invariant and regression checks; never classify solely by diff size |

No full accessibility/device/locale/screenshot matrix after every small task.
Do targeted accessibility on a stable changed UI, including newly revealed states.
Broader automated/manual accessibility belongs to applicable milestone/release
criteria or shared-impact changes. Never disable rules or exclude new violations
for speed. Automation and screenshots do not replace manual accessibility checks.
Unrelated logic changes need no new UI audit only when UI impact is demonstrably absent.

## Browser and Computer Use

Prefer deterministic evidence before screenshot-only diagnosis. For local web work,
inspect source/tests and Browser DOM, console and network state when available. Use
Computer Use for native or GUI-only behavior, simulators, system settings and multi-app
journeys. Define the starting state, target journey and expected result in the capsule.

Batch GUI checks around a stable candidate instead of replaying long journeys after
every edit. Reuse the same valid browser/simulator session when safe, and serialize
shared GUI state. Screenshots prove visible state only; they do not establish hidden
logic, accessibility, persistence or network correctness. Main retains final product
and visual judgment. For difficult screenshot or spatial visual judgment, GPT-6 Astra
may be owner-selected when available; ordinary Computer Use does not justify automatic
Astra escalation.

## Keep evidence usable

Reuse only known-applicable evidence: covered behavior, complete relevant inputs,
dependencies, toolchain/config, data, environment, viewport/theme/locale and scope.
Include owner/untracked changes, not only HEAD. Record execution vs reuse vs
not-applicable vs deferred vs blocked in the existing short handoff with rationale.
No baseline/unknown applicability -> check, not an assumed pass. A file hash alone
is not a test-dependency graph. No blind command-result cache or suppression of gates.

Reuse valid incremental build products and running test servers after confirming
checkout/config/port identity. Clean only for demonstrated stale artifacts or an
explicit clean-build gate. Build once for a stable candidate; run compatible tests
against that build where supported. Debug checks do not prove Release behavior.
Keep screenshots, deep performance runs and full device/locale matrices on-demand
unless explicitly required. Never auto-approve visual snapshots.

Parallelize independent native checks only within CPU/memory and state isolation.
Serialize shared simulator, browser, build-output, database and screenshot state.
Do not create extra LLM agents merely to run two independent shell commands.
Use failure traces where supported; preserve reproduction and relevant evidence.

For verbose commands prefer existing structured reporters or
`runtime/capture_check.py -- <executable> <args...>`. It saves private raw logs and
returns bounded excerpts plus real exit status; it does not assess test coverage,
cache results or call a model. Read native reports/raw output for unknown or failing
results; never rerun solely to recover output already saved. Keep artifacts out of
version control; logs/argv may contain secrets. Do not compress decisive code diffs,
security policies, migrations or visual evidence through a lossy summarizing proxy.
