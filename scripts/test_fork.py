#!/usr/bin/env python3
"""Run inherited functional tests plus the fork's native policy/adoption tests.

Exactly one upstream policy-text test is superseded, not passed or ignored on
failure. It hard-codes intentionally replaced defaults, intake and history-fork
rules. All other inherited tests remain. Native tests cover the new contracts
and pin unchanged worker/skill files by Git hash to retain their full semantics.
"""
from __future__ import annotations
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import test_workflow_runtime as upstream
import test_quality_economy as policies
import test_quality_economy_install as adoption

SUPERSEDED = "test_workflow_runtime.MarkerTests.test_operational_policies_are_compact_and_knowledge_aware"


def flattened(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flattened(item)
        else:
            yield item


def load_tests(loader, standard_tests, pattern):
    inherited = list(flattened(loader.loadTestsFromModule(upstream)))
    matches = [case for case in inherited if case.id() == SUPERSEDED]
    if len(matches) != 1:
        raise RuntimeError("Upstream policy-test layout changed; review the native test mapping.")
    suite = unittest.TestSuite(case for case in inherited if case.id() != SUPERSEDED)
    suite.addTests(loader.loadTestsFromModule(policies))
    suite.addTests(loader.loadTestsFromModule(adoption))
    return suite


if __name__ == "__main__":
    unittest.main()
