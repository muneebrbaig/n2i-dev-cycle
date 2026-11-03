"""Tests for hooks/review-gate.py. Run: python3 -m unittest discover hooks/tests"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "review-gate.py"


def user(text):
    return {"type": "user", "message": {"content": text}}


def tool(name, **inp):
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": name, "input": inp}]}}


def result():
    return {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}}


class ReviewGateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        (root / "repo" / ".n2i-dev-cycle").mkdir(parents=True)
        (root / "repo" / ".n2i-dev-cycle" / "progress.md").write_text("# t\n")
        (root / "plain").mkdir()
        self.repo_file = str(root / "repo" / "a.py")
        self.plain_file = str(root / "plain" / "a.py")

    def run_hook(self, events, active=False):
        transcript = Path(self.tmp.name) / "t.jsonl"
        transcript.write_text("\n".join(json.dumps(e) for e in events))
        out = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps({"transcript_path": str(transcript), "stop_hook_active": active}),
            capture_output=True, text=True, check=True,
        ).stdout
        return json.loads(out) if out.strip() else None

    def turn(self, *steps):
        events = [user("/n2i-dev-cycle fix it")]
        for step in steps:
            events += [step, result()]
        return events

    def test_blocks_an_edit_with_no_review(self):
        self.assertEqual(self.run_hook(self.turn(tool("Edit", file_path=self.repo_file)))["decision"], "block")

    def test_a_review_after_the_last_edit_passes(self):
        events = self.turn(
            tool("Edit", file_path=self.repo_file),
            tool("Agent", subagent_type="n2i-prepush-reviewer"),
        )
        self.assertIsNone(self.run_hook(events))

    def test_a_review_before_a_later_edit_does_not_count(self):
        events = self.turn(
            tool("Agent", subagent_type="n2i-prepush-reviewer"),
            tool("Write", file_path=self.repo_file),
        )
        self.assertEqual(self.run_hook(events)["decision"], "block")

    def test_a_written_skip_line_passes(self):
        events = self.turn(
            tool("Edit", file_path=self.repo_file),
            tool("Bash", command="echo 'Phase 5: review skipped (bounded, 20 lines)' >> .n2i-dev-cycle/progress.md"),
        )
        self.assertIsNone(self.run_hook(events))

    def test_edits_outside_a_ledger_repo_are_ignored(self):
        self.assertIsNone(self.run_hook(self.turn(tool("Edit", file_path=self.plain_file))))

    def test_a_turn_without_edits_is_ignored(self):
        self.assertIsNone(self.run_hook(self.turn(tool("Bash", command="ls"))))

    def test_stays_quiet_without_the_skill_in_the_transcript(self):
        events = [user("hi"), tool("Edit", file_path=self.repo_file), result()]
        self.assertIsNone(self.run_hook(events))

    def test_does_not_loop_once_the_hook_is_active(self):
        self.assertIsNone(self.run_hook(self.turn(tool("Edit", file_path=self.repo_file)), active=True))

    def test_only_edits_since_the_last_user_message_count(self):
        events = [user("/n2i-dev-cycle fix it"), tool("Edit", file_path=self.repo_file), result(), user("thanks, now explain")]
        self.assertIsNone(self.run_hook(events))


if __name__ == "__main__":
    unittest.main()
