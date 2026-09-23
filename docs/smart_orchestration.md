# Smart Orchestration engineering notes

## v1.9 operating model

The canonical parent policy is `codex_workflow/smart_orchestration.md`. Smart has
eight named roles and one global installation surface. There is no project bootstrap,
route selector, release updater, token reporter or inherited documentation framework.

Simple Luna Low owns low-risk mechanical Browser/Computer operation as well as small
established-pattern edits. Routine Luna High is the primary implementation lane.
Default Luna xhigh handles deep bounded implementation/diagnosis. Tester Luna High is
reserved for independent verification that adds judgment. Senior Sol xhigh remains
advisory-first.

The installer preserves the owner's parent model, effort, speed, approvals, tools,
unrelated configuration and every project file.

## Operator versus judge

Browser/Computer Use is split by cognitive job, not by tool. Mechanical navigation,
web lookup, explicit GUI configuration, DOM/console/network inspection, screenshot
collection and checks against explicit criteria are operator work and normally belong
to Simple Luna Low when they require several tool turns.

Product/UX/design interpretation remains main/Senior work. Astra is owner-selected
only for difficult spatial or visual judgment.

## Context and tools

Workers receive bounded capsules with `fork_turns="none"`; follow-ups send deltas.
Companion, Investigator and Archivist distinguish sourced facts, inference and unknown
evidence. Deferred tool loading/tool search and async I/O are used only when exposed
by the runtime.

## Installation and safety

`smart_install.py` is global, transactional, conflict-checked and safe to complete in
an active Codex session. The user restarts Codex manually after a successful apply.

Current `main` is the distribution channel. The installer previews before writing,
tracks hashes for workflow-owned runtime files, retires unchanged legacy-owned files,
preserves locally modified retired files, and creates an exact rollback backup.

Automated tests validate the current package, routing contracts, configuration
preservation, installation, cleanup, rollback and conflict behavior. Historical
migration eras remain in Git history rather than the active source tree.

## Primary references

- https://developers.openai.com/api/docs/guides/model-selection
- https://developers.openai.com/api/docs/guides/latest-model
- https://developers.openai.com/api/docs/guides/prompt-caching
- https://developers.openai.com/api/docs/guides/tools-computer-use
- https://developers.openai.com/api/docs/models/gpt-6-luna
- https://developers.openai.com/api/docs/models/gpt-6-sol
- https://www.orcarouter.ai/blog/gpt-6-luna-vs-gpt-6-sol
