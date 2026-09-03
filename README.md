# n2i-dev-cycle

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill that runs the full development lifecycle, from ticket or prompt to shipped code. Built for vertical-slice .NET + Angular projects with multi-tenant architecture, originally for [Null2Infinity](https://null2infinity.com)'s own projects (N2I) — the methodology is stack-agnostic and the .NET/Angular bindings are config-overridable (see [Using with a different stack](#using-with-a-different-stack)).

## What It Does

Guides development through 8 structured phases, each carrying its own discipline
(classification + approval gate, TDD, evidence-before-claims, systematic debugging,
clean finish):

| Phase | What Happens |
|-------|-------------|
| **1. Ingest, Classify & Align** | Classifies the work (spike / bounded / architectural). No ticket yet → brainstorms a ticket draft for Product review and stops. Ticket already finalized → restates the spec, flags every gap or ambiguity, gets one approval. Searches memory; starts a checkpoint ledger. |
| **2. Branch** | Suggests a branch name or lets you create your own, and offers an isolated git worktree for long or multi-session work. |
| **3. Plan** | Structured implementation plan with concrete field lists, method signatures, and named test cases — no placeholders. Self-reviewed against the spec. Waits for your approval. |
| **4. Implement** | Business logic is test-first (RED → GREEN → REFACTOR); scaffolding is exempt but exercised by the tests that follow. Intra-phase review checkpoints. |
| **5. Validate** | Runs the project's format + build + test — `dotnet` / `ng` by default, or the `BACKEND_VALIDATE_CMD` / `FRONTEND_VALIDATE_CMD` config snippets on any other stack. Evidence-before-claims gate: no "green" without a fresh run in hand. Then a code review of the local diff (findings verified, not rubber-stamped; a real bug routes through the debugging + TDD refs) before anything gets pushed. |
| **6. Handover** | Summarizes changes, lists what to test locally, notes limitations. Builds and runs affected e2e specs against a dev or throwaway DB where possible. |
| **7. Feedback** | Root-cause-first debugging (three failed fixes → question the design, not fix #4). Independent findings dispatched in parallel. Failing repro test before each fix. Re-validates. Repeatable. |
| **8. Ship** | Full suite green → confirm base branch → push + MR → root-cause any CI failure → clean up local branch and worktree after merge. |

Cross-cutting: a **model-selection** table (cheap model for scaffolding, capable for architecture / debugging / review) and a **checkpoint ledger** (`.n2i-dev-cycle/progress.md`) that survives context compaction and cross-session re-entry.

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

### E2E coverage

When the skill detects an e2e config or `e2e/` dir (see Project Detection), Phase 6 Handover
always reviews the change's e2e impact: any spec the change breaks or makes stale gets fixed
regardless of how small the change is. A touched flow with no spec gets one built (test-first),
unless it's minor and you agree a spec isn't warranted — that call is recorded in the handover.
Affected specs run against a dev or fresh throwaway DB where the project supports one, before
Phase 8; where a real run isn't possible it says so rather than claiming coverage. Phase 5
Validate still runs unit/build only.

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

Every entry point runs Phase 1 first: the skill classifies the work
(spike / bounded / architectural), and **nothing is branched, planned, or coded until
you approve the intent** — the ticket draft (discussion mode) or the restated spec
(everything else).

### Discussion / Brainstorm (no ticket yet)

```
/n2i-dev-cycle "let's figure out how org admins should bulk-invite members"
/n2i-dev-cycle @docs/rough-notes-from-call.md
```

You're still deciding what to build. The skill asks clarifying questions one at a time,
proposes approaches for architectural work, and produces a **ticket / sub-ticket draft
for Product review** — then stops. Brainstorming and building are normally separate
sessions.

### From a GitLab Ticket

```
/n2i-dev-cycle #17
/n2i-dev-cycle 42
```

Fetches the ticket via `glab issue view`. Since the planning session starts cold, the
skill runs an **alignment gate** first — restates the spec in a few bullets and lists
every gap or ambiguity it sees — then waits for one approval before Phase 2. It does
not re-brainstorm a finalized ticket.

### From a Prompt

```
/n2i-dev-cycle "Add user name who prepared the document to the PDF report"
```

Uses the description as requirements. Classified and aligned like a ticket.

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

Skips planning. Reads `.n2i-dev-cycle/progress.md` and recent `git log` (they outrank
memory after a compaction), searches memory for prior context, then debugs
root-cause-first — a failing repro test before the fix, and if three fixes don't hold
it stops and questions the design rather than trying a fourth.

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
repo-scoped the skill generates: `config` (see `n2i-dev-cycle.config.example`), the
`progress.md` checkpoint ledger, and an optional `notes.md` you write yourself.

`config` keys (all optional, `KEY=value`, one per line):

| Key | Purpose |
|---|---|
| `BRANCH_PREFIX` | new-branch prefix (`mb/` → `mb/17-add-foo`); default: git-user initials, else `dev/` |
| `DEFAULT_SCOPE` | `backend` \| `frontend` \| `both` when both are detected; default: ask |
| `FORGE` | `gitlab` \| `github`, overriding remote-URL detection |
| `DB_ENGINE` | `postgres` (default) \| `sqlserver` \| `auto` — DbUp only |
| `MIGRATION_DOC` | migration-status doc filename; enables Migration mode |
| `BACKEND_VALIDATE_CMD`, `FRONTEND_VALIDATE_CMD` | Phase 5 shell snippets for non-.NET/Angular stacks; unset → `dotnet` / `npm` |
| `E2E_CMD` | Phase 6 e2e runner; unset → the detected runner |
| `BACKEND_STANDARDS`, `FRONTEND_STANDARDS`, `MIGRATION_STANDARDS` | path to the repo's own convention file (e.g. `backend/CLAUDE.md`); Phase 3 treats it as authoritative over `references/*` |

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

## Embedded References

Loaded on demand — a phase names the files it needs; a frontend-only ticket never pulls in
backend rules.

**Discipline (stack-agnostic)** — the methodology, works with any language or framework:

- **`references/brainstorming.md`** — spike/bounded/architectural classification, approval gate, discussion→ticket and spec'd→alignment flows
- **`references/tdd.md`** — RED-GREEN-REFACTOR, test-first vs exempt scaffolding, rationalization table
- **`references/verification.md`** — evidence-before-claims gate, claim→proof table
- **`references/debugging.md`** — root-cause-first steps, boundary instrumentation, 3-fix rule, parallel dispatch
- **`references/finishing.md`** — suite green → base confirm → push + MR → CI → cleanup

**Standards (stack-specific — .NET + Angular defaults)**:

- **`references/backend-standards.md`** — 7-file entity scaffold, service/controller patterns, DbUp wire-up, xUnit + Moq testing, C# code quality
- **`references/security.md`** — multi-tenancy enforcement, `ResolveWriteContext` pattern, cross-org write checks, FK validation
- **`references/migrations.md`** — DbUp, Postgres (default) + SQL Server (`DB_ENGINE=sqlserver`) dialects, naming rules
- **`references/frontend-standards.md`** — Angular service/component patterns, cascading dropdowns, mobile-first UI, PrimeNG conventions

Each file ends with its own scoped "Common Mistakes to Avoid" list. Project-specific `CLAUDE.md`
instructions override on conflict. A repo that keeps its own conventions (often in
`backend/CLAUDE.md` etc.) points the `BACKEND_STANDARDS` / `FRONTEND_STANDARDS` /
`MIGRATION_STANDARDS` config keys at them, and Phase 3 treats those as authoritative.

## Variants

- **`SKILL.md`** — for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (Claude agent backend)
- **`SKILL.qwen.md`** — for [Qwen agent](https://www.alibabacloud.com/) (parallel implementation, same lifecycle)

Both variants share the same lifecycle and coding standards. Copy the appropriate manifest into your agent platform.

The skill integrates with [claude-mem](https://github.com/anthropics/claude-mem) (if available) to:

- **Search** prior work on the same ticket/feature at the start of each cycle
- **Record** observations at key milestones (plan approved, implementation done, validation pass, shipped)
- **Resume** across sessions. Start a new session with `"fix: ..."` and memory fills in prior context

## Using with a different stack

The 8-phase spine and the five discipline references are stack-agnostic. Only the four
standards references and a handful of detection/command defaults assume .NET + Angular.
To run the skill on any other stack — **no fork required**:

1. **Set the validation commands** in the repo's `.n2i-dev-cycle/config`:
   ```
   BACKEND_VALIDATE_CMD=cargo fmt --check && cargo build && cargo test
   FRONTEND_VALIDATE_CMD=cd "$FRONTEND" && pnpm lint && pnpm build && pnpm test
   E2E_CMD=npx playwright test
   ```
   Unset → the skill falls back to `dotnet` / `npm`. Phases 5 and 6 use these.

2. **Point at your conventions** — either fork the four standards files for your stack,
   or (simpler) set `BACKEND_STANDARDS` / `FRONTEND_STANDARDS` / `MIGRATION_STANDARDS`
   to paths inside the repo (many teams already keep these in `backend/CLAUDE.md`,
   `web/CLAUDE.md`). Phase 3 reads the pointed-at file as authoritative; the Phase 3/4
   plan vocabulary follows from it.

3. **Ignore the DbUp bits** — `DB_ENGINE` and `references/migrations.md` are
   DbUp-specific. On another migration tool, leave `DB_ENGINE` unset and use
   `MIGRATION_STANDARDS`.

Dynamic Context detection degrades gracefully (`BACKEND=none` / `FRONTEND=none`) when
it doesn't recognise the stack — nothing to edit there.

Deeper changes (renaming phases, restructuring the spine) still mean forking `SKILL.md`
and symlinking your fork into `~/.claude/skills/`.

## License

MIT — see [LICENSE](LICENSE).
