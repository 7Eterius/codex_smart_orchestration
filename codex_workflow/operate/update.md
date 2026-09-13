# Quality Economy Update

Supported prompt: `codex_workflow --update`.
Use Python 3.11 or newer and the installed lifecycle CLI.

Release source is ONLY `7Eterius/codex_workflow`. Query that fork's releases,
select the highest usable non-draft SemVer release with a matching universal
ZIP and `SHA256SUMS`, verify its checksum and extract safely. Include prereleases.
If none exists or the network fails, report the error; never fetch upstream as
fallback or install a historical `dist/` ZIP. Routine release updates do not
clone repositories. Initial reviewed source adoption is a separate procedure.

```text
python3 ~/.codex/codex_workflow/runtime/workflow.py update --project <project>
```

The incoming CLI owns package validation. Preserve unrelated configuration,
skills and workers, project documents, personalization, project-local rules,
source backups and enabled/disabled state. Replace only workflow-managed release
inputs through the inherited transaction and verified timestamped backup.
Report the installed version, backup location and failures accurately.

Do not reset or reconstruct owner instructions automatically when drift is
reported. Use the inherited `--legacy-local-instructions <reviewed-file>` option
only after explicitly reviewing a legacy migration. `--allow-downgrade` requires
an intentional reviewed downgrade. A partial or rolled-back update is not success.

A source takeover from upstream must run the incoming fork's reviewed adoption
helper or incoming CLI, not rely on an old upstream launcher choosing this fork.
The native Heavy/Quality Economy defaults require no extra personalization step.
