# Build Loop — Implement → Validate → Handover

Read at the start of Phase 4. Covers the procedure for Phases 4, 5, and 6 — the
part of the lifecycle that only runs once a plan is approved and code is being
written. A discussion / planning-only invocation never loads this.

Discipline refs still load per phase: `tdd.md` at Phase 4, `verification.md` at
Phase 5.

## Contents

- Phase 4 — Implement
  - Intra-phase checkpoints (scaled by class)
- Phase 5 — Validate
  - Pre-push review
- Phase 6 — Handover
  - What Changed
  - What to Test Locally
  - Known Limitations
  - E2E Coverage
  - Memory

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

**Append a ledger line** after each major
milestone (entity done, service+tests green, frontend done, etc.). For a
test-first unit the ledger line carries the RED proof:
`Phase 4: <unit> — RED <test> failed "<reason>" → GREEN (<commit>)`.

If something goes sideways mid-implementation — STOP, reassess, inform user, re-plan if needed. Don't push through blindly.

### Intra-phase checkpoints (scaled by class)

Every stop costs a user turn, so checkpoints scale with the Phase 1 class:

- **Bounded:** no mid-phase stops. Append the ledger line per unit and keep going; the
  Phase 6 handover is the review stop. One exception: pause before running or applying a
  migration script, since that is hard to undo.
- **Architectural:** stop after each unit below, to keep human reviewers and AI agents in
  sync across machines and sessions.
- **Either class:** the user can say "no checkpoints" or "checkpoint every unit". Record the
  choice in the ledger and follow it for the rest of the cycle.

| Checkpoint | After completing |
|---|---|
| Backend scaffold | Entity, DTOs, requests, config, migration, DI + wire-up, build clean |
| Backend service + controller | Methods and endpoints built test-first, all tests green |
| Frontend | Models, service, list + form components built (test-first where applicable), routes swapped, sidebar/nav wired, `ng build` clean |

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

**Final run via `n2i-unit-runner`.** Iterate in the main agent while fixing. For the
final green run, dispatch `n2i-unit-runner` once per active side (backend and frontend
in parallel), handing it the side, the directory, and the exact validate commands. It
returns `RESULT`, each command with its exit code, totals, and failure traces only. A
`pass` report counts as evidence only with the commands and exit codes shown
(`verification.md`). On `fail`, fix in the main agent, then re-dispatch. If the agent
isn't installed, run the commands yourself per the next paragraph and fall back per
`references/execution.md` (named agents).

**Keep the runner noise out of context.** Use the quietest reporter that still
shows exit code and failure count (`-v minimal` / `--watch=false` above; add
`--reporters` / `--logger` equivalents on other stacks). On a green run keep only
the summary line. Read the full output only when it exits non-zero, and then only
the failing cases. (A token-trimming hook, where installed, does this
automatically — this instruction is the fallback for setups without one.)

If validation fails:
1. Fix the issue
2. Re-run validation
3. Repeat until all green
4. Never skip or ignore failures

### Pre-push review

Once green, before Phase 6, scale the review to the Phase 1 class. **Bounded** with a small
diff (roughly under 100 changed lines) that touches no tenant-isolation, auth, or migration
code: skip the prompt, note "review skipped: bounded, small diff" in the handover, and run it
only if the user asks. **Architectural**, a larger diff, or anything touching those areas: ask
user "Run engineering:code-review on this diff before pushing?" Default yes if unsure. Reviewing here — against the local diff, before an MR/PR exists — catches
scope-creep and correctness issues while they're still a `git commit --amend` or a clean follow-up
commit away, instead of a fix-up commit sitting permanently in MR history after the fact. It also
skips triggering a CI run against a state you already know you're about to patch.

- If `engineering:code-review` isn't in the available-skills list this session, say so and
  dispatch the `n2i-prepush-reviewer` subagent instead (read-only, `opus`; hand it the base
  branch and the ticket/spec). If that agent isn't installed either, skip silently — don't block
  the lifecycle — and offer a manual review pass if the user still wants one.
- If accepted and available, invoke it against the diff: `git diff <base-branch>...HEAD` plus any
  uncommitted work (`git diff HEAD`) and untracked files (`git status --porcelain`) (backend
  and/or frontend paths per SCOPE), not a PR URL — no MR/PR exists yet at this point.
  Ask it to also flag silent failures (errors swallowed or turned into defaults) and tests
  that can't go red (`references/tdd.md`).
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
- Run the affected specs before Phase 8 **via the `n2i-e2e-runner` subagent** — hand it the minimum:
  the spec paths to run, `E2E_CMD` (or the detected runner), the DB target (dev, or
  a fresh throwaway DB where the project supports one). It returns pass/fail per
  spec plus the failure trace for failures only — the full runner log stays out of
  the main context. The agent pins `haiku`; if it isn't installed, fall back per
  `references/execution.md` (named agents). Where a
  real run isn't possible, say so rather than claiming coverage. Per
  `verification.md`: a passing report is not evidence — confirm against the run
  output the agent returns.
- Flows already covered and passing → note briefly, no action.

### Memory
- Record handover observation with key details for cross-session continuity
