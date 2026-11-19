import json
import tempfile
import unittest
from pathlib import Path

from brightloop.executor import apply_plan, preview_plan
from brightloop.schema import PlanError, parse_plan, slugify


class PlanValidationTests(unittest.TestCase):
    def test_parses_valid_plan(self):
        raw = json.dumps({
            "summary": "Prepare a revision note.",
            "actions": [{"type": "write_note", "title": "Revision Plan", "content": "Review algebra."}],
        })
        plan = parse_plan(raw)
        self.assertEqual(plan["actions"][0]["type"], "write_note")

    def test_accepts_json_code_fence(self):
        raw = '```json\n{"summary":"Log it","actions":[{"type":"append_log","content":"Finished task"}]}\n```'
        self.assertEqual(parse_plan(raw)["summary"], "Log it")

    def test_rejects_shell_or_unknown_actions(self):
        raw = json.dumps({"summary": "Run a command", "actions": [{"type": "run_shell", "command": "echo hi"}]})
        with self.assertRaises(PlanError):
            parse_plan(raw)

    def test_rejects_empty_or_oversized_plan(self):
        with self.assertRaises(PlanError):
            parse_plan('{"summary":"Nothing","actions":[]}')

    def test_slug_is_a_safe_filename(self):
        self.assertEqual(slugify("../../My Notes!!"), "my-notes.md")


class ApplyPlanTests(unittest.TestCase):
    def test_apply_creates_note_and_log(self):
        plan = {
            "summary": "Save a note and log progress.",
            "actions": [
                {"type": "write_note", "title": "Study Plan", "content": "- Maths\n- Physics"},
                {"type": "append_log", "content": "Created a study plan."},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            changed = apply_plan(plan, workspace)
            self.assertEqual(len(changed), 2)
            self.assertTrue((workspace / "notes" / "study-plan.md").exists())
            self.assertIn("Created a study plan.", (workspace / "daily-log.md").read_text())

    def test_existing_note_is_not_overwritten(self):
        plan = {
            "summary": "Create a note.",
            "actions": [{"type": "write_note", "title": "Existing", "content": "New text"}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            notes = workspace / "notes"
            notes.mkdir(parents=True)
            target = notes / "existing.md"
            target.write_text("Keep this", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                apply_plan(plan, workspace)
            self.assertEqual(target.read_text(encoding="utf-8"), "Keep this")

    def test_preview_does_not_apply_changes(self):
        plan = {
            "summary": "Create a note.",
            "actions": [{"type": "write_note", "title": "Preview", "content": "Hello"}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            text = preview_plan(plan)
            self.assertIn("preview.md", text)
            self.assertFalse(workspace.exists())

    def test_refuses_symlinked_notes_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            outside = root / "outside"
            workspace.mkdir()
            outside.mkdir()
            try:
                (workspace / "notes").symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Directory symlinks are not supported on this platform")

            plan = {
                "summary": "Create a note.",
                "actions": [{"type": "write_note", "title": "Private", "content": "Hello"}],
            }
            with self.assertRaisesRegex(ValueError, "symlinked notes directory"):
                apply_plan(plan, workspace)
            self.assertEqual(list(outside.iterdir()), [])

    def test_refuses_symlinked_daily_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            outside_file = root / "outside.md"
            outside_file.write_text("Do not change", encoding="utf-8")
            try:
                (workspace / "daily-log.md").symlink_to(outside_file)
            except (OSError, NotImplementedError):
                self.skipTest("File symlinks are not supported on this platform")

            plan = {
                "summary": "Append a log entry.",
                "actions": [{"type": "append_log", "content": "Hello"}],
            }
            with self.assertRaisesRegex(ValueError, "symlinked log file"):
                apply_plan(plan, workspace)
            self.assertEqual(outside_file.read_text(encoding="utf-8"), "Do not change")

    def test_rejects_duplicate_note_names_before_writing(self):
        plan = {
            "summary": "Create two notes.",
            "actions": [
                {"type": "write_note", "title": "Study Plan", "content": "First"},
                {"type": "write_note", "title": "Study-Plan", "content": "Second"},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            with self.assertRaisesRegex(FileExistsError, "duplicate note title"):
                apply_plan(plan, workspace)
            self.assertFalse(workspace.exists())


if __name__ == "__main__":
    unittest.main()
