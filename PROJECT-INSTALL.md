# Bundle the skill into a project

Use this when a team repo should carry the skill itself, so engineers never pull it by hand. The skill repo stays the single source of truth. The project holds a git submodule that points at it, and a SessionStart hook keeps it current.

This file is written for people and for coding agents. An agent can follow "Setup" and "Migrate an existing install" as written.

For a single-user install, use the README's Installation section instead.

## How it works

- The skill is a git submodule at `.claude/skills/n2i-dev-cycle`, cloned over HTTPS from this repo (no SSH or credentials needed while the repo is public).
- A hook script in the project, `.claude/hooks/sync-n2i-skill.sh`, runs at every Claude Code session start:
  - initializes the submodule, so a fresh clone needs no `--recurse-submodules`;
  - pulls the tip of `main` at most once a week per clone;
  - links the subagents from `agents/` into the project's `.claude/agents/` and removes links whose target is gone.
- The hook is best-effort. It prints nothing and always exits 0, so an offline machine or a failed fetch never blocks a session. It retries on the next session.
- The hook script lives in the project, not in the submodule, because it has to exist before the submodule does. `scripts/project-sync.sh` in this repo is the template to copy.

## Setup

Run from the project root. A person reviews and commits the result. Agents must not commit or push.

1. Add the submodule and stop git from showing pointer drift:

   ```bash
   git submodule add -b main https://github.com/muneebrbaig/n2i-dev-cycle.git .claude/skills/n2i-dev-cycle
   git config -f .gitmodules submodule..claude/skills/n2i-dev-cycle.ignore all
   ```

   `ignore = all` keeps `git status` and `git commit -a` from reporting or bumping the submodule pointer when the hook moves it to a newer commit.

2. Copy the hook template into the project:

   ```bash
   mkdir -p .claude/hooks
   cp .claude/skills/n2i-dev-cycle/scripts/project-sync.sh .claude/hooks/sync-n2i-skill.sh
   chmod +x .claude/hooks/sync-n2i-skill.sh
   ```

3. Register it in the project's `.claude/settings.json`. Merge into any existing `hooks` object:

   ```json
   {
     "hooks": {
       "SessionStart": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/sync-n2i-skill.sh"
             }
           ]
         }
       ]
     }
   }
   ```

4. Ignore the generated agent links. Add to the project's `.gitignore`:

   ```text
   .claude/agents/n2i-*.md
   ```

5. Commit `.gitmodules`, the submodule entry, the hook script, `settings.json` and `.gitignore`.

6. Restart Claude Code in the project. The first session finishes the setup. If the agents don't show up, restart once more, because agents load at session start.

Notes:
- If the project's `.claude/skills/` is gitignored, remove that rule for this path or the submodule can't be tracked.
- The scripts are bash. On Windows use WSL or Git Bash, and symlinks need Developer Mode.

## How updates reach people

- A change pushed to `main` here reaches every engineer within about a week, with no action on their side.
- To pick one up sooner, delete `.git/n2i-skill-synced` in your clone and start a new Claude session.
- There is no version pin. A bad push to `main` reaches everyone within a week. If a project needs a gate, track a release tag instead of `main`.
- The skill repo's `hooks/settings.snippet.json` (secret scan, verify gate) is not wired by this setup. Add it to the project's `settings.json` if you want it.
- If the template changes, compare the project's copy and re-copy it:

  ```bash
  diff .claude/hooks/sync-n2i-skill.sh .claude/skills/n2i-dev-cycle/scripts/project-sync.sh
  ```

## Migrate an existing install

A personal copy in `~/.claude/skills/n2i-dev-cycle` takes priority over the project copy, so engineers who installed the skill themselves keep running it, and it never auto-updates. They must remove it. Project agents in `.claude/agents/` do take priority over `~/.claude/agents/`, so a leftover personal skill can end up paired with the project's agents at a different version.

A pull does not touch anything under `~/.claude`.

Give this prompt to Claude Code, after the project change is merged, to do the cleanup safely:

```text
Migrate my machine to the project-bundled n2i-dev-cycle skill in this repo. Work step by step, run the checks first, and follow these rules:
- Never run git add, commit, or push.
- Never delete a real folder or file. Delete only symlinks. Anything else gets moved aside with mv to a backup name (suffix .bak-YYYYMMDD) after I confirm.
- Touch only the paths named below. Don't touch other repos or any other skill or agent.
- If a check doesn't match what I describe, stop and tell me instead of improvising.

Background: the n2i-dev-cycle skill and its agents (n2i-*.md) now ship inside this repo as a git submodule at .claude/skills/n2i-dev-cycle, and a SessionStart hook (.claude/hooks/sync-n2i-skill.sh) initializes it, updates it weekly, and links the agents into .claude/agents/. My older personal install in ~/.claude takes priority over the project copy, so it has to go.

1. Locate the repo root (the git repo whose .gitmodules mentions n2i-dev-cycle). If I'm not inside it, ask me for the path.

2. Get the change. Run git branch --show-current and git status --short.
   - If .gitmodules and .claude/hooks/sync-n2i-skill.sh already exist, skip to step 3.
   - If I'm on master and my working tree is clean: run git pull and report the result.
   - If I'm on master with uncommitted changes: show them and ask before pulling.
   - If I'm on another branch: do NOT pull. Tell me my branch doesn't have the change yet and ask whether to merge master into it. Do it only if I say yes.

3. Check for a conflicting project-level path. Inspect .claude/skills/n2i-dev-cycle: it should be an empty folder or a submodule checkout. If it's a symlink or a folder with files that is NOT a submodule (git submodule status shows nothing for it), tell me and ask before moving it aside.

4. Ask me one question: "Do you use n2i-dev-cycle in other repos besides this one?" If yes, do not remove the personal install. Tell me it will shadow the project copy here and I'd need to update it manually, and skip the removals in the next step.

5. Inspect my personal install. Run ls -la on ~/.claude/skills and ~/.claude/agents and report anything named n2i-*.
   - ~/.claude/skills/n2i-dev-cycle is a symlink: note where it points, then remove only the link with rm.
   - It's a real folder: run git -C on it for git status --short and git log @{u}..; if it has uncommitted changes, unpushed commits, or the git log command fails (for example no upstream), treat that as unsaved work, tell me, and stop on this item. If clean, ask me, then mv it out of ~/.claude/skills entirely (for example to ~/.claude/n2i-dev-cycle.bak-YYYYMMDD), since a renamed folder left in ~/.claude/skills can still be loaded as a skill.
   - For each ~/.claude/agents/n2i-*.md that is a symlink: remove it (rm). If one is a real file, ask me first.
   - Remove dangling n2i links if found. List every path you removed or moved.

6. Run the sync hook once by hand from the repo root: .claude/hooks/sync-n2i-skill.sh. It is silent by design.

7. Verify and report a short checklist:
   - git submodule status shows .claude/skills/n2i-dev-cycle checked out (a commit hash with a leading space or +; a leading minus means not initialized).
   - .claude/skills/n2i-dev-cycle/SKILL.md exists.
   - .claude/agents/n2i-*.md are symlinks and each resolves (none dangling).
   - ~/.claude/skills and ~/.claude/agents contain no n2i-* entries (unless I chose to keep them in step 4).
   - git status --short shows no unexpected changes.

8. Finish by telling me to restart Claude Code in this repo, since skills and agents load at session start, and to restart once more if the agents don't appear after the first session.
```

## Troubleshooting

- **Skill not found after setup:** the submodule folder is empty. Run `.claude/hooks/sync-n2i-skill.sh` by hand, or `git submodule update --init`, then restart Claude Code.
- **Agents missing:** run the hook by hand, check `ls -l .claude/agents`, restart Claude Code. Without them the skill falls back to `general-purpose` with an explicit model.
- **Pull fails with "untracked working tree files would be overwritten":** someone has their own `.claude/skills/n2i-dev-cycle` in the project. Move it aside and pull again.
- **Stuck on an old version:** a personal copy in `~/.claude/skills/n2i-dev-cycle` is shadowing the project copy. See "Migrate an existing install".
- **Offline or GitHub unreachable:** nothing breaks. The hook skips the pull and tries again next session.
