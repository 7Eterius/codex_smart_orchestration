# Smart Orchestration memory handoff

Use `archivist` at meaningful completed/paused/blocked checkpoints. Give Task ID,
project root, canonical memory paths, main acceptance decision, verified changes,
in-progress work, open gates, next action and exact evidence references. Use `fork_turns="none"`; no full
conversation fork. Reuse the existing Archivist with a delta when appropriate.

Archivist owns the assigned memory files, including current project state. Append
one concise changelog entry and update the current handoff, preserving older
history and unrelated work. Do not duplicate state in multiple documents, edit
production code, decide acceptance or silently resolve contradictory evidence.
For a read-only request, return a handoff without writing. Missing persistence
must be reported, not presented as a saved checkpoint.

After the main has supplied verified closure facts and all relevant mutations are
finished, use the existing deployment-token-report once with the supplied ID.
Keep the exact table, cutoff and warning semantics. No estimate for missing data.
The main checks the handoff; a memory contradiction reopens only that handoff,
not a whole production re-audit unless it exposes a material acceptance error.
