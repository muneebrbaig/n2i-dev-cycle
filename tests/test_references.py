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

    def test_unit_runner_fallback_is_one_path(self):
        text = read("references/build-loop.md")
        final_run = " ".join(text.split("**Final run via")[1].split("**Keep the runner")[0].split())
        self.assertIn("dispatch `general-purpose` with `model: haiku`", final_run)
        self.assertNotIn("run the commands yourself", final_run)

    def test_fixes_rerun_validation_and_diff_checks_not_the_review(self):
        pre_push = read("references/build-loop.md").split("### Pre-push review")[1].split("\n## ")[0]
        pre_push = " ".join(pre_push.split())
        self.assertIn("re-run the `diff-review.md` checks on the fixes", pre_push)
        self.assertIn("re-dispatch the reviewer only when", pre_push)

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


class TestsThatCanGoRed(unittest.TestCase):
    def test_tdd_gives_a_red_step_when_the_test_is_the_deliverable(self):
        text = read("references/tdd.md")
        section = text.split("## Tests for Behavior That Already Exists")[1].split("\n## ")[0]
        for needle in ("500", "restore", "ledger"):
            with self.subTest(needle=needle):
                self.assertIn(needle, section)
        verify_red = text.split("**Verify RED**")[1].split("\n\n")[0]
        self.assertIn("Tests for Behavior That Already Exists", verify_red)

    def test_tdd_lists_e2e_patterns_that_cannot_go_red(self):
        section = read("references/tdd.md").split("## Tests That Can't Go Red")[1].split("\n## ")[0]
        for needle in ("client-side route change", "layout", "`.first()`"):
            with self.subTest(needle=needle):
                self.assertIn(needle, section)

    def test_reviewer_agent_knows_the_e2e_patterns(self):
        text = read("agents/n2i-prepush-reviewer.md")
        self.assertIn("client-side route change", text)
        self.assertIn("`.first()`", text)

    def test_test_heavy_diffs_always_get_the_review(self):
        pre_push = read("references/build-loop.md").split("### Pre-push review")[1].split("\n## ")[0]
        self.assertIn("mostly tests", pre_push)
        self.assertIn("mostly tests", read("SKILL.qwen.md").split("### Pre-push review")[1])

    def test_review_runs_in_the_fresh_context_opus_agent(self):
        pre_push = read("references/build-loop.md").split("### Pre-push review")[1].split("\n## ")[0]
        self.assertIn('"Run n2i-prepush-reviewer on this diff before pushing?"', pre_push)
        self.assertIn("never invoke a review skill in your own context", pre_push)
        self.assertNotIn("fallback when the agent isn't installed", pre_push)
        self.assertNotIn("If accepted and available", pre_push)
        self.assertNotIn("engineering:code-review", read("references/diff-review.md"))
        for rel in ("references/execution.md", "agents/n2i-prepush-reviewer.md", "README.md"):
            with self.subTest(ref=rel):
                self.assertNotIn("when `engineering:code-review` is unavailable", read(rel))
                self.assertNotIn("when engineering:code-review is not available", read(rel))

    def test_reviewer_agent_chains_review_skills_then_its_checklist(self):
        text = " ".join(read("agents/n2i-prepush-reviewer.md").split("---", 2)[2].split())
        first, second = text.index("`engineering:code-review`"), text.index("`code-review`")
        self.assertLess(first, second)
        self.assertIn("Never pass `--fix`, `--comment` or `ultra`", text)
        self.assertIn("`code-review high --max-findings default`", text)
        self.assertIn("Don't stop to ask what to review", text)
        self.assertIn("whichever skill ran", text)
        self.assertIn("which review skill ran", text)

    def test_a_fix_for_a_test_that_cannot_go_red_is_proven(self):
        pre_push = read("references/build-loop.md").split("### Pre-push review")[1].split("\n## ")[0]
        self.assertIn("go red on the failure", pre_push)

    def test_e2e_assertions_are_chosen_from_each_page_source(self):
        text = read("references/frontend-standards.md")
        section = text.split("## Browser Checks")[1].split("\n## ")[0]
        self.assertIn("loading, empty and error", section)


class SpecConformance(unittest.TestCase):
    def test_alignment_gate_checks_decisions_against_spec_rules(self):
        text = read("references/brainstorming.md")
        self.assertIn("general rule", text)
        self.assertIn("second way", text)

    def test_plan_self_review_checks_decisions_and_the_default_path(self):
        section = read("references/planning.md").split("## Plan Self-Review")[1]
        self.assertIn("general rule", section)
        self.assertIn("default path", section)

    def test_duplicated_rules_are_scanned_and_listed(self):
        text = read("references/diff-review.md")
        self.assertIn("## Duplicated Rules", text)
        self.assertIn("every reader", text)
        self.assertIn("DUPLICATE:", read("agents/n2i-diff-scanner.md"))

    def test_reviewer_checks_the_spec_and_the_sibling_diff(self):
        text = read("agents/n2i-prepush-reviewer.md")
        for needle in ("clause by clause", "sibling", "claims to check", "boundary",
                       "default path", "every reader"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)
        pre_push = read("references/build-loop.md").split("### Pre-push review")[1].split("\n## ")[0]
        self.assertIn("sibling", pre_push)
        self.assertIn("spec", pre_push)

    def test_tests_map_to_acceptance_criteria_and_boundaries(self):
        cycle = read("references/tdd.md").split("## The Cycle")[1].split("\n## ")[0]
        self.assertIn("acceptance criterion", cycle)
        self.assertIn("boundary", cycle)

    def test_pr_follows_repo_rules_and_is_reread(self):
        step = read("references/finishing.md").split("## Step 3")[1].split("\n## ")[0]
        self.assertIn("AGENTS.md", step)
        self.assertIn("re-read", step)
        self.assertIn("left unfixed", step)


class ReadmeCoverage(unittest.TestCase):
    def test_readme_describes_the_new_behaviour(self):
        text = read("README.md")
        for needle in ("diff-review.md", "doubt.md", "silenced checks", "Mutation spot-check",
                       "n2i-diff-scanner", "n2i-doubter", "`Critical`", "400 changed lines",
                       "noticed", "rollback", "mostly tests"):
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
