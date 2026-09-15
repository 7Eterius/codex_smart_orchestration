# Smart Orchestration

One globally installed adaptive Codex workflow, version **1.3.0**. No Heavy,
Medium or Light route selection and no per-repository setup. The main model
plans, makes architectural decisions, seriously audits the result and accepts
it. Narrow workers execute; the Archivist keeps permanent concise project memory.

## How it works

Clear low-risk tasks can use `simple_executor` (Luna Medium). Nontrivial work uses
`default_executor` (Luna Max). A named hard problem can go straight to
`senior_executor` (Sol Medium). After a focused failure, main distinguishes missing
context, capability gaps and environment blockers. It can obtain read-only senior
advice for the original worker or transfer ownership. It does not blindly retry,
force cheap workers to fail on known hard tasks, or pretend to switch an existing
worker's model. Main keeps its owner-selected model and effort.

The independent Tester stays Luna xhigh. Companion (Luna Medium) and Investigator
(Luna High) are conditional. Archivist (Luna Medium) updates a concise current
handoff and dated changelog at meaningful completed, paused or blocked checkpoints.
It does not ingest all history every turn, duplicate current state across files,
invent completion, delete old records or write during a read-only request.

Capsules contain Task ID, goal, owned paths, relevant facts, invariants and done
checks. Follow-ups are deltas. Context is relevant, not arbitrarily truncated.
The main directly inspects decisive diffs and running-product screenshots.
Existing financial, security, permission, data, visual and acceptance constraints
remain binding. No measured savings or equal-quality guarantee is implied.

## One global install

Quit Codex first. From the reviewed/extracted package, run:

```bash
/opt/homebrew/bin/python3.11 codex_workflow/runtime/smart_install.py --apply
```

Use another Python 3.11+ interpreter where appropriate. No project argument,
source-repository search, `sudo`, shell-profile change or API key is needed.
Without `--apply`, the installer previews. `--check` verifies disk configuration.
The installer uses CODEX_HOME when set, otherwise `~/.codex`.

It replaces the owned global instruction region and installs a small documented
`developer_instructions` bootstrap. This handles only legacy workflow routing,
intake and bookkeeping conflicts; it does not override repository product/safety
rules or explicit owner requests. Named worker configs have their own concise
instructions so child agents do not initialize another orchestration tree.

Only Codex-home workflow surfaces are modified. Existing parent model, effort,
speed, permissions, tools, unrelated configuration and owner instruction text are
preserved. Private backups are outside the managed runtime at
`~/.codex/.smart-orchestration-backups/`. A transaction rolls back failed writes.
The installer rejects custom worker tuning/collisions for review instead of
silently discarding it, rejects unsafe symlinks and has an installer lock. The
lock does not stop active Codex agents: quit Codex before applying.

Restart Codex after installation. A substantive task should identify itself as
**Smart Orchestration**. On-disk settings and a self-reported name do not prove
actual role/model selection; verify observable runtime metadata when available.
Repository/CLI/profile configuration can override global configuration. Profile
conflicts found in global config are reported, not silently rewritten. No claim
is made that global AGENTS text magically outranks project guidance.

Project memory remains project-specific, but is not an installation prerequisite.
Existing canonical docs are reused. New current-state/changelog files are created
only at an authorized meaningful checkpoint in an identified source workspace.
An unavailable/read-only memory store is reported honestly; no app-data folders
are used as guessed repository roots.

## Updates and compatibility

Updates use this fork only. `runtime/smart_install.py --update --apply` acquires a
checksummed fork release and applies globally. No usable published release means
an explicit error, not an upstream fallback. A CI artifact is not a release.
The original runtime/lifecycle remains for historical compatibility; use the Smart
installer rather than legacy per-project commands. Heavy/Medium files are short
redirects to the one canonical `smart_orchestration.md`, not alternative workflows.
The legacy marker/role names are compatibility identifiers, not the visible name.

Backups preserve exact previous bytes and a path/hash manifest. For restoration,
quit Codex, compare the manifest's post-install hashes with current target bytes,
and restore only reviewed changed files. If newer edits differ, reconcile them
rather than overwrite a whole old Codex home. Persistent uninstall/disable is not
a new CLI feature in this revision; do not run legacy recursive removal as a
substitute. An explicit no-agent request still disables orchestration for a task.

## Validation

```bash
python3.11 -B scripts/test_fork.py -v
python3.11 -B scripts/test_deployment_token_report.py -v
python3.11 -B codex_workflow/runtime/workflow.py validate --package-root codex_workflow --json
python3.11 -B scripts/package_smart.py --release-tag v1.3.0 --output-dir smart-dist
python3.11 -B scripts/package_smart.py --verify smart-dist/codex_workflow-1.3.0.zip --version 1.3.0
```

The inherited functional/safety tests remain, apart from documented old-policy
assertion replacements. Native tests cover role settings, escalation contracts,
main audit, retained memory, TOML preservation, idempotence, failed-write rollback,
unsafe paths, custom overrides, and a real v1.2 global takeover without modifying
the project. Full-history checkout is needed for the baseline migration fixture;
the installable package itself needs no Git. See `docs/smart_orchestration.md`.

This is a prompt/configuration orchestrator, not a hard deterministic scheduler.
Tests validate software and contracts; real-task quality, routing adherence and
allowance savings still require representative deployments.
