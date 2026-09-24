# Checked review boundaries

Use the existing capsule, not another ledger. For an independent-review unit the
optional `runtime/boundary.py` checks supplied identities and obligations before review,
repair resumption or acceptance. It is read-only, not a native scheduler, lock, evidence
authenticator or authority grant. Ordinary low-risk work does not need this record.

## Capsule and verdict

A record uses schema 1 and exactly these fields:

```json
{
  "schema": 1,
  "unit": "pricing-page",
  "attempt": "A2",
  "contract": "pricing-requirements-v3",
  "candidate": "candidate-fingerprint-or-exact-build-id",
  "target": "preview-build-17/test-account",
  "primary": "main-handle",
  "writer": "routine-handle",
  "reviewer": "tester-handle",
  "hold": "held",
  "gates": {"behavior": true, "reference-check": false}
}
```

Gate booleans mean fresh execution is mandatory (`true`) or applicable reused evidence
is permitted (`false`), not that the gate passed. Main derives this map from authoritative
requirements. All identifiers and references are nonempty and at most 256 characters;
at most 128 gates and 64 KiB of input are accepted. Use a short private evidence reference
when an absolute artifact path exceeds that bound.

The separate Tester verdict has the same unit, attempt, contract, candidate, target
and reviewer; an `artifact` reference; and an exact matching `gates` map. Each verdict
gate contains `status` and `evidence`. `executed-pass` satisfies a gate; `reused-pass`
satisfies only a non-fresh gate after applicability is checked. Failed, blocked, unrun,
deferred and not-applicable never silently satisfy a required gate. Explicitly authorized
changes to obligations require a revised contract and new applicable evidence.

## Check one transition

Pass an existing private JSON input with `record`, `action`, `actor`, and (for acceptance
only) `verdict`:

```bash
python3 -B /absolute/CODEX_HOME/codex_workflow/runtime/boundary.py --input /private/boundary-check.json
```

`write` requires the current writer and a released hold. `review` requires the independent
reviewer and a held candidate. `readback` allows the named participants to inspect state,
not resume editing. `accept` requires Main, a held candidate, a matching independent
verdict and every required gate. Exit codes: 0 consistent, 1 blocked, 2 malformed input.
A zero exit is not permission to commit, integrate or release.

A repair releases the hold first, preserves the rejected verdict, and creates a new
attempt/candidate before review. Update the existing capsule, then reject old verdicts.
After interruption reconcile actual source, build, target and native handles first.
The checker cannot detect an invented observation or an intervening change that was
changed back; actual holds, source/target checks and original evidence remain necessary.

## Allocation inputs in 2.3

Supply the actual `primary` handle separately from spawned threads. For legacy inputs,
only the literal `main` is the default primary; an arbitrary absent caller is not Main.
An owner starting nested review needs `review_authorized: true`, its own unit, and a
running/waiting lifecycle. This boolean records explicit delegation, not native proof.
The caller must separately establish supported nesting and inherited permissions.

Requests default to `intent: "work"`. Both new writers and writer reuse require exclusive
unit ownership. `intent: "readback"` requires an existing stopped matching child and
`reserve: 0`, and never grants writes. `intent: "cleanup"` also requires `reserve: 0`
and no reuse ID. Cleanup can release eligible completed children of a completed/retired
owner without authorizing new work. Observe native closure before counting its slot.
