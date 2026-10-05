# Smart Orchestration 3.1.1

A maintenance and reliability patch for stable daily use. The 3.1 model mix, eleven on-demand
presets, five-worker ceiling, no-manager architecture and risk-based quality gates are unchanged.
No model benchmark, native Codex qualification or measured allowance saving is claimed.

## Audit findings and fixes

### Verification could bypass the freeze through legacy inputs

The 3.1.0 allocator required a candidate hold only when the request already supplied a scope or
hold field. A legacy unscoped request could therefore start a reviewer against a running writer.
An unscoped repair could also bypass an active verifier. The patch requires an explicit scope
and candidate_held=true for all test/review work. Legacy serial execution remains available,
but missing verification facts now request inspection instead of authorizing work. Readback
still grants no writes. The tests execute the exact 3.1.0 allocator to reproduce these gaps,
then verify rejection by the current implementation.

### Stalled work could return to the same inappropriate owner

Procedural testing marked stalled previously selected Tester again. It now routes to diagnosis.
The optional previous_owner fact prevents a known stalled Sol Low owner from being sent back
to Low and a stalled Sol Medium owner from being sent back to Medium. They can move to the
appropriate higher preset; critical risk still takes precedence. A stalled Senior or Main
returns to Main for replanning, not another identical attempt or self-certification of an
independent gate. This rule applies after an evidence-based same-defect correction without
progress, not to ordinary compiler errors or a still-running command.

No compulsory effort ladder is introduced: start at the appropriate depth. Existing six-field
task inputs remain valid; previous_owner is optional and strictly validated. A tiny label can
no longer contradict an explicit deep/serious difficulty.

### Reading a result was confused with starting new work

A completed parent could not read a stopped child's result because the allocator applied fresh
nested-scheduling requirements to readback. The patch separates those actions. Readback still
requires a known owned, stopped direct child of the matching unit and role. It cannot spawn,
reserve capacity, interrupt a live child or authorize a write. New nested work retains its
existing active-owner, authority and one-verifier-at-a-time checks.

### Sandbox defaults unnecessarily overrode inheritance

All named role files previously specified workspace-write even for lookup and semantic-review
roles. The files now omit sandbox_mode and inherit the selected parent sandbox. Existing owner,
project and live runtime restrictions remain binding. This does not claim a native per-path
permission system; role instructions still constrain allowed changes and the allocator checks
supplied scopes. Models and reasoning efforts are byte-for-byte unchanged as parsed values.
Customized managed files continue to cause an explicit installation conflict.

### Worker guide paths were ambiguous

Tester and the semantic reviewers now identify their guides under actual
CODEX_HOME/codex_workflow, with the ~/.codex default explicit. A same-named project document is
not the workflow guide. Project-specific rules remain separate and binding.

## Efficiency and everyday operation

The global bootstrap is shortened rather than restating the complete installed policy. The
suite compares its word count with the exact 3.1.0 source and keeps a tighter size budget.
This is measured instruction reduction, not a measured token, caching or billing improvement.
The full policy is still loaded once for substantive Main work, not by every worker.

At low capacity, preserve the repair capsule, observe the stopped writer's closure, run Tester,
preserve its receipt, close it and run required semantic review. Main keeps the semantic gate
pending even after the allocator's writer record closes. Do not deadlock on a retained slot or
pretend a procedural test result is semantic approval. At higher capacity, retain useful
correction context and overlap genuinely independent work when that is more efficient.

Focused checks during edits, stable integrated full gates, original failure retention, test-run
ownership and valid evidence reuse remain unchanged. No new service, scheduler, task database,
automatic telemetry, mandatory test receipt schema or standing agent team is added.

For research, writing, planning, files and administrative work, use domain-appropriate evidence
rather than invented software tests or obligatory code-review teams. Ordinary tasks must not
trigger workflow audits, installer checks, model research, reinstallations or retuning. Revisit
this workflow for an observed problem, relevant client incompatibility or an explicit request.

## Release housekeeping

Patch releases now require exact version notes, such as docs/v3.1.1.md, instead of republishing
the initial 3.1.0 notes. Initial .0 releases retain the historical series-note fallback. The
actual release shell is tested for both forms and for missing patch-note rejection.

CI uses full commit pins for actions/checkout v7.0.1 and actions/setup-python v7.0.0, verified
against their upstream release tags. Superseded validations of the same pull request can cancel;
main-push validation uses a unique run identity and release publication remains serialized and
non-cancelling. No test matrix entry, historical upgrade or release gate is removed.

Temporary patch-preparation files are excluded from the final release tree. Historical documents,
source caches, rollback backups and unrelated branches are not swept away as housekeeping.

## Validation and limits

Run the current complete suite and syntax/whitespace checks. Existing candidate identity,
preflight evidence, scope/resource conflicts, reservation and installation regressions remain.
New tests cover the exact 3.1.0 counterexamples, stalled routing, safe readback, low-capacity serial
verification, unchanged model choices, inherited sandbox settings, guide paths, bootstrap size,
patch-note selection and pinned CI contracts. Exact 3.1.0 upgrade/no-op/rollback joins the prior
historical migration fixtures. The separate archived 2.7.1 reference suite remains unchanged.

The final source is checked on Linux Python 3.11/3.12 and macOS Python 3.12 before publication.
Tests of supplied-state helpers do not authenticate observations, prove native model selection,
lock files, measure real projects or guarantee future client compatibility. Install, restart
manually and verify only the native capabilities needed by the actual next task.

## Primary references checked 5 October 2026

[Codex custom agent configuration](https://developers.openai.com/codex/subagents/) documents
standalone agent files, explicit model/effort precedence and parent sandbox inheritance.
[Configuration reference](https://developers.openai.com/codex/config-reference/) documents the
spawned-thread cap excluding Main and the legacy alias.
[Checkout v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1) and
[setup-python v7.0.0](https://github.com/actions/setup-python/releases/tag/v7.0.0) identify the
CI dependencies pinned in this patch.

[3.1 design and research](v3.1.md) | [Main policy](../codex_workflow/smart_orchestration.md) |
[Execution](../codex_workflow/execution.md) | [Testing](../codex_workflow/testing.md)
