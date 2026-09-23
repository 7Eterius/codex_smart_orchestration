# Global lifecycle

Use Python 3.11+. Install a reviewed package with `runtime/smart_install.py --apply`.
No project list, repository scan, sudo or API key. An agent running inside Codex must
not quit, relaunch or wait for Codex to exit during installation. Apply in the current
session, let the command finish, then tell the user to restart Codex manually.
Without --apply, operations preview. CODEX_HOME is honored.

v1.5 adds missing child defaults (Luna Medium and concurrency 3), preserves explicit
owner settings, and disables recursive delegation in the eight role configs.
Parent model/effort/speed, approvals and tools remain untouched. Unusual config or
customized managed files require review, not forced replacement. Diagnostic:
`runtime/doctor.py` checks known on-disk files without reading chats or projects.
Its result does not establish live model/agent behavior or available allowance.

`codex_workflow --install`: use this global installer, never project bootstrap.
For the current main-branch distribution flow, apply the extracted `codex_workflow`
package directly with `--package-root ... --apply`. Do not route that flow through
release acquisition. The legacy `--update` and `--check-update` paths remain
release-based and are not the main-branch installer.

Each change creates a private changed-file backup. For a reviewed rollback:
`runtime/smart_install.py --restore-backup <printed-backup-directory>` previews;
add `--apply` to restore. It verifies backup hashes and current post-install bytes,
refuses newer conflicting edits, and backs up the restoration. Do not delete the
whole Codex home or source backups. A rollback is not a generic factory reset.

For `--disable` or `--remove`, do not invoke legacy recursive removal. A one-task
no-agent request is supported; persistent deactivation requires a reviewed surgical
removal of owned startup blocks, not deletion of memory, credentials or sessions.
For `--enable`/`--personal`, preserve explicit user preferences and distinguish
session choices from persistent installation. Do not claim unsupported lifecycle
commands were completed. Project product rules remain ordinary local instructions.


## In-app installation rule

The global installer is designed to complete while the current Codex session is still
running. Managed file writes are conflict-checked and applied with atomic per-file
replacement. Never build a detached helper that waits for Codex to terminate, and
never use AppleScript, `kill`, `pkill`, `open -a`, or equivalent process control
as part of the installation procedure.

After a successful apply, report success and instruct the user to restart Codex
manually so the new configuration is loaded. If a managed file changes between
preview/preparation and apply, stop and report the conflict instead of trying to close
Codex or force the write.
