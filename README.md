# n2i-dev-cycle

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill that runs the full development lifecycle, from ticket or prompt to shipped code. Built for vertical-slice .NET + Angular projects with multi-tenant architecture, originally for [Null2Infinity](https://null2infinity.com)'s own projects (N2I).

## What It Does

Guides development through 8 structured phases:

| Phase | What Happens |
|-------|-------------|
| **1. Ingest** | Fetches ticket from GitLab, reads a prompt, or picks up a migration sub-phase. Searches memory for prior work. |
| **2. Branch** | Detects if current branch matches the task. Suggests a branch name or lets you create your own. |
| **3. Plan** | Produces a structured implementation plan: entities, services, controllers, migrations, frontend components, tests. Waits for your approval. |
| **4. Implement** | Executes the plan following the scope-relevant `references/*.md` standards. |
| **5. Validate** | Runs `dotnet format`, `dotnet build`, `dotnet test`, `ng build`, `ng test`. Loops until all green. Once green, offers a code review of the local diff before anything gets pushed. |
| **6. Handover** | Summarizes changes, lists what to test locally, notes known limitations, flags e2e gaps. |
| **7. Feedback** | Accepts your findings from local testing, fixes issues, re-validates. Repeatable. |
| **8. Ship** | Pushes code on your command. Helps fix CI failures if they occur. |

### Why review happens before push

The skill runs code review at the end of Phase 5, after build and test are green, before anything
gets pushed. Catch a finding there and it's a clean amend or a pre-push commit, not a fix-up
commit stuck in the MR/PR's history for good. CI also only has to run once against a state
you've already reviewed. `engineering:code-review` works straight off a `git diff`, no PR URL
needed, so reviewing before the MR/PR exists costs nothing.

If `engineering:code-review` isn't installed (or `caveman:caveman-review`, which compresses
findings into the handover summary), the skill skips the step and keeps going. Same best-effort
pattern the memory/`claude-mem` integration uses.

### Session naming

Once the skill knows the requirements, at the end of Phase 1, it renames the session to
`<ticket-number>: <short desc>` via `set_session_title`. Run several `n2i-dev-cycle` sessions at
once and the session list stays readable instead of showing the same name for all of them.
Skips silently if the tool isn't available.

### E2E coverage suggestions

When the skill detects an e2e config or `e2e/` dir (see Project Detection), Phase 6 Handover
checks existing specs against the flows the change touched. It flags any flow without a matching
spec and asks whether to add one now or file it separately. This is a suggestion, not a gate:
no e2e suite runs automatically during Phase 5 Validate.

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

The skill auto-detects your project from the current working directory. No hardcoded names.

| What | How |
|------|-----|
| Backend | first `*.slnx`/`*.sln` found (≤3 levels deep); its dir = backend, basename = project |
| Frontend | dir containing `angular.json` (else nearest `package.json`) |
| Forge | `gitlab`/`github` from `origin` remote, with `glab`/`gh` fallback |
| E2E | `playwright.config.*`/`cypress.config.*`, else nearest `e2e/`/`tests/e2e` dir (≤3 levels deep) |

All project-specific input comes from the repo you're in — there is no cross-repo file:
the repo's own `CLAUDE.md` (team conventions) and an optional `.n2i-dev-cycle/notes.md`
(personal gotchas, gitignored).

### Per-repo config: `.n2i-dev-cycle/`

Each target repo gets a gitignored `.n2i-dev-cycle/` folder at its root holding everything
repo-scoped the skill generates: `config` (see `n2i-dev-cycle.config.example`) —
`KEY=value` lines for `DB_ENGINE`, `BRANCH_PREFIX`, `MIGRATION_DOC`, `FORGE`,
`DEFAULT_SCOPE` — and an optional `notes.md` you write yourself.

On the **first run in a repo** (no config found), Phase 1 proposes the file from detected
values and, with your consent, creates `.n2i-dev-cycle/config` at the git root and appends
one line to the repo's `.gitignore`:

```
.n2i-dev-cycle/
```

That `.gitignore` change is the only tracked file touched — you commit it. Decline and the
skill just uses detected values for that run. On later runs the config is the source of
truth; if `DB_ENGINE` is pinned and the codebase later disagrees (e.g. finished migrating to
Postgres), the skill flags the mismatch and asks before changing the key.

## Embedded Standards

Development standards live in `references/`, loaded on demand by scope so a frontend-only ticket
never pulls in backend rules:

- **`references/backend-standards.md`** — 7-file entity scaffold, service/controller patterns, DbUp wire-up, xUnit + Moq testing, C# code quality
- **`references/security.md`** — multi-tenancy enforcement, `ResolveWriteContext` pattern, cross-org write checks, FK validation
- **`references/migrations.md`** — DbUp, Postgres (default) + SQL Server (`DB_ENGINE=sqlserver`) dialects, naming rules
- **`references/frontend-standards.md`** — Angular service/component patterns, cascading dropdowns, mobile-first UI, PrimeNG conventions

Each file ends with its own scoped "Common Mistakes to Avoid" list. `SKILL.md` Phase 3 loads the
files matching the active scope. Project-specific `CLAUDE.md` instructions override on conflict.

## Variants

- **`SKILL.md`** — for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (Claude agent backend)
- **`SKILL.qwen.md`** — for [Qwen agent](https://www.alibabacloud.com/) (parallel implementation, same lifecycle)

Both variants share the same lifecycle and coding standards. Copy the appropriate manifest into your agent platform.

The skill integrates with [claude-mem](https://github.com/anthropics/claude-mem) (if available) to:

- **Search** prior work on the same ticket/feature at the start of each cycle
- **Record** observations at key milestones (plan approved, implementation done, validation pass, shipped)
- **Resume** across sessions. Start a new session with `"fix: ..."` and memory fills in prior context

## Adapting for Your Projects

The skill targets vertical-slice .NET + Angular projects, but you can adapt it:

1. **Fork this repo**
2. **Edit `SKILL.md`**:
   - Update the project detection section (Dynamic Context) with your solution file names
   - Add/remove phases as needed
3. **Edit `references/*.md`** to match your conventions
4. **Symlink** your fork into `~/.claude/skills/`

### Key sections to customize:

- **Dynamic Context** (`SKILL.md`) — project detection logic
- **`references/*.md`** — your coding conventions and per-domain "Common Mistakes to Avoid"
- **Project-Specific Overrides** (`SKILL.md`) — per-project settings

## License

MIT — see [LICENSE](LICENSE).
