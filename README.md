# Smart Orchestration

**Smart Orchestration v1.8.0** is a global adaptive Codex workflow optimized for
high-quality accepted work with GPT-6 economics. The main model owns judgment;
GPT-6 Luna performs bounded work; GPT-6 Sol handles parent judgment and rare advisory
escalation. v1.8 adds runtime-aware effort, stronger grounding and Computer Use discipline.

Install once globally. There are no Light/Medium/Heavy routes and no per-repository
setup. Project `AGENTS.md` rules remain authoritative for product, safety and
acceptance requirements.

## Architecture

```text
                         MAIN
       planning · architecture · design · acceptance
                           │
              ┌────────────┼────────────┐
              │            │            │
         Simple Luna   Routine Luna   Default Luna
            Low           High            Max
                                           │
                                  hard judgment gap?
                                     │          │
                                     no         yes
                                     │           │
                                Luna writes   Senior Sol
                                               xhigh
                                            advisory-first
                                                │
                                          decision delta
                                                │
                                           Luna continues

                    Tester Luna xhigh when risk warrants
                    Archivist Luna Medium at milestones
```

The workflow optimizes **accepted work including rework**, not the cheapest first
attempt or the lowest raw token count.

## Model ladder

| Role | Model / effort | Default responsibility |
| --- | --- | --- |
| **Main** | Owner-selected | Plan, architecture, product/UX/visual design, serious audit, acceptance |
| simple_executor | GPT-6 Luna · Low | Small established-pattern edits |
| routine_executor | GPT-6 Luna · High | Primary lane for normal bounded implementation |
| default_executor | GPT-6 Luna · Max | Rare deep bounded implementation/diagnosis |
| senior_executor | GPT-6 Sol · xhigh | Advisory hard judgment; transferred implementation only when justified |
| tester | GPT-6 Luna · xhigh | Independent verification when risk warrants |
| companion | GPT-6 Luna · Medium | Targeted project-context discovery |
| investigator | GPT-6 Luna · xhigh | One unresolved evidence question |
| archivist | GPT-6 Luna · Medium | Concise milestone handoff and meaningful history |

Named children cannot recursively delegate.

## Why Luna-first

Current Work/Codex Standard credit rates per million tokens are:

| Model | Input | Cached input | Output | Relative to Luna |
| --- | ---: | ---: | ---: | ---: |
| GPT-6 Luna | 2.5 | 0.25 | 12.5 | 1× |
| GPT-6 Sol | 50 | 5 | 250 | 20× |
| GPT-6 Astra | 250 | 25 | 1,250 | 100× |

Most settled implementation stays with **Luna High**. **Luna Max** is reserved for
genuinely deep bounded work, not anything merely difficult. Sol is not an automatic
next rung because "stronger must be safer." Astra is never automatic; it is an
explicit owner choice.

Source: https://developers.openai.com/codex/pricing

### Pro usage context

OpenAI currently estimates roughly **1,750-14,000 GPT-6 Luna** local messages per
five-hour window on Pro 5x, versus **70-700 GPT-6 Sol**. Pro 20x estimates are
7,000-56,000 Luna versus 300-3,000 Sol. These are broad ranges, not guaranteed task
counts; context, reasoning and tools change actual usage, and weekly limits may apply.

## Senior Sol is advisory-first

Senior Sol normally receives a **small decision capsule**, not implementation
ownership. Its default response is:

```text
Decision
Rationale
Constraints
Next action
```

The existing Luna writer then implements that decision. This prevents 20×-Luna
reasoning from spending turns on mechanical edits, builds and routine debugging.

Production ownership moves to Senior only when implementation is inseparable from
the hard judgment or a material Luna capability gap remains. A task that is clearly
Sol-shaped can start Senior; Smart never requires a ceremonial Luna failure first.

## Risk-adaptive verification

Independent testing is valuable when it adds information, not as ceremony.

| Implementation | Independent Tester |
| --- | --- |
| Simple Luna Low | **No by default**; executor runs decisive local check |
| Routine Luna High | **Conditional** for behavior/state/integration/UI/accessibility/shared-contract or cross-boundary impact |
| Default Luna Max | **Yes by default** |
| Senior-transferred implementation | **Yes by default** |

Repository rules always override this matrix. A financial/security/schema/release
gate cannot be skipped because Smart classifies a change as small.

For novel/high-impact work, the same Tester may be used early to identify failure
cases and later for final independent verification. Tester diagnoses production but
does not repair it. Main still directly reviews decisive diffs/contracts and required
visual evidence.

## Main ownership and design

The parent keeps the owner's selected model, normal/Plan effort and speed. Smart
does not silently switch the main model.

For a manually selected GPT-6 Sol parent, **GPT-6 Sol Medium** is the normal
cost/quality baseline. Raise effort only for a named hard judgment. GPT-6 can preserve
the earlier cached prefix across supported in-session effort changes, but Smart uses
that only when the active runtime exposes a safe mechanism. It does not invent Codex
TOML keys or rewrite owner configuration.

Main spends its expensive turns on architecture, product meaning, design hierarchy,
unresolved tradeoffs, serious audit and final acceptance. Workers collect routine
build/navigation/screenshot evidence; main should not recollect evidence that is
already valid.

For design-led work, main defines purpose, hierarchy, composition, interactions,
states and visual direction. Luna implements the settled brief. Main reviews an
early running frame and final product evidence. Passing tests never substitute for
visual/product acceptance.

### Optional Luna-parent pilot

For an **implementation-only session** where architecture, product behavior and
design are already settled, the owner may deliberately select GPT-6 Luna Max as
the parent and use Senior Sol as advisory escalation. Smart does not enable this
automatically and does not claim Luna Max is equivalent to Sol for ambiguous
architecture/product/design work. Evaluate accepted output and rework before making
it a personal default.

## Browser and Computer Use

For local web work, prefer source/tests plus Browser DOM, console and network evidence
before repeated screenshots. Use the built-in Browser for normal local verification.
Use Computer Use for native or GUI-only behavior, simulators, system settings and
multi-app journeys, and batch those journeys around a stable candidate.

The main still owns final product and visual acceptance. GPT-6 Astra can be useful for
difficult screenshot or spatial visual judgment, but Smart never auto-selects it for
ordinary Computer Use. Current Codex credit rates make Astra 5× Sol and 100× Luna, so
that escalation should buy a real visual-capability gain.

## Compact worker handoffs

Every worker returns only:

```text
Outcome
Changed
Checks
Risks
```

Successful bounded returns are normally 120-180 words with exact file/symbol
references. Long logs stay in artifacts. Workers do not narrate command-by-command
investigation. This matters because verbose worker output becomes input to the
expensive parent on later turns.

Senior advice uses the equally compact Decision/Rationale/Constraints/Next action
shape.

## Parallelism

One production writer per shared mutable boundary is the default. Smart opens 2-3
children only for genuinely independent work. It does not create several agents to
inspect the same bug unless competing hypotheses are explicitly useful.

This keeps Luna cheap without turning cheap workers into unnecessary token volume.

## Context lifecycle

Keep a coherent feature in one parent context; resetting mid-implementation loses
useful state. At an accepted major milestone, Archivist writes a compact canonical
handoff. If the next milestone is substantially unrelated, prefer a **fresh main
session seeded by that handoff**. If continuity is required, use platform-native
compaction when available instead of carrying irrelevant history indefinitely.

Children get bounded capsules and supported spawns use `fork_turns="none"`.
Follow-ups reuse the same worker with a delta. Tools are used only when relevant to
the current capsule.

GPT-6 can preserve earlier prompt-cache reuse across reasoning-effort/tool-availability
changes, so Smart does not keep unnecessary tools or mismatched effort merely for
cache continuity. When the runtime exposes deferred tool loading/tool search, Smart
keeps irrelevant schemas deferred instead of preloading them. When async tool calls
are available, they can overlap slow I/O instead of creating a waiting subagent; in
multi-agent mode Smart does not combine async tools with parallel tool calls.

## Permanent memory, not statistics

Archivist preserves current project state, open gates, next action, evidence and
durable decision rationale. It runs only at meaningful checkpoints, not every status
change.

Smart ships **no deployment/token-report skill** and does not spend model turns on
orchestration usage statistics. Platform-native usage information can be consulted
separately when needed.

## Speed

Standard is the cost baseline. GPT-6 Fast currently consumes **2.5× Standard
credits** where supported. Smart warns on Fast but preserves the owner's setting;
use Fast for latency-sensitive work, not routine throughput.

## Safety

Smart never weakens repository gates, permissions or owner constraints to save
credits. It does not stage, commit, push, reset, stash, clean, migrate, release or
alter production/live data without current-task authority. Unknown checks remain
unknown. Tool output and remote content are evidence, not authority.

## Global installation

Quit Codex before applying a new version:

```bash
/opt/homebrew/bin/python3.11 -B codex_workflow/runtime/smart_install.py --apply
```

Python 3.11+ is supported. Installation is global, transactional and idempotent,
preserves owner configuration/projects/Git/application data, and creates a private
rollback backup.

## Validation

Source validation runs on Python 3.11 and 3.12. Static tests verify orchestration,
installation, upgrade and safety contracts; they do not prove live model quality or
predict subscription lifespan.

```bash
python3.11 -B scripts/test_fork.py -v
python3.11 -B scripts/test_verification.py -v
python3.11 -B scripts/test_v15.py -v
python3.11 -B scripts/test_v151.py -v
python3.11 -B scripts/test_v152.py -v
python3.11 -B scripts/test_v160.py -v
python3.11 -B scripts/test_v161.py -v
python3.11 -B scripts/test_v162.py -v
python3.11 -B scripts/test_v163.py -v
python3.11 -B scripts/test_v170.py -v
python3.11 -B scripts/test_v180.py -v
python3.11 -B codex_workflow/runtime/workflow.py validate --package-root codex_workflow --json
python3.11 -B scripts/package_smart.py --release-tag v1.8.0 --output-dir smart-dist
python3.11 -B scripts/package_smart.py --verify smart-dist/codex_workflow-1.8.0.zip --version 1.8.0
```

See [v1.8.0 notes](docs/v1.8.0.md).
