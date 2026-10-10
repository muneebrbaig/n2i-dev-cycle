import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / "references"
DOCS = [ROOT / "SKILL.md", ROOT / "README.md", *REFS.glob("*.md")]


def read(rel):
    return (ROOT / rel).read_text()


class ReferenceFiles(unittest.TestCase):
    def test_every_reference_mentioned_in_docs_exists(self):
        for doc in DOCS:
            for name in re.findall(r"references/([a-z-]+\.md)", doc.read_text()):
                with self.subTest(doc=doc.name, ref=name):
                    self.assertTrue((REFS / name).exists())

    def test_every_reference_is_listed_in_skill_and_readme(self):
        for ref in REFS.glob("*.md"):
            for doc in ("SKILL.md", "README.md"):
                with self.subTest(ref=ref.name, doc=doc):
                    self.assertIn(f"references/{ref.name}", read(doc))


class DiffReview(unittest.TestCase):
    def setUp(self):
        self.text = read("references/diff-review.md")

    def test_silenced_check_markers_listed(self):
        for marker in ("[Ignore]", "@ts-ignore", "eslint-disable", "#pragma warning disable",
                       "SuppressMessage", "NotImplementedException"):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.text)

    def test_mutation_check_restores_the_tree(self):
        section = self.text.split("## Mutation Spot-Check")[1].split("\n## ")[0]
        self.assertIn("Restore", section)
        self.assertIn("git diff", section)
        self.assertIn("read-only", section)

    def test_dead_code_asks_before_deleting_preexisting(self):
        section = self.text.split("## Dead Code")[1].split("\n## ")[0]
        self.assertIn("ask before deleting", section)


class Wiring(unittest.TestCase):
    def test_build_loop_loads_diff_review_in_phase_5(self):
        text = read("references/build-loop.md")
        pre_push = text.split("### Pre-push review")[1].split("\n## ")[0]
        self.assertIn("references/diff-review.md", pre_push)

    def test_build_loop_records_noticed_items_and_hands_them_over(self):
        text = read("references/build-loop.md")
        self.assertIn("Noticed but not touching", text)
        known = text.split("### Known Limitations")[1].split("\n### ")[0]
        self.assertIn("Phase 4: noticed", known)

    def test_tdd_and_verification_point_at_diff_review(self):
        for rel in ("references/tdd.md", "references/verification.md"):
            with self.subTest(ref=rel):
                self.assertIn("diff-review.md", read(rel))

    def test_scan_is_delegated_and_mutation_stays_in_main_agent(self):
        for rel in ("references/diff-review.md", "references/build-loop.md"):
            with self.subTest(ref=rel):
                self.assertIn("n2i-diff-scanner", read(rel))
        execution = read("references/execution.md")
        keep = execution.split("**Keep in the main agent**")[1]
        self.assertIn("mutation spot-check", keep)

    def test_scanner_agent_covers_the_same_markers_as_the_reference(self):
        text = read("agents/n2i-diff-scanner.md")
        for marker in ("[Ignore]", "@ts-ignore", "eslint-disable", "#pragma warning disable",
                       "SuppressMessage", "NotImplementedException", "empty `catch`"):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_reviewer_agent_covers_silenced_checks_and_dead_code(self):
        text = read("agents/n2i-prepush-reviewer.md")
        self.assertIn("silenced checks", text)
        self.assertIn("dead code", text)


if __name__ == "__main__":
    unittest.main()
