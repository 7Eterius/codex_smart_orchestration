# Codex Workflow - Quality Economy

Native **Heavy-by-default** edition of `7Eterius/codex_workflow`, based on
`viettran-edgeAI/codex_workflow` at `6d9b06f73bee7f899001b0bb102c70529a24313f`.

Describe the work. No `use Heavy route` prefix, opt-in profile, or per-prompt
activation is needed in an initialized project. Quality Economy is built into
the installed project and route instructions, not appended personalization.

## Behavior

Substantive work keeps the capable parent, configured Luna production workers,
independent Tester, persistent Companion and recoverable Archivist handoff.
One coherent production owner is the default; additional workers need a concrete
reason. Quality, correct semantics, safety, independent evidence and visual
acceptance come before speed. Worker models and reasoning are unchanged.

Complete questions and small bounded leaf requests use Heavy's worker-free
fast path. They do not start a deployment ceremony. Explicit Light and Medium
remain available; a new session defaults to Heavy. Existing deliberate project
routing overrides are preserved and remain effective.

The main reads core project and owner documents, then relevant module contracts.
Companion locates affected dependencies and cross-cutting constraints. Unknown
impact broadens intake. Evidence is reused only when known applicable and fresh;
changed shared code invalidates relevant prior checks. The main examines final
running-product screenshots itself. Closing Archivists receive exact evidence
and state references instead of an automatic 200-turn inherited transcript.

No model-budget formula or equal-quality savings claim is implied. Measure
complete accepted deployments, rework, token reports and account-allowance
changes. Serial execution alone does not save tokens.

## First adoption from source

Use Python 3.11 or newer. Keep this checkout OUTSIDE application projects and
stop their Codex agents before applying. Use a reviewed commit from a full-history
Git checkout of this fork. The migration tests read the pinned upstream baseline
from local Git history; an extracted source archive alone cannot run that suite.
Do not install old ZIP files under `dist/`: those are historical upstream assets.

From the root of the reviewed checkout, first validate and run tests:

```bash
python3 -B scripts/test_fork.py -v
python3 -B scripts/test_deployment_token_report.py -v
python3 -B codex_workflow/runtime/workflow.py validate --package-root codex_workflow --json
```

Preview adoption for the explicit project directories:

```bash
python3 -B scripts/install_quality_economy.py \
  --project "/absolute/path/to/Materia" \
  --project "/absolute/path/to/RussianReading"
```

Review the paths, warnings, preserved preferences and backup locations. To apply,
repeat that command with `--apply --approve SHA_FROM_REVIEWED_PREVIEW`.
The helper rejects changed preview inputs and uses the inherited compensating
transaction for the combined plan. It does not run Git, change application
source or touch live stores. Stop agents: approval hashing is not a file lock.

A healthy existing upstream install can be adopted in place. Uninstalling first
is unnecessary and loses useful source-backup context. The helper preflights all
explicit project targets, preserves local rules, personalization, disabled state
and durable project documents, and takes lifecycle backups for an existing
runtime. It supports adopting another older project after the shared runtime
has already been updated. A malformed or unrecognized install must be repaired,
not blindly overwritten. Never delete `~/.codex` or `agent_docs/` to force it.

The earlier optional `### Quality Economy v1` personalization block, if present,
must be removed through personalization before adoption to avoid duplicate or
contradictory rules. Preserve unrelated preferences. Native defaults need no
replacement profile.

After application, inspect the JSON `agent_actions`. Fresh/unfinished project
documentation must be initialized by Archivist as specified in
`codex_workflow/operate/install.md`. An installer success alone does not mean
project-context initialization has completed. Restart Codex, then describe work
normally. The helper never selects your parent model or changes its speed.
Sol Medium with Standard speed is a reasonable initial selection, not a
model-quality guarantee or an enforced requirement.

## New projects and ongoing updates

After user-level installation, run once in each new project:

```text
codex_workflow --install
```

Then no route prefix is required. Supported lifecycle commands remain
`--personal`, `--check-update`, `--update`, `--disable`, `--enable`, and `--remove`.
They are Codex prompt commands; deterministic script entry points remain in
`~/.codex/codex_workflow/runtime/workflow.py`.

Release discovery points ONLY to `7Eterius/codex_workflow`. Until a fork release
with a matching universal ZIP and `SHA256SUMS` is published, `--check-update` and
`--update` report that no usable release is available. They must not fall back
to upstream. Source adoption works without a published release.

The legacy ownership IDs and install paths intentionally remain compatible.
They are not update-source settings and do not make this the upstream edition.
Do not run two installers against the same managed paths or automatically sync
upstream over the fork. Review upstream changes and run fork validation first.

## Validation and release

`python3 scripts/test_fork.py -v` runs the inherited functional/safety suite,
replacing its one upstream-specific policy-text test with native policy,
worker-integrity, release-source and adoption tests. The old text test asserts
superseded routing/intake/closure contracts; it is not silently treated as a pass.
The unchanged worker files are checked by Git blob hash as well as TOML parsing.
All other inherited tests and the token-report suite remain required.

The Quality Economy CI builds and verifies a universal package without publishing
a release. Release publication is separate; see `RELEASING.md`. A CI pass validates
software contracts, not LLM adherence, visual judgment or real allowance savings.

See `workflow_breakdown.md` for the native behavior and
`docs/quality_economy_migration.md` for migration boundaries and rollback.
