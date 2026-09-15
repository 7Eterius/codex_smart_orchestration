# Efficiency tuning 1.3.1

Goal: preserve accepted task quality while reducing unnecessary model work on a
$100 Pro plan. Five workdays is a measurement target, not a promised capacity.
No post-change usage report was available when preparing this revision.

## Verified pricing snapshot: 2026-09-15

Published Standard BASE credits per million tokens:

| Model | Uncached input | Cached input | Output |
| --- | ---: | ---: | ---: |
| GPT-5.6 Luna | 5 | 0.5 | 30 |
| GPT-5.6 Terra | 50 | 5 | 300 |
| GPT-5.6 Sol | 100 | 10 | 500 |
| GPT-6 Astra | 250 | 25 | 1250 |

Source: https://learn.chatgpt.com/docs/pricing

These are not dollar API prices or an exact conversion to included weekly
allowance. Sol's temporary purchased-credit promotion does not change included
plan limits. Fast mode and long-context/tool rules are separate. Reverify this
dated snapshot before later financial or capacity decisions.

Additional primary sources:
- https://help.openai.com/en/articles/11481834
- https://help.openai.com/en/articles/20001516-managing-usage-with-gpt-6-astra-in-work-and-codex
- https://learn.chatgpt.com/docs/agent-configuration/speed
- https://learn.chatgpt.com/docs/agent-configuration/subagents

Identical 100,000 uncached input plus 10,000 output tokens have base-credit
references of 0.8 for Luna, 15 for Sol and 37.5 for Astra. That arithmetic does
not establish identical tokens per completed task or identical included-quota
weight. With ten percent of uncached input on Astra and ninety percent on Luna,
Astra still contributes about 85 percent of the base input-credit reference.
A cheap worker team does not make repeated parent turns cheap.

## Changes

Add routine_executor (Luna High) between simple_executor (Luna Medium) and
unchanged default_executor (Luna Max). Use it for bounded feature implementation
whose contracts and objective acceptance are already settled. Known hard work
starts stronger. Low-risk simple work needs both a clear pattern and decisive
checks; missing tests or novel trust/financial/shared-state boundaries exclude it.
Independent Tester remains Luna xhigh; Senior Sol Medium remains available.
Main still directly plans, decides material issues and audits decisive changes
and final visual evidence. No independent or owner-required gate is removed.

Reduce parent administrative turns, not necessary judgment. Send related findings
in a batch. Keep logs and generated files as inspectable artifacts. Use exact
contract references and stable instructions. Preserve worker context for related
repairs; use a compact Archivist handoff between unrelated milestones. Do not
force short contexts or reset after every small edit.

Standard speed is preferred for allowance efficiency. The installer preserves
speed/model/effort and permissions. Use /fast off in Codex when appropriate;
null service_tier in a file is unknown/inherited, not proof that Fast is off.

## Read-only tools, not more agent ceremony

The globally installed runtime/efficiency.py offers:

```bash
python3.11 ~/.codex/codex_workflow/runtime/efficiency.py settings
python3.11 ~/.codex/codex_workflow/runtime/efficiency.py rates
python3.11 ~/.codex/codex_workflow/runtime/efficiency.py compare \
  --input-tokens 100000 --cached-input-tokens 0 --output-tokens 10000
python3.11 ~/.codex/codex_workflow/runtime/efficiency.py pace \
  --remaining-percent 100 --workdays-left 5 --reserve-percent 15
```

These commands do not call a model, read transcripts, query the account, or write
files. Settings reports only selected model/effort/speed fields, not API keys or
instruction text. Missing data remains null/unknown. Input includes cached input;
the comparison subtracts that subset before applying uncached rates. It never
returns an invented included-weekly-percentage conversion.

The pacing command divides observed remaining allowance minus a chosen reserve
by remaining workdays. At reset, a 15-percent reserve leaves 17 percentage points
per working day for five days. This is a budget, not evidence that the same amount
of work will fit. Check at meaningful milestones; do not add repetitive budget
polling or stop required validation to satisfy it. If the pace is too high, reduce
the next authorized scope or change the parent's model deliberately, not claim
unfinished work is complete.

## Validation and scope

Eight configured roles; all previous role configurations remain byte-for-byte
unchanged. The global installer is unchanged. It still backs up managed changes,
preserves unrelated settings and project files, and rejects custom worker conflicts.
The renamed repository is now the canonical release source. Existing runtime paths
and workflow markers remain compatible.

The full fork runner includes 16 new tests for rates, cached-input arithmetic,
unknown data, pacing, read-only privacy, role/quality contracts and repeatable
global installation. Existing version readback tests use the package version
instead of the old hard-coded 1.3.0; no acceptance assertion is removed.

Software tests do not prove optimal task routing or equal model quality. Compare
whole accepted tasks including repair, rejected visuals, missing gates and observed
allowance. Roll back tier selection if added rework defeats the saving. There is
no deterministic quota limiter or guarantee of five days in this revision.
