# Changelog

## 1.9.1 (2026-10-03)

### Fixed
- **Migration prompt in `PROJECT-INSTALL.md`.** It no longer runs a plain `git pull` on a
  feature branch, which pulls that branch's upstream and never delivers the change; it
  pulls only on `master` and otherwise asks before merging. A failed `git log @{u}..` check
  on a personal clone (for example no upstream) now counts as unsaved work instead of
  clean. The submodule check accepts the `+` prefix that a moved pointer produces.

## 1.9.0 (2026-10-03)

### Added
- **Project bundling.** `PROJECT-INSTALL.md` explains how to carry the skill inside a
  team repo as a git submodule, so engineers never pull it by hand. It covers setup,
  how updates flow, and a safe migration prompt for engineers who already have a
  personal install.
- **`scripts/project-sync.sh`.** SessionStart hook template to copy into the project.
  It initializes the submodule every session, pulls the tip of `main` at most once a
  week, and links the subagents into the project's `.claude/agents/`. It is silent
  and always exits 0.
- Tests for the hook in `tests/test_project_sync.py`.

## 1.8.0 (2026-10-02)

### Added
- **`n2i-unit-runner` subagent (haiku).** Phase 5's final validate run (format,
  build, unit tests) now goes to this agent, one dispatch per side, backend and
  frontend in parallel. It returns the result, each command with its exit code,
  totals, and failure traces only, and never edits. The Phase 4 TDD loop stays
  in the main agent.
- **Gate evidence from the unit runner.** `verify-gate.py` counts an
  `n2i-unit-runner` dispatch as a run this turn, since its commands live in the
  subagent's own transcript and the hook would otherwise block a true "tests pass".
- Scenario S10 in `evals/scenarios.md`.

## 1.7.0 (2026-10-02)

The skill now ships three named subagents that pin the model and tools for
delegated work. Its approval gate holds against "just do it", and runs that stop
early load less.

### Added
- **Named subagents in `agents/`.** `n2i-e2e-runner` (haiku) runs E2E specs and
  returns a short pass/fail report. `n2i-ci-triage` (sonnet) finds the root
  cause of one failure domain and proposes a fix without editing. `n2i-prepush-reviewer`
  (opus) reviews the diff read-only. None has Edit or Write. If an agent isn't
  installed, the skill falls back to `general-purpose` with an explicit model.
  Claude Code doesn't read agents from inside a skill folder, so the README now
  has a link step for `~/.claude/agents/`.
- **Structural tests in `tests/`.** They check each agent's frontmatter and
  model, that no agent can edit files, that every `n2i-*` name and model in the
  docs matches a real agent, and that each Contents list matches its file's
  headings. Run with `python3 -m unittest discover -s tests`.
- **Behavior scenarios in `evals/scenarios.md`.** Nine scenarios with pass/fail
  checklists for the gate, classification, `fix:` resume, shipping on a red
  suite, scope selection, and delegation.
- **Contents lists** at the top of `SKILL.md`, `SKILL.qwen.md`, `build-loop.md`,
  and `backend-standards.md`.
- **`scripts/install-agents.sh`.** Links every `agents/n2i-*.md` into
  `~/.claude/agents/` and removes links whose target is gone. Safe to re-run.
- **Start-of-run agent check.** Dynamic Context reports `AGENTS=ok` or
  `AGENTS=missing:<names>`. When agents aren't linked, Phase 1 tells the user once
  and points at the install script. It never links anything unasked.
- **README sections** for installing and updating the agents and for choosing a
  session model (Opus or plan mode for Phases 1–3, Sonnet for implementation),
  with an Opus-versus-Sonnet comparison from one bounded ticket.

### Changed
- **The approval gate no longer bends to "just do it".** In our evals, Sonnet and
  Opus both skipped the gate and edited on that phrase, because the "too simple"
  rule lived in a reference neither loaded. `SKILL.md` now says the gate never
  scales down: a one-line change gets a two-bullet design in chat, then approval.
- **Phase 1 replies start with `Class: spike | bounded | architectural`**, with a
  one-line definition of each, so the class is stated even when the
  brainstorming reference isn't loaded.
- **Phase 7 starts by reading `progress.md` and `git log`**, and appends a
  `Phase 7:` ledger line after each fix. Both used to live only in `debugging.md`,
  which Sonnet often skipped.
- **Phase 5 review scales with the class.** A bounded change under about 100
  changed lines that touches no tenant-isolation, auth, or migration code skips
  the prompt. Anything larger or riskier still asks, defaulting to yes. The
  review also covers uncommitted and untracked work, and falls back to
  `n2i-prepush-reviewer` when `engineering:code-review` isn't installed.
- **Phase 4 checkpoints scale with the class.** Bounded changes run without
  mid-phase stops and pause only before a migration. Architectural work keeps
  its stops, now three instead of four. The user can say "no checkpoints" or
  "checkpoint every unit".
- **Memory observations drop from seven milestones to three:** plan approved,
  handover, and shipped. Everything else is a ledger line.
- **`execution.md` loads after the plan is approved**, not at Phase 1, so
  discussion, spike, and gate-only runs skip about 1.5k tokens.
- **Parallel triage is propose-only.** Parallel agents read logs and code, never
  build or run tests in the shared working tree, and the main agent applies each
  fix test-first. The verification gate accepts a propose-only agent's cited
  `file:line` evidence in place of a diff.
- **New skill description and `argument-hint`.** The description now says when
  to use the skill, with trigger phrases.

### Upgrading from 1.6.x
- Run `scripts/install-agents.sh` once after pulling. Releases that add agents
  need it, because Claude Code reads agents only from `~/.claude/agents/`. Without
  it the skill still works and falls back to `general-purpose`, and it tells you
  at the start of a run.
- `hooks/` is unchanged in this release.

### Known limits
- **Sonnet compresses bounded runs.** In our end-to-end check of a bounded ticket,
  Sonnet held the approval gate and wrote test-first code, but it did not write
  the ledger, create a branch, or load `build-loop.md`, even after the ledger
  instruction moved to the first approval. Opus ran every phase. Use Opus for
  orchestration if you rely on the ledger or the branch step.

## 1.6.4 (2026-09-28)

The frontend standards now cover how to drive the browser when verifying a UI
change. The skill also watches for code that fails silently and tests that can't
fail, and the companion hooks now have tests.

### Added
- **Hook tests.** `hooks/tests/` covers `verify-gate.py` and
  `pre-push-secret-scan.py`: every secret pattern, placeholder lines, commits
  already on the remote, the skill's config file, and when a success claim does
  or doesn't count as verified. Standard-library `unittest`, run with
  `python3 -m unittest discover -s hooks/tests`. The skill never loads them.

### Changed
- **"Tests That Can't Go Red" in `tdd.md`.** Every test must fail if the
  implementation is wrong. The section flags tests with no assertion, mock
  theater, tests that assert their own hard-coded value, and snapshot-only
  coverage of logic changes.
- **Silent failures in the standards.** New backend and frontend "Common
  Mistakes" entries for errors swallowed or turned into defaults: empty
  `catch`, un-awaited tasks, `catchError(() => of([]))` showing "no records"
  on an API error. The Phase 5 pre-push review now asks the reviewer to flag
  both patterns. Both ideas adapted from dotclaude's `silent-failure-hunter`
  and `pr-test-analyzer` agents.
- **New frontend "Browser Checks" section.** Read the page through the
  accessibility tree (`read_page` / `find`, or role and label locators) and
  screenshot only for layout or visual bugs. Batch predictable steps in one
  `browser_batch` call. Wait on the element, URL or response the next step
  needs instead of fixed sleeps. Adapted from the snapshot-first, low round-trip
  approach in browser-use's jev-ultrafast. Mirrored in `SKILL.qwen.md`.

## 1.6.3 (2026-09-28)

The frontend standards now warn about sending business dates as timestamps.

### Changed
- **New frontend "Common Mistakes" entry.** A date-picker `Date` sent to the API
  as a timestamp lands on the previous UTC day for users east of UTC, which
  shifts the date and any fiscal year or period the server derives from it.
  Send a calendar date (`yyyy-MM-dd`) and pin the request payload with a spec.
  Promoted from a Phase 9 instinct seen in two cycles: a re-issued fee challan
  sent the previous day, and invoices dated Jul 1 took the previous fiscal
  year's number. Mirrored in `SKILL.qwen.md`.

## 1.6.2 (2026-09-25)

The frontend standards now ask for a device check on input and form-styling changes.

### Changed
- **New frontend "Common Mistakes" entry.** Input, keyboard or form-styling
  changes, including DOM a directive inserts next to inputs, need a pass on both
  the iOS simulator and an Android emulator before review. Promoted from a Phase 9
  instinct seen in two cycles, where devices caught layout and keyboard bugs that
  headless specs passed. Mirrored in `SKILL.qwen.md`.

## 1.6.1 (2026-09-25)

The frontend standards now warn about Enter handling on touch keyboards.

### Changed
- **New frontend "Common Mistakes" entry.** A directive that turns Enter into
  "next field" on touch keyboards must leave Enter alone on fields that already
  own it: search boxes, `(keyup.enter)` handlers, and the only field of an
  `(ngSubmit)` form. Promoted from a Phase 9 instinct seen in three consecutive
  cycles, where Enter on a phone stopped running the field's own action.
  Mirrored in `SKILL.qwen.md`.

## 1.6.0 (2026-09-24)

Phase 9 lessons now go to a file in the repo instead of memory, so they are saved
and read back even when no memory write tool is connected.

### Changed
- **Instincts live in `.n2i-dev-cycle/instincts.md`.** Phase 9 appends each lesson
  as a short entry (statement, trigger, confidence, tags, tickets seen, why) and
  Phase 1 reads the file back, filtered to the detected stack. Previously both
  steps used `#instinct`-tagged memory observations through `observation_add` /
  `observation_search`, which the current claude-mem MCP doesn't expose, so every
  cycle skipped them and the lessons were lost. The file sits in the gitignored
  `.n2i-dev-cycle/` folder: per repo, per machine, greppable and hand-editable.
- **Near-duplicates bump instead of repeat.** A lesson that matches an existing
  entry adds the ticket to its `Seen:` line and raises confidence one step
  (`low` → `med` → `high`). Promotion to a reference file still triggers at
  `med`+ and is still only ever proposed, never applied.
- Phase 9 no longer skips the instinct steps when memory tools are missing.
  Milestone memory observations (plan approved, shipped, …) are unchanged and
  remain best-effort.
- `SKILL.md`, `SKILL.qwen.md`, `references/improve.md`,
  `references/execution.md` and `README.md` updated to match. Claude and Qwen
  cycles in the same repo now share one instincts file.

## 1.5.0 (2026-09-24)

Subagent dispatches now name a concrete model, with a fallback when that model
isn't available.

### Changed
- **Model tiers map to Agent `model` aliases.** The model-selection table in
  `references/execution.md` now names the alias to pass on each subagent dispatch:
  `haiku` for scaffolding, migration DDL, mechanical edits, and E2E runs; `sonnet`
  for service/component logic, multi-file integration, and test design; `opus` for
  architecture, ambiguous debugging, the Phase 5 pre-push review, and multi-layer
  CI root-cause. Previously the tiers were abstract ("cheap / fast", "standard",
  "most capable") and left the choice to the agent. `SKILL.md` pointer updated.
  `SKILL.qwen.md` is unchanged, since Claude aliases don't apply to the Qwen
  harness.

### Added
- **Unavailable-model fallback.** If a dispatch is rejected because the model is
  unknown, unavailable, or not permitted for the account, the skill retries once on
  the adjacent tier (`haiku` → `sonnet` → `opus`; `opus` steps down to `sonnet`),
  then dispatches with `model` omitted so it inherits the session's model. The
  dispatch note records which model ran. Rate-limit and overload errors retry the
  same model instead of changing tiers.

## 1.4.0 (2026-09-10)

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
- **`SKILL.md` is now a lean spine — every phase procedure moved to a reference.**
  `SKILL.md` keeps the phase list, detection, input parsing, and the two always-on
  phases (1 Ingest, 2 Branch); each later phase is a short pointer to the reference
  that carries its steps, loaded only when that phase runs. New files:
  `references/execution.md` (model selection, delegation, ledger, memory milestones —
  the one always-on reference, loaded at Phase 1), `references/planning.md` (Phase 3
  plan format), `references/build-loop.md` (Phases 4–6: build order + RED→GREEN loop,
  review checkpoints, validate commands + noise handling + pre-push review, handover
  format). Phase 7 orchestration folded into `references/debugging.md`, Phase 8 into
  `references/finishing.md`. `SKILL.md` drops from 583 to ~330 lines; a discussion-
  or planning-only invocation no longer loads the build/ship/improve machinery at
  all. No behaviour change. `SKILL.qwen.md` is unchanged — the Qwen variant is a
  deliberately single-file manifest.
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
