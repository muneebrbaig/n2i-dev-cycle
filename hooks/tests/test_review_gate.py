"""Tests for hooks/review-gate.py. Run: python3 -m unittest discover hooks/tests"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "review-gate.py"
TEMPLATE = Path(__file__).resolve().parents[2] / "references" / "prepush-prompt.md"
FULL_PROMPT = "Review the diff.\n" + TEMPLATE.read_text().split("## Standing checks", 1)[1]


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

    def review(self, prompt=FULL_PROMPT):
        return tool("Agent", subagent_type="n2i-prepush-reviewer", prompt=prompt)

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
            self.review(),
        )
        self.assertIsNone(self.run_hook(events))

    def test_a_review_before_a_later_edit_does_not_count(self):
        events = self.turn(
            self.review(),
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

    def test_a_review_without_the_standing_checks_does_not_count(self):
        events = self.turn(tool("Edit", file_path=self.repo_file), self.review("Review the diff against main."))
        out = self.run_hook(events)
        self.assertEqual(out["decision"], "block")
        self.assertIn("The last review prompt lacked: User-visible strings against the repo glossary", out["reason"])

    def test_a_prompt_missing_one_standing_check_does_not_count(self):
        prompt = FULL_PROMPT.replace("Paths that differ only in case", "")
        out = self.run_hook(self.turn(tool("Edit", file_path=self.repo_file), self.review(prompt)))
        self.assertEqual(out["decision"], "block")
        self.assertIn("lacked: Paths that differ only in case", out["reason"])

    def test_the_repo_checklist_headings_are_required_when_configured(self):
        root = Path(self.tmp.name) / "repo"
        (root / "checklist.md").write_text("# C\n### One encoding for off\nrule\n### Claims are measured\nrule\n")
        (root / ".n2i-dev-cycle" / "config").write_text('BRANCH_PREFIX=mb/\nREVIEW_CHECKLIST="checklist.md"\n')
        out = self.run_hook(self.turn(tool("Edit", file_path=self.repo_file), self.review()))
        self.assertIn("lacked: One encoding for off; Claims are measured", out["reason"])
        with_list = FULL_PROMPT + "\n### One encoding for off\n### Claims are measured\n"
        self.assertIsNone(self.run_hook(self.turn(tool("Edit", file_path=self.repo_file), self.review(with_list))))

    def test_a_missing_checklist_file_keeps_the_gate_shut(self):
        root = Path(self.tmp.name) / "repo"
        (root / ".n2i-dev-cycle" / "config").write_text("REVIEW_CHECKLIST=gone.md\n")
        out = self.run_hook(self.turn(tool("Edit", file_path=self.repo_file), self.review()))
        self.assertIn("REVIEW_CHECKLIST file not found", out["reason"])

    def test_only_edits_since_the_last_review_are_listed(self):
        root = Path(self.tmp.name) / "repo"
        events = self.turn(
            tool("Edit", file_path=self.repo_file),
            self.review(),
            tool("Edit", file_path=str(root / "docs" / "spec.md")),
        )
        reason = self.run_hook(events)["reason"]
        self.assertIn("this turn: docs/spec.md.", reason)
        self.assertNotIn("a.py", reason)

    def test_the_reason_sizes_the_skip_on_the_delta_and_allows_docs_only(self):
        reason = self.run_hook(self.turn(tool("Edit", file_path=self.repo_file)))["reason"]
        self.assertIn("not the whole branch", reason)
        self.assertIn("'docs-only'", reason)
        self.assertIn("adds or alters no number or claim", reason)

    def test_a_skip_line_before_the_edit_does_not_count(self):
        events = self.turn(
            tool("Bash", command="echo 'Phase 5: review skipped (docs-only, typo)' >> .n2i-dev-cycle/progress.md"),
            tool("Edit", file_path=self.repo_file),
        )
        self.assertEqual(self.run_hook(events)["decision"], "block")

    def codex(self, prompt_text, name="codex-prompt-1.md"):
        prompt = Path(self.tmp.name) / name
        prompt.write_text(prompt_text)
        return tool("Bash", command=f"codex exec -s read-only --skip-git-repo-check -o /x/out.md - < {prompt}")

    def enable_codex(self, value="plan+review"):
        (Path(self.tmp.name) / "repo" / ".n2i-dev-cycle" / "config").write_text(f'CODEX="{value}"\n')

    def test_a_codex_run_with_the_full_prompt_counts_where_codex_is_on(self):
        for value in ("review", "plan+review"):
            with self.subTest(value=value):
                self.enable_codex(value)
                events = self.turn(tool("Edit", file_path=self.repo_file), self.codex(FULL_PROMPT))
                self.assertIsNone(self.run_hook(events))

    def test_a_codex_run_does_not_count_where_codex_is_off(self):
        events = self.turn(tool("Edit", file_path=self.repo_file), self.codex(FULL_PROMPT))
        self.assertEqual(self.run_hook(events)["decision"], "block")
        self.enable_codex("off")
        self.assertEqual(self.run_hook(events)["decision"], "block")

    def test_a_codex_prompt_without_the_standing_checks_does_not_count(self):
        self.enable_codex()
        out = self.run_hook(self.turn(tool("Edit", file_path=self.repo_file), self.codex("Review the diff.")))
        self.assertEqual(out["decision"], "block")
        self.assertIn("The last review prompt lacked: User-visible strings", out["reason"])

    def test_a_codex_run_whose_prompt_file_is_gone_does_not_count(self):
        self.enable_codex()
        events = self.turn(
            tool("Edit", file_path=self.repo_file),
            tool("Bash", command="codex exec -s read-only - < /nonexistent/prompt.md"),
        )
        self.assertEqual(self.run_hook(events)["decision"], "block")

    def test_the_reason_names_codex_as_a_way_through(self):
        self.assertIn("codex exec where the repo sets CODEX", self.run_hook(self.turn(tool("Edit", file_path=self.repo_file)))["reason"])


if __name__ == "__main__":
    unittest.main()
