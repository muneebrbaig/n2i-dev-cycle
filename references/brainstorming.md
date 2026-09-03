# Brainstorming, Classification & Alignment

Read at the start of every run (Phase 1). Governs how much process the work needs
and gates everything after it.

## Hard Gate

No branch, no plan, no code, no scaffold until the user approves the **intent**:
- Discussion mode → the ticket / sub-ticket draft.
- Spec'd mode → the restated spec.

The gate never scales down. What scales is the artifact — two bullets in chat for
a one-line fix, a written spec for a new subsystem.

## Classify First

State the class out loud so the user can override it.

| Class | What it is | Output |
|---|---|---|
| **Spike** | Feasibility question ("can we…", "is X possible"). Output is an answer, not kept code. | A recommendation. Anything built is labelled throwaway. |
| **Bounded** | Well-scoped change to a flow that already exists in the repo — a flag, one endpoint, a field, a fix. | Short design in chat, then implement. No spec file. |
| **Architectural** | New project, new subsystem, or a change that reshapes how components fit or alters an interface others depend on. | Written spec under `docs/`, self-reviewed, user-reviewed, then Phase 3. |

When unsure between two, take the heavier one. Hidden complexity found mid-task
upgrades the class — stop and say so. Nothing downgrades mid-task.

"Too simple to need approval" is the trap that wastes the most work. Simple means
a short design, not no design.

## Two Entry Situations

### Discussion mode — no finalized ticket yet

Input was a chat topic, a wiki page, a rough `docs/` markdown, or meeting /
call notes. We are still deciding what to build.

1. Explore project context — files, recent commits, the linked doc.
2. If the request spans multiple independent subsystems, decompose first — name
   the pieces, how they relate, what order. Each piece gets its own ticket.
3. Ask clarifying questions **one at a time** — purpose, constraints, success
   criteria. Prefer multiple choice.
4. For architectural work, propose 2-3 approaches with trade-offs, lead with your
   recommendation.
5. Present the design, scaled to complexity. For architectural work, write it to
   `docs/<date>-<topic>-design.md`, self-review (placeholders, contradictions,
   scope, ambiguity), then ask the user to review.
6. Produce the **ticket / sub-ticket draft** for Product review — title,
   problem, proposed direction, scope (covered vs adjacent-excluded), out of
   scope. PM tone.
7. **STOP.** Brainstorming and building are normally different sessions. Continue
   into Phase 2 only if the user explicitly says so.

### Spec'd mode — ticket already reviewed and finalized

The usual case: the ticket was brainstormed and Product-reviewed in an earlier
session. This session starts cold.

1. Fetch the ticket + every linked wiki / doc. Read all of it.
2. **Alignment gate** — restate in 3-5 bullets:
   - what gets built or changed
   - entities / features / endpoints involved
   - target DB engine (`DB_ENGINE`)
   - prior work found in memory
3. List every **gap, contradiction, or ambiguity** you actually see. Do not
   re-brainstorm a finalized spec — only surface what an implementer would have
   to guess at.
4. Get one explicit approval, then Phase 2.

## Common Mistakes to Avoid

- Skipping the alignment gate because "the ticket looks clear" — a cold session
  has none of the brainstorm context; the restate is where cross-session drift
  surfaces.
- Re-litigating a finalized spec instead of flagging only the unclear parts.
- Starting a branch or plan before the user has said yes to the intent.
- Treating a new project as bounded because the *kind* of app is familiar — no
  existing flow to change means architectural.
