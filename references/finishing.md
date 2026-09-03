# Finishing a Development Branch

Read in Phase 8, once the user asks to ship.

## Step 1 — Full Suite Green

Run the complete suite for the active scope (not `--filter`). Apply the
`verification.md` gate. Failures → stop, report, fix. The steps below only run on
a green suite.

## Step 2 — Confirm Base Branch

The base is whatever this work forked from — usually in the ticket or the branch
upstream. If it isn't certain, ask: "This branch split from `<best guess>` — is
that right?" Merging or targeting the wrong base is expensive to undo.

## Step 3 — Push & MR

```bash
git push -u origin <feature-branch>
```

Create the MR/PR against the confirmed base with the forge CLI (`glab mr create`
/ `gh pr create`), following the repo's template and conventions. Description in
PM tone: problem → what changed → test notes. Fold in the pre-push review
one-liners if they were captured in Phase 5. Report the URL.

If migration mode: update the `MIGRATION_DOC` status table **before** the push.

## Step 4 — CI

Read logs by forge: `glab ci trace` / `gh run view --log-failed`. Root-cause per
`debugging.md` — no blind re-push. Multiple independent job failures → parallel
dispatch (`debugging.md`). Fix, re-validate locally, push.

## Step 5 — Cleanup (after merge)

Only once the MR is merged, and with the user's go-ahead:

```bash
git checkout <base-branch> && git pull
git branch -d <feature-branch>          # -d, not -D — refuses if unmerged
git worktree remove <path>              # only if a worktree was created in Phase 2
git worktree prune
```

Worktree removal refused (modified / untracked files) → show the user the file
list, ask whether to commit, move, or drop them. Never `--force` on your own.

Other local `[gone]` branches → mention them, don't delete unasked.

## Common Mistakes to Avoid

- Shipping off a suite run from before the last fix.
- Assuming the base is `main` without confirming the fork point.
- Blind re-push on CI failure instead of root-causing the logs.
- `git branch -D` (force) when `-d` refuses — the refusal means unmerged commits.
- Force-removing a worktree that holds uncommitted files.
