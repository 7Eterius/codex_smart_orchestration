# Smart Orchestration

**Smart Orchestration v1.9.0** is a standalone global Codex workflow optimized for
high-quality accepted work with GPT-6 economics. The main model owns judgment;
GPT-6 Luna performs bounded work; GPT-6 Sol handles parent judgment and rare advisory
escalation.

There are no Light/Medium/Heavy routes, no per-repository bootstrap, and no inherited
project-documentation framework. Install once globally. Each project's own
`AGENTS.md` remains authoritative for its product, safety and acceptance rules.

## Installation

### Open Codex CLI / Codex app from any project directory

Change permission to **Approve for me** or **Full access**, then send:

```text
Install the latest Smart Orchestration code from the main branch of https://github.com/7Eterius/codex_smart_orchestration. First resolve the current HEAD commit SHA of main, then download the source archive for that exact commit into a temporary directory and extract it. Do not use GitHub Releases, historical dist archives, or another repository. Read the extracted codex_workflow/operate/smart_install.md. Run codex_workflow/runtime/smart_install.py with --package-root codex_workflow without --apply first and inspect the preview. If the preview is clean, run the same command with --apply in this current Codex session. Use Python 3.11 or newer. Do not quit, close, relaunch, or wait for Codex to exit as part of installation. Preserve my existing Codex configuration and all project files. If download, extraction, preview, or installation reports any conflict or error, stop and report it instead of forcing changes. At the end, report the exact main commit SHA that was installed and tell me to restart Codex manually.
```

> ⭐ **Recommended:** use **GPT-6 Luna xhigh** for installation.

🔄 **After the installer reports success, restart Codex manually.**

Smart Orchestration is installed under `~/.codex/`. To update while `main` is the
distribution channel, run the same prompt again. Do not uninstall first.

> Requires **Python 3.11 or newer**.

## Architecture

```text
                         MAIN
       planning · architecture · design · acceptance
                           │
              ┌────────────┼────────────┐
              │            │            │
         Simple Luna   Routine Luna   Default Luna
            Low           High           xhigh
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

                    Tester Luna High when risk warrants
                    Archivist Luna Medium at milestones
```

The workflow optimizes **accepted work including rework**, not the cheapest first
attempt or the lowest raw token count.

## Model ladder

| Role | Model / effort | Default responsibility |
| --- | --- | --- |
| **Main** | Owner-selected | Plan, architecture, product/UX/visual design, serious audit, acceptance |
| simple_executor | GPT-6 Luna · Low | Small edits; mechanical Browser/Computer operation; explicit checks |
| routine_executor | GPT-6 Luna · High | Primary lane for normal bounded implementation |
| default_executor | GPT-6 Luna · xhigh | Deep bounded implementation/diagnosis |
| senior_executor | GPT-6 Sol · xhigh | Advisory hard judgment; transferred implementation only when justified |
| tester | GPT-6 Luna · High | Independent judgment-bearing verification when risk warrants |
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

Most settled implementation stays with **Luna High**. **Luna xhigh** handles deep
bounded work. Max is intentionally absent from automatic routing; use it only when
your own evaluations show a material gain over xhigh. Sol is for judgment/capability
gaps, and Astra remains an explicit owner choice.

Source: https://developers.openai.com/codex/pricing

## Senior Sol is advisory-first

Senior Sol normally receives a small decision capsule rather than implementation
ownership:

```text
Decision
Rationale
Constraints
Next action
```

The existing Luna writer then implements that decision. Production ownership moves to
Senior only when implementation is inseparable from the hard judgment or a material
Luna capability gap remains.

## Risk-adaptive verification

| Implementation | Independent Tester |
| --- | --- |
| Simple Luna Low | **No by default**; executor runs decisive local check |
| Routine Luna High | **Conditional** for behavior/state/integration/UI/accessibility/shared-contract or cross-boundary impact |
| Default Luna xhigh | **Yes by default** |
| Senior-transferred implementation | **Yes by default** |

Repository rules always override this matrix. Financial/security/schema/release gates
cannot be skipped because Smart classifies a change as small.

## Main ownership and design

The parent keeps the owner's selected model, normal/Plan effort and speed. Smart does
not silently switch the main model. For a manually selected GPT-6 Sol parent,
**GPT-6 Sol Medium** is the normal cost/quality baseline. Raise effort only for a named
hard architecture, product, UX or design judgment when the runtime safely supports it.

For design-led work, main defines purpose, hierarchy, composition, interactions,
states and visual direction. Luna implements the settled brief. Main reviews running
product evidence. Passing tests never substitute for visual/product acceptance.

## Browser and Computer Use

Smart separates **operator work** from **judgment**. Simple Luna Low handles mechanical
web lookup, known Browser/Computer flows, explicit development configuration through
a GUI, DOM/console/network inspection, screenshots and checks against stated observable
criteria.

The main or Senior Sol handles UX, interaction, hierarchy and visual critique. Astra
is owner-selected only when difficult spatial/visual judgment itself needs stronger
intelligence. A screenshot or Computer Use task alone never triggers Astra or Tester.

## Compact handoffs and context

Workers return only `Outcome; Changed; Checks; Risks` with exact evidence. Long logs
stay in artifacts. One production writer owns each mutable boundary. Smart opens
multiple children only for genuinely independent work.

Keep a coherent feature in one parent context. At an accepted major milestone,
Archivist writes a compact canonical handoff. For a substantially unrelated next
milestone, prefer a fresh main session seeded by that handoff.

## Safety

Smart never weakens repository gates, permissions or owner constraints to save
credits. It does not stage, commit, push, reset, stash, clean, migrate, release or
alter production/live data without current-task authority. Unknown checks remain
unknown.

The global installer is transactional, conflict-checked and project-safe. It preserves
unrelated Codex configuration and project files, and creates a reversible backup for
every successful change.

## Repository scope

This repository now contains only the standalone Smart runtime, the eight worker
definitions, current policy/verification documentation, and current-state tests.
Historical upstream artifacts and old migration implementations remain available in
Git history instead of the active tree.

## Validation

```bash
python3.11 -B scripts/test_current.py -v
python3.12 -B scripts/test_current.py -v
python3.11 -m compileall -q codex_workflow
```

See [engineering notes](docs/smart_orchestration.md) and
[v1.9.0 notes](docs/v1.9.0.md).
