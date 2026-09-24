# Smart Orchestration 2.2

**One adaptive workflow. One economical execution owner. Independent review when needed.**
Main keeps architecture, product/UI/UX judgment and final acceptance. Luna handles settled
implementation, mechanical browser work and ordinary repairs. No Normal/Coordinated
mode switch, dedicated Chunk Lead or global qualification gate for ordinary named work.

## How work flows

```text
Main: define outcome and authority, settle design, accept decisive evidence
  |
  +--> Simple Luna Low: complete known low-risk journeys and explicit checks
  |
  +--> Routine Luna High (Default xhigh only for deep work)
          implementation + self-check + repair
          |
          +--> Independent Tester Luna High at a stable candidate
               actual-diff / contract review + required behavioral checks

If owner-dispatched review is not supported, main dispatches the same Tester.
The contract, independence and inexpensive models stay the same.
```

Answers and an already-understood trivial operation can stay with main when delegation
costs more. A full browser journey is not many tiny workers. Standalone verification
gets a Tester without an implementer. Design-only requests do not trigger implementation.

Routine/Default can delegate **only one Tester**, only with explicit review scheduling
authority and applicable runtime evidence. They cannot create teams or self-certify an
independent gate. Other roles do not delegate. This is a policy boundary, not a native
role allowlist or security guarantee. No unseen runtime capability is assumed.

## Model map

| Role | Model / effort |
| --- | --- |
| Main | Owner-selected; Sol Medium recommended baseline |
| simple_executor | GPT-6 Luna Low |
| routine_executor | GPT-6 Luna High |
| default_executor | GPT-6 Luna xhigh |
| tester | GPT-6 Luna High |
| senior_executor | GPT-6 Sol xhigh, advisory-first |
| companion | GPT-6 Luna Medium |
| investigator | GPT-6 Luna xhigh |
| archivist | GPT-6 Luna Medium |

The eight model tiers are unchanged; the ninth manager role is retired. Max and Astra
are not automatic upgrades. Preserve explicit owner settings and permission controls.
The installer does not silently upgrade an old generic fallback or change the parent.

## Resource-conscious by construction

A unit targets at most **two Smart-owned open threads**, including reviewer. The existing
configured cap of three stays unchanged and includes other work. Lower limits are
respected; speed is not a reason to fill every slot or run speculative reviewers.

A completed response is **not** a closed thread. Preserve evidence and resource handoff,
close completed owned children natively before their parent, and use reclaimed capacity
only after observing release. A close request is not proof of success. Do not close busy
or unrelated work, kill processes, wipe profiles or change the cap to hide leakage.

If capacity is constrained, reuse compatible stopped same-unit workers or serialize
review after observed release. If that is not safe, checkpoint with the exact blocker.
No blind spawn loop, fake PASS, or silent transfer of all work back to an expensive main.

`runtime/allocation.py` is a small deterministic advisory checker for responsibility
selection and supplied thread observations. Its tests cover completion versus closure,
parent/child ownership, repeated pairs and failure recovery. It calls no native agent
API, creates no telemetry store, and cannot make a false observation true. Use it at
uncertain allocation boundaries, not as another model/tool loop for every tiny task.

## Quality without redundant work

The owner self-checks. Independent Tester covers actual diff/contracts and required
behavior rather than adding a separate reviewer-manager in front of testing. Main
retains high-risk decisions and visual/product acceptance. Repository-mandated distinct
reviewers remain mandatory, serialized when needed. Matching input hashes or a worker's
confidence are not acceptance evidence.

Verification depends on residual risk and explicit obligations, not merely an “UI” label.
Reversible established copy/style changes with decisive checks need no automatic second
review. Auth, payments, persistence, schema and financial invariants retain stronger gates.
Never silently weaken a project's tests or owner approval requirements.

Keep source/build/target stable during independent checks, release before repairs, and
revalidate affected plus mandated fresh gates. Reuse one verified setup and requirement
map, preserve original failures, use predictable test/browser scripts where appropriate,
and bring Sol back for real decisions rather than routine status transitions.

## Installation or update

After 2.2 is present on `main`, open Codex and send:

```text
Install Smart Orchestration from https://github.com/7Eterius/codex_smart_orchestration. Resolve the current HEAD commit SHA of main and download/extract that exact source snapshot outside my projects. Do not use GitHub Releases or historical dist archives. Read codex_workflow/operate/smart_install.md. With Python 3.11+, run codex_workflow/runtime/smart_install.py --package-root codex_workflow without --apply first and inspect the preview. If clean, run the same command with --apply, then --check. Preserve unrelated Codex configuration and every project file. Stop on conflicts, never force changes. Do not quit, relaunch or wait for Codex to exit. Report version, source commit, fingerprint, backup and disk result; tell me to restart Codex manually. A disk check is not live runtime proof.
```

A source upgrade bundle is applied to a clean checkout first; it is not a complete
installer by itself. The repository remains unchanged until that bundle is committed.
Install the complete reviewed checkout using the same preview/apply/check commands.
Do not claim `main` contains this version before it is actually published.

## Validation

```bash
python3 -B -m unittest discover -s scripts -p 'test_*.py' -v
python3 -m compileall -q codex_workflow scripts
```

Historical Git objects are needed for archive migration tests; CI fetches full history.
Tests of pure allocation are not live Codex thread-reclamation tests. Before relying on
owner-dispatched review, use the targeted [runtime checks](codex_workflow/runtime_check.md).
Unverified nesting does not disable direct named Luna work. The failed 2.1 trial remains
failed evidence, not reclassified as a v2.2 success.

See [execution](codex_workflow/execution.md), [verification](codex_workflow/verification.md),
[browser economy](codex_workflow/browser.md), [engineering notes](docs/smart_orchestration.md)
and [v2.2 rationale](docs/v2.2.md). No universal saving percentage or guaranteed error-free
routing is promised. Measure satisfactory accepted work, including repairs and all layers.
