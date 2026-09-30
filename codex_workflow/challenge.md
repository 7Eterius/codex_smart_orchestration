# Optional handoff preflight

Use existing structured facts, never create a task database just to run this helper.
The check is advisory, not a scheduler, permission boundary or semantic reviewer. No model
or test is called. No project files are written. Main's original task defines obligations;
the worker cannot change them, spoof authority or relabel its own breach to get CLEAR.

## Stages, not orchestration modes

`phase: handoff` checks readiness to return work for required review. A blocking finding
marked `addressed` needs current evidence but remains pending independent resolution.
Required gates with `due: accept` stay visible as pending when they are not yet decisive.
A gate already reported failed on the current candidate is actionable worker evidence and
blocks a normal review-ready handoff instead of consuming reviewer time. The next action is
otherwise the original review path, never acceptance. `phase: accept` checks every required
gate and requires blocking findings to be resolved. Only Main accepts after inspecting original evidence.

Omitting phase retains 2.6's strict acceptance behavior. Every gate defaults to due at
handoff; a later due stage must be explicitly assigned by Main. A BLOCKED/abandoned task
can always be reported honestly without making preflight clear.

## Record

Schema 1 retains its required arrays. Optional additions are shown below. Identifiers and
text are at most 512 characters, arrays at most 128 rows and input at most 64 KiB. Paths
are canonical project-relative POSIX paths: no dot segments, duplicate separators, backslashes,
drive prefixes, trailing slash or `.git`. Duplicated row IDs and malformed later rows are
errors, even when an earlier row already contains a contradiction.

```json
{
  "schema": 1,
  "unit": "card",
  "phase": "handoff",
  "current": {"attempt":"A2","contract":"R1","candidate":"C2","target":"preview/2"},
  "owned_paths": ["src/card"],
  "changes": [{"path":"src/card/view.ts","origin":"owner"}],
  "deliverables": [{
    "path":"src/card/view.ts", "required":true, "state":"satisfied",
    "evidence":"artifacts/diff-A2",
    "basis":{"attempt":"A2","contract":"R1","candidate":"C2","target":"preview/2"}
  }],
  "decisions": [],
  "questions": [],
  "findings": [{
    "id":"F1", "blocking":true, "state":"addressed", "evidence":"artifacts/repair-A2",
    "basis":{"attempt":"A2","contract":"R1","candidate":"C2","target":"preview/2"}
  }],
  "evidence": [
    {"gate":"unit","required":true,"fresh_required":true,"status":"executed-pass",
     "evidence":"artifacts/unit-A2",
     "basis":{"attempt":"A2","contract":"R1","candidate":"C2","target":"preview/2"}},
    {"gate":"independent-review","required":true,"fresh_required":true,"status":"unrun","due":"accept"}
  ]
}
```

Changes have origin owner/concurrent/unknown, which are claims, not measured authorship.
Deliverable state is satisfied/missing/unchanged. Main can authorize `allow_unchanged: true`
when the outcome already exists; unchanged then requires evidence, not a fake edit.
Findings are open/addressed/resolved; only the authorized reviewer/Main resolves them.
Decisions are resolved/decision-needed. Questions have id/state and, when answered, answer
and evidence; state is answered/unanswered/unknown. Unknown routes to Main, not guessing.

Gate statuses: executed-pass, reused-pass, failed, blocked, unrun, deferred, not-applicable,
stale, unverified (status spelling is case-insensitive). Reuse cannot satisfy fresh_required.
A required not-applicable/deferred result cannot silently waive an obligation. The gate
vocabulary and freshness rule are shared with boundary.py through runtime/evidence.py.

With `current`, positive evidence for due gates, deliverables, findings and answers must
include an evidence reference and matching `basis`. Missing binding is UNVERIFIED; mismatch
is STALE. Without current, `identity_checked` is false: legacy records do not gain evidence
identity by implication. Empty obligations are unverified, not an empty success.

## Run and act once

```bash
python3 -B /absolute/CODEX_HOME/codex_workflow/runtime/challenge.py --input /private/handoff.json
```

Optional `--manifest /private/candidate.json` reads an existing candidate.py manifest and
freshly verifies its selected inputs. Its fingerprint must equal current.candidate. This
adds actual local identity observation, not served-build provenance, dependency discovery,
continuous locking or proof of authorship. Preserve holds and original evidence. A missing
input/error is not a match. Hashes cannot reveal changes made and later undone.

Exit 0: clear for the requested stage. Exit 1: contradiction/unverified obligation. Exit 2:
malformed/unreadable input or manifest. Output includes a leading issue, up to eight issues,
counts of omitted issues, pending obligations and next_action. No omitted item is a pass.
Main-related issues are shown first so decision-needed includes an actionable Main issue,
not merely a hidden routing flag. Category/input order is retained within each route.
Manifest drift joins the same bounded batch without hiding a protected decision. Read the
record to handle the remaining batch; do not repeatedly invoke the same unchanged check.

Mechanical repair/refresh stays with the current worker. Scope/attribution conflicts stop
for Main, without resetting or deleting another owner's changes. Recheck after relevant
facts change. CLEAR means only no supported contradiction in supplied observations. Missing
obligations, forged facts or authority claims remain invisible; all required independent
review, visual assessment and actual acceptance still apply.
