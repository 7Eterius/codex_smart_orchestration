# Smart Orchestration 2.7

**GPT-6.1 Sol judges. Luna implements, operates and repairs.**

Smart is a global Codex workflow for getting more satisfactory work from a limited
allowance. Main retains product, architecture, UX, visual decisions, detailed assessment
and final acceptance. Named economical workers execute settled work, including small
edits and main's corrections. Slower execution is acceptable; weaker design judgment is not.

There is **one adaptive execution loop**, no Normal/Coordinated modes and no dedicated
Chunk Lead. The workflow is an instruction policy with small deterministic helpers,
not a native scheduler, tool interceptor, security boundary or guaranteed saving.

## What changes in 2.7

2.7 keeps the model map and delegation architecture, while correcting the new preflight
and borrowing further bounded ideas from [Kiborgik/BlaBla](https://github.com/Kiborgik/blabla).

**Handoff is not acceptance.** A worker can return an evidenced repair for independent review
without pretending the reviewer has already approved it. Addressed findings and gates due
at acceptance stay visibly pending. Main still decides acceptance after all required checks.

**Evidence can be bound to the actual assignment.** Optional attempt/contract/candidate/target
identities make mismatching evidence STALE and absent bindings UNVERIFIED. An optional existing
candidate manifest adds a fresh selected-input read, not proof of a deployed build.

**Preflight gives a useful next step.** It validates the whole record first, batches grounded
issues with bounded output and routes mechanical repairs to workers, protected questions to
Main. It no longer treats malformed later rows or an empty obligation set as acceptable input.

**Main can ask the questions it doubts.** A few named questions in the original assignment
must receive evidence-backed answers or an explicit unknown. This complements worker-initiated
DECISION_NEEDED without relying on self-reported confidence or adding a question to every task.

**Required tests are not optional adversarial probes.** Tester runs mandated gates even when
no defect is suspected, checks real entry points and uses meaningful negative controls for
new critical tests where practical. An observer must report failure truthfully.

Known source paths can be read directly after applicable instructions. Notes or unrelated
changes do not invalidate focused evidence. Full failure logs are retained so a summary line
cannot hide errors and another run is not needed merely to recover discarded output.

No new role, manager, execution mode, task database, model setting or permission is introduced.
See [2.7 notes](docs/v2.7.md) and the optional [preflight contract](codex_workflow/challenge.md).

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
  | optional must-answer questions about specific uncertainties
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
             v
         optional deterministic handoff preflight
         mechanical issues return together to the same owner
         protected questions / scope conflicts return to Main
             |
             v
         TESTER / Luna High when independent review is required
         original task, stable candidate, complete diff,
         required gates and separately owned verdict
             |
             v
MAIN examines decisive changes and actual visuals
  |
  +--> findings --> same suitable Luna owner --> fresh evidence --> recheck
  |
  +--> acceptance --> durable handoff --> observed native release
```

Main may dispatch Tester directly, or explicitly authorize Routine/Default to dispatch
one Tester when native nesting, permissions and capacity support it. Only the dispatcher
changes, not the independent reviewer or its contract. Missing nesting does not justify
main taking implementation back. Support roles answer bounded questions or create authorized
checkpoints; they are not a permanent team or an extra manager layer.

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
Repeated same-defect repairs justify bounded diagnosis and ownership reassessment within
authorized models, not automatic upgrading or endlessly repeating a cheap failed approach.

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
contains the outcome and stop condition, unit/attempt, exact requirements and deliverables,
owned/protected paths, starting candidate/target, authority, gates, evidence locations and
absolute relevant guide paths. Design work adds Main's accepted brief and review checkpoint.
A finite coherent group retains per-member gates and dependency order.

Name the events that require Main: **review-ready, completed, decision-needed, blocked,
required checkpoint or real user interruption**. The worker owns commands, test waits,
browser operation and ordinary diagnosis within the assignment. Do not extend a task simply
to keep an agent busy.

Main can include a few must-answer questions, for example which environment a browser is
connected to or whether a particular edge case is covered. The worker returns an answer
with original evidence, or unknown. Silence does not answer a question. This is not a new
mandatory planning round and does not delegate product choices to the worker.

## Context and protected decisions

Read applicable instructions. When the relevant authoritative source is already known,
read it directly. For an unknown location, use the project's status/index/architecture map
or targeted search, then the relevant identity and specific rule/file/evidence. Progressive
disclosure is not a compulsory status -> explain -> explain ritual for every read.

Do not dump all documentation or the Main transcript into a worker. Reuse existing code,
design decisions and trustworthy setup before inventing another implementation. After
compaction consult the current handoff and changed evidence, not the entire archive.

Workers keep ordinary implementation choices. If continuing would choose protected product
meaning, architecture, UX/visual direction, contract semantics, scope or authority, return:

```text
DECISION_NEEDED
Question
Options, if bounded
Evidence
Why this is outside the settled brief
Provisional choice, if useful
```

Main answers the narrow decision and sends the delta back to the same worker. Smart does
not use numeric confidence thresholds or require architecture essays from bounded workers.

## Detailed UI/UX workflow

Design authorship remains with Main. Implementation delegation is not delegation of visual
judgment. The [design guide](codex_workflow/design.md) specifies the complete loop.

### Main settles the brief

Main uses accepted references and actual product evidence to define purpose, hierarchy,
composition, visual language, responsive intent, interactions and important states.
The brief records protected decisions, relevant components/tokens, acceptance criteria,
required viewports and the next review point. It does not prescribe every CSS property or
solve the implementation in advance.

### Luna builds and returns running evidence

Routine normally implements the accepted design; Simple handles an established low-risk
tweak. The capable owner runs appropriate checks and returns the current candidate/build,
state, viewport/theme and original evidence references. An absent browser capability is
a limitation, not permission to claim a visual pass.

### Main examines and delegates corrections

For new compositions, Main inspects an early running frame and final affected screens.
It evaluates hierarchy, typography, spacing, alignment, interaction states, responsiveness
and consistency at the level the brief requires. Passing tests and attaching screenshots
do not replace opening and assessing the evidence.

Main groups related findings into a concrete correction assignment:

```text
Criterion / finding
Expected versus observed
Exact state and evidence
Allowed change and protected decisions
Affected checks and required fresh visual evidence
```

For example: restore the accepted mobile heading scale so it no longer overlaps the cover,
without changing the card hierarchy; return the corrected state and relevant regression check.
This is not a vague instruction to make the design better.

The same suitable worker implements the delta. Release any review hold before repair,
identify the new candidate and refresh affected and mandatory-fresh checks. The worker marks
the finding addressed with evidence; Main/reviewer resolves it after recheck. Missing evidence
stays open. An accepted design violation is a legitimate blocker; optional taste or unrequested
polish is not. Stop when the authorized target and required gates are satisfied.

## Browser and Computer Use

**Operating a GUI and judging its design are different responsibilities.**
Simple Luna Low owns explicit low-risk journeys: page extraction, known GUI configuration,
checklist execution and evidence collection. Main makes aesthetic and interaction decisions.
A long journey can be simple; a single consequential click can require explicit authority.

Check actual worker tools and session access. Prefer structured DOM/network/console/API
readback where sufficient, a real browser for required rendered journeys and Computer Use
for native or GUI-only behavior. Do not replace a required interaction test with an API result.

Reuse verified sessions, builds and setup. One owner controls shared mutable GUI state.
For repeated stable checks, reuse an existing deterministic test or verified recipe with
fresh execution instead of reasoning through every click again. Capture useful requested,
changed/final/failure states, not an unneeded screenshot after every action.

A capable implementation owner can gather short evidence without an extra relay agent.
For a separate substantial mechanical journey, transfer GUI ownership safely to Simple.
Explain an observed capability boundary rather than leaving all operation with Main by habit.
Billing, production, permission changes and destructive actions retain their authority gates.
See [browser economy](codex_workflow/browser.md).

## Optional deterministic preflight

Use [challenge.md](codex_workflow/challenge.md) only when structured handoff facts already
exist. Do not create a project database or mandatory ledger to feed it. The helper is not
an LLM, scheduler or semantic reviewer.

### Handoff and acceptance are different stages

At **handoff**, an addressed finding needs current evidence but remains pending independent
resolution. Gates explicitly assigned to **acceptance** remain visible as pending, allowing
the required reviewer to be dispatched. At acceptance, all required gates and blocking
findings must actually be satisfied. Main owns acceptance; a worker cannot change obligations
to make its own record clear. An honest BLOCKED handoff does not need a CLEAR result.

These stages are not Normal/Coordinated modes or competing architectures. Legacy records
without a phase retain strict acceptance behavior.

### Identity, batching and limits

The helper checks bounded supplied scope/attribution, decisions, deliverables, findings,
questions and gate facts. Optional current attempt/contract/candidate/target identities
require matching evidence references/bases. Missing binding is UNVERIFIED; mismatch is STALE.
Without current identity, output says binding was not checked.

Optional `--manifest` reads an existing candidate.py manifest and freshly verifies the
selected local inputs. Its fingerprint must identify the declared candidate. This does not
prove a served build, external state, complete dependencies, authorship or continuous locking.
No new source scanner is added.

Output contains a leading issue plus up to eight issues, total/omitted counts, pending
obligations and a next action. Batch mechanical repairs back to the current worker rather
than one model round-trip per bookkeeping error. Scope/attribution conflicts and protected
questions go to Main without destructive resets or invented concurrent attribution.

**CLEAR means no supported contradiction in supplied facts, not correctness or approval.**
Undeclared obligations and fabricated observations remain undetectable. A known successful
outcome may be intentionally unchanged with Main's authorization and evidence; do not
produce a cosmetic edit merely to satisfy a changed-file counter.

## Independent verification and candidate holds

Every owner self-checks. Tester is required by project/owner gates or meaningful residual
risk, including behavior/state, integration, shared contracts, accessibility uncertainty,
authentication, payments, schema and financial invariants. Default implementation requires
independent review by default. An established reversible copy/style edit does not gain an
extra reviewer merely because it touches UI.

Tester starts in a context independent of the writer's investigation, with the original
task, complete actual diff, deliverables, questions and authoritative requirements. Reuse
that reviewer for the same repair loop, not unrelated work. It owns its separate verdict.

Read controlling definitions, possible values, guards and helpers before asserting a semantic
defect; inspect sibling cases and seek the smallest concrete counterexample. **Required gates
still run even when no defect is suspected.** Optional extra probes target concrete concerns.
New critical tests should exercise real entry points and meaningful negative controls where
practical. Do not count syntax/setup failures as proof of the intended assertion, or mutate
live work to plant a defect. Observers must report actual failure rather than fabricate success.

Identify relevant staged/unstaged/untracked source, tests/config/lockfiles, contract and actual
build/target/account. Hold relevant inputs stable during independent review. The hold is an
ownership agreement, not a filesystem lock. Tester writes evidence/disposable data, not code
or tests. Release before repair, re-hold the repaired candidate and rerun affected plus mandatory
fresh checks. Main inspects decisive risk and actual visuals without repeating the entire review.

Keep original logs and exit codes. Read exit status first, failure blocks next, summary last.
A passing count in partial output is not a green run. Distinguish executed-pass, reused-pass,
failed, blocked, unrun, deferred, authorized not-applicable, STALE and UNVERIFIED. Notes and
unrelated paths do not invalidate focused evidence; actual dependency changes do. Unknown
impact widens checks. See [verification](codex_workflow/verification.md).

## Waiting, capacity and context lifecycle

A wait timeout is not a new task. Use native completion notifications or supported long,
interruptible waits with actual exposed parameters. Do not SEND for progress, inspect
unfinished diffs, reload the browser or rerun tests merely because waiting returned.
Polling-only clients back off within supported limits, not rapid model turns or sleep loops.
Main re-enters for real decisions, required checkpoints, blockers and acceptance. Ordinary
user-facing progress uses known state; an explicitly requested fresh snapshot is one
coalesced owner request, not a cascade. Honor actual interruptions promptly.

Smart targets **at most two Smart-owned open threads across the run**, usually one owner and
one reviewer. Descendants, support and prior unfinished units count too. Lower client limits
and unrelated open threads remain binding. A final response is not native slot release.

Preserve results, settle writes and transfer useful resources, then use supported native
closure on completed owned children, leaves before parent. Observe release before relying
on capacity. On an error reconcile known handles once; retry only after observed state change.
With one slot, save candidate/repair context, close the writer and dispatch the independent
Tester from Main. Without a safe review path, checkpoint instead of dropping the gate.
Never raise the cap, close unrelated/active work or silently move implementation back to Main.

Closing an agent does not delete source, logs, browser profiles, servers or unique evidence.
Keep the same writer for concrete corrections. Accepted milestones preserve decisions,
candidate, gates, findings, next work and resource ownership. New unrelated contracts get
fresh bounded contexts after release, not repeated login or infrastructure setup. No automatic
parent restart, forced compaction or discarded live conversation. See [execution](codex_workflow/execution.md).

## Configuration and activation

Select **GPT-6.1 Sol / Medium** for Main in the client's supported selector when available.
Senior's managed role selects **gpt-6.1-sol / xhigh**. The installer preserves explicit
parent, profile, Plan effort and generic-child choices. It does not move an active session
to a different model.

The read-only assessment reports configured/recommended parent and `parent_baseline_status`.
A matching disk setting is not observed live selection. A valid different selection is a
warning, not corruption. Actual profile overrides, account access, tools and native capacity
still require client evidence. No new catalog override, permission or concurrency setting
is introduced by 2.7.

## Installation or update

Open Codex in your project directory and send:

```text
Install Smart Orchestration from https://github.com/7Eterius/codex_smart_orchestration. Resolve the current HEAD commit SHA of main and download/extract that exact source snapshot outside my projects. Do not use GitHub Releases or historical dist archives. Read codex_workflow/operate/smart_install.md. With Python 3.11+, run codex_workflow/runtime/smart_install.py --package-root codex_workflow without --apply first and inspect the preview. If clean, run the same command with --apply, then --check. Preserve unrelated Codex configuration and every project file. Stop on conflicts, never force changes. Do not quit, relaunch or wait for Codex to exit. Report version, source commit, fingerprint, backup and disk result; tell me to restart Codex manually. A disk check is not live runtime proof.
```

After success, restart Codex manually and start a fresh conversation. Select the intended
Main baseline explicitly; review preserved overrides before changing them. There is no
per-project installation, uninstall-first requirement or global qualification ceremony.
Use [targeted runtime checks](codex_workflow/runtime_check.md) for an actual uncertainty.

The installer manages declared guides, eight worker definitions, managed instruction regions
and Python helpers. It protects unrelated configuration and project files, stops on ownership
conflicts, and creates exact conflict-checked rollback backups. The new challenge guide is
installed on demand and protected like other managed files. Publication does not update your Mac.

## Validation and evaluation

```bash
python3 -B -m unittest discover -s scripts -p 'test_*.py' -v
python3 -m compileall -q codex_workflow scripts
```

CI runs Ubuntu/Python 3.11, Ubuntu/Python 3.12 and macOS/Python 3.12 with full Git history.
Historical migration tests remain pinned; the new exact 2.6 -> 2.7 -> no-op reapply -> rollback
path checks owner/project preservation, every role setting and local-edit protection.
Executable regressions cover old false-clear inputs, full validation, stage transitions,
identity mismatches, questions, real CLI behavior and candidate-helper integration.

Tests establish shipped instructions, helper behavior and installation, not live Codex
compliance, independent model-review quality or measured savings. For comparison, count all
model layers, setup, Main review, verification and rework per comparable accepted outcome.
Account for carry-in workers once and avoid overlapping inclusive subtree totals. Raw tokens,
cache share and API-price equivalents are diagnostics, not subscription billing.

A lower Main share is useful when settled work moved to Luna, not when necessary judgment
was removed. More agents are not automatically cheaper. No fixed saving percentage or number
of working days follows from this release.

## Documentation

[Main policy](codex_workflow/smart_orchestration.md) ·
[Design](codex_workflow/design.md) ·
[Execution](codex_workflow/execution.md) ·
[Verification](codex_workflow/verification.md) ·
[Browser](codex_workflow/browser.md) ·
[Preflight contract](codex_workflow/challenge.md) ·
[Boundary records](codex_workflow/boundary.md) ·
[Runtime checks](codex_workflow/runtime_check.md) ·
[Engineering notes](docs/smart_orchestration.md) ·
[2.7 notes](docs/v2.7.md) ·
[2.6 history](docs/v2.6.md) ·
[Evaluation](docs/evaluation.md)
