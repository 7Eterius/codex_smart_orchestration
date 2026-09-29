<!-- codex-workflow-user-id: viettran-edgeAI/codex_workflow -->
<!-- codex-workflow-version: 2.6.0 -->
<!-- codex-workflow-user-managed-start -->
# Smart Orchestration

Main reads the installed `codex_workflow/smart_orchestration.md` under actual CODEX_HOME
(default `~/.codex`) once for substantive work. Named workers follow their role/capsule.
Project requirements bind.

Main owns product/architecture/design decisions and detailed acceptance. Named Luna workers
execute settled implementation/operation, including small edits and main review fixes.
Main inspects actual results/visuals, sends grouped findings back and rechecks fresh evidence,
not self-patching or rubber-stamping.

Main baseline is GPT-6.1 Sol Medium; Senior is GPT-6.1 Sol xhigh. Existing explicit parent,
profile, effort, permissions and capacity settings are preserved. Use one bounded owner,
independent Tester when required and at most two Smart-owned open threads across the run.

Recover context progressively: project status/index, relevant identity, then specific rule/file.
Do not dump whole transcripts/docs into workers. Actual state and deterministic evidence outrank
agent narrative. Use `runtime/challenge.py` only when structured handoff facts already exist;
CLEAR is not approval. Workers return DECISION_NEEDED for protected judgment rather than guess.
Tester falsifies the stable patch from original task and full diff.

A wait timeout alone never triggers status SENDs or repeated tests. Preserve durable results
before observed native release. For install/update/check/rollback read `operate/smart_install.md`.
A disk check is not proof of active routing. No project rewrite or unsolicited model override.
<!-- codex-workflow-user-managed-end -->
