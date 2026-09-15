# Smart Orchestration

One globally installed adaptive Codex workflow, version **1.5.2**, from
`7Eterius/codex_smart_orchestration`. Main plans, decides and seriously audits;
Luna workers execute bounded work with parent-controlled escalation. Archivist
keeps concise permanent current state and meaningful dated history. No route
phrase, project-path argument or per-repository installation is needed.

## v1.5.2 design ownership

For design-led work, the main model owns product, UX, interaction and visual
authorship, not just coordination and final approval. It defines the experience,
reviews an early running composition, gives concrete critique and reviews final
evidence. Executors implement the settled brief and return unresolved design
choices or alternatives to main. Routine details remain within agreed patterns.
Tester separates behavior/accessibility checks from main visual judgment and
required owner approval. Archivist records the actual approval state and rationale.
Small approved tweaks reuse direction; no new designer role, mandatory competition
or model-tier change. See [v1.5.2 notes](docs/v1.5.2.md) for scope and validation.

## v1.5.1 refinements

Context expands with uncertainty, not every task. Executors keep routine diagnosis
local; the parent resolves material decisions. The existing Tester can identify
failure cases early on risky work, then independently verify the result. Archivist
preserves decision rationale in existing canonical documents. Installer and doctor
now share configuration assessment with separate errors, warnings and unverified
runtime state, including distinct normal and Plan-mode effort. All model tiers and
parent settings remain unchanged. See [v1.5.1 notes](docs/v1.5.1.md) for exact scope,
legacy-flag handling, regression coverage and unexecuted manual behavior scenarios.

## Capabilities

Simple Executor is Luna Medium; Routine Executor Luna High; difficult Default
Executor Luna Max; Senior help Sol Medium; independent Tester Luna xhigh;
conditional Companion Luna Medium and Investigator Luna High; Archivist Luna
Medium. v1.5 retains all eight role model/effort tiers and disables recursive
delegation inside each child role. Main keeps the owner's
selected model/effort. Known hard tasks can start stronger without cheap retries.
The policy is adaptive instructions, not a deterministic scheduler or a quality
or allowance guarantee. Main inspects decisive source and final actual UI images.

## Change-aware verification and orchestration hardening in 1.5

Plan relevant checks for edit loops, stable-candidate acceptance and authorized
merge/release checkpoints separately. Do not run an entire accessibility, device,
locale or screenshot matrix for every worker task. Target changed UI/interaction,
expand for shared-impact changes or unknown dependencies, and keep explicit
owner/repository gates. Do not disable rules or mark deferred checks passed.
`codex_workflow/verification.md` is read only for validation-bearing planning.

Reuse valid incremental builds, confirmed test servers and applicable evidence;
never guess freshness from HEAD alone or cache a command as proof of acceptance.
Run independent native checks in parallel only when shared state is isolated.
Keep meaningful Archivist checkpoints and independent acceptance. The new local
capture helper retains raw logs while limiting routine output in model context.
It never summarizes with another model, calls a proxy, skips a command, or infers
that exit zero means tests actually ran. See docs/verification-1.3.2.md.

## One global install

Quit Codex. From a reviewed extracted package:

```bash
/opt/homebrew/bin/python3.11 codex_workflow/runtime/smart_install.py --apply
```

Use any Python 3.11+ interpreter elsewhere. No sudo, API key, repo search or
shell-profile edit. Default without --apply previews; --check inspects disk
configuration. CODEX_HOME is honored, otherwise ~/.codex is used.

The v1.5 installer preserves parent model/effort/speed, permissions,
tools, unrelated configuration and surrounding owner instructions. Private backups
and transactional rollback protect managed changes. Custom worker edits block
replacement for review. Application source, stores, Git state and project memory
are not installation targets. Restart Codex after a successful application.

Profile/project/CLI overrides can change effective settings. Neither on-disk files
nor a model's self-reported name prove runtime role/model selection. Global startup
supersedes only legacy workflow procedure, never project product/safety rules.
No shorter context or global output cap, third-party gateway or summarizer is installed.

When child defaults are absent, v1.5 installs a conservative three-thread cap
with Luna Medium fallbacks while preserving explicit owner settings. Named child
roles disable recursive delegation. `runtime/doctor.py` provides a read-only
on-disk contract check, and named installation backups can be restored with the
conflict-checked `smart_install.py --restore-backup <backup>` flow.

## Output capture

Prefer existing structured reporters. For a verbose finite check:

```bash
python3.11 ~/.codex/codex_workflow/runtime/capture_check.py --timeout 600 -- command args
```

Runs exact argv with no implicit shell and no retry. Returns actual command exit,
duration, raw-log path/hash and bounded heuristic excerpts. Logs and JSON receipt
are private under a unique temporary directory, or an existing --artifacts parent.
No environment dump. Logs/arguments may contain secrets: do not publish them.
Failure, timeout or zero-tests ambiguity requires original evidence/native reports.
This wrapper is for authorized noninteractive checks, not watchers, servers,
interactive approvals or detached daemons. Timeout kills its process group on
POSIX; Windows only kills the immediate process and reports that limitation.
No automatic deletion of evidence or claim that the excerpt finds every issue.

## Memory, updates and testing

Use existing canonical handoff/changelog. Read current state, not all history;
append meaningful checkpoint deltas without inventing completion. Read-only tasks
forbid memory writes. Missing persistence is reported, not guessed into app-data.

`runtime/smart_install.py --update --apply` consumes checksummed releases from
this fork only. A CI ZIP is not a published release. No upstream fallback.
Backups live at ~/.codex/.smart-orchestration-backups/ with changed-path/hash
manifests. Reconcile newer owner edits before restoration. Persistent removal
requires reviewed owned-block removal, not legacy recursive uninstall.

Canonical checks:

```bash
python3.11 -B scripts/test_fork.py -v
python3.11 -B scripts/test_deployment_token_report.py -v
python3.11 -B scripts/test_verification.py -v
python3.11 -B scripts/test_v15.py -v
python3.11 -B scripts/test_v151.py -v
python3.11 -B scripts/test_v152.py -v
python3.11 -B codex_workflow/runtime/workflow.py validate --package-root codex_workflow --json
python3.11 -B scripts/package_smart.py --release-tag v1.5.2 --output-dir smart-dist
python3.11 -B scripts/package_smart.py --verify smart-dist/codex_workflow-1.5.2.zip --version 1.5.2
```

Source migration fixtures need full history; package installation needs no Git.
Prior tests remain; v1.5.2 adds design-role contracts and verified v1.5.1 upgrade,
repeat-install, rollback and unchanged-runtime/configuration regression coverage.
Software tests do not prove unchanged app quality or a five-day usage improvement.
