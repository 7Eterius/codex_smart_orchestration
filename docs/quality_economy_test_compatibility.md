# Inherited test compatibility

The canonical suite is `python3 -B scripts/test_fork.py -v`, followed by the
unchanged deployment-token-report suite. It loads the inherited runtime tests
and applies explicit test adaptations rather than catching or suppressing
failures. Source updates that change the expected test identifiers fail loading
until the mapping is reviewed.

## Superseded policy-text test

`MarkerTests.test_operational_policies_are_compact_and_knowledge_aware` hard-codes
the original parent-only objective, full module intake and 200-turn Archivist
fork. Native policy tests replace that monolithic text assertion. The unchanged
worker contracts and token-report skill are checked by exact Git blob hashes;
new policy tests cover native scope, safety, intake, verification and closure.

## Adapted assertions

`PlatformSettingsTests.test_fixed_route_and_worker_need_no_settings_rendering`
still checks that routes need no effective-config rendering or fixed-settings
block and that Default Executor retains Max reasoning. Its one old
`fork_turns="200"` assertion is replaced with `fork_turns="none"` plus an explicit
absence check for the old default.

`LifecycleIntegrationTests.test_projects_update_against_their_recorded_historical_sources`
originally hard-codes its incoming fixture as version 1.2.0. That collides with
this fork's native version and creates two different templates carrying the same
version. The adapted fixture uses the next patch version and verifies it differs
from the installed version. It preserves the two-project update, deliberately
changed template, historical-version assertions, and resulting-template check.

Every other inherited functional test remains unchanged. Additional tests cover
real upstream-to-fork adoption, source discovery, preview approval, unchanged
owner data, protected preferences, disabled projects and staged-source safety.
A passing software suite does not prove model adherence or allowance savings.
