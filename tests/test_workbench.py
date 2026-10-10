from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from workbench.core import (
    add_task,
    format_draft,
    generate_ideas,
    record_reward,
    set_checklist_item,
    write_snapshot,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DraftTests(unittest.TestCase):
    def test_draft_uses_local_template(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "data" / "draft_templates.json").write_text(
                (PROJECT_ROOT / "data" / "draft_templates.json").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            result = format_draft(
                root, "Plain-language service", "service_listing", "local shops"
            )
            body = result.read_text(encoding="utf-8")
        self.assertIn("Plain-language service", body)
        self.assertIn("local shops", body)
        self.assertIn("Template-generated starting point", body)

    def test_idea_generation_returns_five_templates(self) -> None:
        ideas = generate_ideas("editing", "nonprofits")
        self.assertEqual(len(ideas), 5)
        self.assertTrue(all("nonprofits" in idea for idea in ideas))


class RewardTrackerTests(unittest.TestCase):
    def make_root(self, directory: str) -> Path:
        root = Path(directory)
        (root / "data").mkdir()
        (root / "data" / "reward_tasks.json").write_text("[]", encoding="utf-8")
        return root

    def test_add_requires_explicit_permission_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_root(directory)
            with self.assertRaisesRegex(ValueError, "must confirm"):
                add_task(
                    root,
                    "Allowed task",
                    "Example",
                    "https://example.org/terms",
                    "Terms section says permitted",
                    False,
                )

    def test_rewards_require_confirmed_receipt_and_are_user_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_root(directory)
            task = add_task(
                root,
                "Allowed task",
                "Example",
                "https://example.org/terms",
                "Terms section says permitted",
                True,
            )
            with self.assertRaisesRegex(ValueError, "mark reward_received"):
                record_reward(root, task["id"], "0.0001", "BTC", "Payment receipt")

            set_checklist_item(root, task["id"], "reward_received", True)
            record_reward(root, task["id"], "0.0001", "BTC", "Payment receipt")
            stored = json.loads((root / "data" / "reward_tasks.json").read_text())
            receipt = stored[0]["reward_receipt"]
            self.assertEqual(receipt["amount"], "0.0001")
            self.assertTrue(receipt["reported_by_user"])

            tracker, report = write_snapshot(root)
            self.assertTrue(tracker.exists())
            self.assertIn("not independently verified", report.read_text(encoding="utf-8"))

    def test_rejects_non_https_terms_url(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_root(directory)
            with self.assertRaisesRegex(ValueError, "HTTPS"):
                add_task(
                    root,
                    "Allowed task",
                    "Example",
                    "http://example.org/terms",
                    "Terms section says permitted",
                    True,
                )


if __name__ == "__main__":
    unittest.main()
