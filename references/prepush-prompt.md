# Pre-push Review Prompt

Read at the Phase 5 pre-push review, when you dispatch `n2i-prepush-reviewer`. Fill the
slots and copy the standing checks below word for word. Codex prompts (`references/codex.md`) use
the same template. A prompt written from memory is only as
good as your recall, so the review-gate hook (`hooks/review-gate.py`) counts a dispatch only when
its prompt (a dispatch, or a `codex exec` prompt file) holds every standing check, plus every `### ` heading of the repo's `REVIEW_CHECKLIST`
file when config sets one.

## Slots

- `{ticket}`: ticket number and title
- `{spec}`: path to the spec or ticket text
- `{base}`: base branch; add `{sibling}` (path and base branch) when the work spans repos
- `{decisions}`: the decisions approved in the plan
- `{claims}`: what the change says it does, one line each, for the reviewer to check
- `{scanner_hits}`: the `n2i-diff-scanner` hit list, or `none`
- `{round}`: `full` for the first review; for a later round, `delta since round <k>` and the
  files changed since then (the fixes, and any docs or numbers they touched); `final, full diff`
  for the Opus gate after Codex rounds (`codex.md`)
- `{checklist}`: the rules of the `REVIEW_CHECKLIST` file, headings included, or `none`

Write `none` for any slot with no value (no ticket, no sibling repo).
- `{review_read}`: the `REVIEW_READ` files from config (glossary, standards, conventions)

## Prompt

```
Review the local diff against {base} for {ticket}. Spec: {spec}. Sibling: {sibling}.
Round: {round}. On a delta round, review only those changes, and re-measure every number they
state on the input and code path the text names.
Approved decisions: {decisions}.
Diff-scanner hits: {scanner_hits}.
Read first: {review_read}.
Claims to check, each against the code and the spec: {claims}.
Apply every rule of this project checklist to the diff: {checklist}.
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
- Cached or displayed state: when an object is replaced under the same ID, everything cached by
  that ID is invalidated. Caches hold the whole result, metadata included. Component keys carry
  identity, not committed values. A guard that must survive a remount ("save in flight") lives in
  the store. Module-level mutable state has a reset path.
- Retry and failure paths: Retry recreates whatever failed (worker, promise, connection), with one
  retry budget per request (nested loops don't reset it). A later success or render doesn't hide an
  earlier error. The failure path itself has a test.
- Destructive cleanup: it proves the writer has stopped and the files aren't published before
  deleting, and fails closed. Every new endpoint has a test per role. Untrusted strings are
  sanitized before logging. Seeds and fixtures hold no real credentials.
- New tests: watch each fail once (break the code, rerun). Assert content specific to the page plus
  "no failed API responses". A wait after a client-side route change that returns at once, or an
  element a shared layout always renders, proves nothing. Size limits get a test at the boundary
  and one real large input.
- Paths that differ only in case (`Foo.ts` and `foo.tsx`) break case-insensitive checkouts while a
  Linux CI stays green.
