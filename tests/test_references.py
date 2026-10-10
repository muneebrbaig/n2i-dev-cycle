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


class DoubtReview(unittest.TestCase):
    def test_doubt_is_architectural_only_and_opt_in(self):
        planning = read("references/planning.md")
        self.assertIn("architectural class only", planning)
        self.assertIn("only if the user says yes", planning)
        text = read("references/doubt.md")
        self.assertIn("Architectural class", text)
        self.assertIn("only if the user says yes", text)

    def test_doubter_never_receives_the_claim(self):
        text = read("references/doubt.md")
        self.assertIn("artifact and the contract only", text)
        self.assertIn("never", read("references/execution.md").split("Doubt review")[1].split("\n")[0])

    def test_doubter_agent_has_no_approval_answer_and_needs_a_contract(self):
        text = read("agents/n2i-doubter.md")
        self.assertIn('Never answer "looks good"', text)
        self.assertIn("contract is missing, stop", text)

    def test_doubt_stops_after_three_cycles(self):
        self.assertIn("three cycles", read("references/doubt.md"))


class ReviewGuardrails(unittest.TestCase):
    def test_reviewer_uses_all_five_severity_labels(self):
        text = read("agents/n2i-prepush-reviewer.md")
        for label in ("Critical", "Required", "Nit", "Optional", "FYI"):
            with self.subTest(label=label):
                self.assertIn(f"`{label}`", text)

    def test_build_loop_acts_on_severity_and_size(self):
        pre_push = read("references/build-loop.md").split("### Pre-push review")[1].split("\n## ")[0]
        self.assertIn("`Critical` and `Required` before Phase 6", pre_push)
        self.assertIn("400 changed lines", pre_push)

    def test_plan_estimates_size_and_rollback(self):
        text = read("references/planning.md")
        self.assertIn("Changed lines (rough)", text)
        self.assertIn("rollback path", text)
        self.assertIn("400", text)

    def test_handover_has_compatibility_and_docs_section(self):
        text = read("references/build-loop.md")
        section = text.split("### Compatibility & Docs")[1].split("\n### ")[0]
        for needle in ("rollback", "backward-compatible", "current state"):
            with self.subTest(needle=needle):
                self.assertIn(needle, section)


class ReadmeCoverage(unittest.TestCase):
    def test_readme_describes_the_new_behaviour(self):
        text = read("README.md")
        for needle in ("diff-review.md", "doubt.md", "silenced checks", "Mutation spot-check",
                       "n2i-diff-scanner", "n2i-doubter", "`Critical`", "400 changed lines",
                       "noticed", "rollback"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)


class Evals(unittest.TestCase):
    def test_routing_scenario_has_trigger_and_non_trigger_prompts(self):
        text = read("evals/scenarios.md").split("**S12 — routing**")[1].split("\n**S13")[0]
        trigger, no_trigger = text.split("No trigger")
        self.assertGreaterEqual(trigger.count("\n- `"), 4)
        self.assertGreaterEqual(no_trigger.count("\n- `"), 4)

    def test_skill_description_covers_the_trigger_prompts(self):
        head = read("SKILL.md").split("---")[1]
        for phrase in ("ticket", "feature or bug prompt", "spec document", "fix:", "brainstorm"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, head)


if __name__ == "__main__":
    unittest.main()
