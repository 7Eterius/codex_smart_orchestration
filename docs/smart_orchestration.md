# Smart Orchestration engineering notes

## Changes from Quality Economy 1.2

The canonical parent workflow is `codex_workflow/smart_orchestration.md`.
Global activation is shipped, not a manual local patch. `smart_install.py` performs
user-level adoption only and never reads/writes project roots. Its small owned
bootstrap is appended to existing top-level developer instructions via a validated
TOML edit; all other parsed settings must compare equal. Existing managed global
AGENTS is replaced without dropping surrounding owner instructions. An existing
AGENTS override or profile can still change effective behavior and is not erased.

Source discovery and documentation are no longer mandatory support-agent ceremonies.
Only current relevant handoff/contracts are loaded. A simple worker (Luna Medium)
is added; complex implementation and independent verification retain their stronger
prior settings. Lower-effort context and archival roles escalate evidence conflicts
instead of guessing. Main retains all architecture and final acceptance decisions.

The Archivist owns assigned current-state and changelog updates. This deliberately
supersedes generic old workflow ownership of three mandatory state documents, not
a project's actual product or data rules. Existing canonical docs are reused and
older history remains preserved. Memory is neither a repo installation nor an
excuse to mutate a read-only task. Pure questions do not generate changelog noise.

## Promotion semantics

Selection is performed by the main model against clear role contracts. No model
confidence threshold is invented. The evidence packet is expected versus observed,
smallest reproduction, attempted fix and the missing fact/decision. Context gaps
are supplied before needless promotion. Known difficult/risky tasks can start with
a stronger role. Promotion uses a new configured role; it is not an in-place model
switch. Stop prior writers first. Advice-only Senior assignments remain read-only
by their capsule; the same Senior role permits writes only on explicit transfer.
Subagent model/effort configuration must be observed where runtime metadata permits;
the model saying its name is not independent verification.

## Test compatibility

`scripts/test_fork.py` keeps inherited functional tests. The one old monolithic
route-text test is superseded by explicit Smart contracts. The inherited fixed
settings test retains its capability/rendering assertions but now checks no-history
closure. The historical-project fixture uses a next version and the current title.
The archived Quality Economy-specific test file is historical, not the canonical
suite. No runtime failure is caught and reclassified as a pass.

`scripts/package_smart.py` supplies the canonical role set from runtime.layout to
the inherited packager. This removes its duplicated six-role assumption; archive
path traversal, completeness, unexpected-role, checksum and full package validation
checks are retained. simple_executor is required, not ignored as an unknown file.

## Current limits

Automated tests are not live model evaluations. Less instruction text is not an
exact allowance-saving percentage. Project AGENTS files still load through Codex;
this global change removes conflicting workflow procedure, not all local context.
Profile/project/CLI overrides may supersede global configuration. No credentials,
parent-model selection, tool permissions or service tier are changed by installation.

Backups record changed files only, with private permissions. Installation is
idempotent and fails closed on custom worker changes, stale targets, invalid TOML,
unknown markers, disabled subagents, unsafe symlinks and competing installers.
Source/package validation precedes mutation. The compensating transaction handles
write failures; keep Codex stopped because the installer lock is not an agent lock.
Update acquire/checksums are inherited from the fork-only release module.

## Primary configuration references

Verified when preparing this revision; these document Codex behavior, not benchmark
claims for this workflow:
- https://developers.openai.com/codex/subagents/
- https://developers.openai.com/codex/guides/agents-md/
- https://developers.openai.com/codex/config-reference/
