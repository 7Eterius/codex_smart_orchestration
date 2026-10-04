# Bounded ownership and useful concurrency

Main may execute directly; delegation is not compulsory. For a tiny understood correction or
context-heavy critical path, a handoff can cost more than it saves. Otherwise select a coherent
independent assignment and dispatch it before waiting for another result. Main owns integration,
not necessarily every implementation detail. Read only task-relevant guides.

## Choose an owner once

Sol/default_executor owns normal implementation, diagnosis, adaptive tool use and realizing
Main's design. Luna/simple_executor handles explicit mechanical recipes; routine_executor
handles prescribed bulk transformations. Senior handles evidenced depth or scoped advice.
Never route a novel bug to Luna merely because the diff might be small. Do not run multiple
agents to solve the same issue speculatively. The optional allocation.classify helper accepts
kind/risk/settled/tiny/deep/independent_required plus mechanical/in_context/on_critical_path/stalled.
Unknown mechanical fitness favors Sol. Required review is preserved for Main-authored changes.

Give outcome, non-goals, requirements, scope, dependencies, resource/target, authority and checks.
Workers discover technical implementation within the accepted contract. Return protected
choices as DECISION_NEEDED; normal local diagnosis stays local. Preserve the original failure
and evidence. A same-defect correction without progress triggers bounded Sol/Main diagnosis,
not another cheap retry or a forced ladder through all reasoning levels.

## Parallel, not speculative

Start with two independent branches where useful; at most four Smart-owned open threads,
within the actual client cap. Main is not counted. Existing lower caps are preserved. A ready
result can unblock the next assignment without waiting for the whole batch. Main can execute
a disjoint task while helpers work, not duplicate their implementation.

Independence means no write/read or write/write conflict and no unmet prerequisite. Declare
canonical workspace paths and all relevant input/output paths, including shared modules,
lockfiles and build/test inputs. Unknown dependencies widen scopes. Separate source worktrees
do not isolate shared accounts, databases, ports, deployments or browser sessions. Those need
explicit resource identities. Worktrees are optional and require existing Git authority;
never create them or modify Git configuration solely because parallelism is suggested.

A stable preview can be reviewed while a disjoint branch is edited. A reviewer of the mutable
whole application instead holds its full dependency scope. Global checks run at the integration
boundary, not against a changing tree. Tests that write snapshots, profiles or browser state
are writers of those resources even if the agent's source role is read-only.

## Optional allocator observations

Use existing structured facts only. No required ledger. Legacy unscoped observations support
one unit and its reviewer; unrelated concurrent work requires scope information. A scope has
workspace (canonical absolute real path), reads/writes (relative POSIX paths), and
resource_reads/resource_writes (shared hierarchical resource IDs). Relative `.` means the
entire workspace, not a resource wildcard. Resolve aliases before declaring scopes; the helper
does not authenticate real paths or discover dependencies. Resource IDs must match across users.

Both observation threads and request can carry scope. Observation.main_scope is explicit null
when Main has no concurrent access, otherwise Main's scope. Unknown Main/peer activity stops
parallel scheduling. Requests can name depends_on; observation.accepted_units maps accepted
prerequisites to evidence references. A final worker message alone is not an accepted dependency.

Reserve one shared future review slot, when needed, using request.reserve=1 and record the
returned review_reserved obligation on the writer. Pending reviews can share this reusable
slot rather than reserving a slot per unfinished writer. An existing Tester occupies that
pool. Do not fill reviewer capacity with unrelated execution. A reserve is planning, not a
native slot allocation. Completed open threads still count, including retained workers.

For independent review, request.candidate_held=true and stopped writer state describe a real
hold. For repair, release the hold first and explicitly set candidate_held=false; a stopped
reviewer may remain for recheck after its mutable resources are released. Never manufacture
these observations to make the allocator allow work. Parallel results are advisory, not locks.

## Review and repair

Main dispatches Tester directly by default. Routine/Default may dispatch exactly one Tester
and no other role only with explicit scheduling authority and observed native support.
Direct named work needs no nested qualification. Tester starts independently of the writer's
reasoning. Stable candidate, original task and decisive evidence are supplied, not a persuasion
summary. It owns its verdict; Main owns acceptance and actual visual judgment.

Release holds before repair. Reuse suitable writer/reviewer context for concrete corrections.
If Main fixes a small finding, stop/transfer the writer first, include Main's entire delta,
refresh affected evidence and obtain required independent verification. Never write the same
candidate concurrently. Same-reviewer delta review is unavailable when impact is unknown.

## Wait, hand off and release

Workers own commands and their waits. Main waits only after scheduling independent ready work;
use completion notifications or supported long interruptible waits, not progress SEND loops.
Timeout alone does not trigger inspection, tests or acknowledgements. Honor real user
interruptions. A requested fresh status is one owner snapshot.

After acceptance, preserve decisions, candidate, gates, findings, next work and resource owners.
Close completed owned children leaves-first; observe native release before relying on the slot.
Thread closure does not delete source, browser profiles, logs or servers. Keep concrete repair
context, not idle agents indefinitely. A one-slot client can save the repair capsule, release
the writer and run Tester serially. At capacity failure inspect relevant handles once; retry
only after observed change. Never omit a required review, close unrelated work or raise caps.
No automatic restart, hidden model downgrade, ungranted cleanup or permission expansion.
