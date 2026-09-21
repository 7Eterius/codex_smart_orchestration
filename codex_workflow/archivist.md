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

Project memory does not require a token report. Run deployment-token-report only
when explicitly requested for a known deployment/window, never automatically at
closure or repeatedly on unchanged missing data. Main can run it directly without
creating an Archivist solely for reporting. Preserve table, scope and warnings;
unknown usage stays unknown, never a pricing guess or an inferred zero.
The main checks the handoff; a memory contradiction reopens only that handoff,
not a whole production re-audit unless it exposes a material acceptance error.
