# Verification Before Completion

Read in Phase 5, and apply before any claim of success anywhere in the lifecycle.

## The Iron Law

```
NO COMPLETION CLAIM WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the command **in this message**, you can't say it passes.

## The Gate

Before saying any status, or expressing satisfaction:

1. **Identify** the command that proves the claim.
2. **Run** it — full, fresh, complete.
3. **Read** the output — exit code, failure count, warnings.
4. **Verify** the output matches the claim. If not, state the actual status with
   the evidence.
5. **Then** make the claim, with the evidence attached.

Skipping a step is lying, not verifying.

## Claim → Proof

Commands are the .NET + Angular default — substitute `BACKEND_VALIDATE_CMD` /
`FRONTEND_VALIDATE_CMD` / `E2E_CMD` on other stacks.

| Claim | Needs | Not enough |
|---|---|---|
| Backend tests pass | `dotnet test "$SLN" -v minimal` → 0 failed | a run from earlier, "should pass" |
| Frontend tests pass | `npm test -- --watch=false` → 0 failed | backend being green |
| Build succeeds | `dotnet build` / `npm run build` → exit 0 | linter / format clean |
| Format clean | `dotnet format --verify-no-changes` | "I didn't change much" |
| Bug fixed | the repro test now passes AND failed before the fix | code changed, assumed fixed |
| Regression test works | red-green verified — revert fix, test fails, restore, passes | test passes once |
| Requirements met | line-by-line check against the ticket / plan | tests passing |
| Subagent done | the VCS diff shows the change | the agent said "success" |

## Red Flags — Stop

- "should", "probably", "seems to", "looks right"
- "Great!" / "Perfect!" / "Done!" before running anything
- About to commit / push / open an MR without a fresh run
- Trusting a subagent's success report without checking the diff
- Partial check → extrapolating to the whole
- "Just this once" / "I'm confident" / "I'm tired"

## Common Mistakes to Avoid

- Claiming the suite is green off a run from before the last edit.
- "Linter passed" as a stand-in for "build passed" — different tools.
- Marking a phase complete on tests alone without checking requirements.
- Accepting "success" from a dispatched agent without reading its diff.
