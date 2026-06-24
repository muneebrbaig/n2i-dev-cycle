# n2i-dev-cycle

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill that orchestrates the full development lifecycle — from ticket or prompt to shipped code. Built for vertical-slice .NET + Angular projects with multi-tenant architecture.

## What It Does

Guides development through 8 structured phases:

| Phase | What Happens |
|-------|-------------|
| **1. Ingest** | Fetches ticket from GitLab, reads a prompt, or picks up a migration sub-phase. Searches memory for prior work. |
| **2. Branch** | Detects if current branch matches the task. Suggests a branch name or lets you create your own. |
| **3. Plan** | Produces a structured implementation plan: entities, services, controllers, migrations, frontend components, tests. Waits for your approval. |
| **4. Implement** | Executes the plan following embedded coding standards and conventions. |
| **5. Validate** | Runs `dotnet format`, `dotnet build`, `dotnet test`, `ng build`, `ng test`. Loops until all green. |
| **6. Handover** | Summarizes changes, lists what to test locally, notes known limitations. |
| **7. Feedback** | Accepts your findings from local testing, fixes issues, re-validates. Repeatable. |
| **8. Ship** | Pushes code on your command. Helps fix CI failures if they occur. |

## Installation

### Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI installed
- (Optional) [glab](https://gitlab.com/gitlab-org/cli) for GitLab ticket fetching, or [gh](https://cli.github.com/) for GitHub. If neither installed, paste ticket text / CI logs manually.

### Setup

Clone into your skills directory and symlink:

```bash
# Clone
git clone https://github.com/muneebrbaig/n2i-dev-cycle.git ~/projects/skills/n2i-dev-cycle

# Symlink into Claude Code skills
ln -s ~/projects/skills/n2i-dev-cycle ~/.claude/skills/n2i-dev-cycle
```

Or install directly (without separate clone location):

```bash
git clone https://github.com/muneebrbaig/n2i-dev-cycle.git ~/.claude/skills/n2i-dev-cycle
```

### Verify

Start Claude Code and check the skill is listed:

```
claude
# Type /n2i-dev-cycle — should appear in skill suggestions
```

## Usage

### From a GitLab Ticket

```
/n2i-dev-cycle #17
/n2i-dev-cycle 42
```

Fetches the ticket via `glab issue view`, extracts requirements, and starts the cycle.

### From a Prompt

```
/n2i-dev-cycle "Add user name who prepared the document to the PDF report"
```

Uses the description directly as requirements.

### From a Document

```
/n2i-dev-cycle @docs/feature-spec.md
```

Reads the document and extracts requirements.

### Migration Continuation

```
/n2i-dev-cycle "review and continue migration"
```

Reads migration tracking docs (e.g., `docs/migrate-web.md`), finds the next incomplete phase/sub-phase, and picks it up.

### Feedback / Fix Mode

```
/n2i-dev-cycle "fix: dropdown not loading cities after selecting a state"
```

Skips planning, searches memory for prior context, and goes straight to diagnosing and fixing.

## Project Detection

The skill auto-detects your project from the current working directory — no hardcoded names:

| What | How |
|------|-----|
| Backend | first `*.slnx`/`*.sln` found (≤3 levels deep); its dir = backend, basename = project |
| Frontend | dir containing `angular.json` (else nearest `package.json`) |
| Forge | `gitlab`/`github` from `origin` remote, with `glab`/`gh` fallback |

Each project's own `CLAUDE.md` is loaded for project-specific overrides. Optional local hints
live in a gitignored `projects.local.md` (see `projects.local.md.example`) and config in
`.n2i-dev-cycle.env` (see `.n2i-dev-cycle.env.example`).

## Embedded Standards

The skill ships with general development standards covering:

- **Backend**: 7-file entity scaffold, service patterns (multi-tenant, org-scoped queries), controller patterns, DbUp migrations
- **Frontend**: Angular service/component patterns, cascading dropdowns, mobile-first UI, PrimeNG conventions
- **Testing**: xUnit + Moq setup patterns, minimum test coverage per service
- **Security**: Multi-tenancy enforcement, FK validation, cross-org access control
- **Code quality**: Naming conventions, formatting rules, common mistakes to avoid

These serve as the baseline. Project-specific `CLAUDE.md` instructions override when conflicts arise.

## Variants

- **`SKILL.md`** — for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (Claude agent backend)
- **`SKILL.qwen.md`** — for [Qwen agent](https://www.alibabacloud.com/) (parallel implementation, same lifecycle)

Both variants share the same lifecycle and coding standards; copy the appropriate manifest into your agent platform.

The skill integrates with [claude-mem](https://github.com/anthropics/claude-mem) (if available) to:

- **Search** prior work on the same ticket/feature at the start of each cycle
- **Record** observations at key milestones (plan approved, implementation done, validation pass, shipped)
- **Resume** across sessions — start a new session with `"fix: ..."` and memory fills in prior context

## Adapting for Your Projects

The skill is designed for vertical-slice .NET + Angular projects but can be adapted:

1. **Fork this repo**
2. **Edit `SKILL.md`**:
   - Update the project detection section (Dynamic Context) with your solution file names
   - Modify the General Development Standards to match your conventions
   - Add/remove phases as needed
3. **Symlink** your fork into `~/.claude/skills/`

### Key sections to customize:

- **Dynamic Context** — project detection logic
- **General Development Standards** — your coding conventions
- **Project-Specific Overrides** — per-project settings
- **Common Mistakes to Avoid** — your team's known pitfalls

## License

MIT — see [LICENSE](LICENSE).
