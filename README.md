# Smart Orchestration

One globally installed adaptive Codex workflow, version **1.6.1**, from
`7Eterius/codex_smart_orchestration`. The main model owns planning, product/UX/visual
design, architecture and serious acceptance. Workers implement bounded contracts;
Archivist preserves useful current state, decisions and history. No route phrase,
project-path argument or per-repository orchestration installation is needed.

## v1.6.1: launch-benchmark tuning

OpenAI's GPT-6 Sol/Luna launch article adds direct benchmark evidence that was not
used in v1.6.0. Smart now uses GPT-6 Luna High for Routine, Luna Max for difficult
Default implementation, and GPT-6 Sol xhigh only for the Senior escalation role.
Simple, Tester, Companion, Investigator and Archivist remain unchanged.

The tuning is evidence-specific: Luna High improved AutomationBench by 5.4 points
versus its predecessor at 58% lower cost per task; Luna Max scored 66.6% on DeepSWE
and exceeded GPT-5.6 Sol Medium on OSWorld at one tenth the cost; Sol xhigh scored
33.2% on AutomationBench and 60.5% on OSWorld while remaining far cheaper than the
reported competitor baselines. These are benchmark/task-cost results, not a promise
about Codex subscription allowance or every project.

GPT-6 also preserves earlier prompt-cache reuse when reasoning effort or tool
availability changes. Smart therefore no longer keeps an unnecessary tool surface
or mismatched effort merely to protect cache. Owner-selected parent model/effort,
sandbox and approval boundaries remain untouched. See [v1.6.1 notes](docs/v1.6.1.md).

## v1.6.0: GPT-6 worker generation

All named workers now use GPT-6 Luna or GPT-6 Sol. Efforts follow OpenAI's current
model-selection guidance rather than guessed benchmark inheritance: simple Luna Low,
routine Luna Medium, difficult constrained implementation/investigation and Tester
Luna xhigh, Senior Sol Medium, and concise context/memory roles Luna Medium.

OpenAI currently prices GPT-6 Luna at $0.10/$0.01/$0.50 and GPT-6 Sol at
$2/$0.20/$10 per million Standard API input/cached/output tokens for short-context
requests. Those are API economics references, **not a conversion to the included
Codex/ChatGPT plan allowance**. Public GPT-6 Luna/Sol benchmark score tables are not
yet available, so the routing is grounded in the official workload/effort guide and
must be validated on accepted real tasks. See [v1.6.0 notes](docs/v1.6.0.md).

The parent remains owner-selected. GPT-6 Sol Medium is the documented starting
point closest to Smart's normal quality-first main role, but installation never
silently changes your parent model, effort, Plan effort, or speed.

## v1.5.3: evidence-led efficiency

Usage reporting is **opt-in**, separate from permanent project memory. Never spawn
an agent solely to generate it. The local reporter reconciles cumulative counters
instead of summing potentially repeated last-usage snapshots. Missing or ambiguous
telemetry produces an explicit limitation, not guessed totals or repeated retries.

Workers collect permitted build/navigation/screenshot evidence; main directly
judges it without routinely duplicating its collection. Keep design authorship and
independent acceptance. No model downgrades, new proxy, role, fixed cost ratio,
automatic compaction or Computer History/Computer Use permission changes.
See [v1.5.3 notes](docs/v1.5.3.md) for evidence limits, compatibility and tests.

## Capabilities and design ownership

| Role | Model / effort | Responsibility |
| --- | --- | --- |
| simple_executor | GPT-6 Luna · Low | Clear low-risk established-pattern edits |
| routine_executor | GPT-6 Luna · High | Bounded features with settled contracts |
| default_executor | GPT-6 Luna · Max | Difficult implementation and diagnosis |
| senior_executor | GPT-6 Sol · xhigh | Named hard decisions, advice or transferred implementation |
| tester | GPT-6 Luna · xhigh | Independent verification, not production repair |
| companion | GPT-6 Luna · Medium | Conditional relevant-context discovery |
| investigator | GPT-6 Luna · xhigh | Conditional unresolved evidence question |
| archivist | GPT-6 Luna · Medium | Verified current handoff, rationale and meaningful history |

The parent keeps the owner's selected model/effort. Known hard tasks start stronger,
not after a forced cheap-worker failure. Routine diagnosis stays with the Executor;
missing decisive facts, stalled progress and material decisions return to main.

Main defines purpose, hierarchy, composition, states, interactions and visual
language, then critiques actual running frames. Workers implement the settled brief
and propose rather than independently change material design. Tests, worker prose
and mockups cannot substitute for visual acceptance or required owner approval.
See [v1.5.2 design ownership](docs/v1.5.2.md) and [v1.5.1 judgment/diagnostics](docs/v1.5.1.md).

## One global install

Quit Codex. From a reviewed extracted package:

```bash
/opt/homebrew/bin/python3.11 codex_workflow/runtime/smart_install.py --apply
```

Use any Python 3.11+ interpreter elsewhere. No sudo, API key, repository search or
shell-profile edit. Without --apply the installer previews. CODEX_HOME is honored,
defaulting to ~/.codex. Restart Codex after success.

The installer preserves parent model, normal/Plan effort, speed, permissions, tools,
unrelated configuration and surrounding owner instructions. Private changed-file
backups and transactional rollback protect managed updates. Custom worker/skill
edits block overwrite for review. Project source, stores, Git and memory are not
installation targets. Missing child defaults receive GPT-6 Luna Medium and concurrency 3;
explicit owner settings remain. Named workers disable recursive delegation.

The workflow remains an instruction/configuration system, not a deterministic
scheduler. Profile/project/CLI overrides can affect actual behavior. Doctor inspects
known on-disk contracts with separate errors, warnings and unverified state; it does
not inspect sessions, resolve all overrides or prove a live model's identity.

## Verification and project memory

Edit-loop checks, independent stable-candidate acceptance and authorized release
checks are distinct. Target accessibility to affected UI/states, widening for shared
impact or uncertainty. Preserve explicit owner/repository gates. Reuse applicable
builds and evidence, not stale results inferred from HEAD alone. Independent native
checks may run in parallel; shared simulator/browser/build/data state is serialized.
See [verification guide](codex_workflow/verification.md).

Use existing canonical handoff/changelog. Archivist keeps the current goal, work in
progress, blockers/open gates, next action and evidence, with concise meaningful
history. Preserve reasons and rejected approaches in their existing canonical home;
link rather than duplicate. Read-only requests forbid memory writes. A missing usage
report does not invalidate a verified handoff.

## Optional usage diagnostics

On explicit request, main or an existing Archivist may run the local reporting skill.
Its YAML disables implicit invocation in supporting clients. Main can supply
`--root-session-id` with the task's `--deployment-id` marker, or an explicit
`--start-time` and optional `--end-time`. Nondefault CODEX_HOME is supported.

The six-column table remains compatible, but `Rollouts` means reconciled usage
updates, not proven unique model requests. JSON schema 2 adds scope, accounting and
recorded model/effort contexts. Preserve stderr interpretation notes and warnings.
Input includes its cached subset. Ambiguous last-only logs, missing baselines or
counter resets fail clearly. No quota percentage, billing total or old-report
correction is inferred. The Python calculation makes no network or model calls;
asking a model to invoke/read it still has overhead. It is not an acceptance gate.

For verbose authorized checks, prefer native structured reports or the optional
`runtime/capture_check.py` helper. It preserves private raw logs, actual exit status
and bounded excerpts without another model, implicit shell, retry or result cache.
Exit zero is not proof that required tests ran. Keep logs/arguments private; they
may contain secrets. Do not use the wrapper for servers, watchers or interactive
approval. POSIX timeout kills its group; Windows descendants may remain.

## Updates, rollback and validation

`runtime/smart_install.py --update --apply` consumes checksummed releases from this
fork only. No usable release means an error, not upstream fallback. A CI ZIP is not
a published release. Backups live in ~/.codex/.smart-orchestration-backups/.
`--restore-backup <printed-directory>` previews exact restoration; add --apply to
restore only if hashes match and no newer edits conflict. Persistent removal needs
reviewed owned-block removal, not legacy recursive uninstall or deleting Codex home.

Run all source checks before packaging (full history required for baseline fixtures):

```bash
python3.11 -B scripts/test_fork.py -v
python3.11 -B scripts/test_deployment_token_report.py -v
python3.11 -B scripts/test_verification.py -v
python3.11 -B scripts/test_v15.py -v
python3.11 -B scripts/test_v151.py -v
python3.11 -B scripts/test_v152.py -v
python3.11 -B scripts/test_v153.py -v
python3.11 -B scripts/test_v160.py -v
python3.11 -B scripts/test_v161.py -v
python3.11 -B codex_workflow/runtime/workflow.py validate --package-root codex_workflow --json
python3.11 -B scripts/package_smart.py --release-tag v1.6.1 --output-dir smart-dist
python3.11 -B scripts/package_smart.py --verify smart-dist/codex_workflow-1.6.1.zip --version 1.6.1
```

The installable package needs no Git. Automated software and policy tests do not
establish live design quality, optimal routing, savings percentages or five days
of work. Evaluate completed accepted tasks including repairs and rejected visuals.
