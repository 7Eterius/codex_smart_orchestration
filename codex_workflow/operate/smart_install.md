# Global installation

Smart Orchestration is a global Codex workflow. There is no per-project bootstrap,
project documentation scaffold, release updater, or route-selection layer.

Use Python 3.11 or newer. Install from a reviewed/extracted source package with:

```text
python3 codex_workflow/runtime/smart_install.py --package-root codex_workflow
python3 codex_workflow/runtime/smart_install.py --package-root codex_workflow --apply
```

The first command is a preview and performs the same package/configuration conflict
checks without writing. Apply only if the preview is clean.

An agent running inside Codex must not quit, relaunch, or wait for Codex to exit during
installation. Let `--apply` finish in the current session, report its result, then tell
the user to restart Codex manually.

The installer owns only:
- `~/.codex/codex_workflow/`
- the eight Smart worker TOMLs under `~/.codex/agents/`
- the Smart managed region in `~/.codex/AGENTS.md`
- the Smart developer-instructions region and absent child defaults in `config.toml`

It preserves parent model/effort/speed, approvals, tools, unrelated configuration,
unowned workers/skills, projects, Git state and project files. Changed managed files
cause a conflict instead of forced replacement.

Each successful write creates a private changed-file backup under
`~/.codex/.smart-orchestration-backups/`. Preview a rollback with:

```text
python3 codex_workflow/runtime/smart_install.py --restore-backup <backup-directory>
```

Add `--apply` only after reviewing it. Rollback is exact and conflict-checked.

The installer can clean files that an older Smart/codex_workflow installation recorded
as workflow-owned. If a retired file no longer matches its recorded or historical
workflow bytes, it is preserved and reported instead of deleted.

Do not use AppleScript, `kill`, `pkill`, `open -a`, detached wait helpers, GitHub
Releases, historical `dist/` archives, or another repository as part of the current
main-branch installation flow.
