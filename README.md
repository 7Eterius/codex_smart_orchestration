# Smart Orchestration

**Smart Orchestration 2.1.0** is a standalone global Codex workflow for quality at lower
accepted-work cost. Strong models own consequential judgment; inexpensive models handle
bounded implementation and mechanical tool work. Extra coordination must earn its cost.

Normal remains the default. Coordinated mode adds a bounded Luna lead for suitable
qualified runs, not every feature, webpage or verification task. The nine roles and
model/effort map are unchanged from 2.0. The installer preserves owner configuration.

## Installation and updates

Open Codex in your project. Use permissions sufficient for the reviewed global install;
do not disable safeguards or select Full access solely to reduce approval overhead.
Paste this prompt:

```text
Install the latest Smart Orchestration code from the main branch of https://github.com/7Eterius/codex_smart_orchestration. First resolve the current HEAD commit SHA of main, then download the source archive for that exact commit into a temporary directory and extract it. Do not use GitHub Releases, historical dist archives, or another repository. Read the extracted codex_workflow/operate/smart_install.md. Use Python 3.11 or newer. From the extracted repository root, run python3 -B codex_workflow/runtime/smart_install.py --package-root codex_workflow without --apply first and inspect the preview. If it is clean, run the same command with --apply in this current Codex session, then run it with --check instead of --apply to verify the installed disk state. Do not quit, close, relaunch, or wait for Codex to exit. Preserve my existing Codex configuration and all project files. Stop on conflicts or errors instead of forcing changes. Report the installed source commit SHA, version, backup path and check result, then tell me to restart Codex manually. Do not claim live nested-agent qualification from a disk check.
```

Select an installed Python 3.11+ executable if `python3` is older. Restart Codex manually
only after success. Reuse the same prompt to update from `main`, without uninstalling.
`CODEX_HOME` is honored; the default global location is `~/.codex`. No project bootstrap,
release assets, API key or external orchestration service is needed.

## Choose the team for this assignment

| Assignment | Smallest suitable structure |
| --- | --- |
| Question or trivial complete edit | Main directly |
| Mechanical browsing, extraction, explicit low-risk GUI change | Main -> Simple |
| Standalone verification gate | Main -> Tester; no writer or lead by default |
| Normal implementation | Main -> one Executor; Tester when risk requires |
| Bounded investigation/review/repair loop in a qualified run | Main -> Chunk Lead -> required leaves |
| Closely related, pre-approved chunks sharing a contract/setup | One bounded lead for exact named members; each keeps its gates |
| Architecture, product, UX or visual direction | Main/Senior; operator collects evidence cheaply |

Do not create a lead just to forward a result. Grouping never permits an open-ended
checklist, concealed failed member or bypassed approval. Reuse useful correction context;
start a fresh lead after the assigned coherent boundary, not after every tiny step.

```text
Main: authority, dependencies, architecture/design, final milestone acceptance
  |
  +-- Simple: bounded mechanical work
  +-- Tester: validation-only gate
  |
  +-- Chunk Lead: one chunk or exact coherent group, only when justified
        +-- one Executor: implementation and self-check
        +-- Tester: independent required verification
```

## Role map

| Role | Model / effort | Responsibility |
| --- | --- | --- |
| Main | Owner-selected; Sol Medium recommended baseline | Consequential judgment, scheduling and final acceptance |
| simple_executor | GPT-6 Luna Low | Low-risk edits, mechanical Browser/Computer operation |
| routine_executor | GPT-6 Luna High | Settled bounded implementation |
| default_executor | GPT-6 Luna xhigh | Deep bounded implementation/debugging |
| chunk_lead | GPT-6 Luna xhigh | Scoped actual-diff review, corrections, delegated local acceptance |
| senior_executor | GPT-6 Sol xhigh | Advisory hard judgment; exceptional explicit writing transfer |
| tester | GPT-6 Luna High | Independent behavior/contract verification |
| companion | GPT-6 Luna Medium | Targeted discovery |
| investigator | GPT-6 Luna xhigh | Unresolved evidence question |
| archivist | GPT-6 Luna Medium | Verified checkpoint memory |

Max is not an automatic tier. Astra remains owner-selected for exceptional judgment,
not triggered by screenshots. Only `chunk_lead` enables delegation. Its allowed child
roles are a behavioral contract, not a native security allowlist. No additional roles,
model downgrades, capacity increases or undocumented configuration keys are introduced.

## What 2.1 changes

**Assignment-level routing and coherent groups.** Skip unnecessary layers for operation
and validation-only work. Group explicit related members when this avoids cold setup,
while retaining every requirement, acceptance level and stop point.

**Continuation without chatter.** Worker final handoffs end their assignment, not the
coordinator's run. Status replies use commentary and do not end authorized execution.
A fresh status can request one coalesced active-owner snapshot without cascading tests
or worker polls. A real pause still propagates immediately.

**Reuse setup, not stale verdicts.** Fresh lead context does not require a fresh browser,
login, dependency installation or server. Transfer verified target identity, ownership,
consumers and release conditions. Reuse one canonical requirement/gate map after checking
applicability; no duplicated checklists or per-worker report machinery.

**Recoverable acceptance.** Record acceptance/candidate basis before an authorized commit
or consequential external mutation and observed outcome afterward. On interruption,
inspect actual state before retrying. Stale attempt results cannot advance current work.
Local acceptance, commit, integration and release remain separate facts.

**Selective verification.** Preserve independent and required fresh checks, but reopen
only affected gates/dependents when the contract or candidate changes. Unknown impact
widens verification. Functional assertions, browser interaction and visual critique have
complementary jobs, not three redundant copies of each assertion.

## Browser and design quality

Simple is the **operator** for known navigation, exact webpage facts, explicit low-risk
settings and observable checks. Main/Senior is the **judge** for hierarchy, interaction
and visual quality. A trivial permission, billing or production click is not low risk.

Use the least expensive sufficient evidence channel, not a mandatory tool sequence.
Follow actual browser/computer tool skills, preserve required rendered journeys and
manual accessibility, and use full-resolution final evidence where required. A success
toast alone does not prove persistence. Never blindly retry an uncertain write.

## Optional scoped identity checks

The existing `candidate.py` helper snapshots explicitly chosen source inputs, including
untracked additions inside watched directories. A matching fingerprint is **not** a test
verdict, dependency graph, runtime proof or signature. Holds and complete scope still matter.

```bash
python3 -B ~/.codex/codex_workflow/runtime/candidate.py snapshot \
  --root /path/to/project --path src --path package-lock.json \
  --output /existing/private/evidence/candidate.json

python3 -B ~/.codex/codex_workflow/runtime/candidate.py verify \
  --manifest /existing/private/evidence/candidate.json

python3 -B ~/.codex/codex_workflow/runtime/candidate.py verify-many \
  --manifest /existing/private/evidence/reader.json \
  --manifest /existing/private/evidence/signup.json
```

Use `verify-many` only for already-useful evidence scopes: at most 16 manifests, fresh
independent reads, one bounded report retaining every result. Exit 0 means all listed
inputs match; 1 means drift without errors; 2 means an error occurred, even alongside
drift. This is not a cross-candidate atomic snapshot or an automatic acceptance decision.

## Validation and limits

```bash
python3 -B -m unittest discover -s scripts -p 'test_*.py' -v
python3 -m compileall -q codex_workflow scripts
```

CI uses full Git history on Ubuntu Python 3.11/3.12 and macOS Python 3.12. Existing
2.0 tests remain; additional tests cover batch outcomes and an exact archived 2.0 ->
2.1 -> idempotent reapply -> rollback. Tests validate code and policy contracts, not
live orchestration quality. The exact history-dependent migrations require Git objects.

Use [qualification](codex_workflow/qualification.md) in the actual client before
consequential nested use. Reuse applicable prior observations and requalify only changed
mechanics with a stated basis. Static checks cannot prove model availability or savings.

See [engineering notes](docs/smart_orchestration.md), [2.1 design decisions](docs/v2.1.md)
and [2.0 background](docs/v2.0.md). Git history retains older implementation eras.
