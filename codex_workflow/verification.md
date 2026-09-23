# Change-aware verification

Read once when planning validation-bearing work. Main or the bounded lead sends only
relevant gates to workers. Preserve explicit repository/owner obligations; reducing
redundant execution never reduces required coverage or independence.

## Check at the right boundary

During edits use the narrowest checks that can invalidate the change. At a stable
candidate, independently verify affected behavior when risk requires it. At an authorized
integration/release boundary, complete that boundary's gates. Local PASS is not release
acceptance. Deferred or unavailable gates remain OPEN with a reason.

Batch coherent edits under one contract. Repaired behavior requires fresh affected checks.
Widen for shared dependencies, failures or unknown impact. Do not repeat a valid check
solely because another worker is available. Self-checks never replace required independent
execution. Tests must derive intended behavior from authoritative contracts; changing an
assertion merely to agree with the implementation is not a repair.

| Change | Decisive evidence |
| --- | --- |
| Internal documentation | Accurate content, references and executable examples |
| Domain/backend | Unit/contracts; inspect consumers when shape, errors or state change |
| Copy/localization | Keys/placeholders/plurals and affected wrapping/accessibility names |
| Layout/theme/components | Running affected screens, consuming journeys, relevant contrast/zoom/motion |
| Forms/focus/navigation | Keyboard/focus/back continuity, roles/labels, relevant screen-reader states |
| Auth/entitlements/schema/financial | Invariants, denied paths, persistence and regressions |

Use targeted accessibility and representative affected viewports at a stable candidate;
retain any mandated device/theme/locale matrix. Do not disable rules or exclude violations.
Screenshots and automation cannot replace required manual accessibility checks.

## Candidate hold and identity

The validation owner identifies the actual workspace, source including staged/unstaged/
untracked inputs, relevant harness/config/dependencies, running build, account/data and
target. HEAD or a URL alone is insufficient. Hold relevant writer changes and target
replacement while independent checks run; different owners may work only in isolated scope.
On relevant change or uncertain continuity, invalidate affected evidence. Release the hold
before correction, identify the repaired candidate, then revalidate. A hold is an ownership
agreement, not a filesystem lock; external edits can still happen.

For nontrivial holds, the optional `runtime/candidate.py` helper snapshots explicitly
selected files/directories and compares them later. Include shared contracts, lockfiles,
config and newly created files where relevant. It reads without modifying the candidate.
It proves identity only for listed inputs, not test coverage, provenance of a served build,
external state, or absence of changes between snapshots. A hash is not a dependency graph.
Use existing trustworthy build/version evidence rather than creating duplicate inventories.

## Browser evidence

Use `browser.md` for multi-step Browser/Computer work. Mechanical execution and evidence
collection belong to Simple Luna Low; independent interpretation belongs to Tester where
required, and visual/product judgment stays with main/Senior. A GUI alone triggers neither
Tester nor expensive-model escalation. Never substitute API-only checks for a required
real browser journey, nor screenshots for hidden persistence or authorization evidence.

## Reuse and reporting

Reuse evidence only when covered behavior, complete relevant inputs, dependencies,
toolchain/config, data/environment and viewport/theme/locale remain applicable. Record
fresh, reused, failed, unrun, blocked and deferred distinctly. Unknown applicability
requires a check. Reuse stable servers/incremental builds after confirming identity;
clean rebuilds need a stale-artifact cause or explicit gate. Debug does not prove Release.

Use native structured reporters or save stdout/stderr to a private artifact and preserve
the underlying exit status. Filtering/piping must not hide failure, timeout, cancellation
or incomplete collection. Read stored failures instead of rerunning to recover discarded
output. No missing log becomes PASS. Keep artifacts out of source control; redact secrets
from summaries. Do not lossily summarize decisive diffs, policies, migrations or visuals.

Main reviews decisive diffs in Normal mode. In Coordinated mode the lead performs that
review and main verifies the returned candidate, evidence, exceptions and final acceptance.
Neither accepts worker prose without inspectable evidence. New risks can broaden review;
cheap execution never buys permission to skip a gate.
