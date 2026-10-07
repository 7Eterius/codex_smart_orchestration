# Feature branches and worktrees without destructive housekeeping

Use for large features, long-lived parallel changes, risky experiments, or explicit isolation
requests. Small authorized changes can stay in the current suitable checkout. A branch/worktree
is a delivery tool, not a mandatory artifact per task or permission to publish.

## Inspect before creating

Identify canonical repository root, current branch/HEAD, intended base, tracked/staged/untracked
changes, linked worktrees and native workspace ownership. Distinguish linked worktrees, submodules
and detached host-managed workspaces. Reuse suitable existing isolation; do not nest worktrees
because an agent forgot the harness already created one. Main includes its own scope in conflict
checks. Different worktrees can still share databases, accounts, ports, caches and browser state.

Use actual supported native worktree operations first when available. A manual Git worktree is a
fallback only with existing Git/worktree authority. Respect an explicit location/no-worktree
preference; never overwrite an existing branch/directory. Verify the exact selected local parent
is ignored when that is necessary, not some alternate directory. Do not automatically commit
.gitignore changes, alter Git settings, stash/reset dirty work or install dependencies to get ready.

Use project-pinned setup/lockfiles only when needed and authorized. Reuse valid baseline evidence;
run the decisive affected baseline and mandated full baseline, not an automatic full suite in each
worker. Preserve known baseline failures and distinguish them from regressions. A required failing
gate is still failing. If required isolation is unavailable, report the limitation; do not silently
fall back to editing shared main. An in-place alternative needs scope/resource safety and authority.

## Integrate a complete candidate

Record the actual base before each coherent unit. Review the full base-to-candidate change, not
HEAD~1, which can omit earlier commits. Include relevant staged, unstaged and explicitly selected
untracked deliverables, file modes and generated/config inputs. A commit diff alone does not
cover dirty files. Large review packets can be files in an approved private scratch location,
with candidate identity and original requirements; never blindly bundle secrets or whole histories.

Review spec compliance and technical quality in one bounded independent pass. At large-feature
integration, inspect cross-component contracts, deferred findings and the complete integrated
candidate once. Reuse valid task-level evidence while checking new interactions. Do not rerun
identical suites just because another role sees the result. Relevant integration changes still
invalidate affected proof and all mandated fresh gates remain binding.

## Finish with actual authority

Follow the already-authorized finish target rather than forcing a fixed menu. Without merge or
publication authority, leave a tested branch/patch or authorized PR and report its location and
remaining obligations. PR creation, merge, deployment and release are different actions. Verify
remote head/base and required checks for the exact intended candidate before authorized integration;
never force-push or override protections to resolve a stale head. Check the integrated result.

Keep worktrees for PR feedback and pending findings. Cleanup requires recorded creation/ownership,
not merely a path under .worktrees. Check branch reachability, dirty/untracked AND ignored files,
needed reports and resource owners before removal. Use native exit/removal when host-owned.
Refused removal is a stop, not a reason for --force, git clean -fdx or rm -rf. Preserve other tasks,
logs and checkpoints. Destructive cleanup/discard needs explicit authorization; no automatic prune
of unrelated worktrees. A completed release does not authorize erasing useful evidence.
