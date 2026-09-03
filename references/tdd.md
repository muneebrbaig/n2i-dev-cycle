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

**RED** — one behaviour, clear name, real code (mocks only if unavoidable). Name
the production change that would make this test fail before you write it.

**Verify RED** — run it. It must *fail*, not error, and fail because the feature
is missing. Passes immediately → you're testing existing behaviour, fix the test.

**GREEN** — simplest code that passes. No extra params, no options objects, no
"while I'm here". YAGNI.

**Verify GREEN** — run it. Passes, other tests still pass, output clean (no
warnings).

**REFACTOR** — remove duplication, fix names, extract helpers. Stay green. No new
behaviour.

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
- "Tests-after achieve the same thing"
- "It's about spirit not ritual"
