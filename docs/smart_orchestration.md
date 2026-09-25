# Smart Orchestration engineering notes

## Delegation-first, single adaptive loop

2.4 retains the single-owner architecture and strengthens the actual division of labor.
Main owns product/architecture/UX/visual decisions, detailed quality review and acceptance.
Named Luna workers own settled implementation, mechanical operation, evidence and repair.
Small edits and main-authored findings are delegated too; latency is not an exception.

The main policy, managed AGENTS region and installed developer-instructions bootstrap all
carry the rule. Main can answer, write authorized decision briefs and inspect decisive
source/visual evidence. Main-only execution requires an explicit user override or a
verified narrowly authorized tool/permission boundary. The remaining work returns to
workers; no assumed access, generic model substitution or hidden configuration override.

## Design authorship and repair

The on-demand [design guide](../codex_workflow/design.md) defines a short accepted brief,
actual running evidence, main's detail-oriented review and grouped correction tasks.
Workers implement within settled patterns, returning unresolved design choices to main.
Main inspects the result and rechecks repairs instead of implementing its own quick fixes.
An existing capable owner may collect short evidence; Simple handles substantial known
operator journeys. Do not create a new agent per click, file or finding.

Tester independently reviews actual diff/contracts and required behavior. It does not
replace main's visual judgment or an explicit owner approval. Review depth is not bounded
by a delegation percentage. The instruction policy is not a native tool interceptor.

## Capability, lifecycle and evidence

Routine/Default may dispatch one Tester only with explicit authority and observed nested
mechanics. Otherwise main dispatches that same named reviewer. No manager or separate mode.
Use existing source/build/target identity and hold inputs during independent review.
Release before corrections, retain original failures and rerun affected and mandated fresh
gates. Preserve separate Tester verdicts and actual current visual evidence for main.

Keep the same worker for concrete pending review/corrections, not speculative future work.
A completed response does not free capacity. Persist results and transfer resources, close
eligible owned direct children natively, observe release and only then reuse slots. The
two-thread target and existing lower/user caps remain binding. No process killing or
capacity increases to mask lifecycle problems.

`runtime/allocation.py` now routes tiny settled execution to Simple rather than main.
Its capacity/ownership checks, `runtime/candidate.py` and `runtime/boundary.py` are unchanged.
These helpers check supplied data, not native availability, authority,
model behavior or evidence truth. See [boundary contracts](../codex_workflow/boundary.md).
No new helper module, model-call loop, logging daemon or mandatory statistics is added.

## Installation and validation

`design.md` is an explicit package input included in installation and fingerprint checks.
Bootstrap content updates transactionally inside its existing managed region. All other
owner settings and project files remain protected. A new source snapshot is installed by
preview/apply/check, followed by the user's manual client restart and a fresh conversation.

CI runs source/installation tests and exact archived migrations, now including
2.3 -> 2.4 -> no-op reapply -> exact rollback. Prompt contract tests validate instructions,
not whether an LLM obeyed them. The targeted [runtime checks](../codex_workflow/runtime_check.md)
cover actual observations without disabling ordinary direct named execution.

See [2.4 notes](v2.4.md), [2.3 hardening](v2.3.md) and [optional evaluation](evaluation.md).
Savings require observation of comparable satisfactory outcomes across every model layer,
setup and rework. Opaque tool calls and missing pricing are not evidence of waste.
