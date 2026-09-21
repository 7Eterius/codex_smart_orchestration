---
name: deployment-token-report
description: On explicit request only, report scoped local Codex usage with cumulative-counter reconciliation. Not an automatic task-closure step, live quota meter, or reason to spawn an extra agent.
---

# Deployment Token Report

<!-- codex-workflow-skill: deployment-token-report -->

Optional diagnostics, independent from Archivist project memory. Do not invoke
merely because work finished. An explicit reporting request is required; never
spawn an agent just to print a table. Do not upload raw sessions or use an LLM to
summarize them. The bundled Python reads local JSONL without model/network calls.

Main can invoke directly using its known root thread and existing entry marker:

```sh
python3 -B <skill-path>/scripts/report_tokens.py \
  --root-session-id "$CODEX_THREAD_ID" --deployment-id <known_id> --format json
```

Use the actual supported Python path. An existing Archivist may instead supply
its caller session ID (or CODEX_THREAD_ID); the script resolves the parent. Other
worker roles are not an automatic reporting path. Honor CODEX_HOME and tool
permissions. Never infer IDs, pick the newest session, or change access settings.

The marker is `<!-- codex-workflow-deployment-start: <deployment_id> -->`.
An explicit --start-time/--end-time window is supported with a known root; it is
not a whole-account/daily report. Windows use usage-notification timestamps,
not task start/duration or billing timestamps. Default cutoff is script startup.
Do not sum overlapping windows. Reporting and later final responses are not fully
captured. Missing boundary/data is a limitation, not permission to scan prose for
an approximate replacement or retry identical inputs. Failure does not block
product acceptance or project-memory handoff.

The compatibility table remains:

```text
| Agent | Quantity | Rollouts | Cached input | Input | Output |
| --- | ---: | ---: | ---: | ---: | ---: |
| <agent role> | <count> | <count> | <tokens> | <tokens> | <tokens> |
```

Return its scope and accounting notes with the table, not just naked totals.
`Input` includes cached input; output is not added to reasoning output again.
`Rollouts` now counts reconciled cumulative usage updates, not guaranteed unique
API requests, user messages or the old raw event count. Equal cumulative snapshots
are ignored even with fresh timestamps. Distinct equal-sized requests are retained
when cumulative counters advance. Missing counters, resets, or ambiguous deltas
fail without a fabricated table; counters from before the window seed its baseline.
Copied pre-creation history is not charged again to a child session.

JSON includes per-session notification/update counts, duplicate snapshots and
recorded model/effort context when available. Those contexts are log observations,
not independent proof of server billing or role configuration. Roles do not imply
models. Never apply prices, calculate weekly-percent usage, back-correct old reports
by a fixed multiplier, or present raw event totals as model calls. Some unsupported
or missing telemetry can prevent reporting; leave that uncertainty explicit.
