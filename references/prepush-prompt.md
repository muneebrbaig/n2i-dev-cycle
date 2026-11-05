# Pre-push Review Prompt

Read at the Phase 5 pre-push review, when you dispatch `n2i-prepush-reviewer`. Fill the
slots and keep the checks below. A prompt written from memory is only as good as your recall.

## Slots

- `{ticket}`: ticket number and title
- `{spec}`: path to the spec or ticket text
- `{base}`: base branch; add `{sibling}` (path and base branch) when the work spans repos
- `{decisions}`: the decisions approved in the plan
- `{claims}`: what the change says it does, one line each, for the reviewer to check
- `{scanner_hits}`: the `n2i-diff-scanner` hit list, or `none`

Write `none` for any slot with no value (no ticket, no sibling repo).
- `{review_read}`: the `REVIEW_READ` files from config (glossary, standards, conventions)

## Prompt

```
Review the local diff against {base} for {ticket}. Spec: {spec}. Sibling: {sibling}.
Approved decisions: {decisions}.
Diff-scanner hits: {scanner_hits}.
Read first: {review_read}.
Claims to check, each against the code and the spec: {claims}.
Report every finding with a severity label, whatever its severity.
```

## Standing checks

Add these to every prompt:

- User-visible strings against the repo glossary and its Avoid lists.
- Each surface that shows a state (a list, a detail view, a badge) has a test asserting it.
- Silent failures (errors swallowed or turned into defaults) and tests that can't go red
  (`tdd.md`).
- Cost of a user action: does Cancel or Retry restart a download or recompute?
- The human reviewer's previous must-fix items in `.n2i-dev-cycle/instincts.md`: check the
  diff for each.
- Claims written in the spec checked against measured data, not against the spec's own words.
- Output that depends on the environment: run it under two settings and compare
  (`diff-review.md`).
