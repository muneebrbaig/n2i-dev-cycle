# Systematic Debugging

Read in Phase 7 (feedback) and Phase 8 (CI failures).

These are internal steps of the debugging technique — not the skill's numbered
phases. It is loaded from the skill's Feedback and Ship phases.

## The Iron Law

```
NO FIX WITHOUT ROOT-CAUSE INVESTIGATION FIRST
```

Symptom fixes are failure. If you haven't done Step 1 below, you can't propose a
fix.

## Step 1 — Root Cause

1. **Read the error fully** — stack trace, line numbers, error codes. It often
   contains the answer.
2. **Reproduce reliably** — exact steps, every time? Not reproducible → gather
   data, don't guess.
3. **Check recent changes** — `git diff`, recent commits, new deps, config.
4. **Instrument component boundaries** — for a multi-layer path (CI → build →
   sign, controller → service → repo → DB, frontend → API → handler), log what
   enters and exits each boundary, run once, and see *which* boundary breaks
   before touching any one component.
5. **Trace data flow backward** — where does the bad value originate? What passed
   it in? Keep going up until you reach the source. Fix at the source.

## Step 2 — Pattern

Find similar working code in the same repo. Read any reference implementation
completely — every line, not a skim. List every difference between working and
broken, however small.

## Step 3 — Hypothesis

State one hypothesis: "X is the root cause because Y." Test it with the smallest
possible change, one variable at a time. Didn't work → new hypothesis, don't
stack fixes. Don't know → say so, research more.

## Step 4 — Fix

1. Failing test that reproduces the bug first (see `tdd.md`).
2. One fix, addressing the root cause. No bundled refactoring.
3. Re-validate through the skill's Validate phase (verification gate). Test
   passes, nothing else broke.
4. **Three fixes that don't hold → STOP.** Each fix revealing a new problem
   elsewhere, or needing "massive refactoring", means the design is wrong, not
   the hypothesis. Question the architecture with the user before fix #4.

## Parallel Dispatch

When there are **2+ genuinely independent failures** — different subsystems,
unrelated test files, separate CI jobs with different root causes — dispatch one
`Agent` per failure domain in a single message so they run concurrently.

Each agent gets: one failure domain, the error text + failing names, "find the
root cause, don't just increase timeouts / loosen asserts", "don't touch code
outside this domain", "return root cause + what you changed".

Do **not** parallel-dispatch when failures might share a cause (fixing one could
fix the rest — investigate together first) or when you don't yet know what's
broken.

On return: read each summary, check the diffs don't conflict, run the **full**
suite, spot-check.

## Common Mistakes to Avoid

- Proposing a fix before tracing data flow.
- "Quick fix now, investigate later" — the first fix sets the pattern.
- Multiple changes at once — you can't tell which one worked.
- Adapting a reference pattern from a skim instead of reading it fully.
- Fix #4 after three failures instead of questioning the design.
- Parallel-dispatching related failures.
