"""Tests for hooks/pre-push-secret-scan.py. Run: python3 -m unittest discover hooks/tests

Fake secrets are assembled at runtime so this file never matches the scanner
itself and does not block pushes of this repo.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "pre-push-secret-scan.py"

AWS_KEY = "AKIA" + "Q7" * 8
GITHUB_TOKEN = "ghp" + "_" + "a1B2" * 9
SLACK_TOKEN = "xox" + "b-" + "1234567890-abcdef"
PRIVATE_KEY = "-----BEGIN " + "RSA PRIVATE KEY-----"
URL_PASSWORD = "https://deploy:" + "s3cretpw" + "@db.internal/app"
ASSIGNMENT = "api_key" + ' = "' + "q9W8e7R6t5Y4" + '"'

GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
}


class PrePushSecretScanTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.git("init", "-q")
        self.commit("README.md", "hello\n")
        # Stand in for a pushed main: everything after this ref is outgoing.
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")

    def git(self, *args):
        subprocess.run(
            ["git", "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args],
            cwd=self.repo, env=GIT_ENV, check=True, capture_output=True,
        )

    def commit(self, name, content):
        (self.repo / name).write_text(content, encoding="utf-8")
        self.git("add", name)
        self.git("commit", "-q", "-m", f"add {name}")

    def run_hook(self, command="git push", tool="Bash"):
        payload = {"tool_name": tool, "tool_input": {"command": command}}
        proc = subprocess.run(
            [sys.executable, str(HOOK)], input=json.dumps(payload),
            capture_output=True, text=True, cwd=self.repo,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout) if proc.stdout.strip() else None

    def assertDenied(self, out):
        self.assertIsNotNone(out)
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        return out["hookSpecificOutput"]["permissionDecisionReason"]

    def test_each_pattern_blocks_push(self):
        for label, secret in [
            ("AWS access key id", AWS_KEY),
            ("GitHub token", GITHUB_TOKEN),
            ("Slack token", SLACK_TOKEN),
            ("private key block", PRIVATE_KEY),
            ("password in URL", URL_PASSWORD),
            ("generic secret assignment", ASSIGNMENT),
        ]:
            with self.subTest(label):
                self.setUp()
                self.commit("settings.py", f"{secret}\n")
                reason = self.assertDenied(self.run_hook())
                self.assertIn(label, reason)

    def test_block_masks_the_secret(self):
        self.commit("settings.py", f"{AWS_KEY}\n")
        reason = self.assertDenied(self.run_hook())
        self.assertNotIn(AWS_KEY, reason)

    def test_clean_push_passes(self):
        self.commit("app.py", "print('hi')\n")
        self.assertIsNone(self.run_hook())

    def test_placeholder_line_passes(self):
        self.commit("config.example", 'api_key = "your_api_key_here"\n')
        self.assertIsNone(self.run_hook())

    def test_secret_already_on_remote_passes(self):
        self.commit("old.py", f"{AWS_KEY}\n")
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        self.commit("app.py", "print('hi')\n")
        self.assertIsNone(self.run_hook())

    def test_secret_in_skill_config_blocks(self):
        (self.repo / ".n2i-dev-cycle").mkdir()
        (self.repo / ".n2i-dev-cycle" / "config").write_text(f"{GITHUB_TOKEN}\n", encoding="utf-8")
        reason = self.assertDenied(self.run_hook())
        self.assertIn(".n2i-dev-cycle/config", reason)

    def test_non_push_commands_pass(self):
        self.commit("settings.py", f"{AWS_KEY}\n")
        for command in ("git status", "git push --dry-run"):
            with self.subTest(command):
                self.assertIsNone(self.run_hook(command))
        self.assertIsNone(self.run_hook(tool="Read"))


if __name__ == "__main__":
    unittest.main()
