# Smart Orchestration releases

Canonical validation is the active functional/policy/migration suite plus package
validation. Build with `scripts/package_smart.py`, not the legacy packaging entry
point. Version and user marker must match.

Publish only after source review and complete CI. The release workflow validates
the tag, functional/policy/migration checks and package before publishing a ZIP
and SHA256SUMS to this fork. A PR, source version or CI artifact is not a release.
Normal global updates must never fall back to upstream.

One-time global adoption uses `runtime/smart_install.py --apply`; no project list.
Record the private backup location. Global updater is `--update --apply` on that
same script. Do not restore legacy per-project routing during an update.
See README and docs/smart_orchestration.md for constraints and test adaptations.
