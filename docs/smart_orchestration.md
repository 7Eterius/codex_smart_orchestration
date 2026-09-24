# Smart Orchestration engineering notes

## Single adaptive loop

2.2 replaces the two-mode architecture with one bounded execution owner and an
independent reviewer when required. Main retains consequential judgment and final
acceptance. Routine/Default own implementation, self-checks and repairs. Tester now
explicitly owns actual-diff/contract review as well as required behavior verification;
there is no dedicated lead reviewing the same ordinary change again.

Small answers/trivial already-known operations can stay direct. Multi-step mechanical
work goes to Simple, settled implementation to Routine, deep work to Default. These
are responsibilities, not alternative execution modes. Risk and contract uncertainty
still require judgment; no classifier guarantees the globally cheapest correct choice.

## Review dispatch adapts to actual capability

Routine/Default may dispatch only one Tester under delegated scheduling authority,
with applicable observed nested mechanics and an available slot. Otherwise main dispatches
the same named independent reviewer. Unknown per-run telemetry remains unknown, not
proof of failure or a reason to disable all inexpensive named roles. Known safety or
capability failures remain binding. Required independence is never a fallback casualty.

The intended unit uses two Smart-owned open threads, with serial extension for explicit
additional review gates. The unchanged configured cap remains a ceiling including other
work. The previous three-thread trial is evidence for its first loop and against
claiming repeatable group turnover. Its exact slot-accounting cause was not established.

## Lifecycle

Completion, retention for correction, closing, observed closure and resource handoff are
separate states. Only native observed release removes a thread from the available-slot
calculation. Parents close eligible completed direct children before their own closure.
No acknowledgements, blind retries, unrelated thread closures, cap increases or shell
process killing are used to make allocation succeed.

`runtime/allocation.py` provides small pure policy functions and a bounded JSON CLI for
uncertain allocation boundaries. It is deliberately not another agent scheduler or
telemetry store. The active model/native tools must supply truthful observations and
perform any approved actions; the helper cannot enforce native authority or verify its
inputs. Simulated lifecycle tests do not qualify a real Codex backend.

The source installer retires only proven owned worker bytes. Edited retired worker
files block updates; old runtime documents with unverified local edits are preserved
and warned about. Current core guides never activate them. Exact backup restoration,
project non-mutation and explicit configuration preservation remain required.

## Validation scope

New tests cover responsibility selection, two-slot budgeting, completed-versus-closed
threads, stale retry prevention, protected child ownership, independent review dispatch
and source upgrade/retirement. Existing archive migration tests are retained and updated
for current policy, with a new exact 2.1 -> 2.2 -> rollback test. Full migration tests
need real Git history. No claim about native reclamation or savings follows from them.
See [2.2 decisions](v2.2.md) and [targeted runtime checks](../codex_workflow/runtime_check.md).
