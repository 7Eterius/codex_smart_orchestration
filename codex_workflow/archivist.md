# Archivist Assignments

Use Archivist for verified documentation in substantive Heavy or Medium work.
Every assignment has Task ID, Documentation Context + Audience, Documentation
Task + Goal, and Main-Agent Documentation Guidance. Specify the write surface,
verified facts, exact evidence references and material limits. Update only the
changed canonical documents; remove stale detail rather than append chronology.

## Deployment Closure

Assign one Archivist before the final response that completes, pauses or blocks
a substantive deployment. First update main-owned
`agent_docs/project_progress.md`, `agent_docs/project_diary.md`, and
`agent_docs/latest_session_work.md`. Keep those outside Archivist's write scope;
identify them as canonical deployment-state sources.

Reuse an Archivist when its retained context plus a concise delta is sufficient.
Otherwise create one with `agent_type="archivist"`, a unique task name such as
`archivist_<deployment_id>`, and `fork_turns="none"`. Do not automatically copy
200 turns of parent history. Give the deployment ID, closure state, canonical
state paths, verified outcomes, remaining gaps, authorized documentation edits,
and exact evidence references. If the capsule is insufficient, request the
specific missing evidence instead of inheriting the whole conversation.

Combine remaining verified documentation with closure when practical. Keep the
Git handoff read-only unless an explicit separate task authorizes a mutation.
Ensure other workers finish relevant changes before Archivist seals the handoff.
Assign only one reporting owner. Preserve the exact six-column
`$deployment-token-report`, accounting boundary and warning semantics; relay it
without duplicate checks or invented pricing. Cached input is a subset of Input,
not a second quantity to add to it. Keep account-allowance measurements separate.

The token-report script obtains parent ancestry and deployment metadata from
session records; a copied parent transcript is not its reporting boundary.
Report missing metadata as a limitation rather than inventing usage.

A later substantive deployment gets a new ID and its own closure. Complete
questions and small bounded direct-fast-path tasks need neither Archivist nor
a token report. If closure is blocked, state what remains unfinished accurately.
