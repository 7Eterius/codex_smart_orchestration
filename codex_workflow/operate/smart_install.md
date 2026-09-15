# Smart Orchestration global lifecycle

Python 3.11+. Use the actual installed interpreter; on Ilya's Mac the verified
path is `/opt/homebrew/bin/python3.11`, not the system Python 3.9. Never use sudo.

No repository search, project path, or per-project install is needed. From a
reviewed package, `runtime/smart_install.py --apply` installs globally with private
backups and preserves unrelated user config and repository files. Default mode
is preview only; `--check` reports disk activation, not live model behavior.
Quit other Codex sessions before applying. Honor nondefault CODEX_HOME.

For `codex_workflow --install`, use the global installer, not the legacy project
bootstrap. `--check-update` inspects this fork's checksummed releases without
applying; `--update` uses `smart_install.py --update --apply`. No release exists
merely because CI built an artifact. No usable release -> report, never fall back
to upstream. Existing custom worker overrides block replacement for review.

For legacy `--personal`, repository-specific product rules remain ordinary local
instructions; no route profile is needed. For `--disable`/`--enable`, honor an
explicit session request not to orchestrate/to resume. Persistent disable/remove
needs a reviewed removal plan for the Smart config block and managed global
entry; do not invoke the old recursive runtime-removal command. Preserve backups,
project memory, owner config and source. Do not claim a session-only opt-out is a
persistent uninstall. Restoration guidance is in the package README.
