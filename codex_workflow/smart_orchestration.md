# Smart Orchestration 4.0

Optimize accepted quality, elapsed time and total model work, including context, failed attempts,
verification and handoffs. Keep one adaptive loop: understand, choose ownership, execute, verify,
accept. Adopt useful engineering practices, not a second orchestrator or mandatory ceremony.

## Judgment and ownership

Main owns product meaning, architecture, UX/visual direction and final acceptance. Main may implement
small understood changes when handoff costs more than it saves, or context-heavy critical-path
work. Delegate coherent outcomes without pre-solving the entire patch for a cheaper typist.
Required independent review applies equally to Main-authored changes. Never race another writer.

Read controlling sources and existing decisions before asking questions. A clear authorized request
needs no repeated brainstorming/approval. Main settles reversible implementation details within the
accepted contract. Protected product/architecture/contract choices or new authority are
DECISION_NEEDED with evidence and bounded options. Continue safe disjoint work when possible.

## Fixed intelligence, adaptive method

| Responsibility | Default preset |
| --- | --- |
| Main decisions, small direct work, acceptance | Owner-selected; GPT-6.1 Sol Medium recommended |
| Ordinary implementation, bounded unknown bugs, bulk changes | routine_executor / GPT-6 Luna Max |
| Moderate work, adaptive tools, bounded escalation | default_executor / GPT-6.1 Sol Low |
| Deep interacting implementation/diagnosis | deep_executor / GPT-6.1 Sol Medium |
| Serious complexity or critical-risk work | senior_executor / GPT-6.1 Sol High |
| Independent ordinary semantic review | reviewer / GPT-6 Luna Max |
| Deep/critical-risk independent review | senior_reviewer / GPT-6.1 Sol High |
| Approved test execution and waits | tester / GPT-6 Luna Medium |
| Bounded causal investigation | investigator / GPT-6 Luna Max |
| Known GUI recipes/extraction | simple_executor / GPT-6 Luna Max |
| Exact lookup / authorized checkpoint | companion / Luna Max; archivist / Luna Max |

Luna Max is the ordinary delegated baseline, not guaranteed superiority. Start directly with
appropriate Sol for broad uncertainty, weak observability, novel architecture or consequential
security/payment/data risk. No compulsory effort ladder. Preserve explicit Main/profile/speed,
sandbox and permission settings. Verify actual selected model/effort when exposed; unavailable
presets are disclosed, never silently substituted. A role file is not runtime proof.

Choose practices by need, using installed guides only when relevant:

| Trigger | Practice / guide |
| --- | --- |
| Genuinely ambiguous outcome | Targeted brainstorming in `planning.md` |
| Multi-step or long work | Lean deliverables/decisions; durable checkpoint only when useful / `planning.md` |
| Bug, failing build or performance regression | Observe, trace, test one hypothesis, causal repair / `debugging.md` |
| Testable behavior change or reproducible bug | Real RED/GREEN; characterization/alternatives otherwise / `testing.md` |
| Large feature or explicit isolation need | Reuse branch/worktree, safe integration and preservation / `branches.md` |
| Substantial dispatch, constrained quota or explicit budget | Bounded total work and verification reserve / `economics.md` |

Keep source-backed requirements above the plan. Tasks are coherent testable deliverables, not
individual clicks or two-minute actions. Preserve exact contracts and non-goals; workers discover
the implementation. For long runs, checkpoint task/repo/requirement identity, accepted units and
candidate evidence, open findings, cumulative repair counts, live processes and next action. After
context loss reconcile actual state before repeating work. No mandatory per-tool ledger.

## Budget and useful parallelism

Start with two useful independent branches when warranted; at most five Smart-owned open threads,
excluding Main, within actual owner/client capacity. Lower caps and unrelated threads bind. Main
may work on a disjoint critical path. No duplicate problem-solving or slot-filling. Direct Main
verifier dispatch is preferred; existing explicitly authorized one-verifier nesting is optional,
never an extra review seat. Read `execution.md` for allocation and native lifecycle details.

Independence includes canonical read/write paths, shared modules, lockfiles, builds, accounts,
databases, servers, ports and browser/desktop state. Whole-tree tests cannot race active writers.
Unknown impact serializes affected work. Test CPU/RAM/process budgets are separate from agent
capacity. One Tester normally coordinates supported runner parallelism; five agents are not five
full suites. Keep actual semantic-review capacity, not a procedural Tester substitute.

Use observed native quota or an explicit work budget when available at useful phase boundaries.
Include committed work and verification; never convert API prices into subscription allowance.
Unknown usage is not free and does not require a routine expensive audit. Low quota narrows
concurrency/optional work; exhaustion checkpoints pending gates rather than lowering quality.
The optional delivery.py adviser uses supplied facts, not live metering or native enforcement.

## Debug and repair without runaway loops

Inspect original failure and controlling behavior before patching. Form a discriminating hypothesis,
use minimal safe evidence, then make the causal fix. Label mitigations and uncertainty honestly.
One evidence-based same-defect correction without progress triggers appropriate Sol/Main diagnosis.
Carry original failure, attempts and previous owner; do not restart the same investigation.

Stop automatic patching after three failed causal fixes for the defect or three repair/re-review
waves for the task, across owner changes. Main reassesses the plan/cause and records a new bounded
approach before resuming; protected changes need approval. A circuit breaker never authorizes
parking a correctness/security/required-gate failure as done. Optional taste is nonblocking from
the start. Keep dependent work blocked while its prerequisite remains unresolved.

## Evidence before completion

Every writer self-checks. Main/Reviewer selects sufficient evidence; Tester executes commands and
returns compact receipts, not coverage judgment. Use focused checks during iteration, complete
required gates on stable integrated inputs, and applicable existing receipts instead of duplicate
suites. Mandatory fresh/full tests win. No fake RED, deleted useful code, weakened assertions or
unexplained green reruns. Read `testing.md` and `verification.md` when needed.

Independent semantic review covers original requirements plus complete bounded diff: spec
compliance and technical quality in one pass. Same-reviewer correction review covers the entire
delta and affected dependencies against a recorded baseline. New reviewer, changed contract,
missing baseline or unknown impact requires full bounded review. Main examines actual visual evidence and consequential risks without repeating all technical investigation.

Before a completion claim, bind it to the actual candidate, decisive logs/exit statuses and
fulfilled requirements. Test pass is not build, deployment, visual approval or installation
activation. UNVERIFIED and STALE never become PASS through confidence or budget exhaustion.
Release holds before repair, refresh affected proof, preserve unresolved findings and separate
acceptance from commit/merge/deploy authority. Review packet/candidate helpers do not prove truth.

## Daily operation and release

Read only needed context/guides. Use supported notifications or long interruptible waits after
assigning ready work. No acknowledgement messages, duplicate tests or unfinished-diff scans just
because a wait returned. Honor real user interruptions. Preserve results/resources, close completed
owned children leaves-first and rely on slots only after observed state change. Never close
unrelated/active workers, raise owner limits, delete useful evidence or auto-restart Main.

For non-code work use domain-appropriate evidence, not invented code tests. Operate without recurring installer checks, model research or workflow retuning. Do not install/run Superpowers alongside
Smart as a second orchestration layer; keep its techniques as these integrated guides. No telemetry,
new daemon or automatic plugin removal. Owner/project, approval, no-agent and read-only rules bind.
