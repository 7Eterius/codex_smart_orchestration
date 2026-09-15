# Verification and output efficiency 1.3.2

## Design

Reduce redundant work, not assertions or actual design judgment. The main chooses
validation scope from changed behavior, dependencies and the owner's checkpoint.
Edit loops get cheap discriminating checks; stable candidates get independent
verification; authorized merge/release milestones get their applicable full gates.
A required project test plan cannot be silently weakened by the global workflow.

Accessibility is targeted to changed screens, text, state and interaction. A
menu/focus change needs focus, keyboard, semantics and exposed-state checks. Shared
theme changes expand to consuming surfaces and affected themes. Pure internal
logic with demonstrated no UI impact need not trigger another UI audit. Unknown
impact, missing baseline or an actual failure expands verification. Automation
is incomplete, so required manual screen-reader/system-feature checks remain.

Record executed, reused, not-applicable, deferred and blocked separately in the
existing handoff. An owner-deferred gate is OPEN, not a pass. Reuse is justified
by known behavior/input/dependency/toolchain/config/data/environment applicability;
HEAD or one file hash alone is insufficient. No automatic test-result cache.
Do not rewrite test scripts, disable axe rules, remove assertions or approve new
visual baselines just to speed the task.

Build-cache reuse and evidence reuse differ. Valid incremental compilation can
save CPU time; an earlier successful command does not prove current acceptance.
Use existing package/build scripts, keep generated directories out of broad
search, reuse correct test servers, and avoid ritual clean builds. Test-without-
build or related-test selection must be supported by the actual toolchain and
scope. Static dependency selectors miss dynamic/runtime dependencies; they are
an inner-loop aid, not a universal replacement for final integration gates.

Parallel native checks need independent data/output state and adequate memory.
Do not race two builds into the same output directory, two screenshots on one
simulator, or two tests mutating a shared database. Additional LLM coordination
is not required merely to start independent shell processes.

## Tool output without a network proxy

`runtime/capture_check.py` executes one authorized finite argv with no implicit
shell. It streams stdout/stderr to a private combined log, then returns real exit
status, elapsed time, raw byte count/hash, exact byte offsets and a bounded
heuristic excerpt. It retains raw evidence and a JSON receipt, including for
failure, missing executable, interruption and timeout where capture is possible.
Default excerpt is 5,000 text characters and at most 24 entries; metadata adds
size. A long raw line is processed in bounded fragments, not ingested wholesale.

No model, provider switch, credential interception, remote compression service,
new hook or tool-output-token-limit setting is introduced. No test counts or
coverage are inferred. Exit zero can mean zero tests, skipped tests or a command
that hides its own failure; acceptance remains `not_assessed`. A nonzero exit is
preserved. Shell pipelines must be explicitly authorized and retain pipefail;
the wrapper does not parse shell syntax. It does not sandbox or authorize the
underlying command; ordinary permissions and owner instructions still apply.

The excerpt can omit relevant details. Regex matches are not proof of semantic
importance and no-error matches are not proof of success. Read native reports or
the saved raw file when a result is failing/uncertain; never rerun just to recover
already stored logs. Critical code, migration scripts, policies and final visual
evidence are reviewed directly, not through this filter. Do not use the wrapper
for watchers, servers or detached child daemons. POSIX timeout terminates its
process group; on Windows descendants may remain and this is explicitly reported.

Artifacts can contain secrets from argv or program output. Directories are 0700,
files 0600; no environment is dumped. Keep them out of version control and use an
appropriate local artifact-retention policy. No automatic cleanup deletes evidence.
Byte reduction is not equivalent to token savings or a lower included-plan quota.

## Assessment of supplied techniques

- Lower-effort agents: already explicit Medium/High/Max Luna roles. Keep escalation
  and independent verification; do not lower Tester or parent judgment here.
- Session compaction: preserve useful context for related work; compact handoff at
  natural milestones. Stable prefixes matter; arbitrary per-edit resets can add
  reconstruction and lose cache reuse. Do not assume earlier compaction is cheaper.
- Batching: combine coherent edits/checks, not unrelated epics or per-file agents.
- Compression: prefer native structured reports, then bounded raw-backed excerpts.
  RTK documents deterministic command filters and raw-output recovery. Distill's
  99% example is one reduced payload, not verified whole-workflow quota savings.
  Headroom documents broader proxy compression; no corpus-specific quality or
  subscription-level benchmark was established here. No third-party proxy installed.
- Repository restrictions: least privilege is a security benefit; it does not by
  itself change the number of tokens actually retrieved. Narrow queries/paths and
  preserve access to real dependencies. No account permission changes performed.

## Sources checked 2026-09-15

Primary documentation used for technical conclusions:
- https://playwright.dev/docs/accessibility-testing
- https://playwright.dev/docs/test-cli
- https://vitest.dev/guide/cli#related
- https://developer.apple.com/videos/play/wwdc2023/10035/
- https://developers.openai.com/codex/subagents/
- https://developers.openai.com/codex/config-reference/
- https://developers.openai.com/api/docs/guides/prompt-caching
- https://github.com/rtk-ai/rtk
- https://github.com/headroomlabs-ai/headroom

The supplied Reddit threads/Medium article were treated as claims to evaluate,
not independent proof of savings. Both supplied YouTube pages could not be read;
no conclusion relies on their unseen content. No current local app logs were
provided, so speedup and allowance savings remain unmeasured.
