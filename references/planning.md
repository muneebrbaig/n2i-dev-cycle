# Implementation Plan Format

Read in Phase 3, after the `SCOPE` standards. Produce the plan in this shape,
emitting only the subsections for the active `SCOPE`. The **Backend** / **Frontend**
vocabulary below is the .NET + Angular default — on another stack it follows the
`*_STANDARDS` file the repo points at (README "Using with a different stack").

### Requirements Summary
- Bullet list of what the ticket/prompt asks for

### Implementation Plan

**Backend:**
- Entities to create/modify (list fields, FKs, business rules)
- Services to create/modify (list methods, validation logic)
- Controllers to create/modify (list endpoints, auth levels)
- Migration scripts needed (table creates/alters) — note target dialect (`DB_ENGINE`) and the rollback path (a forward-fix script, or why none is needed)
- Wire-up steps (DI, ModelBuilder)

**Frontend:**
- Models/interfaces to create/modify
- Services to create/modify
- Components to create/modify (list vs form vs report vs calendar)
- Route changes
- Sidebar/nav changes

**Tests:**
- Unit tests needed (list test cases)
- What to verify manually

**Migration-specific** (only if a `MIGRATION_DOC` is configured):
- Legacy source files to reference
- Fields to port vs drop
- Business rules to port
- Sub-phase status update needed

### Questions / Ambiguities
- List anything unclear — ask before implementing

### Estimated Scope
- Files to create: N
- Files to modify: N
- Migration scripts: N
- Unit tests: N
- Changed lines (rough): N

## No Placeholders

Every item carries the concrete content, not a description of it:
- entity fields with types + FKs, not "the fields"
- service method signatures + validation rules, not "validation logic"
- exact endpoint routes + auth level, not "the endpoints"
- named test cases, not "unit tests for the above"

An item an implementer can't act on without guessing is a plan failure — fix it
before presenting.

## Plan Self-Review

Before presenting: re-read the spec, confirm every requirement maps to a plan
item (list any gaps), scan for the placeholders above, and check names /
signatures are consistent across sections — a method called one thing under the
entity and another under tests is a bug. Fix inline.

**Size check.** Review quality drops as a change grows: about 100 changed lines reviews
easily, 300 is fine as one logical change, and past roughly 400 it should be split. If
the estimate is over 400, propose the split (stacked branches or commits, one logical
change each) in the plan, and plan any refactor as its own change, apart from the feature.

**Doubt review (architectural class only).** In the same message as the plan, offer
one fresh-context review (`references/doubt.md`). Run it only if the user says yes.

Then **wait for user approval before proceeding.** The user may refine, add, or
remove items.
