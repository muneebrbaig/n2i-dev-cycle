#!/bin/bash
# SessionStart hook (see .claude/settings.json) - keeps the n2i-dev-cycle submodule current and
# links its subagents into .claude/agents/ (Claude Code doesn't read agents from inside a skill).
# Init runs every session; the pull to the remote tip runs at most once a week per clone.
# Best-effort: output is discarded and it always exits 0, so it can never block a session.
cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}" 2>/dev/null || exit 0
SKILL=.claude/skills/n2i-dev-cycle
export GIT_TERMINAL_PROMPT=0 GIT_HTTP_LOW_SPEED_LIMIT=1000 GIT_HTTP_LOW_SPEED_TIME=10
STAMP="$(git rev-parse --git-dir)/n2i-skill-synced"

{
  git submodule update --init -- "$SKILL"
  if [ -z "$(find "$STAMP" -mtime -7 2>/dev/null)" ] && git submodule update --remote -- "$SKILL"; then
    touch "$STAMP"
  fi

  mkdir -p .claude/agents
  for f in "$SKILL"/agents/n2i-*.md; do
    [ -e "$f" ] && ln -sf "../skills/n2i-dev-cycle/agents/$(basename "$f")" ".claude/agents/$(basename "$f")"
  done
  for l in .claude/agents/n2i-*.md; do
    [ -L "$l" ] && [ ! -e "$l" ] && rm "$l"
  done
} >/dev/null 2>&1
exit 0
