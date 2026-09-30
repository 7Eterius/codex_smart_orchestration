"""Integration of 2.7's optional guide, routing and budget-preserving instructions."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "codex_workflow"
sys.path.insert(0, str(PACKAGE))
from runtime import challenge
from test_v270 import record


class HandoffIntegrationContracts(unittest.TestCase):
    def test_main_issue_beyond_worker_preview_is_visible_and_selects_main(self):
        value = record()
        value["questions"] = [dict(id=f"Q{i}", state="unanswered") for i in range(8)]
        value["questions"].append(dict(id="Q9", state="unknown"))
        result = challenge.check(value)
        self.assertEqual(len(result["issues"]), 8)
        self.assertEqual(result["issues"][0]["route"], "main")
        self.assertEqual(result["issues"][0]["reference"], "Q9")
        self.assertEqual(result["reference"], "Q9")
        self.assertEqual(result["issue_count"], 9)
        self.assertEqual(result["omitted_issues"], 1)
        self.assertEqual(result["next_action"], "decision-needed")

    def test_documented_example_is_ready_for_review_not_acceptance(self):
        guide = (PACKAGE / "challenge.md").read_text()
        example = json.loads(re.search(r"```json\n(.*?)\n```", guide, re.S).group(1))
        result = challenge.check(example)
        self.assertEqual(result["status"], "clear")
        self.assertEqual(result["pending_count"], 2)
        self.assertEqual(result["next_action"], "return-for-required-review")
        example["phase"] = "accept"
        self.assertEqual(challenge.check(example)["status"], "challenge")

    def test_pending_batch_reports_all_omitted_obligations(self):
        value = record()
        value["phase"] = "handoff"
        value["evidence"].extend(dict(gate=f"review-{i}", required=True, fresh_required=True,
                                      status="unrun", due="accept") for i in range(12))
        result = challenge.check(value)
        self.assertEqual(result["pending_count"], 12)
        self.assertEqual(result["omitted_pending"], 4)
        value["phase"] = "accept"
        self.assertEqual(challenge.check(value)["issue_count"], 12)

    def test_optional_guide_and_release_links_exist(self):
        for relative in ("README.md", "docs/smart_orchestration.md", "docs/v2.7.md"):
            source = ROOT / relative
            for target in re.findall(r"\]\(([^)]+)\)", source.read_text()):
                if not target.startswith(("https:", "http:", "#")):
                    self.assertTrue((source.parent / target.split("#", 1)[0]).is_file(), target)
        from runtime.layout import INSTALLED_RUNTIME_FILES
        self.assertIn("challenge.md", INSTALLED_RUNTIME_FILES)

    def test_required_gates_and_evidence_questions_remain_explicit(self):
        text = " ".join((PACKAGE / "verification.md").read_text().split())
        self.assertIn("Execute required independent gates even when no defect is suspected", text)
        self.assertIn("real entry point", text)
        self.assertIn("meaningful negative control", text)
        self.assertIn("Named unknown questions require Main's decision", text)
        self.assertIn("accepted UI/design criterion", text)
        execution = " ".join((PACKAGE / "execution.md").read_text().split())
        self.assertIn("Main may include named must-answer questions", execution)
        self.assertIn("A known authoritative path is a direct read", execution)
        self.assertIn("without blind resets", execution)


if __name__ == "__main__":
    unittest.main()
