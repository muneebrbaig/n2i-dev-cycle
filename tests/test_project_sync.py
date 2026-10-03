import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "project-sync.sh"
SKILL = ".claude/skills/n2i-dev-cycle"
GIT_IDENTITY = ["-c", "user.email=t@t", "-c", "user.name=t"]


def git(cwd, *args, **kw):
    return subprocess.run(["git", *GIT_IDENTITY, *args], cwd=cwd, capture_output=True, text=True, check=True, **kw)


class ProjectSync(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.env = {
            **os.environ,
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "protocol.file.allow",
            "GIT_CONFIG_VALUE_0": "always",
        }
        self.upstream = base / "skill"
        (self.upstream / "agents").mkdir(parents=True)
        (self.upstream / "agents" / "n2i-one.md").write_text("one")
        git(self.upstream, "init", "-q", "-b", "main")
        git(self.upstream, "add", "-A")
        git(self.upstream, "commit", "-qm", "v1")

        seed = base / "seed"
        seed.mkdir()
        git(seed, "init", "-q", "-b", "main")
        git(seed, "submodule", "add", "-q", "-b", "main", str(self.upstream), SKILL, env=self.env)
        git(seed, "add", "-A")
        git(seed, "commit", "-qm", "seed")
        self.project = base / "project"
        git(base, "clone", "-q", str(seed), str(self.project))

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self):
        env = {**self.env, "CLAUDE_PROJECT_DIR": str(self.project)}
        return subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True)

    def push_upstream(self, name):
        (self.upstream / "agents" / f"{name}.md").write_text(name)
        git(self.upstream, "add", "-A")
        git(self.upstream, "commit", "-qm", name)

    def head(self):
        return git(self.project / SKILL, "rev-parse", "HEAD").stdout.strip()

    def agents(self):
        return self.project / ".claude" / "agents"

    def test_fresh_clone_initializes_and_links_agents(self):
        self.assertFalse((self.project / SKILL / "agents").exists())
        result = self.run_script()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        link = self.agents() / "n2i-one.md"
        self.assertTrue(link.is_symlink())
        self.assertEqual(link.read_text(), "one")
        self.assertFalse(os.path.isabs(os.readlink(link)))

    def test_pulls_remote_tip_and_stamps(self):
        self.run_script()
        stamp = self.project / ".git" / "n2i-skill-synced"
        stamp.unlink()
        self.push_upstream("n2i-two")
        self.run_script()
        self.assertEqual(self.head(), git(self.upstream, "rev-parse", "HEAD").stdout.strip())
        self.assertTrue(stamp.exists())
        self.assertTrue((self.agents() / "n2i-two.md").is_symlink())

    def test_recent_stamp_skips_remote_pull(self):
        self.run_script()
        pinned = self.head()
        self.push_upstream("n2i-two")
        self.run_script()
        self.assertEqual(self.head(), pinned)

    def test_stale_stamp_pulls_again(self):
        self.run_script()
        stamp = self.project / ".git" / "n2i-skill-synced"
        old = time.time() - 8 * 86400
        os.utime(stamp, (old, old))
        self.push_upstream("n2i-two")
        self.run_script()
        self.assertEqual(self.head(), git(self.upstream, "rev-parse", "HEAD").stdout.strip())

    def test_prunes_dangling_links(self):
        self.run_script()
        gone = self.agents() / "n2i-gone.md"
        gone.symlink_to("../skills/n2i-dev-cycle/agents/n2i-gone.md")
        self.run_script()
        self.assertFalse(gone.is_symlink())
        self.assertTrue((self.agents() / "n2i-one.md").is_symlink())

    def test_leaves_foreign_agent_files_alone(self):
        self.agents().mkdir(parents=True)
        mine = self.agents() / "mine.md"
        mine.write_text("mine")
        self.run_script()
        self.assertEqual(mine.read_text(), "mine")

    def test_unreachable_remote_is_silent_and_not_stamped(self):
        self.run_script()
        (self.project / ".git" / "n2i-skill-synced").unlink()
        git(self.project / SKILL, "remote", "set-url", "origin", str(self.upstream) + "-missing")
        pinned = self.head()
        result = self.run_script()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(self.head(), pinned)
        self.assertFalse((self.project / ".git" / "n2i-skill-synced").exists())

    def test_exits_zero_outside_a_repo(self):
        with tempfile.TemporaryDirectory() as d:
            env = {k: v for k, v in self.env.items() if k != "CLAUDE_PROJECT_DIR"}
            result = subprocess.run(["bash", str(SCRIPT)], cwd=d, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)


class ProjectInstallDocs(unittest.TestCase):
    def test_doc_references_template_and_hook(self):
        text = (ROOT / "PROJECT-INSTALL.md").read_text()
        self.assertIn("scripts/project-sync.sh", text)
        self.assertIn("SessionStart", text)

    def test_prompt_does_not_pull_on_feature_branches(self):
        text = (ROOT / "PROJECT-INSTALL.md").read_text()
        self.assertIn("git branch --show-current", text)
        self.assertIn("do NOT pull", text)

    def test_prompt_treats_failed_unpushed_check_as_unsaved_work(self):
        text = (ROOT / "PROJECT-INSTALL.md").read_text()
        self.assertIn("the git log command fails", text)

    def test_prompt_accepts_plus_in_submodule_status(self):
        text = (ROOT / "PROJECT-INSTALL.md").read_text()
        self.assertIn("leading space or +", text)

    def test_readme_points_at_doc(self):
        self.assertIn("PROJECT-INSTALL.md", (ROOT / "README.md").read_text())

    def test_template_is_executable(self):
        self.assertTrue(os.access(SCRIPT, os.X_OK))


if __name__ == "__main__":
    unittest.main()
