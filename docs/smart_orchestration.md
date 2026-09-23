# Smart Orchestration 2.0 architecture

## Two execution shapes

Normal is the default: main owns a bounded task, delegates to existing leaves when
useful and retains actual-diff and acceptance responsibility. Coordinated is an
optional native-agent policy for longer, settled runs: main schedules one fresh
`chunk_lead` per coherent chunk; the lead owns detailed investigation, review,
correction and explicitly delegated local acceptance.

Main still owns architecture, product meaning, UX/visual direction, serious risk
judgment, integration/release decisions and final milestone acceptance. It verifies
that a returned candidate exists, evidence is applicable and gates are satisfied,
without automatically repeating the lead's complete local review.

Only `chunk_lead` enables delegation. It may spawn Simple, Routine, Default and Tester;
all eight leaves disable delegation. This child-role restriction is a behavioral
contract, not a new native tool allowlist. No guessed maximum-depth configuration,
external scheduler, plugin dependency or root permission change is introduced.

## Admission, capacity and lifecycle

Coordinated admission requires coherent boundaries, settled contracts, run authority
and a relevant live qualification. The bundled [trial](../codex_workflow/qualification.md)
checks nesting, actual models/efforts, bounded context, permissions, candidate holds,
independent validation, pause/recovery and two successive complete worker groups.
Static Python tests do not substitute for it.

One lead plus at most two leaves uses the existing three-child budget when supported
by actual backend accounting. Other live work still consumes capacity. Preserve owner
limits; do not raise caps or remove validation to fit. Normal is the disclosed fallback
before execution unless the user explicitly requires coordinated-only work.

A lead stays through its same-chunk correction loop. A new accepted chunk gets a new
lead and scoped capsule, not a copy of prior investigations. Completion includes the
candidate, applicable gates, evidence, remaining obligations and resource handoff.
A finished worker need not receive acknowledgement chatter. Runtime thread closure,
turn interruption and process/resource release are distinct.

## Evidence and browser operation

Independent testing freezes relevant source, tests, configuration, build inputs and
runtime targets. The writer stops until release; a repair establishes a new candidate
and reruns affected checks. Requirements, not implementation-derived expectations,
are the validation oracle. Local acceptance, commit, integration and release are
separate states.

The optional [candidate helper](../codex_workflow/runtime/candidate.py) fingerprints
explicit scoped inputs including untracked additions. It reads no repository-wide
history and performs no Git/network/model calls. It has bounded input/output and
refuses symlinks, traversal and overwriting existing evidence. Identity equality is
not a test pass, a dependency graph, a concurrency lock or a trusted signature.

Simple Luna Low operates known low-risk browser/GUI flows and collects exact evidence.
Sol remains the product/design judge. Structured tools and deterministic batches are
preferred when sufficient, but never replace an explicitly required real browser
journey. The [browser guide](../codex_workflow/browser.md) adds target verification,
read-back after uncertain writes, reusable sessions and selective screenshots.

## Context and communication

Main loads the core policy once for substantive work. Coordinated and browser details
are on-demand documents, not always-loaded monolithic prompts. The lead receives exact
role/guide paths from one bundle. Follow-ups append deltas; stable instructions are not
rewritten for each turn.

Notifications and supported waits replace repetitive status polling. User progress
updates report last-known facts with uncertainty, not a new round of descendant
queries, tests or screenshot collection. Material blockers, safety issues and explicit
fresh-investigation requests still trigger work.

## Installation and migration

The distribution channel remains pinned `main` source. Preview and apply use the same
package validation; `--check` separately verifies installed hashes, the worker copies
and managed activation blocks. The installer respects `CODEX_HOME`, preserves owner
configuration, never touches projects and never quits its host app. Manual restart
occurs only after successful installation.

The package declares its exact installable inputs and content fingerprint. That
fingerprint identifies bytes, not an authenticated Git commit. Current managed runtime
and template edits now block replacement, not just worker TOML edits. Retirement is
byte-proven; unverified local files, historical source caches and rollback backups
are preserved. Transactions use atomic per-file replacement and compensating rollback,
not global multi-file reader isolation. Avoid concurrent configuration writers.

Legacy ownership marker strings remain deliberately stable to update existing global
blocks without duplication. No old project lifecycle or release machinery returns.

## Validation boundary

Automated tests cover nine-role configuration, policy boundaries and size budgets,
source validation, current install/update/check/rollback behavior, path and retirement
safety, source identity and the exact archived v1.9 upgrade. CI includes Linux and
macOS. The [v2 decision record](v2.0.md) distinguishes implementation from live-runtime
qualification and measured economic outcomes.
