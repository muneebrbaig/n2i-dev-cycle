#!/usr/bin/env python3
"""PreToolUse hook (matcher: Bash) for the n2i-dev-cycle skill.

Blocks a `git push` when the commits about to leave the machine, or the working
copy of `.n2i-dev-cycle/config` / `.n2i-dev-cycle/notes.md`, contain something
shaped like a secret. Every other command passes through untouched.

Best-effort and deliberately conservative: it greps for a short list of
high-signal patterns, not entropy. A hit is a hard block with the file and a
masked match; the fix is to scrub the secret (and rotate it) before pushing.

Wire it in after the skill's own hooks — see hooks/settings.snippet.json.
"""
import json
import re
import subprocess
import sys

PATTERNS = [
    ("AWS access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b")),
    ("private key block", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("password in URL", re.compile(r"://[^/\s:@]+:[^/\s:@]{3,}@")),
    (
        "generic secret assignment",
        re.compile(
            r"""(?ix)\b(api[_-]?key|secret|token|passwd|password|client[_-]?secret)\b\s*[:=]\s*['"][^'"\s]{8,}['"]"""
        ),
    ),
]

# Placeholders that look like the pattern but are not real secrets.
ALLOW = re.compile(r"(?i)(example|dummy|placeholder|your[_-]?|<[^>]+>|xxx+|\.\.\.|changeme|redacted)")


def mask(s: str) -> str:
    s = s.strip()
    return s if len(s) <= 12 else s[:6] + "…" + s[-3:]


def scan(text: str, source: str):
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if ALLOW.search(line):
            continue
        for label, rx in PATTERNS:
            m = rx.search(line)
            if m:
                hits.append(f"  {source}:{lineno}  {label} — {mask(m.group(0))}")
    return hits


def git(*args) -> str:
    try:
        return subprocess.run(
            ["git", *args], capture_output=True, text=True, timeout=10
        ).stdout
    except Exception:
        return ""


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        sys.exit(0)
    cmd = data.get("tool_input", {}).get("command", "")
    if not re.search(r"\bgit\b.*\bpush\b", cmd) or "--dry-run" in cmd:
        sys.exit(0)

    hits = []

    # Commits not yet on the upstream (fall back to a diff against the default base).
    upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}").strip()
    if upstream:
        diff = git("diff", f"{upstream}..HEAD")
    else:
        base = "origin/main" if git("rev-parse", "--verify", "-q", "origin/main").strip() else "HEAD~20"
        diff = git("diff", f"{base}...HEAD")
    added = "\n".join(l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
    hits += scan(added, "outgoing commits")

    for path in (".n2i-dev-cycle/config", ".n2i-dev-cycle/notes.md"):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                hits += scan(fh.read(), path)
        except FileNotFoundError:
            pass

    if not hits:
        sys.exit(0)

    reason = (
        "Possible secret in what you're about to push:\n"
        + "\n".join(hits)
        + "\n\nDo NOT retry with an env var, `git -c`, or any wrapper — this is a "
        "hard stop. Show the user the findings above and let them decide:\n"
        "  - Real secret: they scrub it from the file (and the git history if it's "
        "already committed) and rotate the credential, then you can push.\n"
        "  - False positive: they run the push themselves in a terminal (this hook "
        "only gates the agent):\n"
        f"      {cmd}\n"
        "    or they remove the hook from ~/.claude/settings.json."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
