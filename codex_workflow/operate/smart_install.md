# Global lifecycle

Use Python 3.11+. Install a reviewed package with `runtime/smart_install.py --apply`.
No project list, repository scan, sudo or API key. Quit Codex before applying.
Without --apply, operations preview. CODEX_HOME is honored; restart after changes.

v1.5 adds missing child defaults (Luna Medium and concurrency 3), preserves explicit
owner settings, and disables recursive delegation in the eight role configs.
Parent model/effort/speed, approvals and tools remain untouched. Unusual config or
customized managed files require review, not forced replacement. Diagnostic:
`runtime/doctor.py` checks known on-disk files without reading chats or projects.
Its result does not establish live model/agent behavior or available allowance.

`codex_workflow --install`: use this global installer, never project bootstrap.
`--update`: `runtime/smart_install.py --update --apply` uses this fork's verified
release and incoming installer. `--check-update`: read the fork's release metadata
without installing. A source version/CI artifact is not a published release.
No usable release means an explicit limitation, never upstream fallback.

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
