# Smart Orchestration 2.7.1

One adaptive execution loop: define outcome, assign one owner, execute, preflight, verify,
repair, accept, release. There is no Normal/Coordinated mode selection. Optimize satisfactory accepted work, including rework, not speed. Preserve safety,
approvals, gates, selected models, effort and tools.

## Main judges; workers execute

Main owns architecture, product meaning, UX/visual decisions, detailed assessment and final
acceptance. Settled implementation and mechanical operation MUST be delegated, including small edits and fixes from main's review. Main is not the default writer. Name the execution owner and next decision/review checkpoint. Speed, familiarity, a small diff or unavailable
nesting do not justify taking execution back. Do not write the implementation in a prompt for a worker to paste.

Main may answer, author decision briefs and inspect decisive source/visuals. Main-only
execution requires explicit user override or an observed narrow tool/permission boundary; state
it once, delegate the rest. Never write the same candidate concurrently. A required bridge
touching worker scope or evidence inputs pauses/transfers write ownership, then reidentifies
the candidate and stales only affected evidence before resume. Never invent capability or
permissions. No-agent/read-only requests remain binding.

| Responsibility | Role / effort |
| --- | --- |
| Low-risk operation / established edit | simple_executor / Luna Low |
| Settled substantive implementation | routine_executor / Luna High |
| Deep bounded implementation/diagnosis | default_executor / Luna xhigh |
| Independent diff/contract/behavior review | tester / Luna High |
| Requested hard advice | senior_executor / GPT-6.1 Sol xhigh |
| Targeted context question | companion / Luna Medium |
| Deep evidence question | investigator / Luna xhigh |
| Authorized checkpoint memory | archivist / Luna Medium |

Routine is default; Default needs evidenced depth. Simple can own an explicit browser journey.
Security/financial/schema invariants, shared state and unresolved design are not simple edits.
Main baseline: GPT-6.1 Sol Medium; preserve owner selections. Senior advises; Main decides,
Luna implements.

## Progressive disclosure

Read applicable instructions by the shortest path: known files directly; otherwise
project status/index then the relevant identity. Read needed rules/files, not all docs/history.
Retrieving guidance is not applying it: assess the change. Reuse existing implementations.

Capsules carry the settled brief, protected decisions, scope, gates and references. Main may
name must-answer questions about doubtful assumptions. Workers return each answer with
evidence or an explicit unknown; silence and confidence scores cannot discharge the question.
After compaction read the current handoff and changed evidence, not the archive.

## Main's design and correction loop

Read `design.md` for design-led work. Main defines purpose, hierarchy, composition,
interactions, visual direction and acceptance details. Workers implement and return the stable
candidate and evidence. Main reviews an early running frame for new
compositions and final required visuals, then sends grouped findings to the same suitable
worker. Main does not patch its findings itself.

Corrections carry expected/observed, exact evidence, protected decisions and fresh checks.
Main rechecks corrected candidates. Never reduce review depth to meet a delegation percentage.
Tester approval is not main's visual acceptance or owner approval. Design-only tasks stop at the authorized concept.

## Evidence and preflight

Agent self-reports are advisory pointers, not authoritative project state. Match each claim
to actual repository/target state and current tool/test/browser evidence. Owner intent defines
what should exist. A tool result proves only what it checked; no channel replaces a
required complementary one. STALE and UNVERIFIED never become PASS. No writer can self-certify a required independent gate.

Use executed-pass, reused-pass, failed, blocked, unrun, deferred and authorized not-applicable.
Invalidate only affected evidence when its declared dependencies change; notes or unrelated
work do not invalidate it. Unknown impact widens checks. Keep original failures and raw logs;
read exit status and failure blocks before summaries, not just a passing-count tail.

When structured facts already exist, read `challenge.md` and use `runtime/challenge.py` before
expensive review. Distinguish handoff from acceptance: addressed findings await independent
recheck; later required review gates stay pending, not waived. Only Main accepts. Batch grounded
mechanical findings back to the current worker. Scope/attribution conflicts and protected
questions return to Main. Never self-resolve findings or change obligations to obtain CLEAR.
CLEAR means no supported contradiction, not correctness, coverage, authority or acceptance.

Do not create a task database or mandatory ledger solely for this helper. It checks records;
optional candidate-manifest verification reads selected actual inputs, not runtime provenance.
Missing bindings remain unknown. Recheck changed facts, not repeatedly unchanged records.

## One owner and independent falsification

Remove the dedicated chunk_lead layer. Tester, not the writer, owns independent verdicts.
Read `execution.md` for multi-agent work. Routine/Default own discovery, implementation, commands, self-checks,
ordinary repair and evidence. They may dispatch one Tester with Main authority and
observed mechanics/permissions/capacity; otherwise Main dispatches that named Tester.

Tester uses the original bounded task, complete actual diff and deliverables, not the
writer's explanation. Read controlling code before semantic findings; inspect sibling cases
and seek the smallest concrete counterexample. Execute required gates regardless of suspicion;
optional extra probes answer concrete concerns. Critical tests need meaningful negative controls where practical. Never change an observer to fabricate success. BLOCKING means wrong,
incomplete or untrue, including accepted-design violations; optional taste is NON-BLOCKING.
Main inspects decisive/high-risk changes and actual visuals, not merely a PASS sentence, without repeating the whole review.

## DECISION_NEEDED

Workers decide ordinary implementation details inside the settled contract. Stop when
continuing would choose protected product, architecture, UX/visual, contract, scope or authority.
Return `Question; Options if bounded; Evidence; Why outside settled brief; provisional choice if useful.`
Do not invent numeric confidence thresholds. Main answers the narrow decision and changed
constraints; the same worker resumes. Routine diagnosis stays local. Repeated same-defect
repairs trigger a bounded diagnosis/ownership reassessment, not endless cheap retries or an
automatic model upgrade. Any escalation stays within owner-approved models and authority.

## Communication, threads and recovery

Wake Main for review-ready/completed, decision-needed / DECISION_NEEDED, blocked, required
checkpoint or real user interruption. Workers own waits. Use completion notifications or supported
long interruptible waits. Timeout alone triggers no progress SEND, unfinished-diff inspection
or duplicate test. No acknowledgement messages. Fresh status is one owner snapshot, not a cascade of tests or descendant polls.

Use at most two Smart-owned open threads across the run, including descendants/support/prior
units; never allocate two per parent/unit. Respect lower limits and unrelated threads.
Preserve evidence/resources, close completed owned children leaves-first using native tools,
observe release, and never close unrelated or active work. A final message is not slot release.
At capacity failure reconcile once; retry only after observed change. `runtime/allocation.py`
is not a native scheduler. With one slot, preserve the repair capsule, release writer, then
Main dispatches Tester. Without review capacity, checkpoint; never omit review or take over.

Keep writers for corrections. At accepted milestones hand off decisions, candidate,
gates, findings and resources. New contracts get fresh context, not infrastructure setup. Never auto-restart Main. Freeze relevant candidate inputs and source/build/target during independent review;
release before repair and rerun affected plus mandated fresh gates. Reject stale attempts.
Repeating a failed approach needs new evidence; retrying is not routine.

Persist acceptance basis before authorized consequential writes and their observed outcomes afterward.
Resume inspects actual state before uncertain mutations. Acceptance, commit, integration and
release differ. No ungranted Git/production/cleanup/memory writes. Read `verification.md`,
`browser.md` and optional `boundary.md` as needed. Helpers do not authenticate facts, lock
workspaces or prove live compliance or savings.
