# Global installation and update

Use Python 3.11 or newer. Current `main` in `7Eterius/codex_smart_orchestration` is
the distribution channel. Resolve its HEAD once, obtain that exact source archive,
and safely extract it to a temporary directory. A commit pin identifies the selected
snapshot; it is not a separately signed release checksum. Never use historical ZIPs,
release fallbacks, another repository or an existing project checkout as scratch.

From the extracted repository root, preview and then apply:

```text
python3 -B codex_workflow/runtime/smart_install.py --package-root codex_workflow
python3 -B codex_workflow/runtime/smart_install.py --package-root codex_workflow --apply
```

Use the same verified Python interpreter and extracted package for both commands.
Preview validates the complete package, nine named roles, owned-file conflicts and
configuration. It writes nothing. Apply only a clean plan; on an error stop without
forcing replacement or deleting a stale lock. An explicit lower capacity or different
parent model is preserved, not silently "optimized".

An agent inside Codex must not quit, relaunch, or wait for Codex to exit during
installation. Finish `--apply` in the current session, inspect its exit status and
JSON, then ask the user to restart Codex manually. Do not create detached wait helpers
or run AppleScript, kill/pkill, relaunch or other app-control commands. Avoid simultaneous
configuration edits; writes are atomic per file, not an instantaneous multi-file switch.

The installer respects `CODEX_HOME`, otherwise `~/.codex`. It changes only declared
Smart runtime files, nine worker TOMLs, the managed global AGENTS region and Smart's
developer-instructions block plus absent child defaults. It preserves unrelated
configuration, explicit parent/permission/tool settings and all project files.
It never grants itself full access or scans repositories.

After applying, use the extracted installer for read-only disk verification:

```text
python3 -B codex_workflow/runtime/smart_install.py --check
```

A successful disk check is not live activation. Report installed version, selected
Git commit, package fingerprint, backup location, warnings and any unverified runtime
capabilities. The package fingerprint is content identity, not a Git authentication
claim. Restart manually before using new roles. Normal needs no nested qualification;
Coordinated uses the bundled `qualification.md` once per materially changed arrangement.

Update by repeating the same pinned-main preview/apply flow. Same-version source changes
are supported. No uninstall, tag or formal release is required.

## Backups and safe retirement

Every applied change has a private exact changed-file backup under
`~/.codex/.smart-orchestration-backups/` (or `CODEX_HOME`). To preview one named rollback:

```text
python3 -B codex_workflow/runtime/smart_install.py --restore-backup <backup-directory>
```

Add `--apply` only for the reviewed rollback. It rejects later conflicting edits and
creates its own backup. Do not wipe the Codex home, original source caches or backups.

Current owned-file edits block overwrite. Retired runtime files are removed only when
recorded hashes or verified historical originals match; changed/unknown retired files
are preserved with warnings. A skill ownership comment alone never authorizes directory
clearing. Unrelated files and historical source caches remain intact. Cleanup beyond
these exact verified managed changes requires separate authority.
