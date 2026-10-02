import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "install-agents.sh"
AGENT_NAMES = sorted(p.stem for p in (ROOT / "agents").glob("n2i-*.md"))


def check_command():
    line = next(l for l in (ROOT / "SKILL.md").read_text().splitlines() if l.startswith("- Agents: !`"))
    return line[line.index("!`") + 2 : line.rindex("`")]


class InstallAgents(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        skills = self.home / ".claude" / "skills"
        skills.mkdir(parents=True)
        (skills / "n2i-dev-cycle").symlink_to(ROOT)
        self.dest = self.home / ".claude" / "agents"
        self.env = {**os.environ, "HOME": str(self.home)}

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self):
        return subprocess.run(["bash", str(SCRIPT)], env=self.env, capture_output=True, text=True, check=True)

    def agents_status(self):
        out = subprocess.run(["bash", "-c", check_command()], env=self.env, capture_output=True, text=True, check=True)
        return out.stdout.strip()

    def test_links_every_agent(self):
        self.run_script()
        for name in AGENT_NAMES:
            link = self.dest / f"{name}.md"
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.resolve(), (ROOT / "agents" / f"{name}.md").resolve())

    def test_rerun_is_safe(self):
        self.run_script()
        self.run_script()
        self.assertEqual(sorted(p.stem for p in self.dest.glob("n2i-*.md")), AGENT_NAMES)

    def test_removes_dangling_link(self):
        self.dest.mkdir(parents=True)
        (self.dest / "n2i-gone.md").symlink_to(self.home / "nowhere.md")
        out = self.run_script()
        self.assertFalse((self.dest / "n2i-gone.md").is_symlink())
        self.assertIn("n2i-gone.md", out.stdout)

    def test_leaves_unrelated_agents_alone(self):
        self.dest.mkdir(parents=True)
        other = self.dest / "my-agent.md"
        other.write_text("mine")
        self.run_script()
        self.assertEqual(other.read_text(), "mine")

    def test_check_reports_all_missing_before_install(self):
        status = self.agents_status()
        self.assertTrue(status.startswith("AGENTS=missing:"))
        for name in AGENT_NAMES:
            self.assertIn(name, status)

    def test_check_ok_after_install(self):
        self.run_script()
        self.assertEqual(self.agents_status(), "AGENTS=ok")

    def test_check_names_only_the_missing_agent(self):
        self.run_script()
        (self.dest / f"{AGENT_NAMES[0]}.md").unlink()
        status = self.agents_status()
        self.assertIn(AGENT_NAMES[0], status)
        for name in AGENT_NAMES[1:]:
            self.assertNotIn(name, status)

    def test_check_is_quiet_when_skill_not_under_home(self):
        (self.home / ".claude" / "skills" / "n2i-dev-cycle").unlink()
        self.assertEqual(self.agents_status(), "AGENTS=ok")

    def test_readme_points_at_script(self):
        self.assertIn("scripts/install-agents.sh", (ROOT / "README.md").read_text())


if __name__ == "__main__":
    unittest.main()
