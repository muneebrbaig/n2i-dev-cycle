#!/usr/bin/env python3
"""Stop hook for the n2i-dev-cycle skill: Phase 5 review gate.

The Phase 5 exit gate says the pre-push review (n2i-prepush-reviewer) runs before the handover,
or a skip is written to the ledger with its reason. Prose gets skipped under momentum, so this
hook enforces the order: when the turn edited files inside a repo that keeps a
`.n2i-dev-cycle/` ledger, and nothing after the last such edit either dispatched
`n2i-prepush-reviewer` or wrote a `Phase 5: review skipped` line, it blocks the stop.

It checks that a review was run, not that it was good. Edits made through Bash (python, sed)
are not seen; Edit, Write and NotebookEdit are. Engages only when the transcript mentions
`n2i-dev-cycle`. False positive: write the skip line with its reason, or drop the hook.
"""
import json
import os
import re
import sys

EDIT_TOOLS = ("Edit", "Write", "NotebookEdit")
SKIP_LINE = re.compile(r"Phase 5: review skipped")


def in_ledger_repo(path):
    """True when `path` sits under a directory holding .n2i-dev-cycle/progress.md."""
    folder = os.path.dirname(os.path.abspath(path))
    while True:
        if os.path.isfile(os.path.join(folder, ".n2i-dev-cycle", "progress.md")):
            return True
        parent = os.path.dirname(folder)
        if parent == folder:
            return False
        folder = parent


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


def counts_as_review(use):
    inp = use.get("input") or {}
    if use.get("name") in ("Agent", "Task"):
        return inp.get("subagent_type") == "n2i-prepush-reviewer"
    if use.get("name") == "Bash":
        return bool(SKIP_LINE.search(str(inp.get("command", ""))))
    return False


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

    uses = tool_uses_this_turn(events)
    last_edit = -1
    for i, use in enumerate(uses):
        if use.get("name") in EDIT_TOOLS:
            target = (use.get("input") or {}).get("file_path") or (use.get("input") or {}).get("notebook_path")
            if target and in_ledger_repo(target):
                last_edit = i
    if last_edit < 0:
        sys.exit(0)
    if any(counts_as_review(use) for use in uses[last_edit + 1 :]):
        sys.exit(0)

    print(
        json.dumps(
            {
                "decision": "block",
                "reason": (
                    "Review gate (Phase 5 exit gate): files in a ledger repo changed this turn "
                    "and no pre-push review ran after the last edit. Dispatch "
                    "n2i-prepush-reviewer on the diff and fix what it finds, or append "
                    "'Phase 5: review skipped (<class>, <reason>)' to the repo's "
                    ".n2i-dev-cycle/progress.md. A diff over ~100 lines, or one touching "
                    "auth, tenant or migration code, cannot be skipped."
                ),
            }
        )
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
