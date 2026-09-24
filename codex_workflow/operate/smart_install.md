# Global installation and update

Use Python 3.11+. Current `main` in `7Eterius/codex_smart_orchestration` is the normal
distribution channel: resolve HEAD once, download that exact source snapshot and safely
extract it outside real projects. A source upgrade bundle must first be applied to a
reviewed source checkout; its payload alone is not a complete installable package.
Never use historical dist archives, a different repository or a guessed release.

From the complete source repository root, preview then apply:

```text
python3 -B codex_workflow/runtime/smart_install.py --package-root codex_workflow
python3 -B codex_workflow/runtime/smart_install.py --package-root codex_workflow --apply
python3 -B codex_workflow/runtime/smart_install.py --check
```

Use the same verified interpreter and source for both steps. Preview validates package,
eight named roles, current managed-file conflicts and existing configuration without
writes. Apply only a clean result. On conflicts stop, do not force, delete locks or
uninstall first. Updates from source at the same version are supported.

An agent inside Codex must not quit, relaunch, or wait for Codex to exit during installation.
Let the command complete in this session and inspect its exit status/JSON. Then ask the
user to restart Codex manually. Never create detached wait helpers or use AppleScript,
kill/pkill or app relaunch. Avoid simultaneous configuration changes; replacement is
atomic per file with compensating rollback, not a single instant for all readers.

The installer honors `CODEX_HOME` (default `~/.codex`). It owns only declared workflow
runtime files, its named worker copies, the global managed AGENTS region, the Smart
bootstrap and absent generic child defaults. It preserves explicit parent/model/effort/
speed, tools, permissions, cap and generic fallback choices. It never edits projects.
An older generic child model is warned about, not silently changed. Use named roles.

## What the result means

Report version, selected Git source commit when known, package fingerprint, backup,
warnings and disk check. The fingerprint identifies bytes, not an authenticated Git
commit. `execution_policy: adaptive` describes installed policy; `runtime_observation:
not_inspected` is not an activation failure or an execution-mode gate. No disk check
can prove live role selection, permission inheritance, thread availability or savings.

After manual restart, describe the actual available owner/reviewer when beginning
substantive work. Use `runtime_check.md` only for a needed uncertain mechanism. Do not
run an expensive full qualification or audit during every install. Direct named workers
remain the route when delegated review has not been demonstrated.

## Safe retirement and rollback

Every successful write creates a private changed-file backup under
`CODEX_HOME/.smart-orchestration-backups/`. Preview a named restoration:

```text
python3 -B codex_workflow/runtime/smart_install.py --restore-backup <backup-directory>
```

Add `--apply` only after review. Later local edits block restoration; rollback is itself
backed up. Preserve source caches and older rollback history.

2.2 retires the dedicated chunk_lead and old mode/qualification guides. A previously
owned worker is removed only if its live bytes match a verified previous template;
modified/unverifiable retired workers block the update for review. Unowned workers are
not adopted or deleted. Retired runtime files with unverified edits are preserved and
reported. Preserved historical files are not active policy. A marker alone never grants
permission to wipe a directory. Runtime installation does not close old live Codex
threads; their supported lifecycle or the user's manual restart is separate.
