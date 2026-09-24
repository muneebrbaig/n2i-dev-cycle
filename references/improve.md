# Improve — Distilling Reusable Patterns

Read in Phase 9, after the branch is merged and Phase 8 cleanup is done.

## What to distill

At most 1-3 items per cycle. Only things that will **recur**. A pattern qualifies if:

- it cost real time this cycle — a wrong assumption, a missed convention, a debugging detour, **or**
- it's a decision worth not re-litigating next time — chose X over Y for reason Z, **and**
- it generalizes past this one ticket.

Skip: one-off ticket facts, anything already in a `references/*.md` "Common Mistakes"
list, vague "be careful" notes. The bar is "will recur", not "was true this time".

## Shape of an instinct

One entry per instinct in `.n2i-dev-cycle/instincts.md`. Each entry carries four fields:

- **Statement** — the rule, imperative. *"Forward the original org id, not the resolved one, into a nested service call's `explicitOrganizationId`."*
- **Trigger** — when it applies. *"Any service method that calls another service with an org-id param."*
- **Confidence** — `low` / `med` / `high`:
  - `low` — seen once, plausibly generalizes
  - `med` — seen twice, or once but clearly a whole class of mistake
  - `high` — seen 3+ times, or a hard rule with a concrete failure behind it
- **Scope tags** — stack + domain: `#stack:dotnet #domain:security`, `#stack:angular #domain:forms`, `#stack:any #domain:process`.

## Recording

Append to `.n2i-dev-cycle/instincts.md` (create it with a `# Instincts` heading if
missing). The folder is gitignored, so this is per repo and per machine. One entry:

```markdown
## <statement, imperative>
- Trigger: <when it applies>
- Confidence: low | med | high
- Tags: #stack:<stack> #domain:<domain>
- Seen: <ticket> (<YYYY-MM-DD>)[, <ticket> (<date>)]
- Why: <one line: the concrete failure or decision behind it>
```

Phase 1 step 5 reads this file back, filtered to the cycle's detected stack. A
plain file needs no memory tools and stays greppable and hand-editable.

## Promotion to a reference

Before recording each instinct, read `.n2i-dev-cycle/instincts.md` for a near-duplicate.

- **Match found** → don't add a second entry: append the ticket to its `Seen:` line
  and raise its confidence one step (`low` → `med` → `high`).
- **Match found, and it now reaches `med`+ confidence** → the pattern has
  recurred across cycles. Propose a one-line addition to the matching
  `references/*.md` "Common Mistakes to Avoid" (or the relevant section) as a PR
  to the skill repo — show the exact file and the exact line. The user decides.
- **No match** → just append the instinct. It's staging; the reference file is the
  durable store.

Never edit a `references/*.md` file silently — promotion is always a proposed PR.

## Archive the ledger

Phase 9's last action. First the final ledger line:

```
Phase 9: <N> instincts recorded[, <M> bumped][, promotion proposed for <file>]
```

then archive:

```bash
mkdir -p .n2i-dev-cycle/archive
mv .n2i-dev-cycle/progress.md .n2i-dev-cycle/archive/progress.<ticket-or-slug>.md
```

So the next ticket in this repo starts on a clean ledger. `.n2i-dev-cycle/archive/`
keeps finished ledgers out of the way of routine `find` / `grep` while staying
gitignored (the whole `.n2i-dev-cycle/` folder is) — delete them whenever. Skip if
not in a git repo.

## Common Mistakes to Avoid

- Recording ticket-specific facts as instincts — they don't generalize.
- More than 3 instincts in one cycle.
- Editing a reference file directly instead of proposing the change.
- Skipping the near-duplicate read, so the same instinct lands five times at `low`.
- Recording instincts as memory observations instead of in `instincts.md` — Phase 1
  never reads them back from there.
- Treating Phase 9 as mandatory paperwork — a cycle that produced nothing reusable records nothing.
