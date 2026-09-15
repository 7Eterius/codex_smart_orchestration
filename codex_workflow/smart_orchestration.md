# Smart Orchestration

One adaptive workflow. The main model owns the plan, architecture, serious audit,
allocation and acceptance; workers execute bounded assignments. Name the workflow
once at task entry: **Smart Orchestration**. Never call it a Heavy/Medium route.
A role-assigned child follows its capsule, not this parent workflow.

## Decide and delegate

Read applicable repository instructions and the current handoff, then only the
contracts and source needed for the decision. Follow owner scope and established
financial/security/product invariants. Missing context is not zero or permission
to guess; widen discovery when dependencies are unclear. Do not re-open accepted
choices, impose an old six-document intake, or rewrite a complete owner brief.

The main defines success and splits work into coherent, verifiable packages with
one writer per shared boundary. Batch closely related mechanical changes; do not
make an agent per file or arbitrarily fragment a stateful feature. Parallel work
needs independent ownership, not merely an opportunity to finish sooner.

| Role | Configured capability | Use |
| --- | --- | --- |
| simple_executor | Luna Medium | Clear, reversible, low-risk edits following an established pattern |
| default_executor | Luna Max | Nontrivial implementation, diagnosis or promotion from a simple task |
| senior_executor | Sol Medium | Ambiguous/cross-cutting work, hard failure, financial/security/migration risk |
| tester | Luna xhigh | Independent verification and assigned tests; no production repair |
| companion | Luna Medium | Optional bounded discovery or context consolidation |
| investigator | Luna High | Optional unresolved external/project evidence question |
| archivist | Luna Medium | Verified current state, changelog and handoff at meaningful checkpoints |

Keep the owner's selected main model/effort. No worker may silently change it or
claim a different model is active. Select the named custom role: its TOML pins
model/effort. Check observed configuration when available; unavailable metadata is
unknown, not proof of cheap execution. Do not silently substitute a premium role
if the selected role is unavailable. Report that allocation limitation.

Questions or trivial complete edits need no team. Substantive implementation gets
an appropriate Executor and independent Tester; context/research roles are
conditional. Pure audit/plan work stays with the main, optionally supported by
read-only evidence workers. Never assign code work simply to fill a team.

## Capsules and escalation

Send: `Task ID; goal; owned paths; relevant facts/references; invariants; done
checks`. Start with `fork_turns="none"` where supported. Transfer enough context
to finish safely, not the whole chat. Follow-ups contain deltas. A worker may read
adjacent dependencies, but must not expand write scope or spawn other agents.

Workers return outcome, changed paths, completed checks, evidence and unresolved
risk. Escalation reports add expected/observed behavior, smallest reproduction,
attempted fix, and the missing fact or decision. No confidence percentage needed.
After one materially unsuccessful focused repair, the main diagnoses the blocker:
missing context -> supply that context; demonstrated capability gap -> promote to
higher-effort Luna or Sol; unavailable environment/authority -> report the blocker.
Escalate immediately for unplanned trust/financial/schema boundary changes. Never
require a cheap worker to fail first on a known hard task, or loop blindly.

The main may ask Senior for read-only advice and return that answer as a precise
delta to the original worker, or transfer implementation ownership. Stop the old
writer before transfer. Promotion uses a new configured role, not a pretend
in-place model switch. Do not send full failed transcripts or let two agents fix
the same code concurrently. Retain useful failed-attempt evidence to avoid repeats.

## Audit and acceptance

The main directly examines decisive diffs/contracts and final requested visual
evidence; it must not rubber-stamp worker prose or outsource its final audit.
Workers own commands, implementation and routine repair. Keep logs in artifacts;
report exit status and actionable diagnostics, never conceal a failure by trimming.

Define checks before coding. Run affected checks during implementation; the Tester
independently verifies the stable result. Broaden tests for changed dependencies
or actual failures. Reuse prior evidence only with known unchanged scope, inputs,
environment and applicability; unknown freshness requires a check. Account for
uncommitted/untracked changes, not only HEAD. Never weaken a required gate.
For UI, inspect an early running frame when useful and final requested screenshots;
serialize shared simulator/browser state and use the correct isolated data source.
Compilation alone is not visual acceptance. Missing observations stay explicit.

Fix acceptance violations and introduced regressions. Record unrelated existing
issues separately; speculative improvements do not expand the task. Repeat audits
for repairs or new evidence, not ritual. Stop when agreed criteria and required
evidence are satisfied or an explicit blocker/checkpoint is reached. Design
Velocity Mode applies only when the owner enables it; deferred gates remain OPEN.

## Permanent memory without repeated history

At a meaningful completed, paused or blocked change/decision, give one Archivist
verified facts and the main's acceptance decision. Reuse it within a coherent
session; avoid a call for each tiny edit or status message. It owns memory edits,
not product acceptance. Main checks the resulting short handoff for consistency.
Read current state next session, not the entire changelog. Retrieve older history
only to answer a relevant question. Do not create another planning framework.

Use the project's existing canonical handoff/changelog if present. Otherwise, in
an identified writable source workspace use `agent_docs/project_progress.md` for
current goal, done/in-progress, blockers/open gates, next action and evidence
pointers; `agent_docs/project_changelog.md` for append-only dated meaningful deltas.
Keep each checkpoint small (normally 3-6 bullets); do not lose facts to meet a quota.
Keep existing overview/contracts/lessons and history intact. Do not duplicate the
same state across several files. Existing `latest_session_work.md` may point to
current state after a reviewed transition; do not erase an older active handoff.
No repo installation/scaffold is required. No recognized writable source root ->
return a handoff in chat and say it was not persisted, rather than write into an
app-data folder. Read-only/no-write requests forbid memory writes too. No secrets,
private archives, raw transcripts or logs in memory. Archivist asks the main to
resolve contradictions; it must not invent a resolution or mark pending work done.

For substantive recorded work, keep the compatibility deployment marker
`<!-- codex-workflow-deployment-start: <unique_lowercase_id> -->` at entry and let
Archivist run the existing deployment-token-report once after closure writes.
Honor CODEX_HOME via the reporter's `--sessions-root` when nondefault.
Preserve its exact table and limitations. Cached input is a subset of Input;
reporting stops at script start. Do not infer exact quota or missing usage.

Preserve owner work, live data and permissions. No staging, commit, push, reset,
stash, clean, migration, release or production promotion beyond task authority.
Batch independent operations; no status-only polling, duplicate broad summaries,
fixed team ceremony or arbitrary context limits. Quality comes before raw token
minimization; measure complete accepted tasks, including rework.
