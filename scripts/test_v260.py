"""2.6 lightweight BlaBla-inspired contracts and exact archived 2.5 migration.

The deterministic challenge helper checks supplied facts only. Tests do not prove semantic
correctness, live model behavior, evidence authenticity or allowance savings.
"""
from __future__ import annotations

import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "codex_workflow"
sys.path.insert(0, str(PACKAGE))

from runtime import challenge, smart_install as install
from runtime.layout import INSTALLED_RUNTIME_FILES, PackageLayout
from runtime.smart_restore import prepare_restore
from test_current import VERSION
from test_v240 import snapshot

BASELINE = "f2e618ddff72154486f4f8898e2ecf44fed175c8"


def flat(path):
    return " ".join(path.read_text().split())


def record():
    return {
        "schema": 1,
        "unit": "reader-card",
        "owned_paths": ["src/card"],
        "changes": [{"path": "src/card/Card.tsx", "origin": "owner"}],
        "deliverables": [{"path": "src/card/Card.tsx", "required": True, "state": "satisfied"}],
        "findings": [],
        "evidence": [{"gate": "unit", "required": True, "fresh_required": True,
                      "status": "executed-pass"}],
        "decisions": [],
    }


class ChallengeTests(unittest.TestCase):
    def test_clear_is_bounded_and_does_not_mutate_input(self):
        value = record()
        before = copy.deepcopy(value)
        result = challenge.check(value)
        self.assertEqual(result["status"], "clear")
        self.assertIn("not semantic correctness", result["limitation"])
        self.assertEqual(value, before)

    def test_scope_attribution_and_decision_challenges(self):
        cases = []
        value = record()
        value["changes"].append({"path": "src/auth.ts", "origin": "owner"})
        cases.append((value, "scope-breach"))
        value = record()
        value["changes"][0]["origin"] = "unknown"
        cases.append((value, "attribution-unknown"))
        value = record()
        value["changes"][0]["origin"] = "concurrent"
        cases.append((value, "scope-conflict"))
        value = record()
        value["decisions"] = [{"id": "D1", "state": "decision-needed"}]
        cases.append((value, "decision-needed"))
        for payload, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(challenge.check(payload)["class"], expected)

    def test_deliverable_finding_and_evidence_challenges(self):
        value = record()
        value["deliverables"][0]["state"] = "missing"
        self.assertEqual(challenge.check(value)["class"], "deliverable-missing")
        value = record()
        value["findings"] = [{"id": "F1", "blocking": True, "state": "addressed"}]
        self.assertEqual(challenge.check(value)["class"], "blocking-finding")
        for status, expected in (
            ("failed", "gate-failed"), ("stale", "evidence-stale"),
            ("unverified", "evidence-unverified"), ("blocked", "gate-blocked"),
            ("unrun", "gate-unrun"), ("deferred", "gate-deferred"),
            ("not-applicable", "gate-not-applicable"),
        ):
            value = record()
            value["evidence"][0]["status"] = status
            with self.subTest(status=status):
                self.assertEqual(challenge.check(value)["class"], expected)
        value = record()
        value["evidence"][0]["status"] = "reused-pass"
        self.assertEqual(challenge.check(value)["class"], "fresh-evidence-required")

    def test_nonblocking_and_optional_observations_do_not_block(self):
        value = record()
        value["findings"] = [{"id": "F1", "blocking": False, "state": "open"}]
        value["evidence"].append({"gate": "optional", "required": False,
                                  "fresh_required": True, "status": "unverified"})
        self.assertEqual(challenge.check(value)["status"], "clear")

    def test_malformed_and_duplicate_json_fail_closed(self):
        with self.assertRaises(challenge.ChallengeError):
            challenge.check({"schema": 1})
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "input.json"
            path.write_text('{"schema":1,"schema":1}')
            result = subprocess.run(
                [sys.executable, "-B", str(PACKAGE / "runtime/challenge.py"), "--input", str(path)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn('"status": "error"', result.stderr)


class PolicyContracts(unittest.TestCase):
    def test_version_install_and_prompt_budgets(self):
        self.assertEqual((PACKAGE / "operate/VERSION").read_text(), VERSION + "\n")
        self.assertEqual(PackageLayout.resolve(PACKAGE).version, VERSION)
        self.assertIn("runtime/challenge.py", INSTALLED_RUNTIME_FILES)
        self.assertIn(PACKAGE / "runtime/challenge.py", PackageLayout.resolve(PACKAGE).files)
        for name, limit in (("smart_orchestration.md", 1200), ("execution.md", 1000),
                            ("verification.md", 700), ("browser.md", 650), ("design.md", 600)):
            self.assertLess(len(flat(PACKAGE / name).split()), limit, name)

    def test_progressive_disclosure_evidence_and_decision_boundaries(self):
        policy = flat(PACKAGE / "smart_orchestration.md")
        execution = flat(PACKAGE / "execution.md")
        for phrase in ("Progressive disclosure", "Agent self-reports are advisory pointers",
                       "STALE and UNVERIFIED", "DECISION_NEEDED",
                       "Do not invent numeric confidence thresholds",
                       "CLEAR means no supported contradiction"):
            self.assertIn(phrase, policy)
        self.assertIn("project instructions/status/index first", execution)
        self.assertIn("Retrieving guidance is not applying it", execution)
        self.assertIn("Do not create a ledger solely for this helper", execution)

    def test_tester_is_falsification_first(self):
        text = flat(PACKAGE / "agents/tester.toml")
        for phrase in ("original bounded task", "complete actual diff", "account for every deliverable",
                       "controlling code", "sibling cases", "smallest concrete counterexample",
                       "BLOCKING", "NON-BLOCKING"):
            self.assertIn(phrase, text)
        cfg = tomllib.loads((PACKAGE / "agents/tester.toml").read_text())
        self.assertLess(len(cfg["developer_instructions"].split()), 200)

    def test_workers_return_protected_ambiguity_instead_of_guessing(self):
        for role in ("simple_executor", "routine_executor", "default_executor"):
            text = flat(PACKAGE / "agents" / f"{role}.toml")
            self.assertIn("DECISION_NEEDED", text)
            self.assertIn("Why outside", text)
            self.assertIn("deterministic challenge", text)

    def test_no_new_agent_mode_or_mandatory_project_database(self):
        policy = flat(PACKAGE / "smart_orchestration.md")
        self.assertIn("Do not create a task database or mandatory ledger solely for this helper", policy)
        self.assertNotIn("chunk_lead", {p.stem for p in (PACKAGE / "agents").glob("*.toml")})
        self.assertFalse((PACKAGE / "coordinated.md").exists())


class ActualV25Upgrade(unittest.TestCase):
    def test_archived_25_upgrade_reapply_check_and_exact_rollback(self):
        got = subprocess.run(["git", "archive", BASELINE, "codex_workflow"],
                             cwd=ROOT, capture_output=True)
        if got.returncode:
            if os.environ.get("CI"):
                self.fail("Exact 2.5 history required: " + got.stderr.decode(errors="replace"))
            self.skipTest("Exact 2.5 object unavailable locally; required in CI")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            old = root / "baseline"
            home = root / "home"
            home.mkdir()
            with tarfile.open(fileobj=io.BytesIO(got.stdout)) as archive:
                for member in archive:
                    relative = Path(member.name)
                    self.assertFalse(relative.is_absolute())
                    self.assertNotIn("..", relative.parts)
                    self.assertEqual(relative.parts[0], "codex_workflow")
                    if member.isfile():
                        path = old / relative
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(archive.extractfile(member).read())
                        path.chmod(member.mode & 0o777)
                    else:
                        self.assertTrue(member.isdir())
            package = old / "codex_workflow"
            self.assertEqual((package / "operate/VERSION").read_text(), "2.5.0\n")
            config = ('model="gpt-6.1-sol"\nmodel_reasoning_effort="medium"\n'
                      'approval_policy="on-request"\n[agents]\nmax_threads=2\n'
                      'default_subagent_model="owner-fallback"\n')
            (home / "config.toml").write_text(config)
            (home / "AGENTS.md").write_text("Protected owner instructions.\n")
            project = root / "project"
            project.mkdir()
            (project / "owner.txt").write_text("untouched")
            command = [sys.executable, "-B", str(package / "runtime/smart_install.py"),
                       "--package-root", str(package), "--codex-home", str(home)]
            ran = subprocess.run(command + ["--apply"], capture_output=True, text=True)
            self.assertEqual(ran.returncode, 0, ran.stdout + ran.stderr)
            before, project_before = snapshot(home), snapshot(project)

            plan, prior = install.prepare(PACKAGE, home)
            self.assertEqual(snapshot(home), before)
            backup = install.apply_plan(plan, prior, home)
            self.assertTrue(install.status(home)["disk_ok"])
            self.assertEqual((home / "codex_workflow/operate/VERSION").read_text(), VERSION + "\n")
            self.assertTrue((home / "codex_workflow/runtime/challenge.py").is_file())
            old_cfg = tomllib.loads(before["config.toml"][0].decode())
            new_cfg = tomllib.loads((home / "config.toml").read_text())
            old_cfg.pop("developer_instructions", None)
            new_cfg.pop("developer_instructions", None)
            self.assertEqual(old_cfg, new_cfg)
            self.assertEqual(install.prepare(PACKAGE, home)[0].mutations, [])
            self.assertEqual(snapshot(project), project_before)

            restore, prior = prepare_restore(home, backup)
            install.apply_plan(restore, prior, home)
            self.assertEqual(snapshot(home), before)
            self.assertEqual(snapshot(project), project_before)
            self.assertFalse((home / "codex_workflow/runtime/challenge.py").exists())
            checked = subprocess.run(command + ["--check"], capture_output=True, text=True)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)


if __name__ == "__main__":
    unittest.main()
