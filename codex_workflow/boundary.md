# Optional checked review boundaries

Use an existing capsule, not another ledger. boundary.py checks supplied identities and
obligations before review, repair or acceptance. It is not a native lock, authority grant
or evidence authenticator. Low-risk tasks do not need this record merely to finish.

A schema-1 record contains unit, attempt, contract, candidate, target, primary, writer,
reviewer, hold and gates. Identities/evidence references are nonblank, at most 256 characters,
without control characters. At most 128 gates and 64 KiB of input are supported.

```json
{
  "schema": 1, "unit": "card", "attempt": "A2", "contract": "R1",
  "candidate": "fingerprint-or-build-id", "target": "preview/test-account",
  "primary": "main", "writer": "main", "reviewer": "independent-reviewer",
  "hold": "held", "gates": {"behavior": true, "references": false}
}
```

Main may be the writer. The independent semantic reviewer must still differ from both writer
and primary. A different name is a supplied identity, not proof of a separate model context.
Procedural Tester receipts do not replace that semantic verdict. Primary and worker may differ
as before. Hold is held/released. Each gate boolean means fresh execution required (true), or
applicable reused evidence permitted (false), never PASS.

A separate verdict repeats unit/attempt/contract/candidate/target/reviewer, has an artifact
reference and the exact gate map. Each gate has status/evidence. executed-pass satisfies
freshness; reused-pass satisfies only a non-fresh gate. failed, blocked, unrun, deferred,
not-applicable, stale and unverified cannot satisfy an obligation. Status is case-insensitive
through evidence.py. Required evidence is not waived by Main writing the implementation.

```bash
python3 -B /absolute/CODEX_HOME/codex_workflow/runtime/boundary.py --input /private/boundary.json
```

Input keys are record, action, actor and optional verdict (accept only). write requires the
writer and released hold. review requires the distinct reviewer and held candidate. readback
allows named participants to inspect, not edit. accept requires primary, held candidate and
matching independent verdict with every gate satisfied. Exit 0 is consistent, 1 blocked,
2 malformed; none grants Git/deployment/owner approval.

Release holds before repair, including Main's small corrections. Retain rejected verdicts,
identify the new candidate and update the original capsule. Reject old verdicts. Reconcile
source/build/target after interruptions. Helpers cannot detect forged claims, omitted
obligations or an intervening change that was undone. Actual state/evidence remain necessary.

For allocation, read execution.md: scope-aware parallelism is separate from a review boundary.
The primary handle is explicit, or literal main for old inputs. A completed thread occupies
capacity until native closure is observed. Readback is not reactivation; cleanup is not a new
work grant. Never use a false boundary record to bypass permissions or another writer.
