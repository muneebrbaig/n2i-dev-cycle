"""Tests for hooks/verify-gate.py. Run: python3 -m unittest discover hooks/tests"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "verify-gate.py"


def user(text):
    return {"type": "user", "message": {"content": text}}


def tool_result():
    return {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}}


def assistant_text(text):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


def bash(command):
    return {
        "type": "assistant",
        "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {"command": command}}]},
    }


class VerifyGateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.transcript = Path(self.tmp.name) / "transcript.jsonl"

    def run_hook(self, events, **payload):
        self.transcript.write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
        payload.setdefault("transcript_path", str(self.transcript))
        proc = subprocess.run(
            [sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True, text=True
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout) if proc.stdout.strip() else None

    def assertBlocked(self, out):
        self.assertIsNotNone(out)
        self.assertEqual(out["decision"], "block")

    def test_claim_without_run_blocks(self):
        out = self.run_hook([user("/n2i-dev-cycle 42"), assistant_text("All tests pass.")])
        self.assertBlocked(out)

    def test_claim_with_run_this_turn_passes(self):
        out = self.run_hook([
            user("/n2i-dev-cycle 42"),
            bash('dotnet test "App.sln" -v minimal'),
            tool_result(),
            assistant_text("All tests pass."),
        ])
        self.assertIsNone(out)

    def test_run_before_last_user_message_does_not_count(self):
        out = self.run_hook([
            user("/n2i-dev-cycle 42"),
            bash("npm test -- --watch=false"),
            tool_result(),
            user("rename that variable"),
            assistant_text("Done, build succeeded."),
        ])
        self.assertBlocked(out)

    def test_non_build_command_is_not_evidence(self):
        out = self.run_hook([
            user("/n2i-dev-cycle 42"),
            bash("git status"),
            tool_result(),
            assistant_text("Everything is green."),
        ])
        self.assertBlocked(out)

    def test_no_claim_passes(self):
        out = self.run_hook([user("/n2i-dev-cycle 42"), assistant_text("Plan is ready for review.")])
        self.assertIsNone(out)

    def test_ignored_outside_skill_sessions(self):
        out = self.run_hook([user("fix the typo"), assistant_text("All tests pass.")])
        self.assertIsNone(out)

    def test_stop_hook_active_passes(self):
        out = self.run_hook(
            [user("/n2i-dev-cycle 42"), assistant_text("All tests pass.")], stop_hook_active=True
        )
        self.assertIsNone(out)

    def test_missing_transcript_passes(self):
        out = self.run_hook([], transcript_path=str(Path(self.tmp.name) / "missing.jsonl"))
        self.assertIsNone(out)


if __name__ == "__main__":
    unittest.main()
