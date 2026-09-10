# Changelog

## Unreleased

Batch of improvements informed by a review of the [ecc](https://github.com/affaan-m/ecc)
skill — RED-evidence capture, an instinct/learning loop, leaner always-loaded
context, and enforcement hooks.

### Added
- **Phase 9 — Improve.** After a branch merges, the cycle distills 1–3 reusable
  patterns into `#instinct`-tagged memory observations (statement / trigger /
  confidence `low`–`high` / stack + domain scope tags). Phase 1 step 5 reads them
  back, filtered to the detected stack, as working rules for the new cycle. A
  pattern that recurs across cycles at `med`+ confidence is proposed as a one-line
  PR to the matching `references/*.md` "Common Mistakes" list — never an automatic
  edit. New `references/improve.md`; `SKILL.md` + `SKILL.qwen.md` Phase 9 and Phase
  1 step 5; `references/execution.md` memory-milestone table; README.
- **Companion hooks** in `hooks/` — two Python hooks that enforce lifecycle gates
  outside the model. `pre-push-secret-scan.py` (`PreToolUse`/Bash) blocks a `git
  push` when the outgoing commits or `.n2i-dev-cycle/config` / `notes.md` contain a
  secret shape (AWS/GitHub/Slack tokens, private keys, passwords in URLs, quoted
  `api_key=`-style assignments). `verify-gate.py` (`Stop`, opt-in) blocks a stop
  whose final turn claims a green build/test with no build or test command in that
  turn. Both additive — the prose gates in `verification.md` / `finishing.md`
  remain the fallback. A secret block lists each file:line and, for a false
  positive, echoes the exact `git push` for the user to run in their own terminal
  (the hook only gates the agent). Install via `hooks/settings.snippet.json`; needs
  `python3`. Output-noise trimming stays external (`rtk` / starter-kit).
- **RED evidence in the checkpoint ledger.** Each Phase 4 test-first unit records
  the failing test name and reason before its GREEN commit
  (`Phase 4: <unit> — RED <test> failed "<reason>" → GREEN (<commit>)`), so a later
  session or a different machine can confirm test-first order from the ledger
  instead of trusting recollection. `references/tdd.md` (Verify RED step + red
  flag), `references/verification.md` (claim→proof row + common mistake), `SKILL.md`
  Phase 4 / ledger / memory milestones, mirrored in `SKILL.qwen.md`.
- **Phase 1 skill-state hygiene check.** Every run confirms `.n2i-dev-cycle/` is in
  the repo's `.gitignore` (adds the line if missing) and scans an existing
  `.n2i-dev-cycle/notes.md` for credential shapes, since `notes.md` content flows
  into ledger lines, memory observations, and handover summaries. Warns, never
  blocks. `SKILL.md` + `SKILL.qwen.md` Phase 1, README.

### Changed
- **Cross-cutting machinery moved out of `SKILL.md`** — model selection, subagent
  delegation, the checkpoint ledger, and memory milestones now live in a new
  `references/execution.md`, loaded once at Phase 1 step 8 and kept through Ship.
  `SKILL.md` keeps a short pointer block and sheds ~55 lines of always-loaded
  context. No behaviour change. `SKILL.qwen.md` is unchanged — the Qwen variant is
  a deliberately single-file manifest.
- **Checkpoint-ledger lifecycle.** Phase 9 archives `progress.md` to
  `.n2i-dev-cycle/archive/progress.<slug>.md` as its last step, so the next ticket
  in the repo starts on a clean ledger and finished ledgers stay out of routine
  `find` / `grep`. Phase 1 step 8 archives a stale ledger left by a different,
  already-shipped ticket instead of resuming it. `finishing.md`, `execution.md`,
  both manifests.

## 1.3.0 (2026-09-09)

### Added
- `SKILL.md` **Delegation & Context** section — what goes to a subagent (E2E runs,
  independent Phase 7/8 failures, pre-push review) vs what stays in the main agent
  (reading the ticket/wiki/docs, writing the ticket draft and MR/PR description, the
  Phase 4 TDD loop), with the reasoning.
- Phase 5 guidance to keep test-runner output out of context — quietest reporter,
  summary line only on green, full output only on a non-zero exit (fallback for
  setups without a token-trimming hook).
- `references/verification.md` claim→proof row for subagent-run E2E specs.
- README optional prerequisite + notes: a `PreToolUse`/`Bash` output-filter hook
  ([claude-code-starter-kit](https://github.com/muneebrbaig/claude-code-starter-kit#hooks)
  or `rtk`) for automatic test/build noise trimming, and a section on what the
  lifecycle delegates to subagents versus what stays in the main agent.

### Changed
- Phase 6 runs affected E2E specs via a subagent (minimum context in, pass/fail +
  failure traces out) instead of in the main agent.

## 1.2.0 (2026-09-03)

### Added
- `references/brainstorming.md` — spike/bounded/architectural classification, a hard
  approval gate before any branch/plan/code, the discussion→ticket-draft flow, and the
  spec'd→alignment-gate flow for a ticket brainstormed in an earlier session.
- `references/tdd.md` — RED-GREEN-REFACTOR iron law, what is test-first (service/controller/
  component logic, bug repros) vs exempt scaffolding (entity props, ModelConfiguration, DI,
  migration DDL), rationalization table, red flags.
- `references/verification.md` — evidence-before-claims gate, claim→proof table with the
  N2I commands, red flags.
- `references/debugging.md` — root-cause-first four steps, component-boundary instrumentation,
  the three-failed-fixes → question-the-design rule, and parallel `Agent` dispatch for
  independent failures.
- `references/finishing.md` — full suite green → confirm base branch → push + MR → CI
  root-cause → local branch and worktree cleanup after merge.
- `SKILL.md` **Model Selection** table — cheap model for scaffolding/transcription, standard
  for integration/test design, most capable for architecture/ambiguous debugging/pre-push
  review; state the model on every subagent dispatch.
- `SKILL.md` **Checkpoint Ledger** — `.n2i-dev-cycle/progress.md`, a plain-text phase ledger
  that survives context compaction and cross-session `fix:` / multi-machine re-entry;
  resumed at Phase 1.
- Phase 2 offers an isolated `git worktree` alongside the branch-name choice (default off
  for small/medium tickets).
- **Stack adaptation** — config keys `BACKEND_VALIDATE_CMD` / `FRONTEND_VALIDATE_CMD` /
  `E2E_CMD` (shell snippets Phases 5-6 run instead of the `dotnet`/`npm` defaults) and
  `BACKEND_STANDARDS` / `FRONTEND_STANDARDS` / `MIGRATION_STANDARDS` (point Phase 3 at a
  repo's own convention files, e.g. `backend/CLAUDE.md`, as authoritative over
  `references/*`). The skill now runs on any stack without a fork.

### Changed
- README: "Embedded References" splits the five stack-agnostic discipline refs from the
  four .NET/Angular standards refs; new "Using with a different stack" section replaces
  "Adapting for Your Projects"; Usage section gains a "Discussion / Brainstorm" entry and
  notes the classify + approval gate on every entry point, the alignment gate for tickets,
  and ledger-aware Fix mode; the phase table's Validate row and a full `config` key table
  reflect the new command/standards keys.
- `references/tdd.md` + `references/verification.md` command tables noted as .NET/Angular
  defaults; tdd.md test-first/exempt table reworded stack-neutrally.
- `references/migrations.md` Postgres heading degeneralized (no project codenames).
- Phase 1 renamed **Ingest, Classify & Align**; adds classification, the alignment gate for
  finalized tickets, and ledger start/resume.
- Phase 3 adds a **No Placeholders** rule (concrete fields/signatures/test names) and a
  **Plan Self-Review** pass (spec coverage + naming consistency).
- Phase 4 reordered to test-first for business logic; scaffolding steps marked exempt. The
  intra-phase checkpoint table folds tests into the service/controller checkpoint.
- Phase 5 wraps validation in the verification gate.
- Phase 7 rewritten around systematic debugging + parallel dispatch.
- Phase 8 rewritten around the finishing flow (base-branch confirmation, MR, cleanup).
- Phase 6 e2e step: reviewing the change's e2e impact is now mandatory (a spec the change
  breaks or makes stale must be fixed, however small the change); writing a *new* spec stays
  conditional (skippable for minor changes with the user's agreement, recorded in handover);
  affected specs are run against a dev/throwaway DB where possible.
- Phase 5 pre-push code review: findings now handled with technical-rigor posture (restate,
  verify, push back on wrong/YAGNI); a finding that's a real bug routes through
  `debugging.md` + `tdd.md`. The review itself is unchanged (`engineering:code-review` off
  the local diff, best-effort).
- Input Parsing gains a **Discussion** mode (chat topic / wiki / rough doc, no ticket yet).
- `.n2i-dev-cycle/` folder description updated to name `progress.md`.
- Internal project codenames removed from the skill/reference bodies (kept only the
  README origin credit) — replaced with generic phrasing ("an app mid-migration",
  "one multi-tenant codebase", "meeting/call notes", "invoice PDF").

- `SKILL.qwen.md` synced — same phase changes, discipline layer inlined (no
  `references/` split): classification + alignment gate, TDD block, verification
  gate, systematic-debugging block, finishing flow, Model Selection + Checkpoint
  Ledger sections, a compact Discipline Red Flags list, and a pre-push review step
  (which the Qwen variant previously lacked).

## 1.1.0 (2026-09-03)

### Added
- `DB_ENGINE` config key (`postgres` default, `sqlserver` for legacy apps, `auto` to detect)
- DB engine detection in Dynamic Context (config → migrator call → csproj packages → default
  postgres); migrator match covers `.PostgresqlDatabase(`/`.SqlDatabase(`/`.SqlServerDatabase(`
  and `UseNpgsql`/`UseSqlServer`
- Postgres DbUp migration template (quoted PascalCase, `GENERATED BY DEFAULT AS IDENTITY`,
  `timestamptz`, `IF NOT EXISTS`, no `GO`) alongside the existing SQL Server form

### Changed
- Development standards moved out of `SKILL.md` into `references/backend-standards.md`,
  `references/security.md`, `references/migrations.md`, `references/frontend-standards.md`.
  Phase 3 loads only the files matching the active scope, so a frontend-only ticket no longer
  pays for backend/security/migration text. `SKILL.md` drops from ~750 to ~390 lines. Each
  reference file carries its own scoped "Common Mistakes to Avoid" list. Qwen variant unchanged
  (single-file, keeps standards inline).
- Per-repo config now lives in a gitignored `.n2i-dev-cycle/` folder at the repo root
  (`config` inside it, plus an optional hand-written `notes.md`) — one `.gitignore` line,
  room for future repo-scoped state.
- Phase 1 "Sync project config" step: on the first run in a repo it proposes
  `.n2i-dev-cycle/config` from detected values, writes it at the git root with consent, and
  adds `.n2i-dev-cycle/` to `.gitignore`. Later runs treat the config as source of truth and
  flag `DB_ENGINE` drift (e.g. repo finished migrating to Postgres) before changing anything.
- Config template file: `n2i-dev-cycle.config.example`.

### Removed
- The skill-dir `projects.local.md` roster. Its content was either auto-detected, already
  in `.n2i-dev-cycle/config`, or belonged in the repo's `CLAUDE.md` / `.n2i-dev-cycle/notes.md`.
  Every run had loaded every repo's block; now the skill reads only the repo it's in.

## 1.0.0 (2026-06-18)

### Added
- Initial release
- 8-phase development lifecycle: Ingest, Branch, Plan, Implement, Validate, Handover, Feedback, Ship
- 5 input modes: ticket (GitLab/GitHub), prompt, migration continuation, document, feedback re-entry
- Generic auto-detection of backend solution, frontend dir, and forge (no hardcoded project names)
- General development standards for vertical-slice .NET + Angular architecture
- Memory integration for cross-session continuity
- Branch management with user confirmation
