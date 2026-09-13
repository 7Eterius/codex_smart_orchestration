# Releasing the Quality Economy fork

Release source: `7Eterius/codex_workflow`. Current source version: `1.2.0`.
A version file does not mean a GitHub Release has been published.

Keep `codex_workflow/operate/VERSION` and the version marker in
`codex_workflow/operate/user_AGENTS.md` identical. The legacy ownership marker
is intentional compatibility metadata, not the release source. Review any
upstream integration rather than overwriting native policies automatically.

## Required checks

From a complete source checkout with full history:

```bash
python3 -B scripts/test_fork.py -v
python3 -B scripts/test_deployment_token_report.py -v
python3 -B codex_workflow/runtime/workflow.py validate --package-root codex_workflow --json
python3 -B scripts/package_release.py --release-tag v1.2.0 --output-dir dist
python3 -B scripts/package_release.py --verify dist/codex_workflow-1.2.0.zip --version 1.2.0
git diff --check
```

The fork runner replaces one superseded upstream policy-text test with native
contract and adoption tests; all other inherited tests remain required. No
failure is caught and reclassified as a pass. Unchanged worker definitions and
the token-report skill are pinned by Git blob hash. The adoption tests reconstruct
the exact baseline package with local read-only Git calls, so fetch full history.

The Quality Economy CI validates on Python 3.11 and 3.12, then builds and verifies
the universal ZIP. Its artifact is not a published release. Missing or disabled
GitHub Actions must be reported honestly; perform checks locally before adoption.

## Publish deliberately

After review and successful checks, create the matching version tag and use
`.github/workflows/release.yml` to publish the universal ZIP plus `SHA256SUMS`.
The release workflow targets the fork where it runs. Tag push and manual dispatch
both validate before publication. Do not publish from an unreviewed working tree
or copy old upstream `dist/` files into a new fork release.

The installed updater consumes only this fork's releases. Until the matching
assets exist it fails clearly, without falling back to upstream. Initial source
adoption from a reviewed commit remains available without a published release.

Keep application archives, credentials, owner paths and project screenshots out
of this public repository and its release artifacts. Quality claims require
representative real deployments in addition to these software checks.
