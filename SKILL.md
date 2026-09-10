---
name: n2i-dev-cycle
description: Full development lifecycle — ticket/prompt to shipped code. Handles planning, implementation, validation, feedback loops, and CI fixes across N2I projects. Invoke with a ticket number, prompt, or document reference.
allowed-tools: Bash, Read, Edit, Write, Agent, Grep, Glob, mcp__plugin_claude-mem_mcp-search__observation_add, mcp__plugin_claude-mem_mcp-search__observation_search, mcp__plugin_claude-mem_mcp-search__memory_search, mcp__ccd_session_mgmt__set_session_title
---

# N2I Development Cycle

Full-lifecycle development skill. 9 phases: Ingest/Classify/Align → Branch → Plan → Implement → Validate → Handover → Feedback → Ship → Improve.

Start every discussion, ticket, or fix with this skill — Phase 1 classifies the
work and decides how much process it needs, so brainstorming a topic and shipping
a finalized ticket both enter here.

## Dynamic Context

- Backend: !`SLN=$(find . -maxdepth 3 \( -name '*.slnx' -o -name '*.sln' \) 2>/dev/null | head -1); if [ -n "$SLN" ]; then echo "SLN=$SLN; BACKEND=$(dirname "$SLN"); PROJECT=$(basename "$SLN" | sed 's/\.[^.]*$//')"; else echo "BACKEND=none"; fi`
- Frontend: !`NG=$(find . -maxdepth 3 -name angular.json -not -path '*/node_modules/*' 2>/dev/null | head -1); if [ -n "$NG" ]; then echo "FRONTEND=$(dirname "$NG")"; else PKG=$(find . -maxdepth 3 -name package.json -not -path '*/node_modules/*' 2>/dev/null | head -1); [ -n "$PKG" ] && echo "FRONTEND=$(dirname "$PKG")" || echo "FRONTEND=none"; fi`
- Current branch: !`git branch --show-current 2>/dev/null || echo "not-a-repo"`
- Git remote: !`git remote get-url origin 2>/dev/null || echo "no-remote"`
- Forge: !`URL=$(git remote get-url origin 2>/dev/null); case "$URL" in *gitlab*) F=gitlab;; *github*) F=github;; *) F=unknown;; esac; CLI=none; if [ "$F" = gitlab ] && command -v glab >/dev/null 2>&1; then CLI=glab; elif [ "$F" = github ] && command -v gh >/dev/null 2>&1; then CLI=gh; elif command -v glab >/dev/null 2>&1; then CLI=glab; elif command -v gh >/dev/null 2>&1; then CLI=gh; fi; echo "FORGE=$F; FORGE_CLI=$CLI"`
- DB engine: !`f=$(find . -maxdepth 3 -path '*/.n2i-dev-cycle/config' 2>/dev/null | head -1); [ -n "$f" ] && . "$f" 2>/dev/null; E=${DB_ENGINE:-}; if [ -n "$E" ] && [ "$E" != auto ]; then echo "DB_ENGINE=$E (config)"; else FILES=$(grep -rlE 'PostgresqlDatabase\(|SqlServerDatabase\(|\.SqlDatabase\(|UseNpgsql|UseSqlServer' --include='*.cs' . 2>/dev/null | grep -v '/old/'); MIG=$(echo "$FILES" | xargs grep -hoE 'PostgresqlDatabase\(|SqlServerDatabase\(|\.SqlDatabase\(|UseNpgsql|UseSqlServer' 2>/dev/null | sort -u | tr -d '\n'); if echo "$MIG" | grep -qE 'Postgresql|Npgsql'; then echo "DB_ENGINE=postgres (migrator)"; elif echo "$MIG" | grep -qE 'SqlServer|SqlDatabase'; then echo "DB_ENGINE=sqlserver (migrator)"; else P=$(grep -rhi -E 'Npgsql\.EntityFrameworkCore|dbup-postgresql' --include='*.csproj' . 2>/dev/null); S=$(grep -rhi -E 'EntityFrameworkCore\.SqlServer|dbup-sqlserver' --include='*.csproj' . 2>/dev/null); if [ -n "$P" ] && [ -z "$S" ]; then echo "DB_ENGINE=postgres (pkg)"; elif [ -n "$S" ] && [ -z "$P" ]; then echo "DB_ENGINE=sqlserver (pkg)"; else echo "DB_ENGINE=postgres (default; confirm in Phase 1)"; fi; fi; fi`
- Migration docs: !`c=$(find . -maxdepth 3 -path '*/.n2i-dev-cycle/config' 2>/dev/null | head -1); [ -n "$c" ] && . "$c" 2>/dev/null; if [ -n "${MIGRATION_DOC:-}" ]; then d=$(find . -maxdepth 3 -name "$MIGRATION_DOC" 2>/dev/null | head -1); [ -n "$d" ] && echo "MIGRATION_DOCS=$d" || echo "MIGRATION_DOCS=none"; else echo "MIGRATION_DOCS=none"; fi`
- Config: !`f=$(find . -maxdepth 3 -path '*/.n2i-dev-cycle/config' -not -path '*/node_modules/*' 2>/dev/null | head -1); if [ -n "$f" ]; then . "$f" 2>/dev/null; echo "CONFIG=$f; BRANCH_PREFIX=${BRANCH_PREFIX:-unset}; DEFAULT_SCOPE=${DEFAULT_SCOPE:-unset}; FORGE_OVERRIDE=${FORGE:-unset}; BACKEND_VALIDATE_CMD=${BACKEND_VALIDATE_CMD:+set}; FRONTEND_VALIDATE_CMD=${FRONTEND_VALIDATE_CMD:+set}; E2E_CMD=${E2E_CMD:+set}; BACKEND_STANDARDS=${BACKEND_STANDARDS:-unset}; FRONTEND_STANDARDS=${FRONTEND_STANDARDS:-unset}; MIGRATION_STANDARDS=${MIGRATION_STANDARDS:-unset}"; else echo "CONFIG=none (see n2i-dev-cycle.config.example)"; fi`
- E2E: !`E2ECFG=$(find . -maxdepth 3 \( -name 'playwright.config.*' -o -name 'cypress.config.*' \) -not -path '*/node_modules/*' 2>/dev/null | head -1); if [ -n "$E2ECFG" ]; then echo "E2E=$(dirname "$E2ECFG")"; else E2EDIR=$(find . -maxdepth 3 -type d \( -name 'e2e' -o -path '*/tests/e2e' \) -not -path '*/node_modules/*' 2>/dev/null | head -1); [ -n "$E2EDIR" ] && echo "E2E=$E2EDIR" || echo "E2E=none"; fi`

> **Note:** values above are *detected context*, not exported shell variables. In later
> Bash steps, substitute the literal detected path/value (or re-`source` the config file
> and re-derive `SLN`/`FRONTEND`) — do not rely on `$SLN`, `$FRONTEND`, `$FORGE_CLI`, etc.
> persisting across tool calls.
> Per-repo config lives in `.n2i-dev-cycle/config` at the repo root (a gitignored
> `.n2i-dev-cycle/` folder — anything repo-scoped and skill-generated goes there).
> If a `FORGE` override is set in config, it wins over remote-URL detection.
> `DB_ENGINE` resolves as: config value (`postgres`/`sqlserver`) → else migrator call in
> code → else csproj packages → else **default `postgres`**. Postgres is the current
> standard; only legacy apps still on SQL Server set `DB_ENGINE=sqlserver` in their repo's
> `.n2i-dev-cycle/config`. When detection lands on the ambiguous default, confirm with the
> user in Phase 1 before emitting any DDL.
> **Non-.NET/Angular stacks:** detection degrades gracefully (`BACKEND=none` etc). Set
> `BACKEND_VALIDATE_CMD` / `FRONTEND_VALIDATE_CMD` / `E2E_CMD` and the `*_STANDARDS`
> keys in config; `DB_ENGINE` / `references/migrations.md` are DbUp-specific — ignore
> them and use `MIGRATION_STANDARDS` instead. See README "Using with a different stack".

## Input Parsing

`$ARGUMENTS` determines the mode:

| Input | Mode | Action |
|---|---|---|
| `#17` or `17` (bare number) | **Ticket** | `$FORGE_CLI issue view <number>` → extract title, description, acceptance criteria. If `FORGE_CLI=none`, ask user to paste ticket title/description. Spec'd mode — run the alignment gate (`references/brainstorming.md`). |
| `"let's discuss X"`, a wiki link, a rough `docs/` markdown, meeting/call notes — no ticket yet | **Discussion** | Run brainstorming (`references/brainstorming.md`) → produce a ticket / sub-ticket draft for Product review. Stop there unless told to continue. |
| `"some description or task"` | **Prompt** | Use as-is for requirements |
| `"review and continue migration"` | **Migration** | Read `MIGRATION_DOCS` (detected) → find first ⬜ sub-phase → use as requirements. If `MIGRATION_DOCS=none`, ask user for the migration doc path. |
| `@path/to/doc.md` | **Document** | Read file → extract requirements |
| `"fix: [details]"` or `"feedback: [details]"` | **Feedback** | Skip to Phase 7 (Feedback Loop). Search memory for prior context. |

If input is ambiguous, ask.

## Scope Selection

Leading token of `$ARGUMENTS` may set scope (strip it before mode parsing):

| Token | Scope |
|---|---|
| `-b` / `b` / `--backend` | backend only |
| `-f` / `f` / `--frontend` | frontend only |
| `-bf` / `--both` | both |

If no token: infer from detection —
- BACKEND=none → frontend
- FRONTEND=none → backend
- both present → ask user which (default both)

`SCOPE` gates later phases:
- Phase 3 Plan: emit only the matching **Backend** / **Frontend** subsections.
- Phase 4 Implement: skip steps for the excluded side.
- Phase 5 Validate: run only the matching block.

---

## Phase 1 — Ingest, Classify & Align

**Load `references/brainstorming.md` first.** It holds the classification table,
the hard gate, and both entry flows.

**Hard gate:** no branch, no plan, no code, no scaffold until the user approves
the intent — the ticket draft (discussion mode) or the restated spec (spec'd
mode).

1. **Detect project** from dynamic context above. Read project CLAUDE.md if present
   (try `CLAUDE.md`, then `claude.md` in repo root), and `.n2i-dev-cycle/notes.md` if
   present. If `MIGRATION_DOCS` found, read it (plus `docs/phase3-porting-guide.md` if
   present). If BACKEND=none and FRONTEND=none → ask user for project context.

2. **Sync project config** — `.n2i-dev-cycle/config` under the repo root
   (`git rev-parse --show-toplevel`). The `.n2i-dev-cycle/` folder is gitignored and holds
   everything repo-scoped the skill generates (`config`, the `progress.md` checkpoint
   ledger, an optional hand-written `notes.md`). Skip this whole step if not in a git
   repo — carry detected values in memory.

   **First run for this repo** (`CONFIG=none`): propose a `config` file from detected values:
   - `DB_ENGINE` — from the detection chain; if it landed on the ambiguous default (both
     Npgsql and SqlServer packages — an app mid-migration) ask "Postgres or SQL Server?" first
   - `BRANCH_PREFIX` — config value, else git-user initials if derivable, else omit
   - `MIGRATION_DOC` / `FORGE` — only if already known (migration doc read this run, or
     remote detection was `unknown` and the user named a forge)

   Show the exact file contents and target path (`<root>/.n2i-dev-cycle/config`), plus the
   one `.gitignore` line (`.n2i-dev-cycle/`). Ask once.
   - **Yes** → create the folder + file; append `.n2i-dev-cycle/` to the repo's `.gitignore`
     if missing and tell the user to commit that `.gitignore` change (the only tracked file
     touched).
   - **No** → carry the detected values in memory for this run; don't re-ask this session.

   **Later runs** (config exists): it's the source of truth. If `DB_ENGINE` holds an
   explicit value and code detection now disagrees (e.g. the repo finished migrating to
   Postgres), surface the mismatch and ask whether to update that key. Never rewrite the
   file without consent.

   A `MIGRATION_DOC` describing a legacy SQL Server source does **not** change the target —
   new DDL follows the current `DB_ENGINE`, not the legacy dialect.

   **Skill-state hygiene** (every run, before the folder is used): confirm `.n2i-dev-cycle/`
   is in the repo's `.gitignore` — add the line and tell the user to commit it if it's
   missing (an older repo, or the folder predates the entry). If `.n2i-dev-cycle/notes.md`
   exists, scan it for credential shapes — a password in a URL, `Bearer ` tokens, PEM
   headers, long `key=` / `secret=` literals. `notes.md` content flows into ledger lines,
   memory observations, and handover summaries, so a secret left there leaks into durable
   stores. Warn the user; don't block. (The `hooks/pre-push-secret-scan.py` companion
   hook runs this check automatically at push time; this pass is the fallback.)

3. **Fetch requirements** based on input mode (see Input Parsing above). Read the
   ticket and every linked wiki page / `docs/` markdown in full.

4. **Classify** the work — spike / bounded / architectural (`brainstorming.md`).
   Say the class out loud so the user can override.

5. **Search memory** for prior work on this ticket/topic:
   - `observation_search` with ticket number or key terms
   - `memory_search` for related past decisions
   - `observation_search` `#instinct` filtered to the detected stack
     (`#stack:<backend/frontend stack>`, `#stack:any`) — surface the top ~5 by
     confidence as working rules for this cycle (`references/improve.md`)
   - Surface relevant context to avoid re-deriving

6. **Take the path** (`brainstorming.md`):
   - **Discussion mode** (no finalized ticket): run the brainstorming flow →
     ticket / sub-ticket draft for Product review → **stop** unless told to
     continue. Brainstorming and building are normally separate sessions.
   - **Spec'd mode** (ticket already Product-reviewed): run the **alignment
     gate** — restate in 3-5 bullets (what changes, entities/features/endpoints,
     `DB_ENGINE`, prior memory), then list every gap / contradiction / ambiguity
     you actually see. Do not re-brainstorm a finalized spec. Get one explicit
     approval, then Phase 2.

7. **Set session title** via `set_session_title`: `<ticket-number>: <short desc>`
   (e.g. `17: add user name to invoice PDF`). Skip silently if the tool is unavailable.

8. **Load `references/execution.md`** (model selection, delegation, checkpoint
   ledger, memory milestones — stays relevant through Ship). **Start / resume the
   checkpoint ledger:** if `.n2i-dev-cycle/progress.md` already names this ticket,
   read it and resume at the first incomplete phase instead of restarting. If it
   names a *different* ticket whose last line shows shipped/merged, move it to
   `.n2i-dev-cycle/archive/progress.<slug>.md` and start a fresh ledger.

---

## Phase 2 — Branch Management

1. Resolve `BRANCH_PREFIX`: config value → else derive from git user
   (`git config user.name` initials, lowercased) → else `dev/`.

2. Check current branch vs ticket/task:
   - If ticket mode: expected branch pattern is `<BRANCH_PREFIX><ticket-number>-<slug>`
     (e.g. with prefix `mb/` → `mb/17-add-user-name-to-kashaf-pdf`)
   - If current branch matches ticket → proceed
   - If current branch is `main` or doesn't match:
     - Suggest branch name based on ticket/prompt
     - Ask user: create this branch, modify name, or "I'll create it myself"
     - In the same question, offer isolation:
       **"Work on the branch in place, or set up an isolated git worktree?"**
       Default in place for small/medium tickets. Worktree is worth it for long
       or risky features, or a multi-session/multi-machine effort.
     - Wait for confirmation before proceeding

3. **Worktree, only if chosen:** first detect existing isolation
   (`git rev-parse --git-dir` vs `--git-common-dir` differ, and not a submodule)
   — if already in one, skip creation. Otherwise prefer a native worktree tool;
   else `git worktree add .worktrees/<branch> -b <branch>`. Verify `.worktrees/`
   is gitignored (add the line + commit it if missing) before creating.

4. Never force-create or switch branches, or create a worktree, without explicit
   user approval.

---

## Phase 3 — Plan & Approve

**Load the standards for the active `SCOPE` first** (they stay in context through Phase 5):
- backend in scope → read `references/backend-standards.md` + `references/security.md`
- frontend in scope → read `references/frontend-standards.md`
- plan includes a migration script → read `references/migrations.md`

**Repo-owned standards override.** If `BACKEND_STANDARDS` / `FRONTEND_STANDARDS` /
`MIGRATION_STANDARDS` is set in config, read that repo file as authoritative for the
side and skip the matching skill reference (the reference only fills gaps the repo
file leaves). The working directory's own `CLAUDE.md` auto-loads and wins on any
conflict regardless. Repos on a non-.NET/Angular stack point these at their own
convention files (often `backend/CLAUDE.md`, `web/CLAUDE.md`) — see the README
"Using with a different stack".

**Load `references/planning.md`** and produce the implementation plan in that
shape — `SCOPE` subsections only, concrete content (no placeholders), a scope
estimate, and a self-review against the spec before you present it.

**Wait for user approval before proceeding.** User may refine, add, or remove items.

---

## Phases 4–6 — Implement · Validate · Handover

**Load `references/build-loop.md`.** It carries the full procedure for all three
phases — the build order and RED→GREEN loop, intra-phase review checkpoints, the
validate commands + noise handling + pre-push review, and the handover summary
(what changed / what to test / limitations / E2E coverage / memory). Discipline
refs still load per phase: `references/tdd.md` at Phase 4, `references/verification.md`
at Phase 5.

Nothing in Phases 4–6 runs until the Phase 3 plan is approved — a discussion- or
planning-only invocation never loads `build-loop.md`.

---

## Phase 7 — Feedback Loop

**Load `references/debugging.md`.** No fix without root-cause investigation first;
symptom fixes are failure. Its "Phase 7 orchestration" section holds the per-finding
loop (root cause → failing repro test → one fix → re-validate → report), the
three-failed-fixes stop rule, parallel dispatch for independent findings, and the
`"fix: [details]"` cold-start resume (read `progress.md` + `git log`, search memory,
resume at the first incomplete phase). Repeat until the user is satisfied.

---

## Phase 8 — Ship & CI

**Load `references/finishing.md`.** Only when the user explicitly asks to ship. It
holds all six steps: full suite green → confirm base branch → push + MR (secret-scan
hook where installed) → CI root-cause → migration-doc update → after-merge branch and
worktree cleanup, plus the final memory observation and ledger line. The ledger is
archived at the end of Phase 9.

---

## Phase 9 — Improve

**Load `references/improve.md`.** Runs once, after the branch is merged and Phase 8
cleanup is done. Default-on; skip only if the user says so or the cycle produced
nothing reusable. It holds the flow: distill 1–3 patterns that will recur →
de-dupe against existing `#instinct` observations → record each (statement /
trigger / confidence / scope tags) → propose a promotion PR when one recurs at
`med`+ confidence → write the final ledger line and archive `progress.md` to
`.n2i-dev-cycle/archive/`. Memory tools unavailable → skip the instinct steps,
still archive the ledger.

---

## Cross-Cutting Mechanics

Model selection, subagent delegation, the checkpoint ledger, and memory
integration live in **`references/execution.md`** — loaded once at Phase 1 step 8,
stays relevant through Ship. Pointers:

- **Model** — cheapest model that fits the step; state it when dispatching a
  subagent (omitted → inherits this session's, usually priciest).
- **Delegate** only verbose-in / small-out / independent work: E2E runs (Phase 6),
  independent Phase 7 findings / Phase 8 CI jobs, the pre-push review. The spec,
  the ticket / MR-PR prose, and the Phase 4 TDD loop stay in the main agent.
- **Ledger** — `.n2i-dev-cycle/progress.md`: one line per phase and per Phase 4
  checkpoint as it lands (test-first units record the RED line before the GREEN
  commit). On skill start, resume at the first incomplete phase. After compaction,
  it and `git log` outrank recollection.
- **Memory** — best-effort claude-mem observations at milestones + an
  `observation_search` / `memory_search` at skill start. Skip silently if the
  tools are unavailable; the ledger is the durable fallback.

## General Development Standards

Baseline conventions for all N2I projects, split into reference files under `references/`.
Load only what the active phase / `SCOPE` needs (each phase names its files; re-read if they drop from context).
The repo's own `CLAUDE.md` wins on any conflict.

| File | Read when | Contents |
|---|---|---|
| `references/brainstorming.md` | Phase 1, always | spike/bounded/architectural classification, hard approval gate, discussion→ticket flow, spec'd→alignment gate |
| `references/planning.md` | Phase 3, always | implementation-plan format (backend/frontend/tests/migration), no-placeholders rule, plan self-review |
| `references/build-loop.md` | Phase 4, always | the Implement→Validate→Handover procedure: build order + RED→GREEN loop, checkpoint table, validate commands + noise handling + pre-push review, handover summary format |
| `references/tdd.md` | Phase 4, and every bug fix | RED-GREEN-REFACTOR iron law, what's test-first vs exempt scaffolding, rationalization table, red flags |
| `references/verification.md` | Phase 5, any "done" claim | evidence-before-claims gate, claim→proof table, red flags |
| `references/debugging.md` | Phase 7, Phase 8 CI | root-cause-first 4 steps, boundary instrumentation, 3-fix→question-design rule, parallel dispatch, Phase 7 per-finding loop + `fix:` resume |
| `references/finishing.md` | Phase 8 | ship gate, suite green → base confirm → push + MR → CI → branch/worktree cleanup → final memory + ledger line |
| `references/improve.md` | Phase 9 | what to distill, instinct shape (statement/trigger/confidence/scope), near-duplicate search, promotion-to-reference PR |
| `references/backend-standards.md` | backend in scope | 7-file entity scaffold, entity/ModelConfiguration/service/controller patterns, wire-up, unit testing, C# code quality, backend mistakes |
| `references/security.md` | backend in scope | tenant isolation, `ResolveWriteContext` pattern, cross-org write checks, FK validation — non-negotiable |
| `references/migrations.md` | plan has a migration script | DbUp, Postgres + SQL Server dialects, filename/naming rules, migration mistakes |
| `references/frontend-standards.md` | frontend in scope | Angular file structure, service/component patterns, rich-UI choices, mobile-first, frontend mistakes |

The standards and discipline references each end with a scoped "Common Mistakes to Avoid"
list, so a frontend-only ticket never loads backend/security/migration gotchas.

`references/execution.md` is the exception to lazy-loading — it loads once at
Phase 1 step 8 and stays through Ship (see Cross-Cutting Mechanics above).

---

## Project-Specific Overrides

Detection (Dynamic Context) handles paths generically — no project name needed. Everything
project-specific is read from the repo you're in, nothing from a cross-repo file:

1. `.n2i-dev-cycle/config` — the KEY=VALUE settings (already loaded in Dynamic Context).
2. `.n2i-dev-cycle/notes.md` in the repo, if present — free-text personal gotchas
   (gitignored, this repo only). Read it when it exists; never require it.
3. The repo's own `CLAUDE.md` — team-shared conventions and overrides, wins on conflict.

Repo quirks worth writing down: team-facing ones go in `CLAUDE.md`, personal ones in
`.n2i-dev-cycle/notes.md`. There is no skill-dir roster of repos.
