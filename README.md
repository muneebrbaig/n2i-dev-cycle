# n2i-dev-cycle

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/muneebrbaig/n2i-dev-cycle)

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill that runs the full development lifecycle, from ticket or prompt to shipped code. Built for vertical-slice .NET + Angular projects with multi-tenant architecture, originally for [Null2Infinity](https://null2infinity.com)'s own projects (N2I) — the methodology is stack-agnostic and the .NET/Angular bindings are config-overridable (see [Using with a different stack](#using-with-a-different-stack)).

## What It Does

Guides development through 9 structured phases, each carrying its own discipline
(classification + approval gate, TDD, evidence-before-claims, systematic debugging,
clean finish, pattern capture):

| Phase | What Happens |
|-------|-------------|
| **1. Ingest, Classify & Align** | Classifies the work (spike / bounded / architectural). No ticket yet → brainstorms a ticket draft for Product review and stops. Ticket already finalized → restates the spec, flags every gap or ambiguity, gets one approval. Searches memory; starts a checkpoint ledger; checks skill-state hygiene (`.n2i-dev-cycle/` gitignored, no secrets in `notes.md`). |
| **2. Branch** | Suggests a branch name or lets you create your own, and offers an isolated git worktree for long or multi-session work. |
| **3. Plan** | Structured implementation plan with concrete field lists, method signatures, and named test cases — no placeholders. Self-reviewed against the spec. Waits for your approval. |
| **4. Implement** | Business logic is test-first (RED → GREEN → REFACTOR); scaffolding is exempt but exercised by the tests that follow. Intra-phase review checkpoints (all of them for architectural work, none for bounded changes, adjustable on request). The RED failure line is recorded in the ledger before each GREEN commit, so test-first order survives a session or machine switch. |
| **5. Validate** | Runs the project's format + build + test — `dotnet` / `ng` by default, or the `BACKEND_VALIDATE_CMD` / `FRONTEND_VALIDATE_CMD` config snippets on any other stack. Evidence-before-claims gate: no "green" without a fresh run in hand. Then a code review of the local diff (findings verified, not rubber-stamped; a real bug routes through the debugging + TDD refs) before anything gets pushed. |
| **6. Handover** | Summarizes changes, lists what to test locally, notes limitations. Builds and runs affected e2e specs (in a subagent) against a dev or throwaway DB where possible. |
| **7. Feedback** | Root-cause-first debugging (three failed fixes → question the design, not fix #4). Independent findings dispatched in parallel. Failing repro test before each fix. Re-validates. Repeatable. |
| **8. Ship** | Full suite green → confirm base branch → push + MR → root-cause any CI failure → clean up local branch and worktree after merge. |
| **9. Improve** | Distills 1–3 reusable patterns from the cycle into `.n2i-dev-cycle/instincts.md` (statement / trigger / confidence / stack scope), read back at Phase 1 of the next cycle. A plain file, so it works without memory tools. A pattern that recurs across cycles gets proposed as a one-line PR to the matching reference file. Archives the checkpoint ledger so the next ticket starts clean. |

Cross-cutting mechanics — model selection (`haiku` for scaffolding, `sonnet` for logic and test design, `opus` for architecture / debugging / review, stepping to the adjacent tier when a model is unavailable), subagent delegation, the **checkpoint ledger** (`.n2i-dev-cycle/progress.md`, survives context compaction and cross-session re-entry), and memory milestones — live in `references/execution.md`, loaded once the plan is approved so discussion and spike runs never pay for it and `SKILL.md` itself stays lean.

### Why review happens before push

The skill runs code review at the end of Phase 5, after build and test are green, before anything
gets pushed. Catch a finding there and it's a clean amend or a pre-push commit, not a fix-up
commit stuck in the MR/PR's history for good. CI also only has to run once against a state
you've already reviewed. `engineering:code-review` works straight off a `git diff`, no PR URL
needed, so reviewing before the MR/PR exists costs nothing.

The review scales with the change. A bounded change under roughly 100 changed lines that
touches no tenant-isolation, auth, or migration code skips the prompt, and the handover notes
it. Architectural changes, larger diffs, and anything touching those areas still ask, defaulting
to yes.

If `engineering:code-review` isn't installed, the skill dispatches the read-only
`n2i-prepush-reviewer` agent instead; if that is missing too, it skips the step and keeps going
(`caveman:caveman-review`, which compresses findings into the handover summary, is optional
in the same way). Same best-effort pattern the memory/`claude-mem` integration uses.

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

### What runs in a subagent, and what doesn't

The skill offloads work to a subagent only when the input is bulky, the output is
a short conclusion, and the task is independent of the rest of the lifecycle:
end-to-end runs in Phase 6 (the runner log can be hundreds of lines; what comes
back is pass/fail per spec plus traces for the failures), independent findings in
Phase 7, and separate failing CI jobs in Phase 8. The pre-push code review is
already its own skill. Three named agents in `agents/` back these delegations and pin
each one's model and tools (see [Subagents](#subagents)).

Everything that carries the specification stays in the main agent on purpose:

- **Reading the ticket, wiki pages, and linked docs.** The alignment gate, the
  plan self-review, and every test written in Phase 4 are checked back against the
  exact wording of the spec. A subagent would hand back a summary, and the
  distance between that summary and the real text is where scope quietly drifts.
- **Writing the ticket draft and the MR/PR description.** These are written from
  context the main agent already holds, and the wording matters. Delegating means
  re-supplying nearly everything for almost no saving.
- **The Phase 4 test-first loop.** RED→GREEN cycles run many times in quick
  succession; a subagent round-trip on each one would stall the loop, and the
  verification gate requires the main agent to run the command and read its output
  first-hand.

Phase 5 also asks for the quietest test reporter and keeps only the summary line
on a green run, expanding the full output only when something fails. A
`PreToolUse`/`Bash` filter hook — the one in
[claude-code-starter-kit](https://github.com/muneebrbaig/claude-code-starter-kit#hooks),
or `rtk` — does the same job automatically for every command; the skill's
instruction is the fallback for setups without one.

The mechanism that actually keeps the main context lean is the checkpoint ledger
(`.n2i-dev-cycle/progress.md`) plus memory observations — state is written down as
each checkpoint lands, so a later session reconstructs it from the ledger and
`git log` rather than from a long transcript.

## Installation

### Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI installed
- (Optional) [glab](https://gitlab.com/gitlab-org/cli) for GitLab ticket fetching, or [gh](https://cli.github.com/) for GitHub. If neither installed, paste ticket text / CI logs manually.
- (Optional) a `PreToolUse`/`Bash` hook that filters noisy build and test output before it reaches context — e.g. the one in [claude-code-starter-kit](https://github.com/muneebrbaig/claude-code-starter-kit#hooks), or `rtk`. Without one, Phase 5 falls back to quiet-reporter instructions (see below).

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

### Subagents

`agents/` holds four subagents that pin the model and tools for delegated work:

- `n2i-unit-runner` (haiku) — final validate run (format, build, unit tests), per side
- `n2i-e2e-runner` (haiku) — E2E runs
- `n2i-ci-triage` (sonnet) — root cause for one failing CI job or failure domain
- `n2i-prepush-reviewer` (opus) — read-only pre-push review

None has Edit or Write. All four keep Bash (for git, test runners, CI CLIs), so
"read-only" beyond that rests on each agent's instructions, not on a hard block.

Claude Code doesn't read agents from inside a skill folder, so link them into
`~/.claude/agents/` with the install script (the path below exists under both install
options above):

```bash
~/.claude/skills/n2i-dev-cycle/scripts/install-agents.sh
```

It is safe to re-run. It links each `agents/n2i-*.md` and removes links whose target no
longer exists.

Without them the skill still works: it falls back to the `general-purpose` agent with
an explicit model. Restart Claude Code after linking, since agents load at session start.

### Updating

Pull the new release, then re-run the install script, because a release can add agents and
only the script links them:

```bash
git -C ~/.claude/skills/n2i-dev-cycle pull
~/.claude/skills/n2i-dev-cycle/scripts/install-agents.sh
```

Agents you already linked update on their own, since the links point at the repo files. If
you installed the hooks, check `hooks/settings.snippet.json` for new entries to merge and
read the release's "Upgrading" notes in `CHANGELOG.md`. The skill also checks at the start of
every run and tells you once if an agent isn't linked. It never updates itself or links
anything without asking.

### Bundling into a team project

To make the skill part of a team repo, so engineers never pull it by hand, add it as a git
submodule with a SessionStart hook that keeps it current. See
[`PROJECT-INSTALL.md`](PROJECT-INSTALL.md) for setup, the copy-in hook
`scripts/project-sync.sh`, and a migration prompt for engineers who already have a personal install.

### Choosing a session model

The session model drives how reliably the skill's gates hold. In our evals, Opus followed
the approval gate, the class line and the ledger resume consistently. Sonnet followed
them most of the time but skipped steps more often, at roughly half the cost per turn.
A practical split: run Phases 1–3 (classify, align, plan) on Opus or in plan mode, then
switch to Sonnet for implementation with `/model`. Subagents already pin their own models,
so the switch only affects the main session.

One bounded ticket (add a range check to a function) run end to end, three turns each:

| Check | Sonnet | Opus |
|---|---|---|
| `Class:` line first, approval before code | Yes | Yes |
| Test-first (RED before GREEN) | Yes | Yes |
| No mid-phase stops (bounded change) | Yes | Yes |
| Phase 2 branch | No, stayed on `main` | Yes |
| Separate Phase 3 plan approval | No, merged into the first gate | Yes |
| Ledger (`progress.md`) | Not written | Complete, with RED evidence |
| Pre-push review skipped for a small bounded change | Not shown | Yes |
| Phase 6 handover | Condensed | Full |
| Cost for the three turns | about $0.70 | about $1.30 |

Sonnet gets the code and tests right and holds the approval gate, but it compresses the
surrounding process. If you rely on the ledger or the branch step, use Opus for
orchestration. These are single runs on one fixture, so read them as a pattern, not a
benchmark.

### Verify

Start Claude Code and check the skill is listed:

```
claude
# Type /n2i-dev-cycle — should appear in skill suggestions
# Type /agents — n2i-unit-runner, n2i-e2e-runner, n2i-ci-triage, n2i-prepush-reviewer should be listed
```

### Companion hooks (optional)

`hooks/` holds two Python hooks that enforce lifecycle gates outside the model's
control. They are additive — the skill's prose gates still work without them.

| Hook | Event | What it does |
|---|---|---|
| `pre-push-secret-scan.py` | `PreToolUse` / Bash | Blocks a `git push` when the outgoing commits, or `.n2i-dev-cycle/config` / `notes.md`, contain something shaped like a secret (AWS/GitHub/Slack tokens, private keys, passwords in URLs, quoted `api_key=`-style assignments). Conservative pattern match, not entropy. The block lists each file:line and, for a false positive, echoes back the exact `git push` for the user to run in their own terminal. |
| `verify-gate.py` | `Stop` | Heuristic backstop for `references/verification.md`: blocks a stop whose final turn claims a green build/test when no build or test command ran in that turn. Opt-in — drop it if false positives get noisy. |

Both need `python3` (already a Claude Code hooks prerequisite). Merge
`hooks/settings.snippet.json` into `~/.claude/settings.json`, adding its entries to
the matching `hooks` arrays rather than replacing what's there. Paths in the
snippet assume the skill lives at `~/.claude/skills/n2i-dev-cycle`.

After changing a hook, run its tests (standard library only, nothing to install):
`python3 -m unittest discover -s hooks/tests`. The agent files have their own
structural test: `python3 -m unittest discover -s tests`. The skill never loads these files.

For build/test **output** trimming (a separate concern), use `rtk` or the
`PreToolUse` filter in
[claude-code-starter-kit](https://github.com/muneebrbaig/claude-code-starter-kit#hooks) —
the skill does not ship its own.

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

Every run, Phase 1 also confirms `.n2i-dev-cycle/` is still in `.gitignore` and scans an
existing `notes.md` for accidentally-pasted secrets — its text flows into ledger lines,
memory, and handover summaries. A warning, never a block.

## Embedded References

`SKILL.md` is a lean spine — the phase list, detection, input parsing, and the two
always-on phases (1 Ingest, 2 Branch). Every phase's actual procedure lives in a
reference it names and loads only when that phase runs, so a discussion- or
planning-only invocation never pulls in the build, ship, or improve machinery.
`references/execution.md` is the one always-on reference — loaded once the Phase 3 plan is
approved, kept through Ship, so discussion and spike runs never pay for it — holding the cross-cutting bits (model selection, delegation, ledger,
memory milestones).

**Lifecycle procedure** — one reference per phase (or phase group):

- **`references/brainstorming.md`** — Phase 1: spike/bounded/architectural classification, approval gate, discussion→ticket and spec'd→alignment flows
- **`references/planning.md`** — Phase 3: implementation-plan format, no-placeholders rule, plan self-review
- **`references/build-loop.md`** — Phases 4–6: build order + RED→GREEN loop, review checkpoints, validate commands + noise handling + pre-push review, handover summary format
- **`references/debugging.md`** — Phase 7 (+ Phase 8 CI): root-cause-first steps, boundary instrumentation, 3-fix rule, parallel dispatch, per-finding loop, `fix:` cold-start resume
- **`references/finishing.md`** — Phase 8: ship gate, suite green → base confirm → push + MR → CI → cleanup → final memory + ledger line
- **`references/improve.md`** — Phase 9: what to distill, instinct shape, near-duplicate search, promotion-to-reference PR, ledger archive

**Discipline (stack-agnostic)** — the iron laws, loaded alongside the phase procedure:

- **`references/tdd.md`** — RED-GREEN-REFACTOR, test-first vs exempt scaffolding, tests that can't go red, rationalization table
- **`references/verification.md`** — evidence-before-claims gate, claim→proof table

**Standards (stack-specific — .NET + Angular defaults)**:

- **`references/backend-standards.md`** — 7-file entity scaffold, service/controller patterns, DbUp wire-up, xUnit + Moq testing, C# code quality
- **`references/security.md`** — multi-tenancy enforcement, `ResolveWriteContext` pattern, cross-org write checks, FK validation
- **`references/migrations.md`** — DbUp, Postgres (default) + SQL Server (`DB_ENGINE=sqlserver`) dialects, naming rules
- **`references/frontend-standards.md`** — Angular service/component patterns, cascading dropdowns, mobile-first UI, PrimeNG conventions, browser checks for UI verification

**Beyond the references** — files the skill never loads, for people maintaining it:

- **`agents/`** — four subagent definitions (`n2i-unit-runner`, `n2i-e2e-runner`, `n2i-ci-triage`, `n2i-prepush-reviewer`); link them into `~/.claude/agents/` (see Installation)
- **`scripts/install-agents.sh`** — links the agents into `~/.claude/agents/`; re-run after each pull
- **`PROJECT-INSTALL.md`** — how to bundle the skill into a team repo as a submodule, and how engineers migrate from a personal install
- **`scripts/project-sync.sh`** — SessionStart hook template for that setup; copy it into the project, don't run it from here
- **`tests/`** — structural tests for the agents, the install script and startup check, the project hook, doc references, and Contents lists: `python3 -m unittest discover -s tests`
- **`evals/scenarios.md`** — behavior scenarios with pass/fail checklists, for checking the skill on different models

The standards and discipline references each end with a scoped "Common Mistakes to Avoid"
list. Project-specific `CLAUDE.md` instructions override on conflict. A repo that keeps its own conventions (often in
`backend/CLAUDE.md` etc.) points the `BACKEND_STANDARDS` / `FRONTEND_STANDARDS` /
`MIGRATION_STANDARDS` config keys at them, and Phase 3 treats those as authoritative.

## Variants

- **`SKILL.md`** — for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (Claude agent backend)
- **`SKILL.qwen.md`** — for [Qwen agent](https://www.alibabacloud.com/) (parallel implementation, same lifecycle)

Both variants share the same lifecycle and coding standards. Copy the appropriate manifest into your agent platform.

The skill integrates with [claude-mem](https://github.com/anthropics/claude-mem) (if available) to:

- **Search** prior work on the same ticket/feature at the start of each cycle
- **Record** observations at key milestones (plan approved, handover, shipped; everything else goes to the ledger)
- **Resume** across sessions. Start a new session with `"fix: ..."` and memory fills in prior context
- **Learn** — Phase 9 distills reusable patterns into `.n2i-dev-cycle/instincts.md`, surfaced (stack-filtered) at Phase 1 of later cycles; a recurring one gets proposed as a PR to the matching reference file

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
