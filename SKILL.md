---
name: n2i-dev-cycle
description: Full development lifecycle — ticket/prompt to shipped code. Handles planning, implementation, validation, feedback loops, and CI fixes across N2I projects. Invoke with a ticket number, prompt, or document reference.
allowed-tools: Bash, Read, Edit, Write, Agent, Grep, Glob, mcp__plugin_claude-mem_mcp-search__observation_add, mcp__plugin_claude-mem_mcp-search__observation_search, mcp__plugin_claude-mem_mcp-search__memory_search, mcp__ccd_session_mgmt__set_session_title
---

# N2I Development Cycle

Full-lifecycle development skill. 8 phases: Ingest/Classify/Align → Branch → Plan → Implement → Validate → Handover → Feedback → Ship.

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

3. **Fetch requirements** based on input mode (see Input Parsing above). Read the
   ticket and every linked wiki page / `docs/` markdown in full.

4. **Classify** the work — spike / bounded / architectural (`brainstorming.md`).
   Say the class out loud so the user can override.

5. **Search memory** for prior work on this ticket/topic:
   - `observation_search` with ticket number or key terms
   - `memory_search` for related past decisions
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

8. **Start / resume the checkpoint ledger** (see Checkpoint Ledger below). If
   `.n2i-dev-cycle/progress.md` already names this ticket, read it and resume at
   the first incomplete phase instead of restarting.

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

Produce a structured implementation plan. Format:

### Requirements Summary
- Bullet list of what the ticket/prompt asks for

### Implementation Plan

**Backend:**
- Entities to create/modify (list fields, FKs, business rules)
- Services to create/modify (list methods, validation logic)
- Controllers to create/modify (list endpoints, auth levels)
- Migration scripts needed (table creates/alters) — note target dialect (`DB_ENGINE`)
- Wire-up steps (DI, ModelBuilder)

**Frontend:**
- Models/interfaces to create/modify
- Services to create/modify
- Components to create/modify (list vs form vs report vs calendar)
- Route changes
- Sidebar/nav changes

**Tests:**
- Unit tests needed (list test cases)
- What to verify manually

**Migration-specific** (only if a `MIGRATION_DOC` is configured):
- Legacy source files to reference
- Fields to port vs drop
- Business rules to port
- Sub-phase status update needed

### Questions / Ambiguities
- List anything unclear — ask before implementing

### Estimated Scope
- Files to create: N
- Files to modify: N
- Migration scripts: N
- Unit tests: N

### No Placeholders

Every item carries the concrete content, not a description of it:
- entity fields with types + FKs, not "the fields"
- service method signatures + validation rules, not "validation logic"
- exact endpoint routes + auth level, not "the endpoints"
- named test cases, not "unit tests for the above"

An item an implementer can't act on without guessing is a plan failure — fix it
before presenting.

### Plan Self-Review

Before presenting: re-read the spec, confirm every requirement maps to a plan
item (list any gaps), scan for the placeholders above, and check names /
signatures are consistent across sections — a method called one thing under the
entity and another under tests is a bug. Fix inline.

**Wait for user approval before proceeding.** User may refine, add, or remove items.

---

## Phase 4 — Implement

**Load `references/tdd.md`.** Business logic is test-first: failing test → run it
→ watch it fail for the right reason → minimal code → green → refactor. Code
written before its test gets deleted and redone from the test. Scaffolding (entity
props, `ModelConfiguration`, DI wire-up, migration DDL) is exempt — but the
service/controller/component tests that follow must fail if the scaffold is wrong.

Execute the approved plan following the `references/` standards loaded in Phase 3
(re-read a file if it dropped out of context). Order — each logic step is
RED→GREEN before the next:

1. **Backend entity** + `ModelConfiguration` (scaffold, exempt)
2. **Migration script** (DbUp SQL — scaffold, exempt)
3. **Wire-up** (DI + ModelBuilder — scaffold, exempt)
4. **Service** — test-first per method
5. **Controller** — test-first per endpoint (auth, shape, status)
6. **Frontend models + service**
7. **Frontend components** — test-first where the project tests component behaviour
8. **Route + nav wiring**

**Record memory observation** and **append a ledger line** after each major
milestone (entity done, service+tests green, frontend done, etc.).

If something goes sideways mid-implementation — STOP, reassess, inform user, re-plan if needed. Don't push through blindly.

### Intra-phase checkpoints (mandatory)

After completing each logical unit, **stop and ask the user to review** before continuing. This keeps human reviewers and AI agents in sync — especially across machines and sessions.

| Checkpoint | After completing |
|---|---|
| Backend scaffold | Entity, DTOs, requests, config, migration, DI + wire-up, build clean |
| Backend service + controller | Methods and endpoints built test-first, all tests green |
| Frontend models + service | TypeScript interfaces/enums, service class, barrel exports |
| Frontend components | List + form components built (test-first where applicable), routes swapped, sidebar/nav wired, `ng build` clean |

At each checkpoint, summarize what was built, **append the ledger line**, and ask: **"[Unit] done. Want to review before I continue?"** The user may review, request changes, push/commit, or say continue. **Never skip ahead silently.**

---

## Phase 5 — Validate

**Load `references/verification.md`.** The gate: before saying "green" / "passing"
/ "done", you must have run the exact command **in this message** and read its
output — exit code, failure count. No "should pass", no run from before the last
edit, no "linter passed" standing in for "build passed".

Run all validation commands for the active `SCOPE`. Loop until green.

**If `BACKEND_VALIDATE_CMD` / `FRONTEND_VALIDATE_CMD` is set in config, run that
snippet for the side instead of the block below** (it should cover format + build +
unit tests and exit non-zero on any failure). Otherwise the .NET + Angular default:

```bash
# Backend — only if SCOPE includes backend && BACKEND != none
dotnet format "$SLN"
dotnet build "$SLN" -v minimal      # zero new errors
dotnet test "$SLN" -v minimal       # all pass, 0 failed

# Frontend — only if SCOPE includes frontend && FRONTEND != none
cd "$FRONTEND"
npm run build                       # ng build → zero errors
npm test -- --watch=false           # all pass
```

If validation fails:
1. Fix the issue
2. Re-run validation
3. Repeat until all green
4. Never skip or ignore failures

### Pre-push review

Once green, before Phase 6: ask user "Run engineering:code-review on this diff before pushing?"
Default yes if unsure. Reviewing here — against the local diff, before an MR/PR exists — catches
scope-creep and correctness issues while they're still a `git commit --amend` or a clean follow-up
commit away, instead of a fix-up commit sitting permanently in MR history after the fact. It also
skips triggering a CI run against a state you already know you're about to patch.

- If `engineering:code-review` isn't in the available-skills list this session, say so and skip
  silently — don't block the lifecycle. Offer a manual review pass instead if the user still wants one.
- If accepted and available, invoke it against the diff: `git diff <base-branch>...HEAD` (backend
  and/or frontend paths per SCOPE), not a PR URL — no MR/PR exists yet at this point.
- Handle findings with technical rigor, not performative agreement: restate each finding, verify
  it against the codebase, push back with reasoning if it's wrong or YAGNI, ask the user if it
  conflicts with a prior decision. A finding that's a real bug goes through `references/debugging.md`
  (root cause first) and `references/tdd.md` (failing test first).
- Fix the accepted findings, then **re-run this Phase 5 validation loop** (verification gate)
  before moving to Phase 6.
- Optionally ask: "Compress findings into caveman-review one-liners for the MR/PR description?"
  If yes and `caveman:caveman-review` is available, run it over the findings and fold the output
  into Phase 6's handover summary. If not available, skip silently — the raw findings still stand.
  (No MR comment thread exists yet to post to — that's why this differs from posting comments.)

---

## Phase 6 — Handover

Summarize for user:

### What Changed
- Files created/modified (grouped by concern)
- Migration scripts added

### What to Test Locally
- Specific flows to verify (step-by-step)
- Edge cases to check
- Mobile/responsive checks if UI was touched

### Known Limitations
- Anything deferred or out of scope
- Dependencies on other work

### E2E Coverage
Only if `E2E != none`. **Reviewing the change's e2e impact is mandatory; writing a
new spec is not always.**
- Map every flow the change touches to the existing specs under `E2E`.
- A spec the change **breaks or makes stale** → fix or update it. Not optional,
  no matter how small the change.
- A touched flow with **no** spec → build one now (test-first applies), unless
  it's a minor change and the user agrees a spec isn't warranted — record that
  call in the handover.
- Run the affected specs before Phase 8 (via `E2E_CMD` if set, else the project's
  runner) — against a dev DB, or a fresh throwaway DB where the project supports
  one. Where a real run isn't possible, say so rather than claiming coverage.
- Flows already covered and passing → note briefly, no action.

### Memory
- Record handover observation with key details for cross-session continuity

---

## Phase 7 — Feedback Loop

**Load `references/debugging.md`.** No fix without root-cause investigation first —
symptom fixes are failure.

User reports findings from local testing. For each finding:

1. **Root cause first** — read the error fully, reproduce, check recent changes,
   instrument component boundaries on a multi-layer path, trace the bad value
   back to its source (`debugging.md` Steps 1-3).
2. **Failing test** that reproduces it (`tdd.md`).
3. **One fix** at the root cause — no bundled refactoring.
4. **Re-validate** (Phase 5 gate).
5. **Report** what changed; append a ledger line.

**Three fixes that don't hold → STOP.** Question the design with the user, don't
try fix #4.

**Independent findings** (different subsystems, unrelated) → parallel-dispatch one
`Agent` per domain (`debugging.md` → Parallel Dispatch). Not for findings that
might share a cause.

If starting a new session with `"fix: [details]"`:
- Read `.n2i-dev-cycle/progress.md` and recent `git log` — they outrank memory
- Search memory for prior context on this feature/ticket
- Resume from the ledger's first incomplete phase

Repeat until user is satisfied.

---

## Phase 8 — Ship & CI

**Load `references/finishing.md`.** Only when the user explicitly asks to ship:

1. **Full suite green** — the whole suite for the active scope (not `--filter`),
   through the Phase 5 gate. Failures stop the ship.
2. **Confirm the base branch** with the user before the MR — merging or targeting
   the wrong base is expensive to undo.
3. **Push** (ask for confirmation with the exact command shown), then create the
   MR/PR against the confirmed base via the forge CLI, following repo conventions.
   Code review already happened at the end of Phase 5 — this should be clean.
4. **CI failures:** read logs by forge (`glab ci trace` / `gh run view
   --log-failed`; `FORGE_CLI=none` → ask user to paste). Root-cause per
   `debugging.md` — no blind re-push. Multiple independent job failures →
   parallel dispatch. Fix, re-validate locally, push.
5. **Migration mode:** update the `MIGRATION_DOC` status table before the push.
6. **After merge** (with the user's go-ahead): clean up the local branch
   (`git branch -d`, never `-D` unasked) and the worktree if one was created
   (`finishing.md` Step 5).

**Record memory observation** and a final ledger line (shipped, CI green, merged).

---

## Model Selection

Pick the cheapest model that fits the step. State the model when dispatching a
subagent — an omitted model inherits this session's, usually the priciest.

| Work | Model tier |
|---|---|
| Scaffolding, migration DDL, single-file mechanical edits, transcription from a detailed plan | cheap / fast |
| Service/controller/component logic, multi-file integration, test design | standard |
| Architecture, ambiguous debugging, the Phase 5 pre-push review, CI root-cause on a multi-layer failure | most capable |

## Checkpoint Ledger

`.n2i-dev-cycle/progress.md` (inside the gitignored folder). Best-effort — survives
context compaction and cross-session `fix:` / multi-machine re-entry. Skip if not
in a git repo.

- First line: `# <ticket-or-slug> — <one-line goal>`
- One line per phase as it completes: `Phase N: <what landed> (<commit range>)`
- Phase 4 intra-phase checkpoints get a line too.
- On skill start (Phase 1 step 8): if the first line matches the current ticket,
  resume at the first incomplete phase instead of restarting.
- After compaction, `git log` and this ledger outrank your own recollection.

## General Development Standards

Baseline conventions for all N2I projects, split into reference files under `references/`.
Load only what the active phase / `SCOPE` needs (each phase names its files; re-read if they drop from context).
The repo's own `CLAUDE.md` wins on any conflict.

| File | Read when | Contents |
|---|---|---|
| `references/brainstorming.md` | Phase 1, always | spike/bounded/architectural classification, hard approval gate, discussion→ticket flow, spec'd→alignment gate |
| `references/tdd.md` | Phase 4, and every bug fix | RED-GREEN-REFACTOR iron law, what's test-first vs exempt scaffolding, rationalization table, red flags |
| `references/verification.md` | Phase 5, any "done" claim | evidence-before-claims gate, claim→proof table, red flags |
| `references/debugging.md` | Phase 7, Phase 8 CI | root-cause-first 4 steps, boundary instrumentation, 3-fix→question-design rule, parallel dispatch |
| `references/finishing.md` | Phase 8 | suite green → base confirm → push + MR → CI → branch/worktree cleanup |
| `references/backend-standards.md` | backend in scope | 7-file entity scaffold, entity/ModelConfiguration/service/controller patterns, wire-up, unit testing, C# code quality, backend mistakes |
| `references/security.md` | backend in scope | tenant isolation, `ResolveWriteContext` pattern, cross-org write checks, FK validation — non-negotiable |
| `references/migrations.md` | plan has a migration script | DbUp, Postgres + SQL Server dialects, filename/naming rules, migration mistakes |
| `references/frontend-standards.md` | frontend in scope | Angular file structure, service/component patterns, rich-UI choices, mobile-first, frontend mistakes |

Each reference file ends with its own "Common Mistakes to Avoid" list — scoped to that domain,
so a frontend-only ticket never loads backend/security/migration gotchas.

---

## Memory Integration

> **Best-effort.** Uses the claude-mem MCP tools (`observation_add`, `observation_search`,
> `memory_search`). If unavailable in the session, skip memory steps silently — never block
> the lifecycle on them. The `.n2i-dev-cycle/progress.md` ledger is the durable fallback:
> it is plain git-tracked-adjacent text and does not depend on any MCP tool.

Record observations at these milestones using `observation_add`:

| Milestone | Type | What to record |
|---|---|---|
| Plan approved | `⚖` (decision) | Key decisions, scope, approach chosen |
| Entity/feature implemented | `◆` (feature) | What was built, files created, key design choices |
| Validation pass | `○` (discovery) | Build/test status, any issues found and fixed |
| Handover | `✓` (change) | Summary of all changes, what to test |
| Feedback received | `○` (discovery) | User findings, issues reported |
| Fix applied | `●` (bugfix) | What was fixed and how |
| Shipped / CI green | `✓` (change) | Final status, branch pushed, CI result |

Also search memory at skill start (`observation_search`, `memory_search`) to surface prior work on same ticket/feature.

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
