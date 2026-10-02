# Execution Mechanics

Cross-cutting machinery for every phase: model selection, subagent delegation,
the checkpoint ledger, memory integration. Load once after the Phase 3 plan is approved — it stays
relevant through Ship. `SKILL.md` carries only the one-line pointers; the detail is here.

## Model Selection

Pick the cheapest model that fits the step. State the model when dispatching a
subagent — an omitted model inherits this session's, usually the priciest.

| Work | Model tier | Agent `model` |
|---|---|---|
| Scaffolding, migration DDL, single-file mechanical edits, transcription from a detailed plan, E2E runs | cheap / fast | `haiku` |
| Service/controller/component logic, multi-file integration, test design | standard | `sonnet` |
| Architecture, ambiguous debugging, the Phase 5 pre-push review, CI root-cause on a multi-layer failure | most capable | `opus` |

**Unavailable model.** If the dispatch is rejected because the model is unknown,
unavailable, or not permitted for this account, retry once one tier up
(`haiku` → `sonnet` → `opus`); for `opus`, step down to `sonnet`. If that also
fails, dispatch with `model` omitted so it inherits this session's. Say which
model actually ran in the dispatch note. A rate-limit or overload error is not
unavailability: retry the same model rather than changing tiers.

### Named agents

The repo ships three subagents in `agents/` that pin the model and tools for the
delegations below. Prefer them by name (`subagent_type`):

| Agent | Model | Used for |
|---|---|---|
| `n2i-e2e-runner` | `haiku` | Phase 6 E2E runs |
| `n2i-ci-triage` | `sonnet` | Phase 7/8 root cause for one independent failure domain (no edits) |
| `n2i-prepush-reviewer` | `opus` | Phase 5 pre-push review when `engineering:code-review` is unavailable |

If a named agent isn't installed (dispatch rejects the name), fall back to the
`general-purpose` agent with the `model` from the table above and the same
instructions inline, and say so in the dispatch note. The unavailable-model rule
above still applies.

## Delegation & Context

Delegate to a subagent only work that is **verbose-in / small-conclusion-out and
independent**:

| Delegate | Why |
|---|---|
| E2E runs (Phase 6) — `n2i-e2e-runner` | slow, huge log, result is pass/fail + failure traces |
| Independent Phase 7 findings / Phase 8 CI jobs (`debugging.md` → Parallel Dispatch) — `n2i-ci-triage` | separate root causes, run concurrently |
| Pre-push code review (Phase 5) — `engineering:code-review`, else `n2i-prepush-reviewer` | already its own skill |

**Keep in the main agent** — do not hand off:

- **Reading the ticket / wiki / linked docs (Phase 1).** The spec is the artifact
  the alignment gate, plan self-review, and every TDD assertion check back
  against. A subagent returns a lossy summary; the gap between the summary and the
  real wording is where scope drift enters — the same reason `brainstorming.md`
  keeps the restate in-session.
- **Writing the ticket draft / MR/PR description.** Synthesis from context the
  main agent already holds, and quality-sensitive (product-facing tone,
  stop-slop). Handing off means re-passing almost everything for near-zero saving.
- **The Phase 4 TDD loop.** Rapid RED→GREEN iterations; per-run subagent latency
  kills the loop, and the verification gate requires the main agent to run and
  read the command itself.

The real context lever is the **checkpoint ledger** + memory observations, not
delegation — write the ledger line at each checkpoint and don't re-read what it
already captured.

## Checkpoint Ledger

`.n2i-dev-cycle/progress.md` (inside the gitignored folder). Best-effort — survives
context compaction and cross-session `fix:` / multi-machine re-entry. Skip if not
in a git repo.

- First line: `# <ticket-or-slug> — <one-line goal>`
- One line per phase as it completes: `Phase N: <what landed> (<commit range>)`
- Phase 4 intra-phase checkpoints get a line too.
- Phase 4 test-first units record the RED failure line before the GREEN commit
  (`references/tdd.md`) — the ledger is where test-first order is proven across
  sessions and machines.
- On skill start (Phase 1 step 8, ledger rules summarized there): if the first line matches the current ticket,
  resume at the first incomplete phase instead of restarting. If it names a
  *different* ticket whose last line shows shipped/merged, move it to
  `.n2i-dev-cycle/archive/progress.<slug>.md` and start fresh — don't "resume" a done cycle.
- Phase 9 archives the ledger as its last step (into `.n2i-dev-cycle/archive/`),
  after Phase 8's merge cleanup; archived copies stay gitignored, delete whenever.
- After compaction, `git log` and this ledger outrank your own recollection.

## Memory Integration

> **Best-effort.** Uses the claude-mem MCP tools (`observation_add`, `observation_search`,
> `memory_search`). If unavailable in the session, skip memory steps silently — never block
> the lifecycle on them. The `.n2i-dev-cycle/progress.md` ledger is the durable fallback:
> it is plain git-tracked-adjacent text and does not depend on any MCP tool.

Record observations at these three milestones using `observation_add`. Every other
milestone (units done, validation, feedback, fixes) is a ledger line only — the ledger
already holds it.

| Milestone | Type | What to record |
|---|---|---|
| Plan approved | `⚖` (decision) | Key decisions, scope, approach chosen |
| Handover | `✓` (change) | Summary of all changes, what to test, RED evidence (test + failure reason) per logic unit |
| Shipped / CI green | `✓` (change) | Final status, branch pushed, CI result |

Also search memory at skill start (`observation_search`, `memory_search`) to surface prior work on same ticket/feature.

Phase 9 instincts are **not** memory observations: they go to `.n2i-dev-cycle/instincts.md`
(`references/improve.md`), so they survive a session without memory tools.
