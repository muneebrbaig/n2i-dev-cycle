# Doubt Review

Read when the Phase 3 plan is drafted (architectural class; bounded class when the
change touches a contract between two repos, an export, or a persisted format), or at an
architectural checkpoint (`build-loop.md`). In past use the reviewer's findings were
adopted over 90% of the time, so it runs by default. Your own context
agrees with your own plan, so a reviewer who never saw your reasoning is the check
that can still change direction. The Phase 5 pre-push review comes too late for that.

## Contents

- When to Run
- The Cycle
- Stopping
- Rationalizations
- Red Flags — Stop

## When to Run

Run before the plan is presented, so it costs the user no extra turn. The user can say
"skip doubt" to turn it off. By class (`brainstorming.md`):
- **Architectural:** always. A new subsystem, a shared interface, concurrency or ordering,
  an irreversible step (data migration, public contract).
- **Bounded:** only when the change touches a contract between two repos, an export, or a
  persisted format. Skip a rename, a one-field or one-line change that touches none of
  those, and anything the compiler or a single test settles. The trigger wins: one new
  field in an export is not skipped.
- **Spike:** never.

## The Cycle

1. **Claim.** State the decision in two or three lines and why it matters. If you can't,
   you have a feeling, not a decision. Keep this to yourself.
2. **Extract.** Package the artifact (the plan, or one unit's diff) and its contract:
   the ticket's acceptance criteria plus the constraints it must meet (tenant isolation,
   standards, `DB_ENGINE`). Leave out your reasoning, your conclusions, and the claim.
   Split a large change first.
3. **Doubt.** Dispatch `n2i-doubter` (`opus`; falls back to `general-purpose` with
   `model: opus`, per `execution.md`) with the artifact and the contract only.
4. **Reconcile.** Check each finding against the artifact text, then classify it:
   - contract misread: fix the contract wording, not the artifact;
   - valid and actionable: change the plan or code, then re-validate;
   - valid trade-off: record it in the ledger and the handover;
   - noise: note the context the reviewer lacked.
   Disagreement from the reviewer is input to classify, not a verdict either way.

Append one ledger line per cycle: `Phase 3: doubt <n> — <n> actionable, <n> trade-off,
<n> noise`.

## Stopping

Stop when findings are trivial or already considered, after three cycles (hand the open
ones to the user), or when the user says to proceed. If two cycles return substantive
findings but none are actionable, you are re-arguing the design: stop and tell the user.

## Rationalizations

| Excuse | Reality |
|---|---|
| "I'm confident" | Confidence tracks correctness poorly on novel problems. |
| "The pre-push review will catch it" | It arrives after the structure is built. |
| "The reviewer will nitpick" | Scope the contract to failures, and ignore style. |
| "I'll send my reasoning so it understands" | Then it agrees with you. Send the artifact and contract. |
| "It disagreed, so I'm wrong" | Classify the finding; don't defer to it. |

## Red Flags — Stop

- The reviewer got your conclusion along with the artifact
- Findings accepted without checking them against the artifact
- A fourth cycle
- Running it on a spike, or on a rename or one-field change that touches no cross-repo
  contract, export, or persisted format, because it was cheap to ask
- Skipping it on bounded work that touches a cross-repo contract, an export, or a persisted format
