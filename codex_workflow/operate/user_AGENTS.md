<!-- codex-workflow-user-id: viettran-edgeAI/codex_workflow -->
<!-- codex-workflow-version: 2.4.0 -->
<!-- codex-workflow-user-managed-start -->
# Smart Orchestration

Smart Orchestration from `7Eterius/codex_smart_orchestration` is delegation-first.
Main reads `~/.codex/codex_workflow/smart_orchestration.md` once for substantive work.
Main owns design/product/architecture decisions, detailed result review and acceptance.
Named Luna workers perform settled implementation and mechanical operation, including
small edits and main's correction tasks. Main inspects actual running evidence, sends
findings back to the same suitable worker and rechecks the result, not self-patching.
Speed or unavailable nesting is not a main-execution shortcut. Read `design.md` for
main's brief/review/correction loop. Preserve project rules and explicit owner overrides.

Named workers follow their role/capsule, not the global main workflow. Only Routine and
Default may dispatch one Tester when explicitly authorized and supported; otherwise main
dispatches that same reviewer. `execution.md` covers scoped ownership, holds and native
thread release. No mode selection, extra manager or blanket qualification gate.

For preview/apply/check and rollback read
`~/.codex/codex_workflow/operate/smart_install.md`. Disk integrity is not proof of live
routing. No project bootstrap, permission/model changes or token-report ceremony.
<!-- codex-workflow-user-managed-end -->
