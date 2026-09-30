"""2.7 executable regressions, CLI boundaries and exact archived 2.6 migration.

No paid model runs. These tests do not establish agent compliance or allowance savings.
"""
from __future__ import annotations

import copy
import importlib.util
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
from runtime import challenge

BASELINE = "ce7c841c8d32fbc357f941ba008d30b24deae44e"


def record(bound=False):
    value = {"schema": 1, "unit": "U1", "owned_paths": ["src/card"],
             "changes": [{"path": "src/card/view.ts", "origin": "owner"}],
             "deliverables": [{"path": "src/card/view.ts", "required": True, "state": "satisfied"}],
             "findings": [], "decisions": [],
             "evidence": [{"gate": "unit", "required": True, "fresh_required": True, "status": "executed-pass"}]}
    if bound:
        value["current"] = dict(attempt="A1", contract="R1", candidate="C1", target="preview/1")
        for key in ("deliverables", "evidence"):
            for item in value[key]:
                item.update(evidence="artifact/original", basis=dict(value["current"]))
    return value


class PreflightRegressionTests(unittest.TestCase):
    def test_legacy_record_remains_usable_but_identity_not_claimed(self):
        result = challenge.check(record())
        self.assertEqual(result["status"], "clear")
        self.assertFalse(result["identity_checked"])
        self.assertEqual(result["phase"], "accept")
        self.assertIn("Omitted obligations", result["limitation"])

    def test_entire_record_validated_after_early_issue(self):
        value = record()
        value["changes"][0]["path"] = "outside.ts"
        value["evidence"] = [{"gate": "unit"}]
        with self.assertRaises(challenge.ChallengeError):
            challenge.check(value)

    def test_schema_must_be_exact_integer(self):
        for schema in (True, False, 1.0, "1", None, [], {}):
            with self.subTest(schema=schema), self.assertRaises(challenge.ChallengeError):
                challenge.check({**record(), "schema": schema})

    def test_ambiguous_paths_are_rejected(self):
        for path in ("src/card/..", "src/../escape", "../escape", ".", "./src/card",
                     "src//card", "src/card/", "/tmp/file", "C:/file", "C:\\file",
                     "src/.git/config", " src/card", "src/card\x7f", "src/card\ud800"):
            with self.subTest(path=path):
                value = record()
                value["changes"][0]["path"] = path
                with self.assertRaises(challenge.ChallengeError):
                    challenge.check(value)

    def test_prefix_does_not_grant_adjacent_scope(self):
        value = record()
        value["changes"][0]["path"] = "src/cards/view.ts"
        result = challenge.check(value)
        self.assertEqual(result["class"], "scope-breach")
        self.assertEqual(result["next_action"], "decision-needed")

    def test_duplicate_rows_fail_even_after_known_failure(self):
        for key in ("changes", "deliverables", "evidence"):
            value = record()
            value[key].append(copy.deepcopy(value[key][0]))
            with self.subTest(key=key), self.assertRaises(challenge.ChallengeError):
                challenge.check(value)

    def test_optional_rows_are_validated_not_ignored(self):
        value = record()
        value["evidence"].append(dict(gate="later", required=False, fresh_required=False, status="made-up"))
        with self.assertRaises(challenge.ChallengeError):
            challenge.check(value)

    def test_empty_obligations_cannot_be_clear(self):
        value = record()
        value["deliverables"] = []
        value["evidence"] = []
        self.assertEqual(challenge.check(value)["class"], "obligations-unverified")

    def test_bound_evidence_checks_every_identity_dimension(self):
        for field in challenge.IDENTITY:
            value = record(True)
            value["evidence"][0]["basis"][field] = "different"
            with self.subTest(field=field):
                self.assertEqual(challenge.check(value)["class"], "evidence-stale")

    def test_bound_missing_reference_or_basis_is_unverified(self):
        for field in ("basis", "evidence"):
            value = record(True)
            del value["evidence"][0][field]
            self.assertEqual(challenge.check(value)["class"], "evidence-unverified")

    def test_handback_can_precede_independent_review(self):
        value = record(True)
        value["phase"] = "handoff"
        value["evidence"].append(dict(gate="review", required=True, fresh_required=True,
                                       status="unrun", due="accept"))
        value["findings"] = [dict(id="F1", blocking=True, state="addressed",
                                   evidence="repair/result", basis=dict(value["current"]))]
        result = challenge.check(value)
        self.assertEqual(result["status"], "clear")
        self.assertEqual(result["pending_count"], 2)
        self.assertEqual(result["next_action"], "return-for-required-review")
        self.assertEqual(value["findings"][0]["state"], "addressed")
        value["phase"] = "accept"
        result = challenge.check(value)
        self.assertEqual(result["status"], "challenge")
        self.assertEqual({x["class"] for x in result["issues"]}, {"blocking-finding", "gate-unrun"})

    def test_addressed_requires_evidence_at_handback(self):
        value = record()
        value["phase"] = "handoff"
        value["findings"] = [dict(id="F1", blocking=True, state="addressed")]
        self.assertEqual(challenge.check(value)["class"], "evidence-unverified")

    def test_new_candidate_reopens_addressed_finding(self):
        value = record(True)
        value["phase"] = "handoff"
        basis = {**value["current"], "candidate": "old"}
        value["findings"] = [dict(id="F1", blocking=True, state="addressed", evidence="old", basis=basis)]
        self.assertEqual(challenge.check(value)["class"], "evidence-stale")

    def test_accept_requires_all_stages_and_current_resolution(self):
        value = record(True)
        value["phase"] = "accept"
        value["evidence"][0]["due"] = "accept"
        value["findings"] = [dict(id="F1", blocking=True, state="resolved",
                                   evidence="review/1", basis=dict(value["current"]))]
        self.assertEqual(challenge.check(value)["status"], "clear")
        value["findings"][0]["basis"]["attempt"] = "old"
        self.assertEqual(challenge.check(value)["class"], "evidence-stale")

    def test_stage_cannot_be_invented_to_skip_gate(self):
        value = record()
        value["evidence"][0]["due"] = "release"
        with self.assertRaises(challenge.ChallengeError):
            challenge.check(value)
        value["evidence"][0]["due"] = "accept"
        with self.assertRaises(challenge.ChallengeError):
            challenge.check(value)

    def test_required_failures_never_pass_acceptance(self):
        for status in ("failed", "blocked", "unrun", "deferred", "not-applicable", "STALE", "UNVERIFIED"):
            value = record(True)
            value["evidence"][0]["status"] = status
            with self.subTest(status=status):
                self.assertEqual(challenge.check(value)["status"], "challenge")

    def test_freshness_is_not_satisfied_by_reuse(self):
        value = record(True)
        value["evidence"][0]["status"] = "reused-pass"
        self.assertEqual(challenge.check(value)["class"], "fresh-evidence-required")
        value["evidence"][0]["fresh_required"] = False
        self.assertEqual(challenge.check(value)["status"], "clear")

    def test_legitimate_unchanged_deliverable_does_not_force_fake_edit(self):
        value = record(True)
        value["deliverables"][0].update(state="unchanged", allow_unchanged=True)
        self.assertEqual(challenge.check(value)["status"], "clear")
        del value["deliverables"][0]["evidence"]
        self.assertEqual(challenge.check(value)["class"], "evidence-unverified")

    def test_named_questions_require_answers_and_evidence(self):
        value = record(True)
        value["questions"] = [dict(id="Q1", state="unanswered")]
        self.assertEqual(challenge.check(value)["class"], "question-unanswered")
        value["questions"][0] = dict(id="Q1", state="answered", answer="This is the preview")
        self.assertEqual(challenge.check(value)["class"], "evidence-unverified")
        value["questions"][0].update(evidence="target/readback", basis=dict(value["current"]))
        self.assertEqual(challenge.check(value)["status"], "clear")

    def test_unknown_question_routes_to_main_not_guessing(self):
        value = record()
        value["questions"] = [dict(id="Q1", state="unknown")]
        result = challenge.check(value)
        self.assertEqual(result["next_action"], "decision-needed")
        self.assertEqual(result["class"], "decision-needed")

    def test_batched_issues_are_bounded_not_dropped_silently(self):
        value = record()
        value["findings"] = [dict(id=f"F{i}", blocking=True, state="open") for i in range(12)]
        result = challenge.check(value)
        self.assertEqual(result["issue_count"], 12)
        self.assertEqual(len(result["issues"]), 8)
        self.assertEqual(result["omitted_issues"], 4)
        self.assertEqual(result["next_action"], "repair-or-refresh")

    def test_hidden_main_issue_still_routes_to_main(self):
        value = record()
        value["changes"] = [dict(path=f"src/card/{i}", origin="unknown") for i in range(10)]
        result = challenge.check(value)
        self.assertEqual(result["next_action"], "decision-needed")
        self.assertEqual(result["omitted_issues"], 2)

    def test_valid_unrelated_change_keeps_bound_evidence_current(self):
        value = record(True)
        value["changes"].append(dict(path="docs/other.md", origin="concurrent"))
        self.assertEqual(challenge.check(value)["status"], "clear")
        value["changes"][-1]["origin"] = "unknown"
        self.assertEqual(challenge.check(value)["class"], "attribution-unknown")

    def test_inputs_unchanged_and_results_deterministic(self):
        value = record(True)
        before = copy.deepcopy(value)
        first = challenge.check(value)
        self.assertEqual(first, challenge.check(value))
        self.assertEqual(value, before)


class CliTests(unittest.TestCase):
    def run_cli(self, content, *extra):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "in.json"
            path.write_text(content, encoding="utf-8")
            before = path.read_bytes()
            ran = subprocess.run([sys.executable, "-B", str(PACKAGE / "runtime/challenge.py"),
                                  "--input", str(path), *extra], capture_output=True, text=True, timeout=15)
            self.assertEqual(path.read_bytes(), before)
            return ran

    def test_real_cli_pass_and_failure(self):
        value = record()
        ran = self.run_cli(json.dumps(value))
        self.assertEqual(ran.returncode, 0, ran.stderr)
        self.assertEqual(json.loads(ran.stdout)["status"], "clear")
        value["evidence"][0]["status"] = "failed"
        ran = self.run_cli(json.dumps(value))
        self.assertEqual(ran.returncode, 1, ran.stderr)
        self.assertEqual(json.loads(ran.stdout)["class"], "gate-failed")

    def test_duplicate_nonfinite_nested_and_oversized_json(self):
        for value in ('{"schema":1,"schema":1}', '{"schema":NaN}',
                      '[' * 1100 + '0' + ']' * 1100, ' ' * 65537, '{'):
            ran = self.run_cli(value)
            self.assertEqual(ran.returncode, 2, ran.stdout)
            self.assertEqual(json.loads(ran.stderr)["status"], "error")

    def test_missing_file_is_error(self):
        with tempfile.TemporaryDirectory() as temp:
            ran = subprocess.run([sys.executable, "-B", str(PACKAGE / "runtime/challenge.py"),
                                  "--input", str(Path(temp)/"missing")], capture_output=True, text=True)
            self.assertEqual(ran.returncode, 2)
            self.assertEqual(json.loads(ran.stderr)["status"], "error")

    def test_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"data"; path.write_text(json.dumps(record()))
            link = Path(temp)/"link"; link.symlink_to(path)
            with self.assertRaises(challenge.ChallengeError):
                challenge.read_record(link)


class ManifestIntegrationTests(unittest.TestCase):
    def setUp(self):
        if not (PACKAGE / "runtime/candidate.py").exists():
            if os.environ.get("CI"):
                self.fail("Installed candidate helper is required")
            self.skipTest("Full source fixture unavailable locally; required in CI")
        from runtime import candidate
        self.candidate = candidate
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root/"src").mkdir(); (self.root/"src/value.txt").write_text("one")
        self.manifest = self.candidate.snapshot(self.root, ["src"])
        self.path = self.root/"manifest.json"
        self.candidate.write_manifest(self.manifest, self.path)
        self.value = record(True)
        self.value["current"]["candidate"] = self.manifest["fingerprint"]
        for key in ("deliverables", "evidence"):
            for row in self.value[key]: row["basis"] = dict(self.value["current"])

    def test_fresh_identity_then_real_source_drift(self):
        self.assertTrue(challenge.verify_manifest(self.value, self.path)["matched"])
        (self.root/"src/value.txt").write_text("two")
        self.assertFalse(challenge.verify_manifest(self.value, self.path)["matched"])

    def test_unrelated_path_does_not_invalidate_identity(self):
        (self.root/"notes.txt").write_text("not an input")
        self.assertTrue(challenge.verify_manifest(self.value, self.path)["matched"])

    def test_manifest_must_match_declared_candidate(self):
        self.value["current"]["candidate"] = "not-that-manifest"
        with self.assertRaises(challenge.ChallengeError):
            challenge.verify_manifest(self.value, self.path)

    def test_real_cli_detects_drift_preserves_records(self):
        source = self.root/"input.json"; source.write_text(json.dumps(self.value))
        before = self.path.read_bytes()
        (self.root/"src/value.txt").write_text("two")
        ran = subprocess.run([sys.executable, "-B", str(PACKAGE/"runtime/challenge.py"),
                              "--input", str(source), "--manifest", str(self.path)], capture_output=True, text=True)
        self.assertEqual(ran.returncode, 1, ran.stderr)
        result = json.loads(ran.stdout)
        self.assertEqual(result["class"], "evidence-stale")
        self.assertFalse(result["local_identity"]["matched"])
        self.assertEqual(self.path.read_bytes(), before)


class ArchivedRegressions(unittest.TestCase):
    def test_actual_26_had_false_clear_inputs_fixed_in_27(self):
        ran = subprocess.run(["git", "show", BASELINE+":codex_workflow/runtime/challenge.py"], cwd=ROOT, capture_output=True)
        if ran.returncode:
            if os.environ.get("CI"): self.fail("Exact baseline unavailable")
            self.skipTest("Exact baseline unavailable locally; required in CI")
        scope = {"__name__": "baseline_challenge"}
        exec(compile(ran.stdout, "baseline_challenge.py", "exec"), scope)
        for change in ("boolean-schema", "trailing-parent", "empty-obligations"):
            value = record()
            if change == "boolean-schema": value["schema"] = True
            elif change == "trailing-parent": value["changes"][0]["path"] = "src/card/.."
            else: value["evidence"] = []; value["deliverables"] = []
            self.assertEqual(scope["check"](value)["status"], "clear", change)
            if change == "empty-obligations":
                self.assertEqual(challenge.check(value)["status"], "challenge")
            else:
                with self.assertRaises(challenge.ChallengeError): challenge.check(value)


class PackageAndMigrationTests(unittest.TestCase):
    def test_exact_26_upgrade_reapply_integrity_and_rollback(self):
        ran = subprocess.run(["git", "archive", BASELINE, "codex_workflow"], cwd=ROOT, capture_output=True)
        if ran.returncode:
            if os.environ.get("CI"): self.fail("Exact 2.6 source required")
            self.skipTest("Exact 2.6 unavailable locally; required in CI")
        from runtime import smart_install as install
        from runtime.smart_restore import prepare_restore
        from runtime.errors import ValidationError
        from test_v240 import snapshot
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); old = root/"old"; home = root/"home"; home.mkdir()
            with tarfile.open(fileobj=io.BytesIO(ran.stdout)) as archive:
                for member in archive:
                    path = Path(member.name)
                    self.assertFalse(path.is_absolute()); self.assertNotIn("..", path.parts)
                    self.assertEqual(path.parts[0], "codex_workflow")
                    if member.isfile():
                        dest = old/path; dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(archive.extractfile(member).read()); dest.chmod(member.mode & 0o777)
                    else: self.assertTrue(member.isdir())
            package = old/"codex_workflow"
            self.assertEqual((package/"operate/VERSION").read_text(), "2.6.0\n")
            (home/"config.toml").write_text('model="owner-main"\nmodel_reasoning_effort="high"\n'
                'approval_policy="on-request"\n[agents]\nmax_threads=1\ndefault_subagent_model="owner-child"\n')
            (home/"AGENTS.md").write_text("Owner instructions.\n")
            project = root/"project"; project.mkdir(); (project/"data").write_text("untouched")
            command = [sys.executable, "-B", str(package/"runtime/smart_install.py"),
                       "--package-root", str(package), "--codex-home", str(home)]
            applied = subprocess.run(command+["--apply"], capture_output=True, text=True)
            self.assertEqual(applied.returncode, 0, applied.stdout+applied.stderr)
            before, project_before = snapshot(home), snapshot(project)
            plan, prior = install.prepare(PACKAGE, home)
            self.assertEqual(snapshot(home), before, "Preview must not mutate")
            backup = install.apply_plan(plan, prior, home)
            self.assertTrue(install.status(home)["disk_ok"])
            self.assertEqual(install.status(home)["version"], "2.7.0")
            self.assertEqual((home/"codex_workflow/challenge.md").read_bytes(), (PACKAGE/"challenge.md").read_bytes())
            a = tomllib.loads(before["config.toml"][0].decode()); b = tomllib.loads((home/"config.toml").read_text())
            a.pop("developer_instructions", None); b.pop("developer_instructions", None)
            self.assertEqual(a, b)
            for role in (package/"agents").glob("*.toml"):
                a = tomllib.loads(role.read_text()); b = tomllib.loads((home/"agents"/role.name).read_text())
                for key in ("model", "model_reasoning_effort", "sandbox_mode", "agents"):
                    self.assertEqual(a[key], b[key], (role.name, key))
            self.assertEqual(install.prepare(PACKAGE, home)[0].mutations, [])
            guide = home/"codex_workflow/challenge.md"; content = guide.read_bytes()
            guide.write_bytes(content+b"Owner edit.\n")
            self.assertFalse(install.status(home)["disk_ok"])
            with self.assertRaises(ValidationError): install.prepare(PACKAGE, home)
            guide.write_bytes(content)
            self.assertEqual(snapshot(project), project_before)
            restore, prior = prepare_restore(home, backup); install.apply_plan(restore, prior, home)
            self.assertEqual(snapshot(home), before); self.assertEqual(snapshot(project), project_before)
            self.assertFalse(guide.exists())
            checked = subprocess.run(command+["--check"], capture_output=True, text=True)
            self.assertEqual(checked.returncode, 0, checked.stdout+checked.stderr)


if __name__ == "__main__":
    unittest.main()
