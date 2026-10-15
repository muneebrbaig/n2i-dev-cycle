#!/bin/bash
# SessionStart hook template: keeps every n2i-* skill submodule under .claude/skills/ current
# and links their subagents into .claude/agents/ (Claude Code doesn't read agents from inside
# a skill). One hook serves n2i-dev-cycle, n2i-sec-audit, and any later n2i-* skill.
# A skill is checked out at the commit the project records when it isn't checked out yet or when
# that recorded commit changed since the last sync, so a pointer bump reaches every clone. Otherwise
# it is left alone, so a pulled tip survives. The pull to each remote tip runs at most once a week.
# Best-effort: output is discarded and it always exits 0, so it can never block a session.
cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}" 2>/dev/null || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
export GIT_TERMINAL_PROMPT=0 GIT_HTTP_LOW_SPEED_LIMIT=1000 GIT_HTTP_LOW_SPEED_TIME=10
STAMP="$(git rev-parse --git-dir)/n2i-skill-synced"

{
  DUE=
  [ -z "$(find "$STAMP" -mtime -7 2>/dev/null)" ] && DUE=1
  PULLED=
  mkdir -p .claude/agents
  for SKILL in .claude/skills/n2i-*; do
    [ -e "$SKILL" ] || continue
    REC=$(git rev-parse "HEAD:$SKILL" 2>/dev/null)
    SEEN="$(git rev-parse --git-dir)/n2i-pointer-$(basename "$SKILL")"
    if [ ! -e "$SKILL/.git" ] || { [ -n "$REC" ] && [ "$REC" != "$(cat "$SEEN" 2>/dev/null)" ]; }; then
      git submodule update --init -- "$SKILL" && [ -n "$REC" ] && echo "$REC" >"$SEEN"
    fi
    if [ -n "$DUE" ] && git submodule update --remote -- "$SKILL"; then
      PULLED=1
    fi
    NAME=$(basename "$SKILL")
    for f in "$SKILL"/agents/n2i-*.md; do
      [ -e "$f" ] && ln -sf "../skills/$NAME/agents/$(basename "$f")" ".claude/agents/$(basename "$f")"
    done
  done
  [ -n "$PULLED" ] && touch "$STAMP"
  for l in .claude/agents/n2i-*.md; do
    [ -L "$l" ] && [ ! -e "$l" ] && rm "$l"
  done
} >/dev/null 2>&1
exit 0
