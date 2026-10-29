# Test-Driven Development

Read in Phase 4 and for every bug fix (Phase 7).

## The Iron Law

```
NO BUSINESS LOGIC WITHOUT A FAILING TEST FIRST
```

Write the test. Run it. Watch it fail for the right reason. Write the minimal code
to pass. Refactor while green.

If you didn't watch it fail, you don't know it tests the right thing. Code written
before its test → delete it, redo it from the test. "Keep it as reference" is
still testing after.

**Violating the letter is violating the spirit.**

## What Is Test-First vs Exempt

| Test-first (RED → GREEN → REFACTOR) | Exempt — but the following tests must exercise it |
|---|---|
| Business logic — service methods, rules, validation | Data-model / ORM field definitions |
| API endpoints (auth, shape, status) | ORM ↔ table mapping / schema config |
| UI behaviour — components, guards, pipes, resolvers | Dependency-injection / container registration |
| Bug fixes — failing repro test first | Migration / DDL scripts |

(.NET names for the exempt column: entity properties, `ModelConfiguration`,
`ModelBuilder` wire-up, DbUp SQL.) Exempt scaffolding is not untested — the
logic tests that follow must fail if the scaffold is wrong.

## The Cycle

**Before the first RED**, list each acceptance criterion and the test that will cover it:
each option on its own, the combinations the ticket names ("can be used together"), and
the off state. Add one test per boundary or shared element (an item in two groups, the
first and last element), with the new step on. A criterion with no test is a gap to name.

**RED** — one behaviour, clear name, real code (mocks only if unavoidable). Name
the production change that would make this test fail before you write it.

**Verify RED** — run it. It must *fail*, not error, and fail because the feature
is missing. Passes immediately → you're testing existing behaviour, fix the test
(unless the test is the deliverable: see Tests for Behavior That Already Exists).
Record the failure — test name + the assertion message / reason — in this unit's
ledger line (`SKILL.md` Checkpoint Ledger). A GREEN commit with no RED line before
it is indistinguishable from tests-after.

**GREEN** — simplest code that passes. No extra params, no options objects, no
"while I'm here". YAGNI.

**Verify GREEN** — run it. Passes, other tests still pass, output clean (no
warnings).

**REFACTOR** — remove duplication, fix names, extract helpers. Stay green. No new
behaviour.

## Tests for Behavior That Already Exists

When the test is the deliverable (an e2e spec, a characterization test, coverage for
existing code), it passes on its first run by design. RED then comes from breaking the
behavior: once per kind of assertion, break what it checks in the working tree or the
test setup (return a 500 from the endpoint it depends on, rename the heading, drop the
link), run it, and watch it fail on that assertion. Then restore and confirm with
`git diff`. Record each break and its failure in the ledger as the RED line. A test that
stays green against a broken app is not done, and "go-red not checked" is not a known
limitation to ship with.

## Tests That Can't Go Red

Ask of every test: if the implementation were wrong, would this go red? If not, it
isn't coverage. Watch for:

- No assertion, or only "doesn't throw" on logic that returns a value
- Mock theater: asserting the mock was called with what the test just set up, not
  the behaviour it produced
- Asserting the value the test itself computed or hard-coded into the fake
- A snapshot as the only check on a logic change
- E2E/UI: an absence check (no alert, count 0) that runs before the data request
  settles; a wait that doesn't apply (`waitForLoadState` after a client-side route change
  returns at once); an assertion on an element a shared layout always renders; a step
  skipped for one case of a loop; `.first()` hiding a duplicate match

To prove a test can go red on code that already exists, run the mutation spot-check
in `references/diff-review.md` at the Phase 5 pre-push review.

## Single-test commands

.NET + Angular default (other stacks: derive the single-test form of
`BACKEND_VALIDATE_CMD` / `FRONTEND_VALIDATE_CMD`):

- Backend: `dotnet test "$SLN" --filter <name> -v minimal`
- Frontend: `npm test -- --watch=false --include='**/<name>.spec.ts'`

## Rationalizations

| Excuse | Reality |
|---|---|
| "I'll write tests after" | Tests-after pass on the first run — proves nothing. You verify the cases you remembered, not the ones you'd have found. |
| "Already manually tested" | No record, no re-run, easy to forget a case under pressure. |
| "Too simple to test" | Simple code breaks. The test is 30 seconds. |
| "Deleting my code is wasteful" | Sunk cost. Keeping code you can't trust is the waste. |
| "TDD slows me down" | The shortcut is debugging in prod. TDD catches it before commit. |
| "Scaffolding needs a test too, so this is all exempt" | Only the plumbing is exempt. The logic on top is test-first. |

## Red Flags — Stop and Restart

- Code before test
- Test written after implementation
- Test passed on first run
- Can't explain why the test failed
- No RED failure line recorded before the GREEN commit
- "Tests-after achieve the same thing"
- "It's about spirit not ritual"
