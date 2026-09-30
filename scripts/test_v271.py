"""2.7.1 patch regressions: failed-gate handoff and single-writer bridge safety.

No live model behavior or savings claims. Exact reviewed-2.7 history is required in CI.
"""
from __future__ import annotations

import io
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

from runtime import challenge
from test_current import VERSION, EXPECTED
from test_v240 import snapshot

BASELINE = "388e8e8498bc184b05eddd0f9a1fb9d9e6223c7c"


def current():
    return dict(attempt="A2", contract="R1", candidate="C2", target="preview/2")


def handoff(status="unrun", *, basis=True, evidence=True):
    row = dict(gate="independent-review", required=True, fresh_required=True,
               status=status, due="accept")
    if evidence:
        row["evidence"] = "artifacts/review"
    if basis:
        row["basis"] = current()
    return dict(schema=1, unit="card", phase="handoff", current=current(),
                owned_paths=["src/card"], changes=[],
                deliverables=[dict(path="src/card/view.ts", required=True, state="satisfied",
                                   evidence="artifacts/diff", basis=current())],
                findings=[], decisions=[], questions=[], evidence=[row])


class HandoffGateTests(unittest.TestCase):
    def test_known_current_failure_returns_to_worker_before_review(self):
        result = challenge.check(handoff("failed"))
        self.assertEqual(result["status"], "challenge")
        self.assertEqual(result["class"], "gate-failed")
        self.assertEqual(result["reference"], "independent-review")
        self.assertEqual(result["next_action"], "repair-or-refresh")
        self.assertEqual(result["pending_count"], 0)

    def test_not_yet_run_acceptance_gate_stays_pending(self):
        result = challenge.check(handoff("unrun", basis=False, evidence=False))
        self.assertEqual(result["status"], "clear")
        self.assertEqual(result["pending_count"], 1)
        self.assertEqual(result["pending"][0]["reported_status"], "unrun")
        self.assertEqual(result["next_action"], "return-for-required-review")

    def test_failed_gate_must_be_bound_to_current_candidate(self):
        value = handoff("failed")
        value["evidence"][0]["basis"]["candidate"] = "C1"
        result = challenge.check(value)
        self.assertEqual(result["class"], "evidence-stale")
        self.assertNotIn("gate-failed", [item["class"] for item in result["issues"]])

        value = handoff("failed", basis=False, evidence=False)
        result = challenge.check(value)
        self.assertEqual(result["class"], "evidence-unverified")

    def test_bridge_mutations_are_single_writer_and_review_visible(self):
        policy = " ".join((PACKAGE / "smart_orchestration.md").read_text().split())
        execution = " ".join((PACKAGE / "execution.md").read_text().split())
        verification = " ".join((PACKAGE / "verification.md").read_text().split())
        self.assertIn("Never write the same candidate concurrently", policy)
        self.assertIn("pauses/transfers write ownership", policy)
        self.assertIn("Keep one writer per candidate", execution)
        self.assertIn("stale affected evidence", execution)
        self.assertIn("A Main bridge or concurrent mutation must be included", verification)
        self.assertIn("if its impact is unknown, the optimization is unavailable", verification)


class ReleaseContracts(unittest.TestCase):
    def test_patch_version_and_model_map(self):
        self.assertEqual(VERSION, "2.7.1")
        self.assertEqual((PACKAGE / "operate/VERSION").read_text(), "2.7.1\n")
        self.assertIn("codex-workflow-version: 2.7.1",
                      (PACKAGE / "operate/user_AGENTS.md").read_text())
        self.assertTrue((ROOT / "README.md").read_text().startswith("# Smart Orchestration 2.7.1"))
        self.assertTrue((ROOT / "docs/v2.7.md").read_text().startswith("# 2.7.1:"))
        for role, expected in EXPECTED.items():
            cfg = tomllib.loads((PACKAGE / "agents" / f"{role}.toml").read_text())
            self.assertEqual((cfg["model"], cfg["model_reasoning_effort"]), expected)

    def test_prompt_budgets_are_not_relaxed(self):
        limits = {"smart_orchestration.md": 1200, "execution.md": 1000,
                  "verification.md": 700, "browser.md": 650, "design.md": 600}
        for name, limit in limits.items():
            self.assertLess(len((PACKAGE / name).read_text().split()), limit, name)

    def test_active_runtime_docs_do_not_carry_stale_release_labels(self):
        self.assertNotIn("Smart 2.6", (PACKAGE / "runtime/allocation.py").read_text())
        self.assertNotIn("Smart 2.5", (PACKAGE / "runtime_check.md").read_text())


class ActualReviewedV27Upgrade(unittest.TestCase):
    def test_reviewed_27_to_271_reapply_and_exact_rollback(self):
        ran = subprocess.run(["git", "archive", BASELINE, "codex_workflow"],
                             cwd=ROOT, capture_output=True)
        if ran.returncode:
            if os.environ.get("CI"):
                self.fail("Exact reviewed 2.7 source required: " + ran.stderr.decode(errors="replace"))
            self.skipTest("Reviewed 2.7 history unavailable locally; required in CI")

        from runtime import smart_install as install
        from runtime.smart_restore import prepare_restore

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            old = root / "old"
            home = root / "home"
            home.mkdir()
            with tarfile.open(fileobj=io.BytesIO(ran.stdout)) as archive:
                for member in archive:
                    rel = Path(member.name)
                    self.assertFalse(rel.is_absolute())
                    self.assertNotIn("..", rel.parts)
                    self.assertEqual(rel.parts[0], "codex_workflow")
                    if member.isfile():
                        dst = old / rel
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        dst.write_bytes(archive.extractfile(member).read())
                        dst.chmod(member.mode & 0o777)
                    else:
                        self.assertTrue(member.isdir())

            package = old / "codex_workflow"
            self.assertEqual((package / "operate/VERSION").read_text(), "2.7.0\n")
            (home / "config.toml").write_text(
                'model="owner-main"\nmodel_reasoning_effort="high"\n'
                'approval_policy="on-request"\n[agents]\nmax_threads=1\n'
                'default_subagent_model="owner-child"\n'
            )
            (home / "AGENTS.md").write_text("Protected owner instructions.\n")
            project = root / "project"
            project.mkdir()
            (project / "source").write_text("Protected project.")

            old_command = [sys.executable, "-B", str(package / "runtime/smart_install.py"),
                           "--package-root", str(package), "--codex-home", str(home)]
            first = subprocess.run(old_command + ["--apply"], capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            before, project_before = snapshot(home), snapshot(project)

            plan, prior = install.prepare(PACKAGE, home)
            self.assertEqual(snapshot(home), before, "Preview must not mutate")
            backup = install.apply_plan(plan, prior, home)
            self.assertTrue(install.status(home)["disk_ok"])
            self.assertEqual(install.status(home)["version"], "2.7.1")

            old_cfg = tomllib.loads(before["config.toml"][0].decode())
            new_cfg = tomllib.loads((home / "config.toml").read_text())
            old_cfg.pop("developer_instructions", None)
            new_cfg.pop("developer_instructions", None)
            self.assertEqual(old_cfg, new_cfg)

            for role in (package / "agents").glob("*.toml"):
                old_role = tomllib.loads(role.read_text())
                new_role = tomllib.loads((home / "agents" / role.name).read_text())
                for key in ("model", "model_reasoning_effort", "sandbox_mode", "agents"):
                    self.assertEqual(old_role[key], new_role[key], (role.name, key))

            self.assertEqual(install.prepare(PACKAGE, home)[0].mutations, [])
            self.assertEqual(snapshot(project), project_before)

            restore, prior = prepare_restore(home, backup)
            install.apply_plan(restore, prior, home)
            self.assertEqual(snapshot(home), before)
            self.assertEqual(snapshot(project), project_before)
            checked = subprocess.run(old_command + ["--check"], capture_output=True, text=True)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)


if __name__ == "__main__":
    unittest.main()
