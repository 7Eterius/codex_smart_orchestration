# Smart Orchestration

**Smart Orchestration 2.0.0** is a standalone global Codex workflow for quality per
accepted task, not maximum agents or minimum first-attempt tokens. It keeps expensive
product/design judgment separate from high-volume implementation and GUI operation.

## Install or update from main

Open Codex CLI or the app in any project. Use permissions that allow the requested
global configuration writes; installation does not require blanket full access.
Send:

```text
Install Smart Orchestration from https://github.com/7Eterius/codex_smart_orchestration.
Resolve the current HEAD commit SHA of main and download/extract that exact source
snapshot into a temporary directory. Do not use GitHub Releases or old dist archives.
Read codex_workflow/operate/smart_install.md from that snapshot. With Python 3.11+,
run codex_workflow/runtime/smart_install.py --package-root codex_workflow without
--apply first and inspect the preview. If clean, run the same command with --apply
in this session, then run the extracted installer with --check. Preserve unrelated
Codex settings and every project file. Stop on conflicts; do not force replacement.
Do not quit or relaunch Codex or wait for it to exit. Report version, exact commit,
package fingerprint, backup and verification. Tell me to restart Codex manually.
```

Install once globally under `~/.codex/`, or your existing `CODEX_HOME`. Restart manually
only after successful installation. Update with the same prompt; no releases or uninstall
step. Existing project `AGENTS.md` rules remain binding. Installation preserves explicit
models, effort, speed, tool permissions and thread limits.

## Two modes, not two permanent hierarchies

**Normal is the default** for a question, bounded feature, fix, design task or mechanical
browsing. Main works directly where that is cheaper, otherwise uses the existing leaves
and independent testing when required. Several files or tool calls alone do not justify
an extra lead.

**Coordinated is conditional** for longer authorized runs with coherent chunks and settled
contracts. One fresh Luna lead owns each chunk's investigation, actual-diff review,
corrections and delegated local acceptance. Main handles dependencies, consequential
judgment, exceptions and final milestone acceptance without repeating every local review.

```text
Normal                           Coordinated, after live qualification
Main                             Main: schedule, judgment, final acceptance
  -> Executor                      -> fresh Chunk Lead for one coherent chunk
  -> Tester when required               -> one Executor
                                         -> independent Tester when required
                                    <- candidate, verdict, evidence, open gates
                                  -> fresh lead for the next accepted dependency
```

The new lead is not a license for recursive teams. Only `chunk_lead` has delegation
enabled; it may use only Simple, Routine, Default and Tester. The eight leaves keep
delegation disabled. Permitted child roles and ownership rules are instructions, not
a claimed native allowlist or a replacement for sandbox permissions.

One lead plus its writer and Tester fits the existing default of three spawned threads
excluding main **if the actual backend supports that nesting/accounting**. Do not raise
limits automatically. Reuse a valid live qualification or run the bundled
[qualification trial](codex_workflow/qualification.md) before consequential coordinated
execution. Structural tests do not prove nested behavior. Normal remains available when
nesting is unsupported; an explicitly coordinated-only request stays blocked.

## Models and responsibilities

| Role | Model / effort | Purpose |
| --- | --- | --- |
| Main | Owner-selected; Sol Medium recommended | Architecture, product, UX/design and final acceptance |
| Simple | Luna Low | Low-risk edits, mechanical browsing/GUI and explicit observations |
| Routine | Luna High | Settled bounded implementation |
| Default | Luna xhigh | Deep bounded implementation and diagnosis |
| Chunk Lead | Luna xhigh | One coordinated chunk's review/correction/local acceptance |
| Senior | Sol xhigh | Advisory hard judgment; exceptional explicitly transferred writing |
| Tester | Luna High | Independent behavior/contract verification |
| Companion | Luna Medium | Targeted context discovery |
| Investigator | Luna xhigh | One unresolved evidence question |
| Archivist | Luna Medium | Grounded durable milestone handoff |

Max and Astra are not automatic escalation tiers. Astra remains an owner choice.
The model names/efforts are package defaults, not proof of account availability.
Changing parent effort mid-session is used only through the actual runtime's supported
mechanism; the installer does not rewrite it. Standard speed is preferred over paying
for latency the task does not need.

## Operator work versus judgment

Simple handles known page navigation, exact factual extraction, explicit low-risk GUI
settings, screenshots and checks against stated observations. Main/Senior decides product
meaning, hierarchy, interaction design and visual quality. A screenshot does not make a
task intelligent, and an easy click does not make a billing/security/production action safe.

For web work use structured evidence or a connector when sufficient, real browser flows
when user experience is under test, and Computer Use where a GUI is necessary. Reuse
verified sessions, batch predictable actions, collect only useful visual states and keep
per-action failures visible. Never replace a required browser journey with API-only checks.

## Fewer expensive turns, stronger evidence

Communication is event-driven: completion, material blockers and decisions. No repetitive
polling, acknowledgements, or fresh GUI/test runs merely to answer a progress question.
Keep corrections inside the same chunk and send deltas. New chunks get new leads, not old
investigation transcripts. Stable instructions stay stable; task-specific guides load on demand.

Independent validation holds the relevant candidate and running target steady. The writer
stops until the hold is released; changed inputs require renewed applicable evidence.
Source, untracked files, config and build identity matter, not just HEAD or a URL.

An optional deterministic helper makes scoped input identity cheap to inspect:

```bash
python3 -B codex_workflow/runtime/candidate.py snapshot \
  --root /path/to/project --path src --path package.json --path package-lock.json \
  --output /path/to/evidence/candidate-before.json
python3 -B codex_workflow/runtime/candidate.py verify \
  --manifest /path/to/evidence/candidate-before.json
```

Choose real relevant input paths; output must be outside the watched scope and not
already exist. The helper reads source without changing it, detects scoped additions,
removals/content/mode changes, and prints bounded results. It is **not** a test verdict,
a dependency graph, a lock, proof of a deployed build or authentication of evidence.
No mandatory inventory, new reporting database or per-command fingerprints are introduced.

## Quality and authority

Risk-based independent testing remains. Normal main reviews decisive diffs; Coordinated
leads perform detailed local review while main verifies candidate/evidence completeness
and high-risk exceptions. Main retains final visual/product acceptance. Tests do not imply
owner approval, a commit does not imply integration, and local PASS does not imply release.

Pauses stop new dispatch and propagate to descendants. Resume checks actual files,
operations, holds and evidence before retrying uncertain writes. Preserve unique unfinished
work and original failures on durable storage. Cleanup requires exact ownership and released
consumers. No implicit commit, push, merge, deploy, migration or permission-change authority.

## Validation and limits

```bash
python3 -B -m unittest discover -s scripts -p 'test_*.py' -v
python3 -m compileall -q codex_workflow scripts
```

CI includes the preserved current tests, new v2 contracts, filesystem/candidate failures,
configuration preservation and an actual archived v1.9 -> v2 -> rollback regression.
An isolated file/test pass does not establish live Codex qualification or cost savings.
Use the bundled trial and representative accepted tasks before broadly adopting Coordinated.

See [architecture](docs/smart_orchestration.md), [v2 decisions and sources](docs/v2.0.md),
[operating policy](codex_workflow/smart_orchestration.md) and
[coordinated contract](codex_workflow/coordinated.md).
