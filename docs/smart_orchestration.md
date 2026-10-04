# Smart engineering notes

## 3.0: optimize the accepted outcome, not the cheapest individual call

The current architecture restores direct Main execution for small/context-heavy critical-path
work and makes Sol Medium the normal solver. Luna has a bounded recipe lane. This intentionally
supersedes 2.x mandatory delegation and its two-thread ceiling.

Parallel work needs proven independence in read/write scopes, dependencies and mutable
resources, including Main's activity. The optional allocator checks those supplied facts with
native capacity/lifecycle observations. Up to four owned threads is a ceiling, not a fan-out
target. Existing explicit lower limits remain binding. One future reviewer slot is shared by
waiting tasks, and completed useful results can advance without a batch-wide barrier.

Main can write, but a required independent reviewer must still be a different agent. Holds,
original evidence, meaningful tests, exact target identity and separate acceptance/deployment
authority remain. Main retains product/design decisions and actual visual acceptance.

The installer modifies only declared global Smart files and managed instruction regions.
Explicit owner configuration, project files, locally modified managed files and exact rollback
are protected. Fresh missing defaults differ from preserved old values; disk checks make that
visible without claiming current-session activation.

The test organization now separates current 3.0 behavioral tests from the exact historical
2.7.1 suite. Current policy is not constrained by obsolete literal 2.x prompt strings. Historical
source is never silently rewritten to satisfy new expectations. Archived upgrade/rollback tests
exercise the real old installers with the new package.

No runtime database, telemetry, dependency crawler, model-price calculator or global mandatory
qualification gate is added. Optional helper output is only as trustworthy as its supplied
facts. Source CI does not measure live speed, model judgment or allowance savings.

See [3.0 review](v3.0.md), [current architecture](../README.md),
[execution](../codex_workflow/execution.md) and [verification](../codex_workflow/verification.md).
Earlier version documents remain historical records, not current instructions.
