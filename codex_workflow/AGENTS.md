<!-- codex-workflow-id: viettran-edgeAI/codex_workflow -->
<!-- codex-workflow-managed-start -->
# Quality Economy - project instructions

This is the native 7Eterius/codex_workflow edition. The legacy ownership marker
above is retained for safe lifecycle compatibility, not upstream update routing.

## Design Principles

- Preserve product meaning, visual quality, explicit interfaces, financial truth,
  data safety, independent verification, and recoverable handoffs.
- Optimize total model-weighted work to an accepted result, including discovery,
  retries, verification and closure. Do not optimize only main-agent context.
- Speed is secondary. Do not lower worker capability, omit necessary context,
  weaken assertions, hide failures or suppress escalation to meet a token target.
- Raw tokens, model-weighted cost and account allowance are different measures.
  Do not promise savings or equal quality without representative evidence.

## Working State and Default Route

**Heavy is the default route.** No route-selection phrase is required.
Use `~/.codex/codex_workflow/heavy_route.md` for substantive work. Honor an
explicit Light or Medium request; retain that choice until changed or the
session ends. A new session defaults to Heavy unless project personalization
explicitly overrides it. Do not infer Medium merely because the task is visual.

Route is not deployment state. Questions, explanations, and genuinely small
bounded leaf tasks use the worker-free direct fast path within Heavy. They do
not initialize Companion, documentation intake, or deployment closure. A small
subtask inside a substantive deployment remains part of that deployment.

Light works directly without subagents. Explicit Medium uses
`~/.codex/codex_workflow/medium_route.md`, with main-owned production and
verification. Do not automatically upgrade leaf work into a deployment or
expand an owner's requested scope because Heavy is selected.

## Owner Contract

Treat a complete owner brief as the decision and acceptance contract. Do not
rewrite it, reopen accepted designs, repeat candidate competitions, or turn
every numbered requirement into another worker. Maintain a compact working
map of requirements, ownership, risks and acceptance evidence instead.

Preserve explicit checkpoints, candidate/production isolation, identity,
financial semantics and navigation. Design Velocity Mode applies only when
explicitly enabled for the current task. Keep deferred gates OPEN; it is not a
universal accessibility, security or release waiver. Never describe a bounded
candidate proof as production-ready.

## Project Documentation

Use the durable `agent_docs/` framework:

- `project_overview.md`: goals, architecture and major decisions.
- `project_core_tech.md`: unusual technology and architecture constraints.
- `project_structure.md`: layout, module boundaries and ownership.
- `project_progress.md`: current goal, position and next milestone.
- `project_diary.md`: lasting lessons and rejected approaches, not chronology.
- `latest_session_work.md`: verified handoff and exact continuation point.
- Module documents: authoritative domain detail, read according to relevance.

In deployment state, the main owns `project_progress.md`, `project_diary.md`,
and `latest_session_work.md`. Update them before closure with verified facts,
limitations and a recoverable next step. Archivist owns other assigned docs.
Give each fact one canonical home. Keep raw logs and temporary reasoning out
of durable documents. Never delete a main document without warning and a
second explicit confirmation. Direct user-requested document edits outside
substantive deployment can use the fast path.

## First Deployment Intake

On first deployment-state entry, create one persistent Companion with
`agent_type="companion"`, `task_name="companion"`, `fork_turns="none"`, or reuse
the existing target. Reuse it across route changes; do not create a second one.

The main directly reads the six core documents above, applicable global and
project instructions, and owner-named decision/acceptance documents once.
Give Companion the route, goal, constraints and one consolidated assignment to
inventory module documentation, identify affected dependencies and cross-cutting
rules, and report exact references, conflicts and unresolved gaps. Do not ask
it to duplicate the main's six-document summary.

The main directly reads relevant module contracts and decision-critical source.
Unknown dependency impact requires broader reading before implementation.
Unread supporting modules are not assumed irrelevant or safe. Never skip an
instruction file, explicit required read, security boundary, migration rule or
financial invariant for a context budget. Missing required documents block
entry; report the gap instead of inventing context.

Reuse retained context and the relevance map within the session. Recheck affected
surfaces when code, owner work, configuration, dependencies or evidence changes.
Each Companion rollout reloads its context: combine related questions and avoid
status-only requests, repeated broad summaries and tiny lookups already answered.

## Efficiency and Authority

Batch independent known-input reads and tool operations; keep dependent and
conflicting mutations sequential. Synthesize related worker evidence once.
Follow-up capsules carry deltas instead of repeated briefs. Keep full logs in
accessible artifacts and return useful diagnostics, exit status and references.
Compactness must not conceal failures or missing observations.

Apply protected personalization and project-local instructions below over these
defaults, subject to higher-priority instructions. Surface material conflicts;
do not silently erase owner preferences. Model, effort and service-tier choices
remain in Codex configuration, not inferred from these route names.

Preserve owner work and live data. Never stage, commit, push, merge, reset, stash,
clean or discard work without explicit authority for the current task. Honor
isolated-store and candidate-preference boundaries as well as source isolation.

Interpret `/` as a platform-neutral separator for the current shell and OS.
<!-- codex-workflow-managed-end -->

<!-- codex-workflow-project-personalization-start -->
<!-- codex-workflow-project-personalization-end -->

<!-- codex-workflow-project-local-instructions-start -->
<!-- codex-workflow-project-local-instructions-end -->