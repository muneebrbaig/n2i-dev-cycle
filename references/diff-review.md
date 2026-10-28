# Diff Review Checks

Read at the Phase 5 pre-push review, before you review your own diff or hand it to
`n2i-prepush-reviewer`. Three checks that a green suite
cannot give you: whether a check was silenced to get green, whether the new tests
can actually go red, and whether the diff leaves dead code behind.

Delegation: the silenced-check scan and the dead-code candidate list are mechanical
and verbose-in, so hand them to `n2i-diff-scanner` (`haiku`, read-only; falls back
to `general-purpose` with `model: haiku`, per `execution.md`). It returns hits with
`file:line`; you judge them. The mutation spot-check and the dead-code decisions stay
in the main agent, since the first edits the tree and the second needs judgment about
hidden callers.

## Contents

- Silenced Checks
- Mutation Spot-Check
- Dead Code
- Red Flags — Stop
- Common Mistakes to Avoid

## Silenced Checks

A green run proves nothing if the change quietly weakened the check. Scan the full
diff (committed, uncommitted, and untracked) for these moves:

| Move | Looks like |
|---|---|
| Threshold lowered | a coverage floor, lint level, or analyzer severity reduced in config |
| Test made easier | `.skip`, `xit`, `xdescribe`, `fit`, `[Fact(Skip = …)]`, `[Ignore]`; an assertion removed or loosened |
| Checker silenced | `eslint-disable`, `@ts-ignore`, `@ts-expect-error`, `#pragma warning disable`, `[SuppressMessage]`, `NOSONAR`, `// noinspection`, a `.editorconfig` rule set to `none` |
| Unfinished work | an empty `catch`, a stub or `throw new NotImplementedException()` body, a `TODO` standing in for logic |
| New exception | a new ignore-list, baseline, or allow-list entry nobody discussed |

Tightening a check needs no ceremony. **Loosening one is loud:** each hit goes to the
user with the file, line, and why the change needed it. A silenced check the user did
not approve is a finding, not a style note, and it gets fixed at the cause. Pre-existing
suppressions that the diff did not touch are out of scope.

## Mutation Spot-Check

A new test passing proves little. Prove it can fail on the code that exists now:

1. Pick one branch, condition, or comparison the change added in business logic.
2. Invert it in the working tree (`>` to `<=`, drop a guard, swap a return).
3. Run only the tests for that unit (single-test commands in `tdd.md`).
4. Expect red. Still green means a test is missing or can't go red: name the case
   and add it test-first (`tdd.md`).
5. **Restore the line exactly** and confirm with `git diff` that the tree matches what
   it was before the mutation. Re-run the unit green.

Main agent only; the pre-push reviewer is read-only. One mutation per logic unit is
enough, so skip scaffolding (`tdd.md` exempt column) and pure UI markup. Never leave a
mutation in place across a tool call you might not finish.

## Dead Code

List code the change leaves unused or unreachable: a method nothing calls now, an
unused import or parameter, a branch that can no longer be taken, a commented-out block.

- **Your own orphans** (made unused by this change): remove them.
- **Pre-existing** dead code: list it with `file:line` in the handover under Known
  Limitations and ask before deleting. Never remove code you can't prove is unused;
  reflection, DI registration, and route tables hide callers.

## Red Flags — Stop

- Suite went green in the same diff that touched a skip, a suppression, or a threshold
- A new test that survives every mutation you try
- "The suppression was already there" without checking `git blame` or the diff
- Deleting pre-existing "unused" code because the diff made it look orphaned

## Common Mistakes to Avoid

- Scanning only the committed diff and missing uncommitted or untracked files.
- Treating a lowered threshold as config noise.
- Leaving the mutation in the tree after the run.
- Mutating scaffolding (entity props, DI wire-up) and calling the empty result a gap.
- Deleting pre-existing dead code without asking.
