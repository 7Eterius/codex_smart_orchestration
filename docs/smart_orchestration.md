# Smart Orchestration engineering notes

## v1.9 operating model

The canonical parent policy is `codex_workflow/smart_orchestration.md`. v1.9 keeps
the eight named roles and changes effort allocation, not the runtime architecture.

Simple Luna Low now owns low-risk mechanical Browser/Computer operation as well as
small established-pattern edits. Routine Luna High remains the primary implementation
lane. Default Luna moves from Max to xhigh. Tester moves from xhigh to High and is
reserved for independent verification that adds judgment, not deterministic GUI
navigation. Senior Sol xhigh remains advisory-first.

The installer still preserves the owner's parent model, effort, speed, approvals and
tool permissions. For a manually selected Sol parent, Medium is the normal baseline.
When the runtime exposes safe in-session effort updates, hard architecture, product,
UX or design decisions may temporarily use High/xhigh and then return to Medium.

## Operator versus judge

Browser/Computer Use is split by cognitive job, not by tool. Mechanical navigation,
web lookup, explicit GUI configuration, DOM/console/network inspection, screenshot
collection and checks against explicit criteria are operator work and should normally
use Simple Luna Low when they require several tool turns.

Product/UX/design interpretation remains main/Senior work. Astra is owner-selected
only for difficult spatial or visual judgment. Computer Use alone is never a reason
to escalate to a stronger model.

## Context and tools

Workers receive bounded capsules with `fork_turns="none"`; follow-ups send deltas.
Companion, Investigator and Archivist distinguish sourced facts, inference and unknown
evidence. Deferred tool loading/tool search and async I/O are used only when exposed
by the runtime; Smart does not invent configuration keys.

## Installation and safety

`smart_install.py` remains global, transactional and project-safe. Existing owner
configuration is preserved. Automated tests validate package, migration and policy
contracts, not live model quality or subscription lifespan.

## Primary references

- https://developers.openai.com/api/docs/guides/model-selection
- https://developers.openai.com/api/docs/guides/latest-model
- https://developers.openai.com/api/docs/guides/prompt-caching
- https://developers.openai.com/api/docs/guides/tools-computer-use
- https://developers.openai.com/api/docs/models/gpt-6-luna
- https://developers.openai.com/api/docs/models/gpt-6-sol
- https://www.orcarouter.ai/blog/gpt-6-luna-vs-gpt-6-sol
