#!/usr/bin/env python3
"""Stop hook for the n2i-dev-cycle skill — heuristic verification gate.

`references/verification.md` says: no "green" / "passing" / "done" without a
fresh build or test run in the same turn. This hook is the enforcement fallback
for that rule. When the final assistant turn claims success but no build/test
command ran since the last user message, it blocks the stop and asks for the
evidence.

Heuristic and opt-in. It only engages when the transcript mentions
`n2i-dev-cycle`, matches a short list of strong claim phrasings, and errs toward
staying quiet. False positive → tell Claude the run is already done, or drop this
hook from settings.
"""
import json
import re
import sys

CLAIM = re.compile(
    r"(?i)\b("
    r"all tests?\s+(pass|passing|green)"
    r"|tests?\s+(are\s+)?(now\s+)?(pass|passing|green)"
    r"|build\s+(succeed|succeeds|succeeded|passes|passed|is\s+green|clean)"
    r"|suite\s+(is\s+)?green"
    r"|everything\s+(is\s+)?green"
    r"|all\s+green"
    r")\b"
)
EVIDENCE = re.compile(
    r"(?i)\b("
    r"dotnet\s+(test|build)|npm\s+(test|run\s+build|run\s+test)|yarn\s+(test|build)"
    r"|pnpm\s+(test|build|run\s+\w+)|ng\s+(test|build)|cargo\s+(test|build)"
    r"|go\s+test|pytest|jest|vitest|gradle\s+\w*test|mvn\s+(test|verify)|make\s+\w*test"
    r")\b"
)


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

    last_assistant_text = ""
    bash_since_user = []
    for e in reversed(events):
        role = e.get("type")
        msg = e.get("message", {}) or {}
        content = msg.get("content", [])
        if role == "user":
            is_tool_result = isinstance(content, list) and any(
                isinstance(b, dict) and b.get("type") == "tool_result" for b in content
            )
            if not is_tool_result:
                break
        if role == "assistant" and isinstance(content, list):
            for b in content:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text" and not last_assistant_text:
                    last_assistant_text = b.get("text", "")
                if b.get("type") == "tool_use" and b.get("name") in ("Bash", "BashOutput"):
                    bash_since_user.append(json.dumps(b.get("input", {})))

    if not last_assistant_text or not CLAIM.search(last_assistant_text):
        sys.exit(0)
    if any(EVIDENCE.search(c) for c in bash_since_user):
        sys.exit(0)

    print(
        json.dumps(
            {
                "decision": "block",
                "reason": (
                    "Verification gate (references/verification.md): the turn claims a "
                    "green build/test but no build or test command ran in it. Run the "
                    "exact command now and read its output — exit code, failure count — "
                    "then state the real status with that evidence. If the run genuinely "
                    "already happened this turn, say so and stop."
                ),
            }
        )
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
