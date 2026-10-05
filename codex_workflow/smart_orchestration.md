# Smart Orchestration 3.1

Optimize accepted quality, elapsed time and total model work, including handoffs, reasoning,
failed attempts and review. Cheap tokens alone are not the objective. One adaptive loop:
understand, choose ownership, execute independent work, verify, accept. No manager layer.

## Judgment and useful delegation

Main owns product meaning, architecture, UX/visual direction and final acceptance. Main may
implement an already-understood small change when delegation costs more than it saves, or
own context-heavy critical-path work. Do not build a team for a typo. Delegate coherent work
that saves substantial effort, isolates noisy output or can run usefully in parallel.
Do not solve the whole patch first and then ask a worker to paste it.

Give the outcome, non-goals, protected decisions, references, read/write scope, dependencies,
resources, authority and decisive checks. The worker chooses implementation within that contract.
Main can make a small correction after explicit ownership transfer and evidence refresh.
Required independent review applies equally to Main-authored changes.

## Intelligence allocation

| Responsibility | Named preset |
| --- | --- |
| Main judgment, direct fixes, acceptance | Owner-selected; GPT-6.1 Sol Medium baseline |
| Ordinary implementation and bounded unknown bugs | routine_executor / GPT-6 Luna Max |
| Moderate complexity, adaptive tools, bounded escalation | default_executor / GPT-6.1 Sol Low |
| Deep implementation or multi-component diagnosis | deep_executor / GPT-6.1 Sol Medium |
| Serious complexity, critical-risk implementation | senior_executor / GPT-6.1 Sol High |
| Independent ordinary semantic review | reviewer / GPT-6 Luna Max |
| Deep or critical-risk semantic review | senior_reviewer / GPT-6.1 Sol High |
| Approved test execution and reporting | tester / GPT-6 Luna Medium |
| Bounded causal investigation | investigator / GPT-6 Luna Max |
| Known GUI recipes and extraction | simple_executor / GPT-6 Luna Max |
| Exact lookup / authorized checkpoint | companion / Luna Max; archivist / Luna Max |

Luna Max is the ordinary delegated baseline, not a claim of universal superiority or guaranteed
savings. A locally reproducible unknown bug can start there. Broad uncertainty, weak observability,
security/payment/data-integrity exposure, novel architecture and difficult cross-system behavior
justify starting directly with Sol. Sol Low is the middle lane, not an obligatory stop before
Medium or High. Max is an effort setting, not a different model or a permission to overthink.
Support roles are on demand; these presets do not imply a standing eleven-agent team.

Settle product/architecture/contract ambiguity in Main first. Escalate protected choices as
DECISION_NEEDED with evidence and bounded options; ordinary technical decisions stay local.
After one evidence-based correction of the same defect without progress, transfer to an
appropriate Sol owner with the original failure, attempts and remaining hypotheses. Do not
traverse every effort level, duplicate investigation or keep retrying until something passes.
Routine compile errors with progress do not require a new model.

Read exact named role configuration and verify actual native model/effort availability. No
silent max-to-xhigh substitution, hidden downgrade, automatic Fast/Astra routing or per-spawn
option invented from prose. Preserve explicit settings and disclose an unavailable preset.

## Useful parallelism

Start with two useful independent branches when available; use up to five Smart-owned open
threads only when work and actual capacity justify them. Main is excluded. Lower owner caps
and unrelated open threads bind. Main may work on a disjoint critical path. Do not wait for a
whole batch when one completed result unblocks useful work; do not fill slots for their own sake.

Independence includes canonical workspaces, read/write dependencies, lockfiles, shared modules,
build inputs, accounts, servers, ports, databases and browser/desktop sessions. A write conflicts
with another owner's reads or writes. Unknown impact serializes the affected work. An immutable
isolated preview can overlap another implementation; whole-tree tests cannot race active writers.
Budget CPU, RAM and test-runner processes separately: five agents do not mean five full suites.
Read `execution.md` for scope, review-reservation and lifecycle details.

## Testing and semantic review are different

Every writer self-checks. Use `tester` to own long/noisy approved commands, their waits and compact
receipts. Main or the semantic reviewer chooses sufficient gates; Tester does not decide that
coverage is adequate. Read `testing.md`. Focused checks support iteration; execute required full
suites on a stable integrated candidate. Reuse an applicable verified run instead of asking
writer, Main and reviewer to launch it again. Required fresh/full gates override reuse.

Independent Reviewer is required for explicit gates or meaningful behavior/integration risk;
Senior Reviewer covers critical or deep semantic risk. Low-risk reversible copy/style edits
with decisive checks need not create a reviewer or Tester. A green suite is not semantic sign-off.
Test design and causal failure investigation belong to Luna Max or an appropriate Sol preset,
not the procedural Tester. No weakening tests, snapshot acceptance or production repair by Tester.

Initial independent review reads original requirements and the entire bounded diff without
writer reasoning/history. Same-reviewer correction checks may use the complete delta from a
recorded baseline, affected dependencies and original findings. New reviewer, changed contract,
unknown impact or missing baseline requires full bounded review. Include Main and concurrent
changes. Main inspects actual visual evidence and consequential risks without repeating all
technical investigation. Read `verification.md`, `design.md` and `browser.md` only when relevant.

## Evidence, waiting and recovery

Original results outrank summaries. Missing proof is UNVERIFIED; affected drift makes evidence
STALE. Preserve raw logs, real exit codes, candidate identity and unresolved failures. Hold
source/config/build/target stable during review; release before repair and refresh affected gates.
Optional consistency helpers are not native locks, authenticated evidence or deployment approval.
No mandatory database, per-tool ledger or preflight ceremony.

Use completion notifications or supported long interruptible waits after useful ready work is
assigned. No acknowledgement messages or repeated unfinished-diff scans after a timeout.
Workers own command waits; never restart a still-running suite. Honor actual user interruptions.

Persist results, settle writes and transfer resources, then close completed owned children
leaves-first with native operations. A final message is not a freed slot. At capacity failure
reconcile once and retry only after observed state change. Never close unrelated/active agents,
raise owner caps or auto-restart Main. Preserve a correction capsule before releasing context.
If required review cannot run safely, checkpoint rather than waive it. Acceptance, commit and
deployment are separate authorities. Owner/project, no-agent, read-only and approval rules bind.
