# Bounded ownership and useful concurrency

Main may execute small understood or context-heavy critical-path work directly. Otherwise
select a coherent independent assignment and dispatch ready work before waiting. Main owns
integration, not every implementation detail. Read task-relevant guides only.

## Choose the appropriate owner

Routine/Luna Max owns ordinary implementation and bounded unknown bugs, including prescribed
bulk changes. Simple/Luna Max handles known GUI journeys and extraction. Investigator/Luna Max
handles bounded causal discovery. Default/Sol Low is the moderate-complexity lane, Deep/Sol Medium
handles substantial interacting logic, and Senior/Sol High handles serious or critical-risk work.
Use the appropriate lane immediately; no compulsory failure ladder. Main settles protected
product/design/architecture choices, not every local technical decision.

The optional allocation.classify helper accepts the existing six fields plus mechanical,
in_context, on_critical_path, stalled, previous_owner and optional difficulty (ordinary/moderate/deep/serious).
Legacy deep=true still means deep work; difficulty cannot lower it. Critical risk selects Senior.
kind=verification remains semantic review; kind=testing means approved procedural test execution.
Stalled testing routes to diagnosis. Known previous_owner prevents retrying the same stalled Sol
preset; Senior exhaustion goes to Main for replanning, never independent self-approval.
Tester is not the legacy semantic reviewer. Use fresh post-upgrade conversations, not mixed
old/new role contexts. The helper recommends; it does not inspect native model availability.

Give requirements, non-goals, scopes, accepted prerequisites, targets/resources, authority and
checks. Workers solve implementation within that brief. Return protected choices as DECISION_NEEDED.
Keep original failures. One same-defect evidence-based repair without progress triggers an
appropriate Sol/Main diagnosis; ordinary errors with progress do not require changing owners.

## Parallelism and resources

Start with two useful branches; at most five Smart-owned open threads, excluding Main, within
actual client capacity. Existing lower caps and unrelated threads count. Main may work on a
disjoint critical path. Use completed independent results without a slowest-worker barrier.

Canonical read/write scopes include shared modules, lockfiles and all relevant build/test inputs.
A write conflicts with another owner's reads or writes. Unknown dependencies widen scope.
Separate worktrees do not isolate databases, accounts, ports, deployments or browser sessions.
Declare shared mutable resource identities and Main's concurrent scope. Worktrees require
existing Git authority; never create them or alter Git configuration just to manufacture parallelism.

A stable isolated preview can overlap independent implementation. Global integrated checks run
on stable inputs, never a changing whole tree. Test outputs, profiles and browser state have
owners even when candidate source is read-only. Limit CPU/RAM and runner processes separately
from agent threads. One test coordinator is the default; sharding requires supported, isolated
resources and complete shard aggregation. Multiple agents must not launch the same suite.

## Optional allocator observations

Use existing structured facts, not a required ledger. A scope has workspace (canonical absolute
real path), reads/writes (relative POSIX paths), resource_reads/resource_writes (shared hierarchical
resource IDs). Relative `.` means the entire workspace. Resolve aliases; the helper does not
discover dependencies or authenticate paths. Equivalent reordered path sets remain equivalent.

Observation.main_scope is null when Main is idle, otherwise explicit. Unknown Main/peer activity
stops parallel allocation. Requests may name depends_on; observation.accepted_units maps accepted
prerequisites to evidence. A final worker message is not acceptance. Unscoped legacy records allow
one unit and review, not unproven fan-out or a downgrade from known scopes.

Reserve one shared future semantic-review slot with request.reserve=1. Record returned
review_reserved obligations, including reuse. Reviewer and Senior Reviewer can serve that queue;
Tester cannot consume it as semantic sign-off. A retained unrelated, closing or unknown reviewer
is not reusable capacity. Reservations share one future slot, not one per writer. A queued unit's
reviewer may consume it; unrelated work must not steal it. Completed open threads still count.

All testing/review requires explicit scope and candidate_held=true, including legacy requests. A held candidate cannot resume writing.
Release the hold before repair and set candidate_held=false. Stopped verifiers may remain for
recheck only when resource handover is safe. Readback grants no writes. Verifier output scopes
must not overlap candidate inputs. Observations remain advisory, not locks or native scheduling.

## Verification and handoff

Main dispatches verifiers directly by default. Routine/Default may dispatch one required verifier
at a time, only with explicit same-unit scheduling authority and observed native support. No other
nested roles are permitted. Tester executes approved gates; Reviewer owns a separate semantic
verdict. Main owns final acceptance and actual visual judgment. Required gates remain binding
when Main wrote the change. Read `testing.md` and `verification.md` when relevant.

Reuse suitable writer/reviewer context for concrete corrections. If Main fixes a finding, stop
and transfer the writer first, include Main's entire delta, refresh affected proof and obtain
required independent review. Preserve a repair capsule before releasing an owner to free capacity.

## Wait and release

Workers own commands and waits. Use completion notifications or long interruptible waits after
ready independent work is assigned, not repeated progress SENDs. Timeout alone triggers neither
a new test nor an acknowledgement. A requested status is one existing-state snapshot.

After acceptance preserve candidate, gates, findings, decisions, next work and resource owners.
Close completed owned children leaves-first; observe native release before relying on a slot.
Closure does not delete source, logs, profiles or servers. At low capacity, preserve the repair capsule and release the stopped writer, then run Tester
and Reviewer serially, observing closure between them. Do not wait indefinitely on a reservation
or waive semantic review; Main retains the required gate after closing its writer record. On capacity errors reconcile once and retry only after
observed change. Never omit required review, raise owner caps, close unrelated work, expand
permissions, silently downgrade models or automatically restart Main.
