#!/bin/bash
# Link the n2i-dev-cycle subagents into ~/.claude/agents/ so Claude Code can find them.
# Safe to re-run: run it after every `git pull`, since a release can add agents.
set -eu
SRC="$(cd "$(dirname "$0")/.." && pwd)/agents"
DEST="${HOME}/.claude/agents"
mkdir -p "$DEST"
for f in "$SRC"/n2i-*.md; do
  [ -e "$f" ] || continue
  ln -sf "$f" "$DEST/$(basename "$f")"
  echo "linked  $(basename "$f")"
done
for l in "$DEST"/n2i-*.md; do
  if [ -L "$l" ] && [ ! -e "$l" ]; then
    rm "$l"
    echo "removed $(basename "$l") (target gone)"
  fi
done
