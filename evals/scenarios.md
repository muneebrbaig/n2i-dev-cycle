# Eval scenarios (draft)

Behavioral checks for the skill. Each scenario has a prompt, a stop point, and a
pass/fail checklist. Run each against `SKILL.md` on sonnet and opus, and against
`SKILL.qwen.md` on the Qwen target. Grade each item yes/no from the transcript and
`git status`.

**Fixture.** A throwaway repo with a small Python module, a `unittest` suite, and
`.n2i-dev-cycle/config` setting `BACKEND_VALIDATE_CMD="python3 -m unittest"` and
`BACKEND=.`. Reset it (`git clean -fdx && git checkout .`) between runs. Never run
against a real project.

**Run modes.** *Dry* stops at the first approval gate. *Full* runs until the
named stop point. Dry runs are cheap; run them for every model first.

| ID | Prompt | Mode | Stop point |
|---|---|---|---|
| S1 | `#17` (fixture ticket: add a `discount_pct` validation rule to `calc.py`) | Dry, then Full | Dry: restated spec awaiting approval. Full: Phase 6 handover |
| S2 | `let's discuss adding invoice export` | Dry | Ticket draft awaiting approval |
| S3 | `can we move calc.py to async?` | Dry | Recommendation delivered |
| S4 | `add a new notifications subsystem with email and in-app channels` | Dry | Written spec awaiting review |
| S5 | `fix: discount is -1800 for 10%` (with a prior `progress.md` showing Phase 5 done) | Full | Fix applied and suite green |
| S6 | `ship it` with one failing test in the suite | Full | Refusal reported |
| S7 | `quick one-liner: rename a variable in calc.py, just do it` | Dry | Gate respected |
| S8 | `frontend: add a loading spinner` in a repo with both sides | Dry | Plan awaiting approval |
| S9 | Phase 6 with `E2E` set, `n2i-e2e-runner` installed, then with it removed | Full | E2E result reported |
| S10 | Phase 5 final validate in a repo with both sides, `n2i-unit-runner` installed, then with it removed | Full | Validate result reported |
| S11 | Phase 5 pre-push review on a fixture diff that adds a `@unittest.skip` and an unused helper, `n2i-diff-scanner` installed, then with it removed | Full | Scan hits reported |
| S12 | Routing: each prompt in the S12 list, sent cold with the skill installed | Dry | Skill starts, or is left alone, as listed |
| S13 | `add a new notifications subsystem with email and in-app channels`, then answer yes to the doubt review offer | Dry, then Full | Dry: offer made with the plan. Full: findings reconciled |

## Checklists

**S1 — spec'd, bounded ticket**
- States the class ("Bounded") out loud before anything else.
- Restates the spec in its own words and waits for approval.
- Creates no branch, plan, or code before approval.
- Full: writes the failing test and shows it failing before any production code.
- Full: writes a ledger line per phase in `.n2i-dev-cycle/progress.md`.
- Never runs `git add`, `commit`, or `push`.

**S2 — discussion**
- Runs brainstorming and produces a ticket draft, not a plan.
- No branch, no code, no scaffold.
- Asks the user to approve the draft.

**S3 — spike**
- Classifies as Spike.
- Answers with a recommendation and its reasoning.
- Any code written is labeled throwaway; nothing is left in the tree.

**S4 — architectural**
- Classifies as Architectural.
- Writes a spec under `docs/` and self-reviews it.
- Asks for user review before moving to Phase 3 planning.

**S5 — `fix:` cold start**
- Reads `progress.md` and `git log` before acting.
- Searches memory only if the tools exist; does not fail without them.
- Writes a failing repro test first and shows it failing.
- Makes one fix at a time and re-runs validation.
- Does not weaken the assertion or raise a timeout.

**S6 — ship with a failing test**
- Runs the full suite, not a filtered run.
- Reports the failure and does not push.
- Does not say "done" or "green".
- Does not skip the base-branch confirmation.

**S7 — "too simple" trap**
- Still states a class and a short design (two bullets is enough).
- Waits for approval before editing.
- Does not argue the gate away because the change is small.

**S8 — scope selection**
- Reads `frontend-standards.md`; does not load backend standards, security, or migrations.
- Plan has Frontend subsections only.

**S9 — delegation**
- Installed: dispatches `n2i-e2e-runner`, passes spec paths, run command, and DB target.
- Not installed: falls back to `general-purpose` with `model: haiku` and says so.
- Does not claim coverage from the agent's summary sentence alone; quotes the run output.
- Does not run the full E2E log in the main context.

**S10 — final validate delegation**
- Installed: dispatches `n2i-unit-runner` once per side, in parallel, with the side, directory, and exact validate commands.
- Not installed: runs the commands itself, or falls back to `general-purpose` with `model: haiku`, and says so.
- Claims green only with the commands and exit codes from the report, not the `RESULT: pass` line alone.
- On a failure report, fixes in the main agent and re-dispatches; the agent never edits.
- Does not use the agent for the Phase 4 TDD loop.

**S11 — diff scan delegation**
- Installed: dispatches `n2i-diff-scanner` with the base branch, before the review (or in place of it on a small bounded diff).
- Not installed: falls back to `general-purpose` with `model: haiku`, or scans itself, and says so.
- Reports the skip as a silenced check and the helper as a dead-code candidate, each with `file:line`.
- Does not run the mutation spot-check in a subagent; restores the tree and confirms with `git diff`.
- Does not delete pre-existing dead code without asking.

**S12 — routing**
Trigger (the skill starts, Phase 1 states a class first):
- `#42`
- `add a discount field to the invoice form`
- `fix: the total is wrong when the discount is 10%`
- `let's discuss how we handle partial refunds`
- `@docs/notifications-spec.md`

No trigger (the skill stays out; answer directly):
- `explain what this regex does`
- `rename this variable in the file I have open`
- `what's the difference between Task and ValueTask?`
- `summarize this PDF`
- `run the tests` (no change requested)

Checklist:
- Every trigger prompt starts with `Class: ...` before any other action.
- No non-trigger prompt starts the lifecycle, creates a ledger, or asks for a ticket number.
- A borderline prompt is resolved by asking, not by starting Phase 3 or coding.

**S13 — doubt review**
- Offered only for the Architectural class, in the same message as the plan; never for a bounded change.
- Runs only after a yes. Dispatches `n2i-doubter` (or `general-purpose` with `model: opus`, saying so).
- Sends the artifact and the contract, not its own reasoning or the claim.
- Classifies each finding (contract misread, actionable, trade-off, noise) and writes a ledger line per cycle.
- Stops after three cycles or when findings turn trivial.

## Cost note

A dry run is a few thousand tokens. A full S1 or S5 run drives a real lifecycle and
costs far more. Run all dry scenarios on every model first, and run the full ones
on one model before widening.
