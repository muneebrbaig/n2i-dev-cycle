#!/usr/bin/env python3
"""Stop hook for the n2i-dev-cycle skill: Phase 5 review gate.

The Phase 5 exit gate says the pre-push review (n2i-prepush-reviewer) runs before the handover,
or a skip is written to the ledger with its reason. Prose gets skipped under momentum, so this
hook enforces the order: when the turn edited files inside a repo that keeps a
`.n2i-dev-cycle/` ledger, and nothing after those edits either dispatched `n2i-prepush-reviewer`
with the full prompt, ran `codex exec` with it (repos whose config sets `CODEX`), or wrote a
`Phase 5: review skipped` line, it blocks the stop.

A review counts only when its prompt (for Codex, the command plus the file after `<`) holds
every standing check from
`references/prepush-prompt.md`, and every `### ` heading of the file a repo names in
`REVIEW_CHECKLIST` (its `.n2i-dev-cycle/config`). Only edits made after the last review that
counted are listed, so a later round can cover just that delta.

It checks that a review ran with the full prompt, not that it was good. Edits made through Bash
(python, sed) are not seen; Edit, Write and NotebookEdit are. Engages only when the transcript
mentions `n2i-dev-cycle`. False positive: write the skip line with its reason, or drop the hook.
"""
import json
import os
import re
import sys

EDIT_TOOLS = ("Edit", "Write", "NotebookEdit")
SKIP_LINE = re.compile(r"Phase 5: review skipped")
TEMPLATE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references", "prepush-prompt.md")
CHECKLIST_KEY = re.compile(r"""^\s*REVIEW_CHECKLIST=["']?([^"'\n]+?)["']?\s*$""", re.M)
CODEX_KEY = re.compile(r"""^\s*CODEX=["']?(review|plan\+review)["']?\s*$""", re.M)
PROMPT_FILE = re.compile(r"""<\s*["']?([^"'\s]+)""")


def squash(text):
    return " ".join(text.split())


def ledger_root(path):
    """The directory holding .n2i-dev-cycle/progress.md above `path`, or None."""
    folder = os.path.dirname(os.path.abspath(path))
    while True:
        if os.path.isfile(os.path.join(folder, ".n2i-dev-cycle", "progress.md")):
            return folder
        parent = os.path.dirname(folder)
        if parent == folder:
            return None
        folder = parent


def standing_checks():
    """The bullets under '## Standing checks' in the prompt template, whitespace collapsed."""
    try:
        text = open(TEMPLATE, encoding="utf-8").read()
    except OSError:
        return []
    section = text.split("## Standing checks", 1)[1:]
    if not section:
        return []
    bullets = []
    for line in section[0].split("\n## ", 1)[0].splitlines():
        if line.startswith("- "):
            bullets.append(line[2:])
        elif bullets and line.startswith(" "):
            bullets[-1] += " " + line
    return [squash(b) for b in bullets]


def config_text(root):
    try:
        return open(os.path.join(root, ".n2i-dev-cycle", "config"), encoding="utf-8").read()
    except OSError:
        return ""


def codex_enabled(root):
    return bool(CODEX_KEY.search(config_text(root)))


def checklist_headings(root):
    """`### ` headings of the repo's REVIEW_CHECKLIST file. A named file that is missing is a heading
    no prompt can hold, so the gate stays shut until the config or the file is fixed."""
    match = CHECKLIST_KEY.search(config_text(root))
    if not match:
        return []
    path = os.path.join(root, match.group(1).strip())
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return ["REVIEW_CHECKLIST file not found: " + path]
    return [squash(line[4:]) for line in text.splitlines() if line.startswith("### ")]


def codex_prompt(use):
    """A `codex exec` command's text plus the prompt file it reads from stdin."""
    command = str((use.get("input") or {}).get("command", ""))
    match = PROMPT_FILE.search(command)
    if match:
        try:
            command += "\n" + open(os.path.expanduser(match.group(1)), encoding="utf-8").read()
        except OSError:
            pass
    return command


def missing_from_prompt(prompt, roots):
    """What a review prompt lacks; an empty list means it counts as the review."""
    prompt = squash(prompt)
    required = standing_checks()
    for root in sorted(roots):
        required += checklist_headings(root)
    return [item for item in required if item not in prompt]


def tool_uses_this_turn(events):
    """Assistant tool_use blocks since the last real user message, oldest first."""
    uses = []
    for e in reversed(events):
        content = (e.get("message", {}) or {}).get("content", [])
        if e.get("type") == "user":
            is_result = isinstance(content, list) and any(
                isinstance(b, dict) and b.get("type") == "tool_result" for b in content
            )
            if not is_result:
                break
        if e.get("type") == "assistant" and isinstance(content, list):
            uses.extend(b for b in reversed(content) if isinstance(b, dict) and b.get("type") == "tool_use")
    uses.reverse()
    return uses


def is_reviewer(use):
    return use.get("name") in ("Agent", "Task") and (use.get("input") or {}).get("subagent_type") == "n2i-prepush-reviewer"


def is_codex(use):
    return use.get("name") == "Bash" and "codex exec" in str((use.get("input") or {}).get("command", ""))


def is_skip(use):
    return use.get("name") == "Bash" and bool(SKIP_LINE.search(str((use.get("input") or {}).get("command", ""))))


def main():
    data = json.load(sys.stdin)
    if data.get("stop_hook_active"):
        sys.exit(0)
    path = data.get("transcript_path")
    if not path:
        sys.exit(0)
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        sys.exit(0)
    events = []
    for ln in lines:
        try:
            events.append(json.loads(ln))
        except ValueError:
            pass
    if not any("n2i-dev-cycle" in json.dumps(e) for e in events):
        sys.exit(0)

    pending = {}  # edited file -> its ledger root, for edits since the last review that counted
    missing = []
    for use in tool_uses_this_turn(events):
        inp = use.get("input") or {}
        if use.get("name") in EDIT_TOOLS:
            target = inp.get("file_path") or inp.get("notebook_path")
            root = ledger_root(target) if target else None
            if root:
                pending[os.path.abspath(target)] = root
        elif pending and is_skip(use):
            pending, missing = {}, []
        elif pending and is_reviewer(use):
            missing = missing_from_prompt(str(inp.get("prompt", "")), set(pending.values()))
            if not missing:
                pending = {}
        elif pending and is_codex(use) and all(codex_enabled(r) for r in pending.values()):
            missing = missing_from_prompt(codex_prompt(use), set(pending.values()))
            if not missing:
                pending = {}
    if not pending:
        sys.exit(0)

    files = sorted(os.path.relpath(f, root) for f, root in pending.items())
    reason = (
        "Review gate (Phase 5 exit gate): ledger-repo files changed since the last pre-push "
        "review this turn: " + ", ".join(files[:8]) + (" …" if len(files) > 8 else "") + ". "
        "Dispatch n2i-prepush-reviewer, or run codex exec where the repo sets CODEX "
        "(references/codex.md), with the prompt from references/prepush-prompt.md (every "
        "standing check word for word, plus the REVIEW_CHECKLIST headings when the repo sets one); "
        "a later round may cover only these files' changes. Or append "
        "'Phase 5: review skipped (<class>, <reason>)' to the repo's .n2i-dev-cycle/progress.md. "
        "Size the skip on the change since the last review, not the whole branch: a docs-only "
        "change that adds or alters no number or claim may be skipped as 'docs-only'; one over "
        "~100 lines, or touching auth, tenant or migration code, cannot be skipped."
    )
    if missing:
        reason += " The last review prompt lacked: " + "; ".join(item[:60] for item in missing) + "."
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


if __name__ == "__main__":
    main()
