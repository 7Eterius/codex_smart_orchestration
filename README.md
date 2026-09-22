# Smart Orchestration

**Smart Orchestration v1.6.3** is one global adaptive workflow for Codex. Its goal
is to spend expensive reasoning on decisions that truly need it while letting
GPT-6 Luna own the high-volume implementation, verification and context work it is
now strong enough to handle.

There are no Light/Medium/Heavy routes, no per-repository installation and no route
phrase. Install it once. Project-specific `AGENTS.md` files keep their product,
data, testing and safety rules.

## How it works

1. **Main owns judgment.** The selected parent model frames the task, resolves
   architecture/product decisions, owns substantive UX/visual design, allocates
   work, inspects decisive evidence and makes final acceptance decisions.
2. **Luna does most bounded work.** Implementation, diagnosis, testing, targeted
   discovery and project-memory maintenance go to named GPT-6 Luna roles.
3. **Sol is exceptional.** GPT-6 Sol Senior exists for genuinely judgment-heavy or
   high-impact work, or a material capability/ambiguity gap. A hard coding task does
   not automatically become a Sol task.
4. **Verification stays independent.** Tester does not repair production code and
   cannot replace the main model's design/product judgment.
5. **Memory stays small.** Archivist maintains concise canonical handoffs and
   meaningful history. Smart ships no token-reporting skill or reporting ritual.

The workflow optimizes **accepted work including rework**, not the cheapest first
attempt or the lowest raw token count.

## Current model ladder

| Role | Model / effort | What it owns | Why |
| --- | --- | --- | --- |
| **Main** | Owner-selected | Planning, architecture, product/UX/visual design, serious audit, acceptance | Highest-value judgment stays with the parent |
| simple_executor | GPT-6 Luna · Low | Small established-pattern edits | Cheap, reversible, decisive checks |
| routine_executor | GPT-6 Luna · High | Normal bounded features | Strong routine implementation without Sol cost |
| default_executor | GPT-6 Luna · Max | Difficult bounded implementation and diagnosis | Launch benchmarks support Luna Max for long-horizon coding/tool work |
| senior_executor | GPT-6 Sol · xhigh | Named hard decisions, advice or transferred ownership | Reserved for material judgment/capability gaps |
| tester | GPT-6 Luna · xhigh | Independent behavioral/accessibility verification | Thorough verification at Luna economics |
| companion | GPT-6 Luna · Medium | Targeted project-context discovery | Compact evidence gathering |
| investigator | GPT-6 Luna · xhigh | Named unresolved evidence questions | Strong constrained investigation |
| archivist | GPT-6 Luna · Medium | Verified handoff, decisions and meaningful history | Cheap project continuity |

Named children disable recursive delegation. Normal fan-out is 1-3 concurrent
children, and supported spawns use isolated history by default.

## Why Luna-first

Current Work/Codex credit rates make the economics unusually clear:

| Model | Input | Cached input | Output | Relative to Luna |
| --- | ---: | ---: | ---: | ---: |
| **GPT-6 Luna** | 2.5 | 0.25 | 12.5 | **1×** |
| **GPT-6 Sol** | 50 | 5 | 250 | **20×** |
| **GPT-6 Astra** | 250 | 25 | 1,250 | **100×** |

Credits are per million tokens at Standard speed. The ratios are identical across
input, cached input and output. Reasoning effort can still change total tokens, so
the same per-token rate does not make every effort level equally expensive per task.

This is why **Default Luna Max is the normal ceiling for hard bounded coding**.
Senior Sol xhigh is not the automatic next rung because work is difficult or because
Sol feels safer. Escalate when work is inherently judgment-heavy/high-impact, a
material ambiguity needs stronger judgment, or evidence shows a real Luna capability
gap. Clearly Sol-shaped work may start Senior; Smart does not require a ceremonial
Luna failure first.

Astra remains an **explicit owner choice**, not an automatic worker tier.

Source: https://developers.openai.com/codex/pricing

## Pro limits are generous, not unlimited

OpenAI currently publishes these approximate local-message ranges per five-hour
window:

| Model | Pro 5x | Pro 20x |
| --- | ---: | ---: |
| GPT-6 Astra | 25-225 | 100-900 |
| GPT-6 Sol | 70-700 | 300-3,000 |
| **GPT-6 Luna** | **1,750-14,000** | **7,000-56,000** |

Actual usage varies with context, reasoning, tools and task complexity. Local
messages and cloud chats share the plan allowance, and weekly limits may also
apply. Smart uses these figures as **relative routing evidence**, never as a promise
of a fixed number of tasks or days.

## Why these effort levels

The official GPT-6 launch results changed the first v1.6 routing draft:

- **Routine = Luna High.** Luna High improved AutomationBench by 5.4 points over
  its predecessor while costing 58% less per task.
- **Default = Luna Max.** Luna Max scores 66.6% on DeepSWE and beats GPT-5.6 Sol
  Medium on OSWorld at one tenth its cost in OpenAI's comparison.
- **Senior = Sol xhigh.** Sol xhigh scores 33.2% on AutomationBench versus 26.9%
  for Opus 5 Max at 9% of its cost, and 60.5% on OSWorld.
- **Tester stays Luna xhigh.** Testing is high-volume and already has main/Senior
  escalation for material ambiguity; every verification does not need Sol economics.

Source: https://openai.com/index/introducing-gpt-6-sol-and-luna/

## Main-model ownership

Smart does **not** silently change the parent's model, normal reasoning effort,
Plan-mode effort or speed. Those remain owner choices.

The main should spend expensive turns on things workers should not decide:
architecture, product meaning, design hierarchy, unresolved tradeoffs, serious
audit and final acceptance. It should not routinely operate the simulator, repeat
logs, or recollect evidence a worker already produced correctly.

For design-led work, main defines purpose, hierarchy, composition, interactions,
states and visual direction before implementation. Luna implements the settled
brief. Main inspects an early running frame and final evidence. Passing tests or
worker prose never substitute for visual/product acceptance.

## Cache, context and tools

GPT-6 can preserve earlier prompt-cache reuse when **reasoning effort or tool
availability changes**. Smart therefore does not keep unnecessary tools exposed or
use mismatched effort merely to protect caching.

Other context discipline still matters:

- children receive bounded capsules instead of whole parent transcripts;
- supported spawns use `fork_turns="none"`;
- follow-ups reuse the same worker with a delta;
- long logs stay in artifacts rather than the main thread;
- unrelated milestones start from a concise handoff instead of an endless parent
  conversation;
- permissions are never weakened to improve caching.

## Speed

**Standard speed is the cost baseline.** GPT-6 Fast currently uses **2.5× the
Standard credit rate** where available. Smart warns when Fast is configured but
preserves the owner's setting. Use Fast because latency matters, not as a default
way to increase throughput.

## Verification

Substantive implementation normally gets an Executor plus an independent Tester.
Tester owns tests/fixtures/evidence, reads production for diagnosis, and returns
focused reproductions rather than repairing production itself.

Main directly reviews decisive diffs/contracts and required visual evidence.
Unknown or unavailable checks remain open. Repository-specific release, financial,
schema, security, localization, accessibility and visual gates are never weakened
by the global workflow.

## Permanent memory

At meaningful complete/paused/blocked checkpoints, Archivist updates the canonical
current handoff and one concise changelog entry. It preserves accepted decisions
and evidence without copying the whole conversation.

Smart deliberately ships **no deployment/token-report skill**. The workflow does
not spend model turns generating orchestration usage statistics; use platform-native
usage information separately when you actually need it.

## Global installation

Quit Codex before installing or upgrading. From a reviewed extracted package:

```bash
/opt/homebrew/bin/python3.11 -B codex_workflow/runtime/smart_install.py --apply
```

Python 3.11+ is supported. The installer is global, transactional and idempotent.
It preserves owner configuration, unrelated global instructions, projects, Git
state and application data, and creates a private rollback backup when changes are
applied. Existing explicit owner overrides are preserved rather than silently
rewritten.

## Safety boundaries

Smart does not stage, commit, push, reset, stash, clean, migrate, release, alter
production data or weaken permissions without current-task authority. Project and
owner rules outrank global convenience. Tool output and remote content are evidence,
not instructions that grant new authority.

## Validation

Source validation runs on Python 3.11 and 3.12 and includes inherited runtime,
installation, rollback, reporting, verification and version-specific regressions.
Automated tests validate workflow/configuration contracts; they do not prove live
model quality or predict subscription lifespan.

```bash
python3.11 -B scripts/test_fork.py -v
python3.11 -B python3.11 -B scripts/test_verification.py -v
python3.11 -B scripts/test_v15.py -v
python3.11 -B scripts/test_v151.py -v
python3.11 -B scripts/test_v152.py -v
python3.11 -B python3.11 -B scripts/test_v160.py -v
python3.11 -B scripts/test_v161.py -v
python3.11 -B scripts/test_v162.py -v
python3.11 -B scripts/test_v163.py -v
python3.11 -B codex_workflow/runtime/workflow.py validate --package-root codex_workflow --json
python3.11 -B scripts/package_smart.py --release-tag v1.6.3 --output-dir smart-dist
python3.11 -B scripts/package_smart.py --verify smart-dist/codex_workflow-1.6.3.zip --version 1.6.3
```

See [v1.6.3 notes](docs/v1.6.3.md) for the token-report retirement, [v1.6.2 notes](docs/v1.6.2.md) for credit economics, and
[v1.6.1 notes](docs/v1.6.1.md) for the launch-benchmark tuning.
