# Native Quality Economy migration

## What is replaced

The shared workflow runtime, managed project instructions and route documents
become the 7Eterius edition. Model/worker capabilities and the inherited lifecycle
schema remain unchanged. Release discovery is pinned to the fork. Ownership IDs
retain their upstream names for compatibility with existing recoverable installs.

Do not install the earlier opt-in profile on top of this native edition. Heavy
and Quality Economy are defaults after project initialization, not per-prompt
switches. Explicit project routing overrides still take precedence; review any
such preference rather than silently deleting it.

## Preflight and adoption

Keep the reviewed source checkout outside application projects. Stop active
Codex agents. Run the fork suite, token-report suite and package validator from
the checkout before touching your real Codex home. Do not treat unavailable tests
as passes. The source helper requires Python 3.11 or newer.

Run `scripts/install_quality_economy.py` with explicit `--project` arguments.
The default is preview only. Review every planned path, warnings, documentation
actions, version and backup location. Apply the same command with `--apply` and
`--approve` using the printed approval hash. Changed inputs invalidate approval.
The hash is not a lock: keep agents stopped until application is finished.

The helper preflights every target before writes, rejects conflicting writes,
and applies the combined inherited compensating transaction. Existing updates
use lifecycle backups. Fresh document scaffolds still require the returned
Archivist actions. Disabled projects stay disabled. No application Git commands,
source modifications or live-store operations are performed.

A project containing old `Codex_Workflow` staging files is refused rather than
silently cleaned. Move reviewed staging material outside the project first.
Malformed markers, unreconciled personalization, missing historical source, or
a newer installed version block adoption. Do not delete instructions or force a
downgrade. Older unstructured local modifications need the inherited explicit
legacy migration, not automated inference.

The first target can update the shared runtime; other old projects can then be
adopted with the same helper. Do not use an old upstream launcher to select a
fork release: it still points to upstream until the takeover has completed.

## After adoption

Check the installed `operate/VERSION`, user command marker, fork-only
`runtime/release.py` and generated project's Heavy default. Review the
`agent_actions` result and complete required initialization. Restart Codex.
A raw local lifecycle success is not evidence of LLM or UI quality.

Until a fork release has both a matching universal ZIP and `SHA256SUMS`, normal
update discovery reports no usable release. This is intentional; no upstream
fallback exists. Files under the old `dist/` directory are not new fork builds.

## Rollback

The migration does not uninstall first. Existing lifecycle backups and historical
source remain available. Record the printed backup directories. Before rollback,
stop agents and compare backed-up managed files with current state. Restore only
reviewed workflow-managed state; preserve newer local preferences, unrelated
Codex configuration, project documents and owner source. Do not restore an entire
old Codex home over newer sessions, skills or credentials.

For source-level rollback, revert the fork change in Git and build the intended
version using a deliberate version policy. Normal updates reject unintended
downgrades. Never work around that protection by deleting version markers.
