# Verification proportional to residual risk

The owner self-checks every change. Add independent Tester when the repository/owner
requires it or when a meaningful risk remains: behavior/state/integration, shared
contracts, uncertain accessibility, security, payments, schema or financial invariants.
Default and transferred Senior implementation require independent review by default.
Low-risk, reversible copy/style/established edits with decisive checks do not acquire
another reviewer merely because they touch UI. A browser visit alone is not a review gate.
Never use these defaults to waive an existing project obligation.

## One independent reviewer, not duplicate layers

Tester reviews the actual diff, affected callers and authoritative contract, and executes
required independent checks. These replace the dedicated lead's routine detailed review,
not a repository's explicitly separate reviewers. Main retains consequential product,
architecture, visual and final acceptance judgments. A writer's confidence is not evidence.

Use canonical requirement IDs with acceptance level and expected behavior. Check coverage
independently; do not create a new matrix at every handoff or derive assertions from the
implementation's actual output. Preserve original failures. Changing tests to agree with
a bug is not repair. Standalone validation has no implementer or manager.

During edits use the narrowest decisive checks. At a stable candidate test affected
behavior independently where needed. At integration/release complete that level's gates.
Required local failures block local acceptance. Later OPEN release checks remain OPEN
without being falsely labeled either completed or failed locally.

## Candidate hold

Identify source including staged, unstaged and untracked inputs; test/config/lockfiles;
contract revision; actual served build, target, account and relevant environment. HEAD
or a URL alone is insufficient. Freeze relevant writer changes and target replacement
throughout independent review. Tester writes evidence/disposable data only, not candidate
source or tests. The hold is an ownership agreement, not a filesystem lock.

Release before same-owner repairs, identify the new candidate, re-hold and rerun affected
plus required fresh checks. Retain unrelated applicable evidence. New shared risk or
unknown impact widens checks. Stale attempt or changed-contract results cannot advance
acceptance. If capacity requires writer closure, preserve a complete repair capsule and
candidate before an independent main-dispatched Tester starts; never reopen writes during
its hold. Thread closure is not permission to destroy the workspace.

The optional `runtime/candidate.py` fingerprints explicit selected inputs. Its
`verify-many` batches existing manifests while keeping per-scope match/drift/error visible.
These prove identity only for listed inputs, not test coverage, runtime provenance,
external data, absence of intervening changes, or authority. No automatic hash cache or
mandatory manifest for every trivial edit. Reuse trustworthy existing build evidence.

## Useful, non-duplicative evidence

| Change | Focus |
| --- | --- |
| Docs/copy | Correct references, executable examples, keys/placeholders and wrapping |
| Domain/backend | Invariants, affected consumers, contracts and denied/error paths |
| UI behavior/navigation | Real interaction, keyboard/focus/labels and relevant accessibility |
| Layout/theme | Running affected screens, required viewports, contrast/zoom/motion |
| Auth/billing/schema/financial | Independent security, persistence, migration and regression gates |

Preserve mandated device/theme/locale matrices and manual accessibility checks; do not
repeat entire matrices after each small edit. Structured tests prove hidden behavior,
browser journeys interaction, screenshots appearance. Do not substitute one for a
required complementary channel. Main directly inspects requested design evidence.

Separate executed-pass, reused-pass, failed, blocked, unrun, deferred and authorized
not-applicable. Missing logs or unknown applicability never become PASS. Save private
raw stdout/stderr and exit status; preserve timeout/cancellation and incomplete results.
Filtering must not swallow failures; inspect retained logs rather than rerunning to
recover discarded output. Keep stable servers and incremental builds after checking
identity; clean rebuilds need a cause or gate.

Return exact candidate and reviewer identity, gate dispositions, failures/resolutions,
evidence and remaining authority/lifecycle obligations. The owner cannot convert its
own self-check into independent approval. Main checks applicability and decisive risks
without routinely repeating the full source investigation. No implied commit, integration,
release, owner sign-off or savings follows from a test pass.
