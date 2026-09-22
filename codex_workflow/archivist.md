# Smart Orchestration memory handoff

Use `archivist` only at meaningful completed/paused/blocked checkpoints or an
accepted major milestone. Give Task ID, canonical memory paths, verified changes,
main acceptance decision, open gates, next action and evidence references. Spawn
with `fork_turns="none"`; reuse the same Archivist with deltas when appropriate.

Archivist owns only assigned canonical memory. Keep current state concise and append
one meaningful changelog delta; preserve older history and decision rationale without
duplicating it. For a read-only request return a proposed handoff without writing.
Missing persistence is a blocker, not a saved checkpoint.

A milestone handoff is the seed for a future fresh main session when the next work
is substantially unrelated. Do not perform token/usage accounting or orchestration
statistics. Main checks the handoff; a memory contradiction reopens that handoff,
not the whole product audit unless it exposes a material acceptance error.
