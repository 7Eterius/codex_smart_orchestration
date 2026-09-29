# Smart Orchestration 2.5

**GPT-6.1 Sol judges. Luna implements, operates and repairs.**

Smart is a global Codex workflow for getting more satisfactory work from a limited
allowance. Main retains product, architecture, UX, visual decisions, detailed assessment
and final acceptance. Named economical workers execute settled work, including small
edits and main's corrections. Slower execution is acceptable; weaker design judgment is not.

There is **one adaptive execution loop**, no Normal/Coordinated modes and no dedicated
Chunk Lead. The workflow is an instruction policy with small deterministic helpers,
not a native scheduler, tool interceptor, security boundary or guaranteed saving.

## What changes in 2.5

The recommended Main baseline becomes **GPT-6.1 Sol Medium**. The installed Senior role
uses **GPT-6.1 Sol xhigh**. All seven Luna role settings remain unchanged.

The other changes focus on avoidable supervision rather than adding another agent layer:

- Give assignments explicit events that require main's attention.
- Do not turn a wait timeout into a progress message, another inspection or a test rerun.
- Count the two-thread Smart budget across the entire run, not separately per assignment.
- Reuse a writer through corrections, but retire accumulated investigation at accepted
  milestone boundaries and preserve a compact handoff.
- Expose the recommended parent and any on-disk mismatch in configuration assessment,
  without silently replacing owner settings or claiming live model selection.

The release preserves the design loop, independent verdicts, candidate holds, required
fresh checks, native thread release and exact install/rollback protections.
See [2.5 notes](docs/v2.5.md).

## Architecture

```text
USER
  |
  v
MAIN: GPT-6.1 Sol Medium recommended; owner selection preserved
  goal, product meaning, architecture, UX/visual decisions
  protected brief, acceptance criteria, authority
  detailed inspection of real results, final acceptance
  |
  | one complete bounded assignment
  |
  +--> SIMPLE / Luna Low
  |      established low-risk edits, exact extraction,
  |      complete mechanical browser/GUI journeys
  |
  +--> ROUTINE / Luna High
  |      normal implementation of settled requirements/design,
  |      scoped discovery, commands, self-checks, ordinary repairs
  |
  +--> DEFAULT / Luna xhigh
         genuinely deep bounded implementation/diagnosis
           |
           +--> TESTER / Luna High when independent review is required
                   authoritative requirements, stable candidate,
                   actual diff and behavior, separate verdict
           |
           v
       candidate + original evidence + remaining gates
           |
           v
MAIN examines decisive changes and actual visuals
  |
  +--> findings --> same suitable Luna owner --> fresh evidence --> MAIN
  |
  +--> acceptance --> durable handoff --> observed native release
```

Main may dispatch Tester directly, or explicitly authorize Routine/Default to dispatch
one Tester when native nesting, permissions and capacity support it. Only the dispatcher
changes, not the independent reviewer or its contract. Missing nesting does not justify
main taking implementation back.

Support roles answer bounded questions or create authorized checkpoints. They are not a
permanent team and do not multiply the run's thread budget.

## Responsibilities and model map

| Responsibility | Role | Configured model / effort |
| --- | --- | --- |
| Product, architecture, UX/visual judgment and acceptance | Main | Owner-selected; **GPT-6.1 Sol Medium** baseline |
| Explicit low-risk operation or established small edit | `simple_executor` | GPT-6 Luna Low |
| Normal settled implementation and repair | `routine_executor` | GPT-6 Luna High |
| Deep bounded implementation or diagnosis | `default_executor` | GPT-6 Luna xhigh |
| Independent diff/contract/behavior verification | `tester` | GPT-6 Luna High |
| Requested hard advisory judgment | `senior_executor` | **GPT-6.1 Sol xhigh** |
| Targeted context question | `companion` | GPT-6 Luna Medium |
| Deep unresolved evidence question | `investigator` | GPT-6 Luna xhigh |
| Grounded milestone handoff | `archivist` | GPT-6 Luna Medium |

Routine is the settled implementation default. Default needs a real depth reason, not a
large file count or slow tools. Simple can own a long known journey when intent, target
and expected observations are explicit. Novel shared state, security, payments, schema
invariants and unresolved design are not low-risk edits simply because the patch is short.

Senior is advisory-first. Main considers its decision/rationale/constraints/next action,
settles the decision and returns implementation to Luna. Transferred Senior implementation
requires an explicit ownership transfer for an evidenced capability gap or inseparable
judgment/implementation, with independent review. Max/Astra are not automatic tiers.

## Main owns judgment, not routine execution

Main defines the outcome and protected decisions, resolves ambiguity, selects the execution
owner and review checkpoint, and inspects enough source and product evidence to decide.
It directly reviews consequential changes and real visuals. It does not rubber-stamp a
worker's confidence or a PASS summary.

After the contract is settled, the worker owns implementation and ordinary repairs.
Main does not make a quick CSS patch, implement alongside an active writer, or write a
complete solution for Luna to paste. A small diff, familiarity or faster direct execution
is not sufficient reason to abandon delegation.

Main can answer directly, author authorized briefs and inspect decisive evidence. An
explicit no-agent request remains binding. A verified tool or permission boundary can
justify a narrowly authorized main-only bridge action; state that boundary once and
return the remaining work to the worker. Never invent access or widen permissions.

## The assignment contract

Give a complete bounded job rather than one worker per file or click. The existing capsule
contains the outcome and stop condition, unit/attempt, exact requirements, owned/protected
paths, starting candidate/target, authority, gates, evidence locations and absolute relevant
guide paths. Design work adds main's accepted brief and a review checkpoint.

The capsule also names the events that require main: **review-ready, completed,
decision-needed, blocked, or a real user interruption**. The worker owns running commands,
test waits, browser operation and ordinary diagnosis within that contract.

A finite coherent group may share setup and contracts but retains per-member gates and
dependency order. Do not extend it simply to keep a worker busy. Workers report missing
product/design/architecture decisions before inventing them; main sends a contract delta.

## Detailed UI/UX workflow

Design authorship remains with main. Implementation delegation is not delegation of visual
judgment. The [design guide](codex_workflow/design.md) specifies the complete loop.

### Main settles the brief

Main uses accepted references and actual product evidence to define purpose, hierarchy,
composition, visual language, responsive intent, interactions and important states.
The brief records protected decisions, relevant components/tokens, concrete acceptance
criteria, required viewports and the next review point. It does not prescribe every CSS
property or solve the implementation in advance.

### Luna builds and returns running evidence

Routine normally implements the accepted design; Simple handles an established low-risk
tweak. The capable owner runs appropriate checks and returns the current candidate/build,
state, viewport/theme and original evidence references. An absent browser capability is
a limitation, not permission to claim a visual pass.

### Main examines the actual result

For new compositions, main inspects an early running frame and the final affected screens.
It evaluates hierarchy, typography, spacing, alignment, interaction states, responsiveness
and consistency at the level the brief requires. Passing tests and the mere presence of
screenshots do not replace opening and assessing the evidence.

### Findings return to the worker

Main groups related findings into one concrete correction assignment:

```text
Criterion / finding
Expected versus observed
Exact state and evidence
Allowed change and protected decisions
Affected checks and required fresh visual evidence
```

For example: restore the accepted heading scale at mobile width so it no longer overlaps
the cover, without changing card hierarchy; return that state and the relevant regression
check. This is not a vague request to make the design better.

The same suitable worker implements the delta. Release any independent-review hold before
repair, identify the new candidate, and refresh affected and mandatory-fresh checks. Main
inspects the corrected evidence before closing findings. Missing evidence remains open.
The loop stops when the authorized quality target and gates are satisfied, not when a
fixed delegation percentage is reached and not after unlimited out-of-scope polish.

## Browser and Computer Use

**Operating a GUI and judging its design are different responsibilities.**
Simple Luna Low owns worthwhile, explicit low-risk journeys: page extraction, known GUI
configuration, checklist execution and screenshot collection. Main makes aesthetic and
interaction decisions. A long journey can still be simple; a single consequential click
can still require authority and stronger verification.

Check actual worker tool and session access. Use structured DOM/network/console/API evidence
where sufficient, a real browser for required rendered journeys and Computer Use for native
or GUI-only behavior. Do not substitute an API response for a required interaction test.

Reuse verified sessions, builds and setup. One owner controls shared mutable GUI state.
For repeated stable local checks, reuse an existing deterministic test or verified recipe
with fresh execution instead of reasoning through every click again. Capture requested
changed/final/failure states, not an unneeded image after every action.

A capable implementation owner can collect short evidence without an extra relay agent.
For a separate substantial mechanical journey, transfer GUI ownership safely and use
Simple. Explain an observed capability exception rather than leaving all browser operation
with main by habit. See [browser economy](codex_workflow/browser.md).

## Waiting without expensive supervision loops

The parent should not manufacture a new task each time a tool returns a wait timeout.
Use native completion notification or a supported long, interruptible wait. Choose
parameters from the exposed tool schema; Smart does not invent a universal timeout API.

A timeout alone is not a failure, evidence change or reason to SEND a progress request,
list all agents, inspect unfinished files, reload the page or rerun tests. Continue
supported waiting without duplicating those operations. Clients limited to polling should
back off within their supported limits, not run rapid model turns or shell sleep loops.

Investigate a real blocker, error, missed authorized checkpoint or an explicit fresh-status
request. Honor user interruptions promptly. Ordinary status uses last-known state; an
explicit fresh snapshot is one coalesced active-owner request, not a chain of leaf queries.
Required user-facing progress can still be reported without creating new investigation.

Main's review of an early design frame is intentional judgment, not unwanted supervision.
The goal is fewer empty coordination turns, never less attention to the finished product.

## Independent verification and candidate holds

Every owner self-checks. Tester is required by project/owner gates or meaningful residual
risk, including behavior/state, integration, shared contracts, uncertain accessibility,
authentication, payments, schema or financial invariants. Default implementation requires
independent review by default. A reversible established copy/style edit does not gain a
second reviewer merely because it touches UI.

Tester derives expected behavior from authoritative requirements, reviews the actual diff
and consumers, and executes the required checks. It owns a separate verdict artifact.
The writer may reference that verdict, not rewrite it or turn self-checks into independence.

Identify relevant source, staged/unstaged/untracked files, test/config/lockfile inputs and
the actual served build/target/account. Hold those inputs stable through independent review.
The hold is an ownership agreement, not a filesystem lock. Release before repair, re-hold
the repaired candidate, then rerun affected plus mandatory-fresh checks. Retain unrelated
applicable evidence. Preserve original failures and distinguish executed, reused, failed,
blocked, unrun, deferred and authorized not-applicable results.

Main examines applicability, decisive risks and actual visuals without routinely repeating
the full technical investigation. Technical approval, main acceptance, owner sign-off,
commit, integration and release are separate. See [verification](codex_workflow/verification.md).

## Thread capacity and lifecycle

Smart targets **at most two Smart-owned open threads across the entire run**, normally one
owner and one independent reviewer. Descendants, support workers and unfinished previous
units count in the same budget. It is not two per parent or per assignment. Lower client
limits and unrelated open threads remain binding.

A completed response is not observed native slot release. Preserve results and resource
handoffs, close eligible completed owned direct children with supported native operations,
leaves before parent, and observe the result before relying on reclaimed capacity.
Retain a writer for concrete pending main review/corrections, not indefinite possible work.

On a capacity error reconcile the relevant known handles once. Retry only after an
observed state change. With one available slot and verified release, serialize writer,
independent Tester and any replacement writer using durable evidence. Otherwise checkpoint;
do not raise the cap, blindly respawn, close unrelated/active work or move execution to main.

Closing a thread does not authorize deleting source, browser profiles, servers, logs or
unique evidence. See [execution and lifecycle](codex_workflow/execution.md).

## Context lifecycle

Reuse the same suitable worker through a concrete correction loop. At an accepted milestone,
preserve an authorized compact handoff: accepted decisions, candidate/target, gate outcomes,
open findings, next work and resource ownership. Give a new contract a fresh bounded worker
after safe release rather than appending unrelated work to an ever-growing thread.

Fresh context is not fresh infrastructure. Preserve applicable browser/server setup and
run recipes. After compaction consult the current handoff and changed inputs instead of
re-reading the archive. A parent-session transition must be explicit; Smart never restarts
the app, forces compaction or discards an active conversation automatically.

Follow-ups carry deltas, logs stay in artifacts and only relevant guides are loaded. These
are cost controls, not a guarantee about exact context size or cache behavior.

## Configuration and activation

Select **GPT-6.1 Sol / Medium** for Main in the client's supported model selector when
available. Senior's installed TOML explicitly selects **gpt-6.1-sol / xhigh**. The installer
preserves existing explicit parent, profile, Plan effort and generic-child selections.
It does not silently move a running conversation to the new model.

The disk check's configuration assessment reports `configured_parent`, `recommended_parent`
and `parent_baseline_status`. A match describes the supplied disk configuration, not
observed live model selection. A different valid owner selection is a warning, not corruption.
Known unsupported `none`/`minimal` efforts for GPT-6.1 Sol are rejected rather than silently
rewritten. Profile overrides and account/model availability still require actual client evidence.

No new model-catalog override, permissions, agent concurrency settings or orchestration mode
is installed. Main-only tool boundaries and explicit user instructions remain authoritative.
See OpenAI's [model contract](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
and [subagent configuration](https://developers.openai.com/codex/subagents).

## Installation or update

Open Codex in your project directory and send:

```text
Install Smart Orchestration from https://github.com/7Eterius/codex_smart_orchestration. Resolve the current HEAD commit SHA of main and download/extract that exact source snapshot outside my projects. Do not use GitHub Releases or historical dist archives. Read codex_workflow/operate/smart_install.md. With Python 3.11+, run codex_workflow/runtime/smart_install.py --package-root codex_workflow without --apply first and inspect the preview. If clean, run the same command with --apply, then --check. Preserve unrelated Codex configuration and every project file. Stop on conflicts, never force changes. Do not quit, relaunch or wait for Codex to exit. Report version, source commit, fingerprint, backup and disk result; tell me to restart Codex manually. A disk check is not live runtime proof.
```

After success, restart Codex manually and start a fresh conversation. Select the new Main
baseline explicitly; inspect any preserved override before changing it. There is no
per-project installation, uninstall-first requirement or general qualification ceremony.
Use [targeted runtime checks](codex_workflow/runtime_check.md) only for an actual uncertainty.

The package installs its declared guides, eight worker definitions, managed instruction
regions and Python runtime helpers. It preserves unrelated configuration and project files,
stops on ownership conflicts, and creates exact conflict-checked rollback backups. Source
publication does not update your Mac automatically.

## Validation and evaluation

```bash
python3 -B -m unittest discover -s scripts -p 'test_*.py' -v
python3 -m compileall -q codex_workflow scripts
```

CI runs Ubuntu/Python 3.11, Ubuntu/Python 3.12 and macOS/Python 3.12 with full Git history.
It retains historical installation tests and checks exact 2.4 -> 2.5 -> no-op reapply ->
rollback, preserved owner settings, the authorized Senior model change, baseline assessment,
prompt budgets and run-wide capacity behavior.

These tests validate shipped instructions, helpers and installation. They do not establish
native runtime compliance, design quality or measured savings. Main still judges the work.
The helpers check supplied observations; they are not native locks or authenticated telemetry.

For usage analysis, keep primary session totals and separately reported carry-in workers
explicit, avoid adding overlapping inclusive subtrees, and distinguish tokens from quota.
Unknown role/assignment metadata is not missing work. Wait counts and overlapping lifetimes
are investigation signals, not proof of wasted requests or live slot occupancy.

Compare similar accepted outcomes including setup, Main review, verification and rework.
Do not pursue a delegation percentage at the expense of judgment. Public API-equivalent
prices are useful normalization, not subscription accounting. No fixed savings percentage
or number of working days follows from this release.

## Documentation

[Main policy](codex_workflow/smart_orchestration.md) ·
[Design](codex_workflow/design.md) ·
[Execution](codex_workflow/execution.md) ·
[Verification](codex_workflow/verification.md) ·
[Browser](codex_workflow/browser.md) ·
[Boundary records](codex_workflow/boundary.md) ·
[Runtime checks](codex_workflow/runtime_check.md) ·
[Engineering notes](docs/smart_orchestration.md) ·
[2.5 notes](docs/v2.5.md) ·
[Evaluation](docs/evaluation.md)
