# Smart Orchestration 2.4

**Main decides and judges. Luna implements, operates and repairs.**

Smart Orchestration is a global Codex workflow for getting more satisfactory work from a limited model allowance without giving up strong product, architecture, UX or visual judgment.

The core idea is deliberately simple:

> Use the expensive Main model for decisions that benefit from its intelligence and attention to detail. Delegate settled execution to the cheapest named worker that can do it reliably. Bring the result back to Main for assessment. If Main finds problems, send those findings back to the worker as another bounded implementation task.

Smart 2.4 has **one adaptive execution loop**. There are no Normal/Coordinated modes, no dedicated manager layer and no requirement to build a full agent team for every task.

## Architecture at a glance

```text
USER
  |
  v
MAIN / owner-selected model
  product meaning
  architecture
  UX and visual decisions
  acceptance criteria
  consequential authority
  detailed result review
  final acceptance
  |
  |  once the decision/contract is settled
  |
  +----> SIMPLE / GPT-6 Luna Low
  |        small established edits
  |        webpage extraction
  |        known low-risk GUI actions
  |        complete mechanical browser journeys
  |        explicit observable checks
  |
  +----> ROUTINE / GPT-6 Luna High
  |        normal implementation
  |        implementation of an accepted design
  |        scoped discovery needed to implement
  |        self-checks
  |        ordinary repairs
  |
  +----> DEFAULT / GPT-6 Luna xhigh
  |        genuinely deep bounded implementation
  |        difficult debugging with settled goals
  |        tangled cross-module diagnosis
  |
  +----> TESTER / GPT-6 Luna High
  |        independent diff/contract review
  |        required behavioral verification
  |        separate verdict
  |
  +----> SUPPORT ROLES
           Companion      Luna Medium   targeted context
           Investigator   Luna xhigh    deep evidence gap
           Archivist      Luna Medium   durable checkpoint
           Senior         Sol xhigh     hard advisory judgment

                    implementation/result
                             |
                             v
MAIN inspects decisive evidence and actual visuals
                             |
                 +-----------+-----------+
                 |                       |
              ACCEPT                  FINDINGS
                                         |
                                         v
                           same suitable Luna worker
                           applies bounded corrections
                                         |
                                         v
                              fresh evidence/result
                                         |
                                         +----> MAIN rechecks
```

The architecture is intentionally asymmetric. **Main is the judgment layer, not the default execution layer.** The workers are the execution layer. Tester is the independent verification layer when residual risk or project rules require it.

## Why this architecture

A long-lived Main conversation can become expensive because every implementation turn, browser action, progress check and correction may repeatedly invoke a large high-quality context. Smart tries to reserve that context for work where its intelligence has the highest value:

- deciding what should be built;
- resolving ambiguous requirements;
- architecture and product tradeoffs;
- UX, information hierarchy and interaction decisions;
- visual judgment and detailed design critique;
- consequential security, financial or authority decisions;
- inspecting decisive evidence;
- final acceptance.

Once those decisions are settled, writing the CSS, changing a component, editing configuration, replaying a known browser flow or applying a clearly described correction generally does not require Main to remain the writer.

This is **delegation for economics, not delegation for speed**. Waiting for a cheaper worker is acceptable. A small diff, familiarity with the code, or the fact that Main could perform the edit faster is not by itself a reason for Main to take execution back.

Smart does not promise a fixed saving percentage. Model behavior, task mix, context, tools, cache behavior, corrections and subscription accounting all matter. The workflow optimizes the structure of the work; actual savings should be measured on real accepted outcomes.

## The control plane: what Main owns

Main remains responsible for the parts of the task where judgment matters.

### Main should do

- Understand the user's goal and define the outcome.
- Resolve ambiguity before implementation.
- Make product and architecture decisions.
- Decide UX hierarchy, interaction behavior, visual direction and responsive intent.
- Define protected decisions and acceptance criteria.
- Inspect enough source or product evidence to make those decisions.
- Decide which named role should own the settled execution.
- Review decisive/high-risk changes and evidence applicability.
- Open and assess actual UI evidence when visual quality matters.
- Turn review findings into precise correction assignments.
- Decide whether corrected results satisfy the brief.
- Give final workflow acceptance, separately from commit/deploy/owner approval.

### Main should normally not do

- Routine implementation after the contract is settled.
- A “quick” code or CSS fix simply because it is easy.
- Mechanical webpage navigation that can be assigned to Simple.
- Repeated browser clicking while a worker owns the journey.
- Parallel implementation while a worker is already implementing.
- Poll unfinished diffs or repeatedly ask workers for progress.
- Re-run the worker's entire investigation just to supervise it.
- Pre-write the complete patch and use a worker as a paste mechanism.
- Silently take work back because nested delegation is unavailable.

Main can still answer questions directly, write the design/architecture brief, inspect decisive source and evidence, or perform a narrowly necessary main-only bridge action when an **observed** tool/permission boundary makes delegation impossible. That exception stays narrow; the remaining execution returns to workers.

An explicit user request for direct/no-agent execution also remains binding.

## The execution plane: choosing the cheapest sufficient owner

Smart routes by **responsibility and uncertainty**, not by file count, number of clicks or how impressive a task looks.

| Work | Default owner | Why |
| --- | --- | --- |
| Direct answer or unresolved judgment | Main | No execution handoff is useful yet |
| Product/architecture/UX/visual decision | Main | Judgment is the valuable part |
| Small established low-risk edit | Simple, Luna Low | Settled execution |
| Known webpage/GUI journey | Simple, Luna Low | Mechanical operation |
| Normal settled implementation | Routine, Luna High | Primary implementation lane |
| Accepted design implementation | Routine, Luna High | Main has already made design decisions |
| Deep bounded debugging/implementation | Default, Luna xhigh | More reasoning, still cheaper than Main |
| Standalone independent verification | Tester, Luna High | No implementation owner is required |
| One targeted context question | Companion, Luna Medium | Cheap bounded retrieval |
| Deep unresolved evidence question | Investigator, Luna xhigh | Investigation without taking product authority |
| Difficult advisory judgment | Senior, Sol xhigh | Advice returns to Main; it is not another manager |
| Meaningful durable checkpoint | Archivist, Luna Medium | Compact grounded handoff |

Routine is the **normal implementation default**. Default is not selected merely because many files are involved. It needs a real depth reason, such as a difficult causal bug, tangled cross-module behavior or prolonged tool-heavy diagnosis.

Simple is deliberately useful for more than one-line edits. A twenty-step browser journey can still be Simple work when the target, actions and expected observations are explicit and low risk.

## Mixed tasks are split at judgment boundaries

A real task often contains both high-value judgment and low-value execution.

Example:

> Redesign the story card for mobile, implement it, test the filters, and check the final page.

Smart should not give that whole request to Main or blindly give it all to Luna.

The intended flow is:

1. Main inspects the existing product and decides the new hierarchy, composition, interaction and acceptance criteria.
2. Routine implements that settled design.
3. The implementation owner performs local checks and returns the current candidate with running evidence.
4. Simple can own a separate worthwhile mechanical browser journey when appropriate, or the capable implementation owner can gather short evidence without introducing another relay worker.
5. Main opens the actual visual result and assesses it.
6. Main converts concrete findings into a bounded correction task.
7. The same suitable worker applies the correction.
8. Main reviews the fresh result and accepts or repeats the correction loop.

The expensive model therefore remains deeply involved in **what good looks like**, while cheaper models perform the repetitive editing and operation needed to get there.

## UI/UX and design workflow

Design work is a first-class case in 2.4 because delegating implementation must not accidentally delegate design authority.

See [`design.md`](codex_workflow/design.md) for the detailed contract.

### 1. Main writes the brief

Main settles enough of the design to make implementation mechanical rather than interpretive:

- purpose and user outcome;
- information hierarchy;
- composition;
- interaction model and important states;
- responsive intent;
- relevant visual language;
- accepted references;
- protected decisions;
- required viewports/states;
- concrete acceptance criteria;
- the next visual review checkpoint.

Main should not prescribe every CSS declaration or implementation detail. The worker still owns implementation.

### 2. Luna implements

Routine normally implements the accepted design. Simple is appropriate for an established low-risk visual edit.

The worker can choose ordinary implementation details inside existing patterns. If implementation reveals a missing hierarchy, interaction, product or visual-language decision, it returns that decision to Main instead of inventing one.

### 3. Worker returns the real candidate

The worker self-checks and returns actual running evidence tied to the current candidate, including the relevant state, viewport/theme and artifact references.

A worker saying “looks good,” a source preview, a mockup, or simply attaching screenshots is not visual acceptance.

### 4. Main judges the result

For a new composition, Main inspects an early running frame. Main also directly reviews the final affected screens.

The review can include:

- hierarchy and visual emphasis;
- typography;
- spacing and alignment;
- composition and rhythm;
- responsive behavior;
- interaction states;
- consistency with the accepted design language;
- obvious visual regressions;
- whether the evidence actually belongs to the current candidate.

Passing tests and Tester approval do not replace this visual judgment.

### 5. Main delegates corrections

Main does **not** make the quick patch itself. It groups related findings into a bounded correction assignment:

```text
Finding / acceptance criterion
Expected vs observed
Exact state or evidence
Allowed change
Protected decisions
Fresh checks
Requested updated visual evidence
```

The same suitable worker receives the delta whenever possible.

### 6. Main reassesses

After correction, Main inspects fresh evidence from the new candidate. Old screenshots and worker assurances do not close a new finding.

The loop ends when the authorized quality target and required gates are satisfied, not when a delegation percentage is reached and not after endless polish beyond the brief.

## Browser and Computer Use economy

See [`browser.md`](codex_workflow/browser.md).

The key distinction is:

> **Operating a GUI and judging a GUI are different jobs.**

Simple Luna Low is the default operator for explicit low-risk tasks such as:

- opening pages and extracting exact information;
- replaying a known user journey;
- checking explicit expected states;
- changing an established low-risk development setting;
- collecting screenshots or observable evidence;
- checking several pages against a concrete checklist.

Main remains the judge when the question is:

- Does this composition feel balanced?
- Is the information hierarchy clear?
- Is this interaction confusing?
- Which responsive layout should we choose?
- Does this look polished enough to accept?

Smart prefers structured evidence when it proves the requested result more directly. DOM, network, console, APIs or deterministic browser tests can avoid repeated model-guided clicking. A real browser is still required when the acceptance contract requires the rendered journey.

Reuse a verified browser session, server and build setup. Do not repeat login, browser installation or rebuilds just because one worker finished. One owner controls shared mutable GUI state at a time.

A mechanically easy click can still be consequential. Billing, permissions, production, destructive actions and other sensitive boundaries retain their authority requirements.

## Implementation, review and repair

Every execution owner self-checks its work. Independent Tester is added when residual risk or repository/owner rules require it.

See [`verification.md`](codex_workflow/verification.md).

Typical reasons for independent review include:

- meaningful behavior or state changes;
- shared contracts and integrations;
- uncertain accessibility behavior;
- authentication/security;
- payments;
- schema/data migrations;
- financial invariants;
- Default-level implementation;
- any repository-required independent gate.

A reversible established copy/style change with decisive local checks does not automatically acquire another model reviewer merely because it touches UI.

### Candidate hold

When independent review starts, the relevant candidate is held stable:

```text
writer finishes candidate
        |
        v
identify source/config/build/target
        |
        v
HOLD candidate
        |
        v
Tester independently reviews and runs required gates
        |
   +----+----+
   |         |
 PASS      FAILURE
   |         |
   |      release hold
   |         |
   |      same writer repairs
   |         |
   |      identify new candidate
   |         |
   |      hold + fresh affected checks
   |         |
   +-----> Main acceptance
```

Tester owns its separate verdict. The writer can reference it but cannot rewrite it. Original failures stay preserved.

Main checks whether the evidence is applicable and inspects decisive/high-risk changes, but should not routinely redo the Tester's complete source investigation.

## Correction ownership

Corrections are intentionally economical.

When Main or Tester finds a defect, the default is **not**:

```text
failure -> new planner -> new writer -> rediscover everything
```

It is:

```text
failure -> concise evidence-backed delta -> same suitable writer -> fresh checks
```

This preserves useful implementation context and avoids paying for rediscovery.

A correction should identify:

- the failed requirement or Main review finding;
- exact evidence;
- the allowed delta;
- protected decisions;
- affected gates;
- which fresh evidence must return.

A repeated failure needs new evidence or a revised diagnosis. It does not automatically justify a stronger model.

## Thread lifecycle and capacity

See [`execution.md`](codex_workflow/execution.md).

Smart targets **one execution owner plus one independent reviewer when needed**, at most two Smart-owned open threads for the current unit. The user's configured Codex limit remains authoritative and may include unrelated work.

Important distinction:

> A worker returning its final message does not prove its native thread slot has been released.

When the client supports native closure:

1. persist the worker's result and evidence;
2. settle pending writes;
3. transfer any browser/server/evidence resources that must survive;
4. close completed owned leaf threads before their parent;
5. observe actual release before relying on the reclaimed slot.

Thread closure is separate from resource deletion. Closing an agent must not delete source, logs, browser profiles, servers or unique evidence.

On `agent thread limit reached`, Smart reconciles the relevant known handles once. It may retry only after an observed state change. It does not raise the cap, blindly respawn, close unrelated work or silently move implementation back to expensive Main.

Routine and Default may dispatch exactly one Tester only when Main explicitly delegated review scheduling and the relevant native nesting/lifecycle behavior is supported. Otherwise Main dispatches that same named Tester directly. The reviewer contract and model stay the same.

Direct named Luna work does not depend on nested-agent support.

## Main stays quiet while execution is settled

A major economic goal is to reduce unnecessary re-entry into the large Main context.

During a bounded worker assignment, Main should not repeatedly:

- ask “how is it going?”;
- inspect unfinished diffs;
- re-run the worker's checks;
- operate the same GUI in parallel;
- acknowledge every worker message;
- re-explain the entire task on follow-up.

Use completion notifications or supported waiting. Ordinary status is a snapshot of last-known state, not a reason to launch new investigation.

A follow-up correction should contain the **delta**, not the full original task again.

Main re-enters when it has something valuable to do: resolve a decision, address a blocker, inspect a required checkpoint, assess the returned result, or accept/reject the candidate.

## Context economy

Smart tries to reduce both expensive-model usage and redundant context work.

- Workers receive bounded capsules rather than the entire conversation.
- Scoped history such as `fork_turns="none"` is preferred when supported.
- Stable setup and accepted briefs are reused.
- Follow-ups send deltas.
- Existing deterministic tests and browser recipes are reused when valid.
- Raw logs stay outside concise handoffs.
- Only relevant guides/tools are loaded.
- One coherent assignment is preferred over a worker per file or click.
- A manager layer is not added just to relay messages.
- Main does not solve the implementation before delegating it.

The objective is not the fewest possible model calls. It is the lowest practical allowance cost for a **satisfactory accepted result**, including corrections and verification.

## Model map

| Role | Model / effort | Primary purpose | Does not own |
| --- | --- | --- | --- |
| Main | Owner-selected, Sol Medium recommended baseline | Product/architecture/design judgment, result assessment, final acceptance | Routine execution |
| `simple_executor` | GPT-6 Luna Low | Established edits, extraction, mechanical Browser/Computer Use | New product/design decisions |
| `routine_executor` | GPT-6 Luna High | Normal settled implementation and repair | Final acceptance |
| `default_executor` | GPT-6 Luna xhigh | Deep bounded implementation/diagnosis | Product authority |
| `tester` | GPT-6 Luna High | Independent diff/contract/behavior verification | Production repair |
| `senior_executor` | GPT-6 Sol xhigh | Difficult advisory judgment | Routine implementation or final authority |
| `companion` | GPT-6 Luna Medium | One targeted context question | Broad execution |
| `investigator` | GPT-6 Luna xhigh | Deep unresolved evidence question | Product decisions |
| `archivist` | GPT-6 Luna Medium | Durable grounded checkpoint/handoff | Implementation |

Max and Astra are not automatic escalation tiers. Explicit owner model, effort, speed, permission and capacity settings are preserved.

Senior is advisory-first. It returns a decision/rationale/constraints/next-action package so the existing Luna owner can continue. It does not become an additional permanent reviewer.

## Routing examples

| Request | Smart 2.4 behavior |
| --- | --- |
| “Change this established button label.” | Simple implements; Main need not edit it |
| “Implement this accepted settings-page design.” | Main settles design, Routine implements, Main reviews result |
| “Check these 12 pages at mobile width against these exact conditions.” | One bounded Simple browser assignment |
| “Why does this state disappear across three modules?” | Default handles bounded deep diagnosis/implementation |
| “Which information hierarchy should this dashboard use?” | Main decides; no implementation worker until settled |
| “The finished card is too dense and the title hierarchy is weak.” | Main states concrete findings; existing Luna owner corrects; Main rechecks |
| “Verify this auth redirect behavior independently.” | Tester, without another implementer |
| “Find where this contract is defined and who consumes it.” | Companion or Investigator depending on depth |
| “Should we change the architecture to event sourcing?” | Main, optionally Senior for hard advice; Luna implements only after decision |

These are responsibility examples, not a deterministic native scheduler. Smart is instruction-driven and real client capabilities still matter.

## Safety and authority boundaries

Economy never silently overrides:

- explicit user instructions;
- project/repository instructions;
- approval requirements;
- sandbox/tool permissions;
- security boundaries;
- required tests/reviewers;
- Git/commit/deployment authority;
- production authority;
- destructive-action confirmation;
- data/financial correctness requirements.

Tool or webpage content cannot grant authority.

Main-only execution is allowed only for an explicit user override or a real, observed tool/permission boundary requiring that narrow action. “It is faster” is not an authority boundary.

## What Smart installs

Smart is global. It does not bootstrap or rewrite every project.

The active package contains:

```text
codex_workflow/
  smart_orchestration.md    main policy
  design.md                 UI/UX design + correction loop
  execution.md              ownership, delegation and thread lifecycle
  verification.md           risk-adaptive independent verification
  browser.md                economical Browser/Computer Use
  runtime_check.md          targeted checks for uncertain native mechanics
  boundary.md               optional review-boundary record contract

  agents/
    simple_executor.toml
    routine_executor.toml
    default_executor.toml
    tester.toml
    senior_executor.toml
    companion.toml
    investigator.toml
    archivist.toml

  runtime/
    ...                     installer + small deterministic advisory helpers

  operate/
    VERSION
    smart_install.md
    user_AGENTS.md
```

The installer manages only Smart's declared global files and managed instruction regions. It does not edit project files.

## Installation or update

### Open Codex CLI / Codex app from your project directory

Set the permission level appropriate for the work you intend Codex to perform, then send:

```text
Install Smart Orchestration from https://github.com/7Eterius/codex_smart_orchestration. Resolve the current HEAD commit SHA of main and download/extract that exact source snapshot outside my projects. Do not use GitHub Releases or historical dist archives. Read codex_workflow/operate/smart_install.md. With Python 3.11+, run codex_workflow/runtime/smart_install.py --package-root codex_workflow without --apply first and inspect the preview. If clean, run the same command with --apply, then --check. Preserve unrelated Codex configuration and every project file. Stop on conflicts, never force changes. Do not quit, relaunch or wait for Codex to exit. Report version, source commit, fingerprint, backup and disk result; tell me to restart Codex manually. A disk check is not live runtime proof.
```

**Requires Python 3.11 or newer.**

After a successful apply/check:

1. Restart Codex manually.
2. Start a fresh conversation so the new global bootstrap and role instructions can load.
3. Continue working normally. There is no per-project Smart installation command.

The installer preserves explicit parent model/effort/speed, generic child fallback, permissions, capacity and all project files. It stops on managed-file conflicts instead of forcing replacement.

A successful source publication or GitHub release does not update an existing installation. Current pinned `main` source remains the normal installation/update channel.

## Validation

Repository validation:

```bash
python3 -B -m unittest discover -s scripts -p 'test_*.py' -v
python3 -m compileall -q codex_workflow scripts
```

Smart 2.4 is covered by the existing CI matrix:

- Ubuntu, Python 3.11
- Ubuntu, Python 3.12
- macOS, Python 3.12

The test suite includes exact historical installation/migration and rollback checks, including 2.3 -> 2.4 -> no-op reapply -> rollback.

Passing source tests establish package, helper and installation contracts. They do **not** prove native Codex routing behavior, UI quality or a particular allowance saving.

Use [targeted runtime checks](codex_workflow/runtime_check.md) only when a specific native mechanism is uncertain. There is no global qualification ceremony blocking ordinary direct named-worker delegation.

## Measuring whether it helps

The success metric is not “maximum delegation.”

It is:

> **How much satisfactory, accepted work do I get from my available allowance, including setup, worker execution, Main review, verification and repairs?**

A lower Main share can be desirable when settled implementation moved to Luna, but Main usage is not automatically waste. Main should remain active wherever its judgment materially improves the product.

Likewise, more workers are not automatically cheaper. Over-fragmentation creates handoff and rediscovery cost. Smart therefore favors one complete bounded job, one owner, and one independent reviewer only when needed.

For serious evaluation, compare similar accepted tasks and include rework and quality outcomes. Raw token totals, cache share and public API-equivalent prices are useful diagnostics, not subscription billing.

## Documentation

- [Main orchestration policy](codex_workflow/smart_orchestration.md)
- [Design and UI/UX loop](codex_workflow/design.md)
- [Execution and thread lifecycle](codex_workflow/execution.md)
- [Verification policy](codex_workflow/verification.md)
- [Browser and Computer Use economy](codex_workflow/browser.md)
- [Optional boundary records](codex_workflow/boundary.md)
- [Targeted runtime checks](codex_workflow/runtime_check.md)
- [Engineering notes](docs/smart_orchestration.md)
- [2.4 release notes](docs/v2.4.md)
- [Optional evaluation guidance](docs/evaluation.md)

## In one sentence

**Smart 2.4 spends Main on deciding what excellent work should be and judging whether it got there, while Luna performs as much of the settled implementation, operation and correction work as safely possible.**
