import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS = sorted((ROOT / "agents").glob("n2i-*.md"))
MODELS = {"haiku", "sonnet", "opus"}
READ_ONLY = {"n2i-prepush-reviewer", "n2i-ci-triage", "n2i-e2e-runner", "n2i-unit-runner"}
WRITE_TOOLS = {"Edit", "Write", "NotebookEdit"}


def frontmatter(path):
    m = re.match(r"---\n(.*?)\n---\n", path.read_text(), re.S)
    assert m, f"{path.name}: no frontmatter"
    return dict(line.split(": ", 1) for line in m.group(1).splitlines())


class AgentFiles(unittest.TestCase):
    def test_expected_agents_exist(self):
        self.assertEqual({p.stem for p in AGENTS}, READ_ONLY)

    def test_frontmatter_valid(self):
        for p in AGENTS:
            fm = frontmatter(p)
            with self.subTest(agent=p.stem):
                self.assertEqual(fm["name"], p.stem)
                self.assertIn(fm["model"], MODELS)
                self.assertTrue(fm["description"].strip())
                self.assertTrue(fm["tools"].strip())

    def test_no_agent_can_edit_files(self):
        for p in AGENTS:
            tools = {t.strip() for t in frontmatter(p)["tools"].split(",")}
            with self.subTest(agent=p.stem):
                self.assertFalse(tools & WRITE_TOOLS)

    def test_agents_are_referenced_in_docs(self):
        docs = {
            "execution": (ROOT / "references/execution.md").read_text(),
            "readme": (ROOT / "README.md").read_text(),
        }
        for p in AGENTS:
            for name, text in docs.items():
                with self.subTest(agent=p.stem, doc=name):
                    self.assertIn(p.stem, text)

    def test_every_agent_token_in_docs_is_a_real_agent(self):
        names = {p.stem for p in AGENTS}
        docs = [ROOT / "SKILL.md", ROOT / "SKILL.qwen.md", ROOT / "README.md", *(ROOT / "references").glob("*.md")]
        for doc in docs:
            for tok in re.findall(r"(?<![.\w-])n2i-[a-z0-9-]+", doc.read_text()):
                if tok.startswith("n2i-dev-cycle"):
                    continue
                with self.subTest(doc=doc.name, token=tok):
                    self.assertIn(tok, names)

    def test_model_named_next_to_agent_matches_frontmatter(self):
        models = {p.stem: frontmatter(p)["model"] for p in AGENTS}
        docs = [ROOT / "SKILL.md", ROOT / "SKILL.qwen.md", ROOT / "README.md", *(ROOT / "references").glob("*.md")]
        for doc in docs:
            text = doc.read_text()
            for m in re.finditer(r"(?<![.\w-])(n2i-[a-z0-9-]+)", text):
                if m.group(1) not in models:
                    continue
                near = re.search(r"\b(haiku|sonnet|opus)\b", text[m.end():m.end() + 60])
                if near:
                    with self.subTest(doc=doc.name, agent=m.group(1)):
                        self.assertEqual(near.group(1), models[m.group(1)])

    def test_contents_lists_match_headings(self):
        for doc in [ROOT / "SKILL.md", ROOT / "SKILL.qwen.md", *(ROOT / "references").glob("*.md")]:
            lines = doc.read_text().split("\n")
            if "## Contents" not in lines:
                continue
            start = lines.index("## Contents") + 1
            listed, i = [], start
            while i < len(lines) and not lines[i].startswith(("---", "## ")):
                if lines[i].lstrip().startswith("- "):
                    listed.append(lines[i].strip()[2:])
                i += 1
            fence, heads = False, []
            for l in lines[i:]:
                if l.startswith("```"):
                    fence = not fence
                if not fence and re.match(r"#{2,3} ", l):
                    heads.append(l.lstrip("#").strip())
            with self.subTest(doc=doc.name):
                self.assertTrue(listed)
                for item in listed:
                    self.assertIn(item, heads)

    def test_execution_model_table_matches_frontmatter(self):
        text = (ROOT / "references/execution.md").read_text()
        for p in AGENTS:
            m = re.search(rf"\| `{p.stem}` \| `(\w+)` \|", text)
            with self.subTest(agent=p.stem):
                self.assertTrue(m, "missing row in named-agents table")
                self.assertEqual(m.group(1), frontmatter(p)["model"])


if __name__ == "__main__":
    unittest.main()
