# Smart Orchestration engineering notes

## v1.8 operating model

The canonical parent workflow is `codex_workflow/smart_orchestration.md`. Global
activation remains a small validated bootstrap; project product, safety and acceptance
rules stay authoritative.

v1.8 keeps the eight named GPT-6 roles. Routine Luna High is the primary bounded
implementation lane. Default Luna Max is a rare deep-work lane. Senior Sol xhigh stays
advisory-first and takes production ownership only when hard judgment and implementation
cannot be separated. The installer never rewrites the owner's parent model, effort,
speed, approvals or tool permissions.

For manually selected GPT-6 Sol parents, Medium is the documented cost/quality
baseline. Supported runtimes may raise reasoning effort around one hard decision and
then lower it while retaining the earlier cached prefix. Smart does not emulate this
with undocumented Codex configuration.

## Context and tools

Workers receive bounded capsules with `fork_turns="none"` and follow-ups send deltas.
Companion, Investigator and Archivist distinguish sourced facts, inference and unknown
evidence.

When available, deferred tool loading/tool search is preferred to carrying irrelevant
schemas. Async slow I/O can replace a waiting worker, but GPT-6 multi-agent mode must
not combine async tools with parallel tool calls. These are runtime capabilities, not
new static TOML keys in this package.

## Browser and Computer Use

Local web verification starts with source/tests and Browser DOM, console and network
evidence. Computer Use is for native or GUI-only behavior, simulators, system settings
and multi-app journeys. GUI checks are batched around stable candidates. The main owns
visual/product acceptance. Astra remains owner-selected for genuinely difficult
screenshot or spatial visual judgment, not a default Computer Use model.

## Installation and safety

`smart_install.py` performs user-level adoption only and never scans or mutates
project roots. Existing owner configuration is preserved. Backups contain changed
files only, installation is idempotent, and custom managed-worker edits require
review rather than forced replacement.

Automated tests validate package, migration and policy contracts, not live model
quality or subscription lifespan.

## Primary configuration references

- https://developers.openai.com/codex/subagents/
- https://developers.openai.com/codex/guides/agents-md/
- https://developers.openai.com/codex/config-reference/
- https://developers.openai.com/codex/app/browser
- https://developers.openai.com/codex/app/computer-use
- https://developers.openai.com/api/docs/guides/model-selection
