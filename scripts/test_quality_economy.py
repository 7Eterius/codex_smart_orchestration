"""Native policy/release contracts; no model calls or network access."""
from __future__ import annotations
import hashlib
import io
from pathlib import Path
import sys
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "codex_workflow"
sys.path.insert(0, str(PACKAGE))
from runtime import release
from runtime.errors import ValidationError


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class NativePolicyTests(unittest.TestCase):
    def setUp(self):
        self.agents = text("codex_workflow/AGENTS.md")
        self.heavy = text("codex_workflow/heavy_route.md")
        self.medium = text("codex_workflow/medium_route.md")
        self.closure = text("codex_workflow/archivist.md")

    def test_heavy_default_and_explicit_alternatives(self):
        self.assertIn("**Heavy is the default route.**", self.agents)
        self.assertIn("No route-selection phrase is required", self.agents)
        self.assertIn("explicit Light or Medium request", self.agents)
        self.assertIn("A new session defaults to Heavy", self.agents)
        self.assertNotIn("Use Light when none is selected", self.agents)

    def test_leaf_fast_path_is_not_for_deployment_subtasks(self):
        self.assertIn("worker-free direct fast path within Heavy", self.agents)
        self.assertIn("do\nnot initialize Companion", self.agents)
        self.assertIn("A small\nsubtask inside a substantive deployment", self.agents)
        self.assertIn("no workers, deployment intake", self.heavy)

    def test_native_policy_not_opt_in_resource(self):
        self.assertNotIn("profiles/quality-economy", self.agents + self.heavy)
        self.assertIn("native 7Eterius/codex_workflow", self.agents)
        self.assertIn("project-local instructions", self.agents)

    def test_owner_scope_and_checkpoint_are_preserved(self):
        for phrase in ("decision and acceptance contract", "repeat candidate competitions",
                       "financial semantics and navigation", "candidate/production isolation"):
            self.assertIn(phrase, self.agents)
        self.assertIn("Stop at the owner's checkpoint", self.heavy)

    def test_all_agent_work_is_in_objective(self):
        self.assertIn("total model-weighted work", self.heavy)
        self.assertIn("not just main turns", self.heavy)
        self.assertNotIn("Aggregate subagent token use is not an optimization target", self.heavy)
        self.assertIn("Speed is secondary", self.agents)

    def test_no_savings_or_quality_guarantees(self):
        self.assertIn("Do not promise savings or equal quality", self.agents)
        self.assertIn("account allowance are different measures", self.agents)

    def test_worker_capability_and_escalation_kept(self):
        self.assertIn("Do not lower worker capability", self.agents)
        self.assertIn("Security, migration, concurrency, financial and cross-cutting risks", self.heavy)
        self.assertIn("not a hard worker-count or retry budget", self.heavy)

    def test_one_writer_and_independent_tester(self):
        self.assertIn("one production writer at a time", self.heavy)
        self.assertIn("one independent Tester", self.heavy)
        self.assertIn("Executor self-checks do not replace", self.heavy)
        self.assertIn("early independent test design", self.heavy)

    def test_main_does_not_duplicate_production(self):
        self.assertIn("main must not write production code or tests", self.heavy)
        self.assertIn("Worker unavailability does not authorize", self.heavy)
        self.assertIn("same Tester for recheck", self.heavy)
        self.assertIn("Create and coordinate every worker directly", self.heavy)

    def test_core_and_named_documents_still_required(self):
        for name in ("project_overview.md", "project_core_tech.md", "project_structure.md",
                     "project_progress.md", "project_diary.md", "latest_session_work.md"):
            self.assertIn(name, self.agents)
        self.assertIn("main directly reads the six core documents", self.agents)
        self.assertIn("owner-named decision/acceptance documents", self.agents)
        self.assertIn("one persistent Companion", self.agents)

    def test_module_intake_expands_on_uncertainty(self):
        self.assertIn("inventory module documentation", self.agents)
        self.assertIn("Unknown dependency impact requires broader reading", self.agents)
        self.assertIn("Unread supporting modules are not assumed irrelevant or safe", self.agents)
        self.assertIn("Missing required documents block", self.agents)

    def test_context_and_retries_are_bounded_not_blind(self):
        self.assertIn("Follow-ups repeat the ID and changed capsule parts", self.heavy)
        self.assertIn("After repeated focused failure, reconsider", self.heavy)
        self.assertIn("Do not poll workers", self.heavy)
        self.assertIn("blocker, not blind retries", self.heavy)

    def test_capsule_fields_and_deployment_boundary_preserved(self):
        for phrase in ("**Task ID**", "**Project Context Scope**", "**Evidence Question + Goal**",
                       "**Implementation Context + Ownership**", "**Verification Context**",
                       "**Documentation Context + Audience**", "codex-workflow-deployment-start"):
            self.assertIn(phrase, self.heavy)
        self.assertIn('fork_turns="none"', self.heavy)

    def test_evidence_reuse_requires_known_freshness(self):
        for phrase in ("Unknown freshness requires a", "Do not describe reused evidence as newly executed",
                       "HEAD alone is insufficient", "owner changes and untracked inputs",
                       "invalidate relevant candidate evidence"):
            self.assertIn(phrase, self.heavy)

    def test_no_weakening_of_independent_assertions(self):
        self.assertIn("Never weaken assertions, hide failures", self.heavy)
        self.assertIn("do not blindly\nrepeat unaffected suites or prohibit a necessary broad rerun", self.heavy)

    def test_visual_acceptance_is_direct_and_real(self):
        for phrase in ("main must inspect the final requested screenshots itself",
                       "running-product frame", "one operator for shared simulator/browser",
                       "Changed UI requires fresh affected", "Builds and tests do not prove visual quality",
                       "Never substitute generated mockups", "image count, resolution and direct-chat delivery"):
            self.assertIn(phrase, self.heavy)

    def test_velocity_mode_is_explicit_and_scoped(self):
        self.assertIn("Design Velocity Mode applies only when\nexplicitly enabled for the current task", self.agents)
        self.assertIn("deferred gates OPEN", self.agents)
        self.assertIn("Other tasks retain their full applicable acceptance gates", self.heavy)

    def test_owner_data_and_git_authority_unchanged(self):
        self.assertIn("Preserve owner work and live data", self.agents)
        for word in ("stage", "commit", "push", "merge", "reset", "stash", "clean", "discard"):
            self.assertIn(word, self.agents)
        self.assertIn("explicit authority for the current task", self.agents)
        self.assertIn("candidate-preference boundaries", self.agents)

    def test_closing_archivist_has_no_automatic_history_fork(self):
        self.assertIn('fork_turns="none"', self.closure)
        self.assertNotIn('fork_turns="200"', self.closure)
        self.assertIn("specific missing evidence", self.closure)
        self.assertIn("only one reporting owner", self.closure)

    def test_closing_ownership_and_accounting_retained(self):
        for name in ("project_progress.md", "project_diary.md", "latest_session_work.md"):
            self.assertIn(name, self.closure)
        self.assertIn("outside Archivist's write scope", self.closure)
        self.assertIn("exact six-column", self.closure)
        self.assertIn("Cached input is a subset of Input", self.closure)
        self.assertIn("session records", self.closure)

    def test_explicit_medium_retains_direct_implementation(self):
        self.assertIn("Use only after the owner explicitly selects Medium", self.medium)
        self.assertIn("Medium does not\ndelegate production or verification", self.medium)
        self.assertIn("Deferred gates stay OPEN", self.medium)

    def test_version_and_marker_identity(self):
        version = text("codex_workflow/operate/VERSION").strip()
        self.assertGreater(release.parse_semver(version), release.parse_semver("1.1.17"))
        user = text("codex_workflow/operate/user_AGENTS.md")
        self.assertIn(f"<!-- codex-workflow-version: {version} -->", user)
        self.assertIn("codex-workflow-user-id: viettran-edgeAI/codex_workflow", user)
        self.assertIn("codex-workflow-id: viettran-edgeAI/codex_workflow", self.agents)
        for pair in ("managed", "project-personalization", "project-local-instructions"):
            self.assertEqual(self.agents.count(f"<!-- codex-workflow-{pair}-start -->"), 1)
            self.assertEqual(self.agents.count(f"<!-- codex-workflow-{pair}-end -->"), 1)

    def test_policies_remain_bounded(self):
        for policy, limit in ((self.agents, 145), (self.heavy, 200), (self.medium, 100), (self.closure, 60)):
            self.assertLess(len(policy.splitlines()), limit)


class WorkerIntegrityTests(unittest.TestCase):
    def test_original_worker_capabilities_and_contracts_unchanged(self):
        import tomllib
        expected = {
            "archivist": "0c9f4b7d7fc3e7ed3e19632896ca617bc2a07007",
            "companion": "724918d8d6c64dac3f04f894a7ab1284e9b80aee",
            "default_executor": "6330f8ac606bdf4d85be680f0a1ca0e714e8f39f",
            "investigator": "b7889555e25fd0e3679ef71f99bcb01f2ad667a3",
            "senior_executor": "34d6860e7fe59f6365fe520c038ca0766b99912e",
            "tester": "ae9c4fdf23c5bf1aac9314d1b6154c399acb768b",
        }
        self.assertEqual({p.stem for p in (PACKAGE / "agents").glob("*.toml")}, set(expected))
        for name, sha in expected.items():
            with self.subTest(worker=name):
                raw = (PACKAGE / "agents" / f"{name}.toml").read_bytes()
                self.assertEqual(hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest(), sha)
                config = tomllib.loads(raw.decode())
                self.assertTrue(config["developer_instructions"])
                self.assertEqual(config["model"], "gpt-5.6-sol" if name == "senior_executor" else "gpt-5.6-luna")
                expected_effort = "medium" if name == "senior_executor" else "max" if name == "default_executor" else "xhigh"
                self.assertEqual(config["model_reasoning_effort"], expected_effort)

    def test_token_report_skill_contract_unchanged(self):
        raw = (PACKAGE / "skills/deployment-token-report/SKILL.md").read_bytes()
        self.assertEqual(hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest(),
                         "361e08925991b89a95ab85c1004af61ee0eae63f")


class ForkReleaseTests(unittest.TestCase):
    def test_discovery_uses_only_fork(self):
        with mock.patch.object(release, "_read_json_url", return_value=[]) as reader:
            with self.assertRaises(ValidationError):
                release.select_releases()
        reader.assert_called_once_with("https://api.github.com/repos/7Eterius/codex_workflow/releases?per_page=100", 30)

    def test_unusable_release_never_falls_back(self):
        with mock.patch.object(release, "_read_json_url", return_value=[{"tag_name":"v1.2.0", "assets":[]}]) as reader:
            with self.assertRaisesRegex(ValidationError, "no release"):
                release.select_latest()
        self.assertEqual(reader.call_count, 1)

    def test_checksums_required_and_release_ordering_retained(self):
        records = []
        for version in ("1.2.0", "1.2.1-rc.1", "1.2.1"):
            base = f"https://github.com/7Eterius/codex_workflow/releases/download/v{version}/"
            records.append({"tag_name":f"v{version}", "assets":[
                {"name":f"codex_workflow-{version}.zip", "browser_download_url":base+f"codex_workflow-{version}.zip"},
                {"name":"SHA256SUMS", "browser_download_url":base+"SHA256SUMS"}]})
        records.append({"tag_name":"v99.0.0", "assets":[]})
        with mock.patch.object(release, "_read_json_url", return_value=records):
            self.assertEqual([r.version_text for r in release.select_releases()], ["1.2.1", "1.2.1-rc.1", "1.2.0"])

    def test_bad_checksum_is_rejected(self):
        selection = release.ReleaseSelection("1.2.0", release.parse_semver("1.2.0"), "codex_workflow-1.2.0.zip", "zip", "sums")
        with mock.patch.object(release, "_read_url", side_effect=[b"wrong", b"0"*64+b"  codex_workflow-1.2.0.zip\n"]):
            with self.assertRaisesRegex(ValidationError, "checksum mismatch"):
                release.acquire(selection)

    def test_unsafe_archive_paths_rejected(self):
        for name in ("../x", "/absolute", "codex_workflow/../../x", "other/x"):
            with self.subTest(name=name), self.assertRaises(ValidationError):
                release._validate_member(zipfile.ZipInfo(name))

    def test_symlinks_rejected(self):
        item = zipfile.ZipInfo("codex_workflow/link")
        item.external_attr = 0o120777 << 16
        with self.assertRaises(ValidationError):
            release._validate_member(item)


if __name__ == "__main__":
    unittest.main()
