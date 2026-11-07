# Codex Review

Read at Phase 3 and Phase 5 when config sets `CODEX` to `review` or `plan+review`. Codex is a
second model family. In past rounds it found bugs the Claude reviewers missed, and they found
bugs it missed, so neither replaces the other. Codex takes the review volume (round 1 and the fix
rounds). Opus sees the full diff once, at the end.

## Contents

- When It Runs
- Preflight and Failures
- Running Codex
- Plan Review
- Phase 5 Rounds
- Red Flags — Stop

## When It Runs

- `CODEX=off` or unset (the default): nothing here applies. `n2i-doubter` and
  `n2i-prepush-reviewer` do every review.
- `CODEX=review`: Phase 5 rounds only.
- `CODEX=plan+review`: the Phase 3 plan review too.

Codex sends the spec, the code and the diff to a third-party model. Set the key only in a repo
whose owner approved that, and record who approved it in the project's own notes. The skip
rules in `SKILL.md` (Phase 5 step 3) apply to the whole review, Codex rounds included.

## Preflight and Failures

Before the first run in a session:

```bash
codex login status
```

Codex is **unavailable** when it isn't logged in, when the login differs from the approved one
in the project notes, when it reports a usage limit, or when a run errors or returns an empty
report twice in a row (retry once first). When it is unavailable, say so and follow
`CODEX_FALLBACK`:
- `wait` (the default): stop and ask the user. Don't spend Opus runs unasked.
- `opus`: run that review with `n2i-doubter` (plan) or `n2i-prepush-reviewer` (diff) and note
  "Codex unavailable: <reason>, Opus ran instead" in the ledger and the handover.

## Running Codex

Write the prompt to the session scratchpad and give the literal absolute path, never a
variable, and never a path inside the repo. The review-gate hook reads that file. Run it from the
repo root (or the worktree):

```bash
codex exec -s read-only --skip-git-repo-check -o /abs/scratchpad/codex-out-<n>.md - < /abs/scratchpad/codex-prompt-<n>.md
```

Every prompt says: read-only (no edits, commits, pushes, network or database access); findings
ranked by severity with `file:line` and a concrete failure scenario; verify by reading the code.
Codex can't run anything in that sandbox. Before you believe a numerical, performance or
determinism finding, run it yourself.

## Plan Review

With `plan+review`, the plan review runs on the same triggers as `doubt.md` (When to Run).
Extract the plan and its contract as `doubt.md` says, without your reasoning.
- **Architectural:** Codex and `n2i-doubter` in parallel.
- **Bounded with a trigger:** Codex alone. If you dispute a finding, give `n2i-doubter` the
  finding and your position, and take its verdict.

Reconcile per `doubt.md` and write
`Phase 3: codex plan review — <n> actionable, <n> trade-off, <n> noise`.

## Phase 5 Rounds

Build every prompt from `references/prepush-prompt.md`: slots filled, the standing checks
copied word for word, and the `REVIEW_CHECKLIST` rules included. The hook counts a Codex run
only when its prompt file holds them.

1. **Round 1, full diff (`{round}` = `full`).** Two Codex runs in parallel, each with one
   brief added to the template:
   - **Spec and standards:** every ticket bullet and spec line is implemented, nothing unasked
     is added, nothing implemented is wrong. Quote the spec line for each finding. Apply the
     standards files, `REVIEW_READ` and every checklist rule.
   - **Lens:** output that depends on the environment (thread count, CPU kernel, locale,
     timezone), async dead ends and Retry, what Cancel and Retry cost (re-downloads,
     recomputes), unbounded memory or output size, and the edges of every range.
2. **Fix rounds (`{round}` = `delta since round <k>`).** Fix every Critical and Required
   finding, then one Codex run on the change since the last round. It re-measures every
   number the fixes state. Repeat until a round finds no Critical or Required item, at most
   `REVIEW_ROUNDS_MAX` fix rounds (default 3). Still finding them after that: stop and ask.
3. **Final gate.** One `n2i-prepush-reviewer` on the full diff (`{round}` = `final, full
   diff`), even when the Codex rounds came back clean. Settle any split between it and Codex
   with `n2i-doubter`.
4. **Fixes from the final gate.** One Codex run on that delta. Opus doesn't run again unless
   Codex is unavailable and `CODEX_FALLBACK=opus`.

Ledger, one line per round:
`Phase 5: review round <k> (<codex|opus>, <full|delta: files>, <n> Critical/Required fixed)`.
The final gate also writes `Phase 5: review run (<n> Critical/Required fixed)`.

## Red Flags — Stop

- A Codex run in a repo whose config doesn't set `CODEX`
- A prompt or report written inside the repo
- A Codex finding believed without reading the code, or a number without running it
- Opus run on a delta only, never on the full diff
- A fourth fix round without asking the user
