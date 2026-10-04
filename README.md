# Smart Orchestration 3.0

**Solve with intelligence. Delegate when it helps. Run independent work in parallel.**

Smart is a global Codex workflow for balancing response time, model usage and accepted quality.
Main retains product, architecture, UX/design judgment and final acceptance. Unlike 2.x, it
can finish small tasks itself. GPT-6.1 Sol handles normal problem-solving; Luna handles known,
prescribed work where its lower price is actually useful.

The workflow is instructions plus bounded deterministic helpers, not a native scheduler,
permission system or guarantee of savings. Actual tools, model availability and owner settings bind.

## What changes in 3.0

The 2.7.1 design deliberately traded latency for cheap delegation. That is no longer the goal.
Mandatory handoffs for tiny edits, a two-thread policy ceiling and Luna as the ordinary coding
lane could make inexpensive individual calls an expensive and slow overall task.

| Responsibility | 2.7.1 | 3.0 |
| --- | --- | --- |
| Small understood fix | Mandatory worker handoff | Main can finish directly |
| Ordinary implementation / unknown bug | Routine Luna High | Main or Default Sol Medium |
| Deep implementation | Default Luna xhigh | Sol Medium first; Senior Sol xhigh for demonstrated depth |
| Independent semantic review | Luna High | Sol Medium, only when risk or explicit gates require it |
| Causal investigation | Luna xhigh | Sol Medium |
| Known extraction / GUI recipe | Luna Low | Luna Low, in coherent batches |
| Prescribed bulk transformations | Luna High | Luna High, explicitly bounded |
| Open Smart worker budget | Two across the run | Up to four with verified independence and actual capacity |
| Main during worker execution | Mainly waits | Can work on a disjoint critical path |

No new manager or role is introduced. Stronger models have higher token prices; fewer calls or
repairs may offset them, but that is a hypothesis to measure, not a promised cheaper bill.

## Architecture

```text
USER
  |
  v
MAIN: owner-selected model, GPT-6.1 Sol Medium recommended
  product / architecture / UX / visual judgment
  small direct fixes and context-heavy critical-path work
  final assessment and acceptance
  |
  +--> DEFAULT: Sol Medium
  |      coherent feature, unknown bug, adaptive browser work
  |
  +--> SIMPLE / ROUTINE: Luna Low / High
  |      known recipe, extraction, prescribed transformation
  |
  +--> Independent work starts concurrently where safe
         distinct read/write scopes, accepted dependencies, resources
         initial two useful branches, at most four open Smart threads
                |
                v
         stable candidate + decisive evidence
                |
                +--> TESTER: Sol Medium, when independent review is required
                |      may overlap another isolated implementation
                v
MAIN examines actual result and required visuals
  corrections: same suitable owner, or a small direct fix after ownership transfer
  accept -> preserve evidence/resources -> observe native thread release
```

A short task should not automatically create a writer, a reviewer and a handoff record.
A complex task should not automatically be forced through several cheap-model failures.
Main chooses the least complicated ownership structure that can deliver the accepted outcome.

## Roles and intelligence

| Role | Configured model / effort | Intended work |
| --- | --- | --- |
| Main | Owner-selected; GPT-6.1 Sol Medium baseline | Decisions, direct small tasks, critical path, visual judgment and acceptance |
| `default_executor` | GPT-6.1 Sol Medium | Normal problem-solving, implementation, difficult diagnosis and adaptive tools |
| `senior_executor` | GPT-6.1 Sol xhigh | Deep bounded advice or explicitly transferred implementation |
| `tester` | GPT-6.1 Sol Medium | Independent semantic review and required gates |
| `investigator` | GPT-6.1 Sol Medium | Causal investigation and uncertain evidence |
| `simple_executor` | GPT-6 Luna Low | Known GUI journeys, exact extraction, established low-risk off-path edits |
| `routine_executor` | GPT-6 Luna High | Prescribed repetitive implementation, not general problem-solving |
| `companion` | GPT-6 Luna Medium | Exact bounded lookup |
| `archivist` | GPT-6 Luna Medium | Authorized compact checkpoint memory |

Role names are retained for installation compatibility, but **Routine is no longer the normal
coding lane**. Normal implementation belongs to Default or Main.

Luna is appropriate when the recipe, pattern and success condition are clear. A small function
with an unknown causal defect can still require Sol. A twenty-step browser recipe can remain
Luna work. A novel dashboard, confusing GUI state or unfamiliar API is not cheap work merely
because the patch or click count is small.

### Why not Luna Max everywhere?

Higher reasoning effort is not a substitute for selecting the right model family. Luna Max
remains an owner-selected experiment for well-specified work, not the default difficult-work
lane and not a compulsory step before Sol. Start with Sol Medium for actual problem-solving;
use Senior xhigh when observed depth justifies it. There is no automatic Fast/Astra/Max ladder.

## Direct execution without losing judgment

Main may implement an already-understood small task or context-heavy critical-path fix when a
handoff would cost more than it saves. It still self-checks and observes all risk-based gates.
Main can also handle a small review correction, but not while another writer owns the same inputs.

Delegate when a task is large enough to benefit from a separate owner, keeps noisy tool output
out of Main, or can run usefully in parallel. Give the outcome and constraints rather than
pre-writing a patch for a worker to paste. The implementation owner chooses the technical solution
inside the accepted design and contract.

If the same defect survives one evidence-based repair with no progress, or a worker cannot
diagnose it, stop the cheap loop. Main or Sol examines the original failure and takes ownership
as appropriate. Ordinary compile errors do not require escalation. Increasing effort through
Low, High, xhigh and Max by ritual is not a recovery plan.

## Safe parallelism, not fan-out for its own sake

Dispatch ready independent work before waiting. Begin with two useful branches; use up to four
Smart-owned open threads only when the work, model allowance and client capacity justify them.
The primary thread is excluded. Existing lower caps and unrelated open threads count.

Parallelism requires more than different filenames. Identify canonical workspaces, read and
write sets, dependencies and shared mutable resources. A write conflicts with another owner's
reads or writes. Shared styles, lockfiles, builds, test accounts, servers, ports, browser sessions
and the desktop mouse can couple apparently separate assignments.

Main may work in parallel too, but its activity belongs in the same conflict check. Unknown
impact serializes the affected work rather than inventing isolation. An isolated immutable
preview can be reviewed while another scope changes. A test against the mutable whole tree
cannot safely ignore active writers just because the test process is read-only.

Do not wait for the slowest worker before using an independent completed result. Pipeline
ready review and integration points. Share one future reviewer slot rather than reserving one
unused slot per writer: a preserved capacity of three can support two independent writers and
one reviewer, when their actual scopes and resources allow it.

The optional [allocation protocol](codex_workflow/execution.md) checks supplied scopes,
accepted dependencies, Main activity, reservations and native lifecycle observations. It does
not discover dependencies, authenticate scopes, lock files, spawn agents or change capacity.
Unscoped legacy records do not gain unproven parallelism.

## Design and browser work

Main still defines product meaning, hierarchy, composition, interaction, visual language and
responsive intent. Sol realizes nontrivial designs; Luna applies settled repetitive details.
Main inspects the actual rendered result, not a worker's assurance or the existence of screenshots.

Use an early running frame for a genuinely new composition or uncertain direction. An established
spacing or copy correction can go straight to the relevant final visual check. Group related
findings, correct through the same suitable owner where useful, and stop at the accepted quality
level instead of generating endless optional polish.

For browser work, distinguish operation from judgment. Simple handles known low-risk recipes
and extraction. Sol handles unknown states, investigation or adaptation. Reuse valid sessions,
builds and existing deterministic tests. A substantial repeatable journey can be one assignment;
a worker per click adds overhead. Different agents never share an uncontrolled desktop or mutable
browser session. Billing, permissions, destructive actions and production retain approval gates.

See [design](codex_workflow/design.md) and [browser work](codex_workflow/browser.md).

## Review and evidence

Every writer self-checks, including Main. Add independent Tester for explicit requirements or
meaningful behavioral, integration, security, payment, schema and data-integrity risk. The Default
role now means normal implementation, so its name alone no longer requires maximum verification.
A reversible established copy/style change with decisive checks does not automatically need Tester.

Initial review uses the original requirements and complete bounded diff in an independent context.
The same reviewer can inspect the complete correction delta, affected dependencies and original
findings against a recorded reviewed candidate. New reviewer, changed contract, unknown impact
or missing baseline requires a full bounded review. All mandated fresh/full tests remain binding.
Include Main-authored fixes and any concurrent changes in the reviewed delta.

Main may be the writer, but never its own independent reviewer. The boundary helper now supports
that distinction. Holds, separate verdicts and all required evidence still apply. Freeze the
reviewed source/config/build/target; release before repair and refresh affected evidence.

Keep original logs and exit codes. UNVERIFIED and STALE never silently become PASS. Required tests
run regardless of whether an optional adversarial probe found a suspected bug. The unchanged
[preflight helper](codex_workflow/challenge.md) remains optional for existing structured facts;
do not create a ledger simply to run it. CLEAR is not truth, approval or permission to deploy.

See [verification](codex_workflow/verification.md) and [boundaries](codex_workflow/boundary.md).

## Context, waiting and lifecycle

Read applicable instructions and known sources directly. Use targeted search/indexes to locate
unknown material. Do not front-load every guide or the entire Main transcript. A bounded brief
contains the outcome, protected decisions, useful references, scope/resources and decisive checks.
Worker questions go to Main only when they require protected judgment or authority.

Use supported completion notifications or long interruptible waits after dispatching useful
independent work. A timeout is not a new task: no repeated progress messages, unfinished-diff
inspections or duplicate checks merely because waiting returned. User-facing updates use known
state and actual interruptions remain binding.

Persist results, settle writes, transfer resources and close completed owned threads using native
operations, leaves before parent. A final message is not a freed slot. Never close unrelated or
active agents. On a capacity error reconcile once, retry only after observed change and respect
lower owner limits. Without a safe independent-review path, checkpoint rather than omit the gate.
New tasks get fresh bounded context, not needless reinstall/login/rebuild. Never auto-restart Main.

## Installation or update

Open Codex CLI or the Codex app and send:

```text
Install Smart Orchestration from https://github.com/7Eterius/codex_smart_orchestration. Resolve the current HEAD commit SHA of main and download/extract that exact source snapshot outside my projects. Do not use GitHub Releases or historical dist archives. Read codex_workflow/operate/smart_install.md. With Python 3.11+, run codex_workflow/runtime/smart_install.py --package-root codex_workflow without --apply first and inspect the preview. If clean, run the same command with --apply, then --check. Preserve unrelated Codex configuration and every project file. Stop on conflicts, never force changes. Do not quit, relaunch or wait for Codex to exit. Report version, source commit, fingerprint, backup and disk result; tell me to restart Codex manually. A disk check is not live runtime proof.
```

After successful preview/apply/check, restart Codex manually and start a fresh conversation.
Use the supported selector to choose the recommended Main model. Installing a recommendation
does not switch an already-running conversation.

**Existing explicit settings are preserved.** An old cap of two or three remains two or three;
3.0 reports that limitation instead of silently increasing it. Named roles explicitly choose
their new models even when an old generic fallback is retained. Fresh installations with no
explicit values receive a four-thread cap and Sol Medium generic fallback. Any deliberate change
to existing capacity, parent/profile/Plan effort, permissions or speed is separate from installation.

Locally customized managed role/policy files cause a conflict, not a forced overwrite. Exact
rollback restores previous bytes/settings while retaining the backup trail. No project bootstrap
or per-project database is required. Python 3.11+ is required.

## Validation and evaluation

```bash
python3 -B -m unittest discover -s scripts -p 'test_*.py' -v
python3 -m compileall -q codex_workflow scripts
```

CI checks Ubuntu Python 3.11/3.12 and macOS Python 3.12. The active tests cover new routing,
parallel read/write/resource conflicts, dependencies, reviewer capacity, native lifecycle,
Main-authored review, evidence gates, installation and exact historical upgrades/rollback.

Obsolete 2.x prompt/model expectations are not retained as assertions about 3.0. Instead the
exact archived 2.7.1 source and its unchanged 309-test suite run separately as a historical
reference. That is not a substitute for tests of 3.0. Core candidate, hardening and release
regressions remain active; current evidence and installer regressions are grouped by behavior.
Git history is required in CI. A source archive without it reports historical tests unavailable,
not passed.

Measure time to accepted result, total model work, correction rounds and required quality on
comparable tasks. Model prices, cached tokens or lower Main share alone cannot measure your
subscription allowance or productive speed. Parallelism can increase simultaneous consumption;
smarter models can still cost more. No benchmark or native-compliance claim follows from CI.

[3.0 review and release notes](docs/v3.0.md) | [Main policy](codex_workflow/smart_orchestration.md) |
[Execution](codex_workflow/execution.md) | [Targeted runtime checks](codex_workflow/runtime_check.md) |
[Engineering notes](docs/smart_orchestration.md)
