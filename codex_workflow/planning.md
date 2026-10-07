# Scaled discovery and decision-oriented plans

Use for genuinely unclear goals, consequential choices or multi-step work. An explicit request
with settled requirements is already a brief; do not reopen it to perform a brainstorming ritual.
Read project instructions and controlling sources before asking questions answered there.

## Discover only what changes the decision

For a vague request, identify the intended user/outcome, constraints, non-goals and evidence of
success. Ask the smallest set of consequential questions, preferably one decisive question at a
time. Compare two or three materially different approaches only when a real choice exists;
recommend one with its tradeoff. Do not invent alternatives to fill a template.

Main may choose reversible implementation details within existing authority and state important
assumptions. New product meaning, public contracts, irreversible changes, security boundaries or
spending beyond an explicit budget require the appropriate decision/approval. Continue disjoint
safe work while a decision is pending. Do not ask permission to continue an already-authorized
plan, nor interpret silence as approval for a new protected choice.

For a feasibility spike, timebox the question and report findings and limitations. Mark prototype
code as experimental; do not silently promote it to production or delete it as a TDD ritual.

## The smallest plan that prevents mistakes

A tiny understood task needs only outcome and decisive check. Multi-step work needs a short
in-chat/native plan. Large features, long runs or handoffs need a durable plan/checkpoint in an
existing project-approved location; no new task database. Scale down when complexity resolves.

Record goal and authoritative requirement references; protected decisions/non-goals; affected
components and interfaces; risks; coherent deliverables with dependencies/owners; decisive checks;
and authorized finish target (working patch, commit, PR, merge or release). Keep exact values and
interface contracts verbatim where they matter. Distinguish assumptions and unresolved decisions.

A task is a testable deliverable, not each shell command. Batch same-shape edits. Do not prewrite
all implementation code for Main to hand to a cheaper typist. Include exact code only for an
important contract, regression case or genuinely mechanical transformation. The implementation
owner solves the technical problem. Avoid 2-minute microtasks and unnecessary per-step commits.

Self-check once: every requirement maps to a deliverable/check; producers and consumers agree;
shared writes serialize; dependencies are achievable; baseline failures are visible. A plan is
subordinate to the requirements. Correct a discovered contradiction with its reason and impact;
never blindly follow the plan or silently change the required behavior.

## Resume without repeating accepted work

For long work, keep a compact checkpoint alongside the plan: canonical repo/workspace, task and
requirement identity/revision, base/candidate commits or fingerprints, accepted units and evidence,
open findings, cumulative repair counts, outstanding commands/owners and next action. Use full
identity, not just a plan basename that could collide. No ledger for a typo or per-tool event log.

After context loss, compare the checkpoint with actual Git/files/process state. Do not redispatch
accepted work, restart a live test process or treat a stale completion line as proof. Unknown or
changed identity requires reconciliation. Changing workers does not reset repair budgets. Preserve
checkpoint/evidence through integration; cleanup is a separate authorized action.
