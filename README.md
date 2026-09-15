# Smart Orchestration

One globally installed adaptive Codex workflow, version **1.3.1**, from
`7Eterius/codex_smart_orchestration`. No Heavy/Medium route selection and no
per-repository install. Main plans, makes architecture decisions and seriously
audits the result. Workers execute bounded assignments; Archivist keeps concise
permanent project state and meaningful dated history.

## Capability and quality

| Role | Model / effort | Assignment |
| --- | --- | --- |
| simple_executor | Luna Medium | Clear, reversible low-risk edits with decisive checks |
| routine_executor | Luna High | Bounded feature work with settled contracts |
| default_executor | Luna Max | Difficult implementation or higher-effort Luna help |
| senior_executor | Sol Medium | Named hard decisions, advice or transferred ownership |
| tester | Luna xhigh | Independent verification, not production repair |
| companion | Luna Medium | Conditional relevant-context discovery |
| investigator | Luna High | Conditional unresolved evidence question |
| archivist | Luna Medium | Verified current handoff and concise changelog |

The parent retains its selected model and effort. Sol Low is a practical baseline
for an owner already succeeding with it; Astra remains available for harder
planning/audit. No model is guaranteed best on every task. Known hard work starts
stronger, not after a forced cheap-model failure. Parent supplies missing context,
requests senior advice or transfers ownership after stopping the old writer.

Main directly audits decisive source and final running-product screenshots.
Independent testing, financial/security truth, data safety, owner scope and open
acceptance gates remain intact. Lower effort is not a license to weaken checks.
The adaptive allocation is an instruction policy, not a deterministic scheduler.

## One global install

Quit Codex. From a reviewed extracted package, run:

```bash
/opt/homebrew/bin/python3.11 codex_workflow/runtime/smart_install.py --apply
```

Use another Python 3.11+ interpreter elsewhere. No project argument, repository
search, sudo, new API key or shell-profile change. Without --apply it previews;
--check verifies disk configuration. CODEX_HOME is honored, defaulting to ~/.codex.

The unchanged installer preserves parent model/effort/speed, permissions, tools,
unrelated configuration and surrounding owner instructions. It replaces only
managed global/runtime files with private backups and transactional rollback.
It refuses custom worker edits for review instead of silently overwriting them.
Project source, stores, Git state and memory are not installation targets.

Restart Codex. A substantive task should identify **Smart Orchestration**.
A name or on-disk file does not prove actual runtime role selection; inspect
observable metadata when available. Project/profile/CLI overrides can change
effective global settings and are not silently removed. The owned bootstrap
supersedes only legacy workflow procedure, never repository product/safety rules.

Prefer Standard speed for allowance efficiency; use /fast off where supported.
Installation does not silently alter your speed selection. The new read-only
runtime/efficiency.py can show configured tiers, dated base-credit comparisons
and pacing arithmetic. It does not read account limits or estimate weekly quota
from tokens. See docs/efficiency-1.3.1.md for sources and limitations.

## Memory

Use existing canonical project handoff/changelog. At meaningful authorized
completed/paused/blocked checkpoints, Archivist updates current goal, done and
in-progress work, blockers/open gates, next action and evidence references,
then appends a concise dated delta. Do not repeatedly ingest the whole changelog
or duplicate current state across files. Preserve old decisions and history.
Read-only tasks forbid memory writes. Missing persistence is reported honestly.

## Updates, rollback and verification

runtime/smart_install.py --update --apply uses checksummed releases from this
renamed fork only. No usable release means an explicit error, not an upstream
fallback. A CI ZIP is not a published release. Use the Smart installer, not
legacy per-project lifecycle commands. Old route files are compatibility
redirects to smart_orchestration.md, not alternative workflows.

Private backups live under ~/.codex/.smart-orchestration-backups/ and record
changed paths and hashes. Before restoration, quit agents and compare current
files to the manifest; reconcile newer owner edits rather than overwrite an
entire old Codex home. Persistent disable/uninstall still requires a reviewed
owned-block removal, not the legacy recursive removal command.

Canonical source checks:

```bash
python3.11 -B scripts/test_fork.py -v
python3.11 -B scripts/test_deployment_token_report.py -v
python3.11 -B codex_workflow/runtime/workflow.py validate --package-root codex_workflow --json
python3.11 -B scripts/package_smart.py --release-tag v1.3.1 --output-dir smart-dist
python3.11 -B scripts/package_smart.py --verify smart-dist/codex_workflow-1.3.1.zip --version 1.3.1
```

Full history is required only for the source suite's baseline migration fixture;
the global installable package needs no Git. See docs/smart_orchestration.md for
baseline contracts and docs/efficiency-1.3.1.md for this revision. No measured
savings, equal-quality guarantee or five-day work-capacity guarantee is claimed.
