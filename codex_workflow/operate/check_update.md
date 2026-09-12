# Check Quality Economy Updates

For the exact prompt `codex_workflow --check-update`, run:

```text
python3 ~/.codex/codex_workflow/runtime/workflow.py check-update --json
```

Use Python 3.11 or newer. This operation reads release metadata without installing.
The source is `7Eterius/codex_workflow` only. Report the installed and available
versions and the returned release summaries. If the fork has no usable release
with a matching ZIP and `SHA256SUMS`, report that limitation; do not silently
switch to upstream or promise a release exists. Never perform an update merely
because the user asked to check.
