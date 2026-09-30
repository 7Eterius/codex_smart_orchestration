"""2.7 review regressions: coherent evidence, actionable batches and bounded re-review.

No live model use or quota claims. Exact historical source is required in CI.
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
from contextlib import redirect_stdout
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "codex_workflow"
sys.path.insert(0, str(PACKAGE))
from runtime import boundary, challenge, evidence
from test_current import VERSION

BASELINE = "8b5e5de112dd3c8b468d6a55c81051556124a2ef"


def boundary_record():
    return dict(schema=1, unit="U1", attempt="A1", contract="R1", candidate="C1", target="preview/1",
                primary="main", writer="writer", reviewer="reviewer", hold="held", gates={"unit": True})


def verdict(record, status="executed-pass"):
    value = {k: record[k] for k in (*boundary.IDENTITY, "reviewer")}
    value.update(artifact="review/original", gates={"unit": dict(status=status, evidence="logs/unit")})
    return value


def preflight():
    return dict(schema=1, unit="U1", owned_paths=["src"], changes=[], deliverables=[], findings=[],
                decisions=[], evidence=[dict(gate="unit", required=True, fresh_required=True,
                                             status="executed-pass")])


class SharedEvidenceTests(unittest.TestCase):
    def test_both_helpers_use_the_same_status_vocabulary(self):
        self.assertIs(challenge.EVIDENCE, evidence.STATUSES)
        for status in evidence.STATUSES:
            for spelling in (status, status.upper()):
                for fresh in (True, False):
                    with self.subTest(status=spelling, fresh=fresh):
                        expected = status == "executed-pass" or (status == "reused-pass" and not fresh)
                        record = boundary_record(); record["gates"]["unit"] = fresh
                        self.assertEqual(boundary.check(record, "accept", "main", verdict(record, spelling))["allowed"], expected)
                        value = preflight(); value["evidence"][0].update(status=spelling, fresh_required=fresh)
                        self.assertEqual(challenge.check(value)["status"] == "clear", expected)

    def test_negative_states_are_blocked_not_malformed_at_real_cli(self):
        for state in ("stale", "STALE", "unverified", "UNVERIFIED"):
            record = boundary_record()
            value = dict(record=record, action="accept", actor="main", verdict=verdict(record, state))
            with self.subTest(state=state), tempfile.TemporaryDirectory() as temp:
                path = Path(temp)/"boundary.json"; path.write_text(json.dumps(value))
                before = path.read_bytes()
                ran = subprocess.run([sys.executable, "-B", str(PACKAGE/"runtime/boundary.py"),
                                      "--input", str(path)], capture_output=True, text=True, timeout=10)
                self.assertEqual(ran.returncode, 1, ran.stdout + ran.stderr)
                self.assertEqual(json.loads(ran.stdout)["reason"], "required_gates_unsatisfied")
                self.assertEqual(path.read_bytes(), before)

    def test_blank_or_control_evidence_cannot_support_acceptance(self):
        for bad in (" ", "\t", "\u00a0", "\x7f", "\x85", "\ud800"):
            record = boundary_record(); result = verdict(record)
            result["gates"]["unit"]["evidence"] = bad
            with self.subTest(value=repr(bad)), self.assertRaises(boundary.BoundaryError):
                boundary.check(record, "accept", "main", result)
        record = boundary_record(); result = verdict(record); result["artifact"] = "   "
        with self.assertRaises(boundary.BoundaryError):
            boundary.check(record, "accept", "main", result)

    def test_valid_unicode_reference_remains_accepted(self):
        record = boundary_record(); result = verdict(record)
        result["gates"]["unit"]["evidence"] = "артефакты/проверка-1"
        self.assertTrue(boundary.check(record, "accept", "main", result)["allowed"])

    def test_freshness_authority_and_holds_are_not_weakened(self):
        record = boundary_record(); result = verdict(record, "reused-pass")
        self.assertFalse(boundary.check(record, "accept", "main", result)["allowed"])
        result = verdict(record)
        self.assertFalse(boundary.check(record, "accept", "writer", result)["allowed"])
        record["hold"] = "released"
        self.assertFalse(boundary.check(record, "accept", "main", result)["allowed"])

    def test_invalid_states_and_truthy_freshness_are_rejected(self):
        for state in ("PASS", " skipped ", None, True, [], {}):
            with self.subTest(state=state), self.assertRaises(ValueError):
                evidence.normalize_status(state)
        for fresh in (1, 0, "false", None):
            with self.subTest(fresh=fresh), self.assertRaises(ValueError):
                evidence.satisfies_gate("executed-pass", fresh)

    def test_checks_do_not_mutate_input(self):
        record = boundary_record(); result = verdict(record, "STALE")
        before = copy.deepcopy((record, result))
        boundary.check(record, "accept", "main", result)
        self.assertEqual((record, result), before)


class ActionableBatchTests(unittest.TestCase):
    def mixed_record(self):
        value = preflight()
        value["questions"] = [dict(id=f"Q{i}", state="unanswered") for i in range(10)]
        value["questions"].append(dict(id="protected-choice", state="unknown"))
        return value

    def test_main_decision_is_visible_not_only_routed(self):
        value = self.mixed_record(); before = copy.deepcopy(value)
        result = challenge.check(value)
        self.assertEqual(result["next_action"], "decision-needed")
        self.assertEqual(result["reference"], "protected-choice")
        self.assertEqual(result["issues"][0]["route"], "main")
        self.assertEqual(result["issue_count"], 11)
        self.assertEqual(result["omitted_issues"], 3)
        self.assertEqual(len(result["issues"]), challenge.MAX_PREVIEW)
        self.assertEqual(value, before)
        self.assertEqual(challenge.check(value), result)

    def test_worker_only_batch_keeps_input_order_and_counts(self):
        value = self.mixed_record(); value["questions"].pop()
        result = challenge.check(value)
        self.assertEqual(result["reference"], "Q0")
        self.assertEqual(result["next_action"], "repair-or-refresh")
        self.assertEqual(result["omitted_issues"], 2)

    def test_manifest_drift_does_not_hide_existing_main_decision(self):
        value = self.mixed_record()
        identity = dict(matched=False, expected="before", observed="after", limitation="test double")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"record.json"; path.write_text(json.dumps(value))
            output = io.StringIO()
            # This test isolates aggregation. Real manifest integration remains tested below.
            with patch.object(challenge, "verify_manifest", return_value=identity), redirect_stdout(output):
                code = challenge.main(["--input", str(path), "--manifest", str(Path(temp)/"manifest")])
            result = json.loads(output.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(result["reference"], "protected-choice")
        self.assertEqual(result["issue_count"], 12)
        self.assertEqual(result["omitted_issues"], 4)
        self.assertIn("evidence-stale", [r["class"] for r in result["issues"]])

    def test_real_manifest_cli_preserves_main_issue_and_drift(self):
        if not (PACKAGE/"runtime/candidate.py").exists():
            if os.environ.get("CI"): self.fail("Real candidate helper required in CI")
            self.skipTest("Only scoped helpers available locally; full source exercised in CI")
        from runtime import candidate
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); (root/"src").mkdir(); (root/"src/input").write_text("before")
            manifest = candidate.snapshot(root, ["src"]); path = root/"manifest.json"
            candidate.write_manifest(manifest, path)
            value = self.mixed_record()
            value["current"] = dict(attempt="A1", contract="R1", candidate=manifest["fingerprint"], target="T1")
            value["evidence"][0].update(basis=dict(value["current"]), evidence="original/result")
            source = root/"record.json"; source.write_text(json.dumps(value))
            (root/"src/input").write_text("after")
            ran = subprocess.run([sys.executable, "-B", str(PACKAGE/"runtime/challenge.py"),
                                  "--input", str(source), "--manifest", str(path)],
                                 capture_output=True, text=True, timeout=10)
            self.assertEqual(ran.returncode, 1, ran.stderr)
            result = json.loads(ran.stdout)
            self.assertEqual(result["reference"], "protected-choice")
            self.assertFalse(result["local_identity"]["matched"])


class ReviewPolicyTests(unittest.TestCase):
    def test_rechecks_keep_full_baseline_and_mandatory_gates(self):
        guide = " ".join((PACKAGE/"verification.md").read_text().split())
        for phrase in ("complete actual diff", "Read every hunk of the correction delta",
                       "Missing review baseline", "changed contract", "new reviewer",
                       "mandated fresh gates always override", "Main directly inspects required design evidence"):
            self.assertIn(phrase, guide)
        self.assertLess(len(guide.split()), 700)
        cfg = tomllib.loads((PACKAGE/"agents/tester.toml").read_text())
        self.assertEqual((cfg["model"], cfg["model_reasoning_effort"]), ("gpt-6-luna", "high"))
        self.assertLess(len(cfg["developer_instructions"].split()), 200)


class HistoricalAndInstallationTests(unittest.TestCase):
    def archive(self, *args):
        ran = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
        if ran.returncode:
            if os.environ.get("CI"): self.fail("Exact 2.7 source required: " + ran.stderr.decode(errors="replace"))
            self.skipTest("Exact 2.7 Git history unavailable locally; required in CI")
        return ran.stdout

    def test_baseline_reproduces_fixed_errors(self):
        modules = {}
        for name in ("boundary", "challenge"):
            raw = self.archive("show", BASELINE + f":codex_workflow/runtime/{name}.py")
            scope = {"__name__": "old_" + name}
            exec(compile(raw, "old_" + name + ".py", "exec"), scope)
            modules[name] = scope
        old = modules["boundary"]; record = boundary_record()
        with self.assertRaises(old["BoundaryError"]):
            old["check"](record, "accept", "main", verdict(record, "stale"))
        result = verdict(record); result["gates"]["unit"]["evidence"] = "   "
        self.assertTrue(old["check"](record, "accept", "main", result)["allowed"])
        value = preflight(); value["questions"] = [dict(id=f"Q{i}", state="unanswered") for i in range(8)]
        value["questions"].append(dict(id="hidden", state="unknown"))
        result = modules["challenge"]["check"](value)
        self.assertEqual(result["next_action"], "decision-needed")
        self.assertTrue(all(item["route"] == "worker" for item in result["issues"]))

    def test_same_version_upgrade_exact_rollback_and_owner_protection(self):
        raw = self.archive("archive", BASELINE, "codex_workflow")
        from runtime import smart_install as install
        from runtime.smart_restore import prepare_restore
        from runtime.errors import ValidationError
        from test_v240 import snapshot
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); old = root/"old"; home = root/"home"; home.mkdir()
            with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
                for member in archive:
                    rel = Path(member.name)
                    self.assertFalse(rel.is_absolute()); self.assertNotIn("..", rel.parts)
                    self.assertEqual(rel.parts[0], "codex_workflow")
                    if member.isfile():
                        dst = old/rel; dst.parent.mkdir(parents=True, exist_ok=True)
                        dst.write_bytes(archive.extractfile(member).read()); dst.chmod(member.mode & 0o777)
                    else: self.assertTrue(member.isdir())
            package = old/"codex_workflow"
            (home/"config.toml").write_text('model="owner-main"\nmodel_reasoning_effort="high"\n'
                'approval_policy="on-request"\n[agents]\nmax_threads=1\ndefault_subagent_model="owner-child"\n')
            (home/"AGENTS.md").write_text("Protected owner instructions.\n")
            project = root/"project"; project.mkdir(); (project/"source").write_text("Protected project.")
            command = [sys.executable, "-B", str(package/"runtime/smart_install.py"),
                       "--package-root", str(package), "--codex-home", str(home)]
            ran = subprocess.run(command+["--apply"], capture_output=True, text=True)
            self.assertEqual(ran.returncode, 0, ran.stdout+ran.stderr)
            before, project_before = snapshot(home), snapshot(project)
            plan, prior = install.prepare(PACKAGE, home)
            self.assertEqual(snapshot(home), before)
            backup = install.apply_plan(plan, prior, home)
            self.assertTrue(install.status(home)["disk_ok"])
            self.assertEqual((home/"codex_workflow/operate/VERSION").read_text(), VERSION+"\n")
            helper = home/"codex_workflow/runtime/evidence.py"
            self.assertEqual(helper.read_bytes(), (PACKAGE/"runtime/evidence.py").read_bytes())
            a = tomllib.loads(before["config.toml"][0].decode()); b = tomllib.loads((home/"config.toml").read_text())
            a.pop("developer_instructions", None); b.pop("developer_instructions", None); self.assertEqual(a, b)
            for role in (package/"agents").glob("*.toml"):
                a = tomllib.loads(role.read_text()); b = tomllib.loads((home/"agents"/role.name).read_text())
                for key in ("model", "model_reasoning_effort", "sandbox_mode", "agents"):
                    self.assertEqual(a[key], b[key], (role.name, key))
            self.assertEqual(install.prepare(PACKAGE, home)[0].mutations, [])
            content = helper.read_bytes(); helper.write_bytes(content+b"# Local owner edit\n")
            self.assertFalse(install.status(home)["disk_ok"])
            with self.assertRaises(ValidationError): install.prepare(PACKAGE, home)
            helper.write_bytes(content)
            self.assertEqual(snapshot(project), project_before)
            restore, prior = prepare_restore(home, backup); install.apply_plan(restore, prior, home)
            self.assertEqual(snapshot(home), before); self.assertEqual(snapshot(project), project_before)
            self.assertFalse(helper.exists())
            ran = subprocess.run(command+["--check"], capture_output=True, text=True)
            self.assertEqual(ran.returncode, 0, ran.stdout+ran.stderr)


if __name__ == "__main__":
    unittest.main()
