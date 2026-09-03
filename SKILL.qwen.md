---
name: n2i-dev-cycle
description: Full development lifecycle — ticket/prompt to shipped code. Handles planning, implementation, validation, feedback loops, and CI fixes across N2I projects. Invoke with a ticket number, prompt, or document reference.
type: skill
---

# N2I Development Cycle (Qwen Variant)

Full-lifecycle development skill. 8 phases: Ingest/Classify/Align → Branch → Plan → Implement → Validate → Handover → Feedback → Ship.

Discipline layer (inline below, no separate files): classification gate, TDD,
verification gate, systematic debugging, finishing, model selection, checkpoint ledger.

## Dynamic Context

Resolve at runtime via shell commands. Values substituted inline — no shell variable persistence across tool calls.

- **Backend:** `find . -maxdepth 3 \( -name '*.slnx' -o -name '*.sln' \) 2>/dev/null | head -1`
- **Frontend:** `find . -maxdepth 3 -name angular.json -not -path '*/node_modules/*' 2>/dev/null | head -1` (fallback: `package.json`)
- **Current branch:** `git branch --show-current`
- **Git remote:** `git remote get-url origin`
- **Forge:** derive from remote URL (gitlab/github). CLI: `glab` or `gh` if available.
- **Config:** `.n2i-dev-cycle/config` at repo root (source-able KEY=VALUE). Keys: `BRANCH_PREFIX`, `DEFAULT_SCOPE`, `FORGE`, `DB_ENGINE`, `MIGRATION_DOC`, and for non-.NET/Angular stacks `BACKEND_VALIDATE_CMD` / `FRONTEND_VALIDATE_CMD` / `E2E_CMD` / `BACKEND_STANDARDS` / `FRONTEND_STANDARDS` / `MIGRATION_STANDARDS`.
- **DB engine:** `DB_ENGINE` from config → else migrator call in `*.cs` (`PostgresqlDatabase(`/`UseNpgsql` vs `SqlDatabase(`/`SqlServerDatabase(`/`UseSqlServer`, `old/` excluded) → else csproj packages (`Npgsql.EntityFrameworkCore`/`dbup-postgresql` vs `EntityFrameworkCore.SqlServer`/`dbup-sqlserver`) → else default `postgres`.
- **Project overrides:** repo's `.n2i-dev-cycle/notes.md` + `CLAUDE.md` if present. No cross-repo file.

> If a `FORGE` override is set in config, it wins over remote-URL detection.
> Per-repo config + generated state live in a gitignored `.n2i-dev-cycle/` folder at the
> repo root (`config`, the `progress.md` checkpoint ledger, optional `notes.md`).
> `DB_ENGINE` default is `postgres`; SQL Server apps set
> `DB_ENGINE=sqlserver` in `.n2i-dev-cycle/config`. Ambiguous detection (both Npgsql and
> SqlServer packages — an app mid-migration) → confirm with the user in Phase 1 before emitting DDL.
> A legacy SQL Server `MIGRATION_DOC` source does not change the target dialect.

## Input Parsing

`$ARGUMENTS` determines the mode:

| Input | Mode | Action |
|---|---|---|
| `#17` or `17` (bare number) | **Ticket** | `glab issue view` or `gh issue view` → extract title, description, acceptance criteria. If no CLI, ask user to paste ticket. Spec'd mode → run the alignment gate (Phase 1). |
| `"let's discuss X"`, wiki link, rough `docs/` markdown — no ticket yet | **Discussion** | Run the brainstorming flow (Phase 1) → ticket / sub-ticket draft for Product review. Stop unless told to continue. |
| `"some description or task"` | **Prompt** | Use as-is for requirements |
| `"review and continue migration"` | **Migration** | Read migration doc → find first ⬜ sub-phase → use as requirements. If no doc, ask for path. |
| `@path/to/doc.md` | **Document** | Read file → extract requirements |
| `"fix: [details]"` or `"feedback: [details]"` | **Feedback** | Skip to Phase 7. Search Qwen memory for prior context. |

If input is ambiguous, ask.

## Scope Selection

Leading token of `$ARGUMENTS` may set scope (strip it before mode parsing):

| Token | Scope |
|---|---|
| `-b` / `b` / `--backend` | backend only |
| `-f` / `f` / `--frontend` | frontend only |
| `-bf` / `--both` | both |

If no token: infer from detection —
- BACKEND=none → frontend
- FRONTEND=none → backend
- both present → ask user which (default both)

`SCOPE` gates later phases:
- Phase 3 Plan: emit only the matching **Backend** / **Frontend** subsections.
- Phase 4 Implement: skip steps for the excluded side.
- Phase 5 Validate: run only the matching block.

---

## Phase 1 — Ingest, Classify & Align

**Hard gate:** no branch, no plan, no code, no scaffold until the user approves
the intent — the ticket draft (discussion mode) or the restated spec (spec'd mode).
Ceremony scales with the task; the gate never does.

1. **Detect project** from dynamic context. Read project AGENTS.md/claude.md and `.n2i-dev-cycle/notes.md` if present. If migration doc configured, read it (plus `docs/phase3-porting-guide.md` if present). If BACKEND=none and FRONTEND=none → ask for project context.

2. **Sync project config** — `.n2i-dev-cycle/config` under repo root (`git rev-parse --show-toplevel`); the `.n2i-dev-cycle/` folder is gitignored and holds all repo-scoped skill state. Skip if not a git repo (use detected values in memory).
   - **First run (`CONFIG=none`):** propose a `config` from detected values (`DB_ENGINE` from detection — ask "Postgres or SQL Server?" if ambiguous default; `BRANCH_PREFIX` if derivable; `MIGRATION_DOC`/`FORGE` if already known). Show file + path + the `.gitignore` line (`.n2i-dev-cycle/`), ask once. Yes → create folder+file, append `.n2i-dev-cycle/` to repo `.gitignore` if missing (user commits that). No → in-memory for this run, don't re-ask.
   - **Later runs (config exists):** config is source of truth. If explicit `DB_ENGINE` disagrees with current code detection (repo migrated), surface it, ask to update. Never rewrite without consent.
   - Legacy SQL Server `MIGRATION_DOC` source does not change the target dialect.

3. **Fetch requirements** based on input mode. Read the ticket and every linked wiki / `docs/` page in full.

4. **Classify** — spike / bounded / architectural. Say it out loud so the user can override.
   - **Spike**: feasibility question, output is an answer not kept code.
   - **Bounded**: scoped change to a flow that already exists in the repo. Short design in chat, then implement.
   - **Architectural**: new project/subsystem, or a change that reshapes interfaces others depend on. Written spec under `docs/`, self-reviewed, user-reviewed, then Phase 3.
   - Unsure between two → take the heavier. Hidden complexity mid-task upgrades the class; nothing downgrades.

5. **Search Qwen memory** for prior work on this ticket/topic. Surface relevant context.

6. **Take the path:**
   - **Discussion mode** (no finalized ticket): explore context, decompose if multi-subsystem, ask clarifying questions one at a time, propose 2-3 approaches for architectural work, present a design (spec doc for architectural). Produce the **ticket / sub-ticket draft** for Product review — problem → proposed direction → scope (covered vs adjacent-excluded) → out of scope, PM tone. **Stop** unless told to continue.
   - **Spec'd mode** (ticket already Product-reviewed): **alignment gate** — restate in 3-5 bullets (what changes, entities/features/endpoints, `DB_ENGINE`, prior memory), then list every gap / contradiction / ambiguity you actually see. Don't re-brainstorm a finalized spec. One explicit approval, then Phase 2.

7. **Set session title** (if the runtime supports it): `<ticket-number>: <short desc>`.

8. **Start / resume the checkpoint ledger** (see Checkpoint Ledger below). If `.n2i-dev-cycle/progress.md` names this ticket, resume at the first incomplete phase.

---

## Phase 2 — Branch Management

1. Resolve `BRANCH_PREFIX`: config value → else derive from `git config user.name` initials → else `dev/`.

2. Check current branch vs ticket/task:
   - Ticket mode: expected pattern `<BRANCH_PREFIX><ticket-number>-<slug>`
   - If current branch matches → proceed
   - If `main` or doesn't match → suggest branch name, ask user: create, modify, or "I'll do it myself". In the same question offer isolation: **"branch in place, or an isolated git worktree?"** — default in place for small/medium; worktree for long / risky / multi-session work.
   - Worktree, only if chosen: detect existing isolation first (`git rev-parse --git-dir` vs `--git-common-dir` differ, not a submodule) → skip if already in one. Else `git worktree add .worktrees/<branch> -b <branch>`; verify `.worktrees/` is gitignored (add + commit the line if missing).
   - Never force-create/switch a branch, or create a worktree, without explicit approval.

---

## Phase 3 — Plan & Approve

**Standards source:** if `BACKEND_STANDARDS` / `FRONTEND_STANDARDS` /
`MIGRATION_STANDARDS` is set in config, read that repo file — it is authoritative
over the inline General Development Standards below. The working dir's own
AGENTS.md/CLAUDE.md auto-loads and wins on conflict regardless.

Structured implementation plan. Format:

### Requirements Summary
- Bullet list of what ticket/prompt asks for

### Implementation Plan

**Backend:**
- Entities to create/modify (fields, FKs, rules)
- Services to create/modify (methods, validation)
- Controllers to create/modify (endpoints, auth)
- Migration scripts needed — note target dialect (`DB_ENGINE`)
- Wire-up steps (DI, ModelBuilder)

**Frontend:**
- Models/interfaces to create/modify
- Services to create/modify
- Components to create/modify
- Route changes
- Sidebar/nav changes

**Tests:**
- Unit tests needed (list cases)
- What to verify manually

**Migration-specific** (only if migration doc configured):
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

### No Placeholders + Self-Review

Every item carries concrete content — entity fields with types + FKs, service
method signatures + validation rules, exact routes + auth level, named test cases.
"validation logic" / "the endpoints" / "tests for the above" are plan failures.
Before presenting: re-read the spec, confirm every requirement maps to an item
(list gaps), check names/signatures are consistent across sections. Fix inline.

**Wait for user approval before proceeding.**

---

## Phase 4 — Implement

**TDD (iron law):** no business logic without a failing test first. Write the
test, run it, watch it fail for the right reason, write minimal code to pass,
refactor while green. Code written before its test → delete it, redo from the
test. "Keep as reference" / "test after" are violations.

Test-first: service methods, controller endpoints, component behaviour, bug
repros. Exempt (but exercised by the tests that follow): entity properties,
`ModelConfiguration`, DI wire-up, migration DDL.

Order — each logic step RED→GREEN before the next:

1. Backend entity + `ModelConfiguration` (scaffold, exempt)
2. Migration script (DbUp SQL — scaffold, exempt)
3. Wire-up (DI + ModelBuilder — scaffold, exempt)
4. Service — test-first per method
5. Controller — test-first per endpoint (auth, shape, status)
6. Frontend models + service
7. Frontend components — test-first where the project tests component behaviour
8. Route + nav wiring

**Save Qwen memory observation + append a ledger line** after each milestone.

If something breaks — STOP, reassess, inform user, re-plan. No blind pushes.

### Intra-phase checkpoints (mandatory)

After completing each logical unit, **stop and ask the user to review** before continuing. This keeps human reviewers and AI agents in sync — especially across machines and sessions.

| Checkpoint | After completing |
|---|---|
| Backend scaffold | Entity, DTOs, requests, config, migration, DI + wire-up, build clean |
| Backend service + controller | Methods and endpoints built test-first, all tests green |
| Frontend models + service | TypeScript interfaces/enums, service class, barrel exports |
| Frontend components | List + form components built (test-first where applicable), routes swapped, sidebar/nav wired, `ng build` clean |

At each checkpoint, summarize what was built, **append the ledger line**, and ask: **"[Unit] done. Want to review before I continue?"** The user may review, request changes, push/commit, or say continue. **Never skip ahead silently.**

---

## Phase 5 — Validate

**Verification gate:** before saying "green" / "passing" / "done", you must have
run the exact command **in this message** and read its output — exit code,
failure count. No "should pass", no run from before the last edit, no "linter
passed" standing in for "build passed". Same rule before any completion claim
anywhere in the lifecycle.

Loop until green. If `BACKEND_VALIDATE_CMD` / `FRONTEND_VALIDATE_CMD` is set in
config, run that snippet for the in-scope side instead of the block below (it
covers format + build + unit tests, exits non-zero on any failure).

```bash
# Backend — only if SCOPE includes backend && BACKEND != none
dotnet format "$SLN"
dotnet build "$SLN" -v minimal
dotnet test "$SLN" -v minimal

# Frontend — only if SCOPE includes frontend && FRONTEND != none
cd "$FRONTEND"
npm run build
npm test -- --watch=false
```

If validation fails: fix → re-run → repeat until green. Never skip failures.

### Pre-push review

Once green, before Phase 6: run a code review against the local diff
(`git diff <base-branch>...HEAD`, per SCOPE) — a third-party review skill if
available, else a manual pass. Reviewing here (before the MR exists) keeps a
finding a clean amend instead of a fix-up commit in MR history, and avoids a CI
run against a state you're about to patch. Handle findings with technical rigor:
restate, verify against the codebase, push back on wrong / YAGNI. A finding
that's a real bug goes through Systematic Debugging (root cause first) + TDD
(failing test first). Fix accepted findings, re-run the Phase 5 gate.

---

## Phase 6 — Handover

### What Changed
- Files created/modified (grouped by concern)
- Migration scripts added

### What to Test Locally
- Specific flows to verify
- Edge cases to check
- Mobile/responsive checks if UI touched

### Known Limitations
- Deferred items
- Dependencies on other work

### E2E Coverage
Only if an e2e config / `e2e/` dir exists. **Reviewing the change's e2e impact is
mandatory; a new spec is not always.**
- Map every touched flow to existing specs.
- A spec the change **breaks or makes stale** → fix/update it. Not optional,
  however small the change.
- A touched flow with **no** spec → build one (test-first), unless it's minor and
  the user agrees no spec is warranted — record that call in the handover.
- Run affected specs before Phase 8 (via `E2E_CMD` if set, else the project's
  runner) — against a dev DB or a fresh throwaway DB where the project supports
  one. Can't run for real → say so, don't claim coverage.

### Memory
- Save Qwen memory observation + a ledger line with key details.

---

## Phase 7 — Feedback Loop

**Systematic debugging (iron law): no fix without root-cause investigation first.**
Symptom fixes are failure.

1. **Root cause** — read the error fully; reproduce; check recent changes; for a
   multi-layer path (controller→service→repo→DB, frontend→API→handler,
   CI→build→sign) log what enters/exits each boundary and run once to see which
   boundary breaks; trace the bad value back to its source.
2. **One hypothesis** — "X is the cause because Y"; test with the smallest change,
   one variable at a time. Didn't work → new hypothesis, don't stack fixes.
3. **Failing test** that reproduces it (TDD).
4. **One fix** at the root cause — no bundled refactoring. Re-validate (Phase 5 gate).
5. Report; append a ledger line.

**Three fixes that don't hold → STOP.** Question the design with the user, don't
try fix #4.

**Independent findings** (different subsystems, unrelated) → dispatch one agent
per domain concurrently (one message), each scoped to its domain, "find root
cause, don't just loosen asserts / bump timeouts", "don't touch other code",
"return root cause + change". Not for findings that might share a cause. On
return: read summaries, check diffs don't conflict, run the full suite.

If starting a new session with `"fix: [details]"`:
- Read `.n2i-dev-cycle/progress.md` + recent `git log` — they outrank memory
- Search Qwen memory for prior context
- Resume from the ledger's first incomplete phase

Repeat until user satisfied.

---

## Phase 8 — Ship & CI

Only on explicit user request:

1. **Full suite green** — whole suite for the active scope (not filtered),
   through the Phase 5 gate. Failures stop the ship.
2. **Confirm the base branch** with the user before the MR.
3. **Push** (confirm exact command), then create the MR/PR against the confirmed
   base via forge CLI, repo conventions, PM-tone description. Code review already
   happened in Phase 5 — should be clean.
4. **CI failures:** read logs (`glab ci trace` / `gh run view --log-failed`; no
   CLI → ask user to paste). Root-cause per Systematic Debugging — no blind
   re-push. Multiple independent job failures → parallel dispatch. Fix,
   re-validate locally, push.
5. **Migration mode:** update the migration doc status table before the push.
6. **After merge** (with the user's go-ahead): `git branch -d <feature-branch>`
   (never `-D` unasked); `git worktree remove <path>` + `git worktree prune` if
   one was created in Phase 2. Removal refused (uncommitted files) → show the
   user, ask; never `--force`.

**Save Qwen memory observation + final ledger line** (shipped, CI green, merged).

---

## Model Selection

Pick the cheapest model that fits the step; state the model when dispatching a
subagent (omitted = inherits this session's, usually priciest).

| Work | Model tier |
|---|---|
| Scaffolding, migration DDL, single-file mechanical edits, transcription from a detailed plan | cheap / fast |
| Service/controller/component logic, multi-file integration, test design | standard |
| Architecture, ambiguous debugging, pre-push review, CI root-cause on a multi-layer failure | most capable |

## Checkpoint Ledger

`.n2i-dev-cycle/progress.md` (gitignored folder). Plain text, no MCP dependency —
survives context compaction and cross-session `fix:` / multi-machine re-entry.
Skip if not in a git repo.

- First line: `# <ticket-or-slug> — <one-line goal>`
- One line per phase as it completes: `Phase N: <what landed> (<commit range>)`
- Phase 4 intra-phase checkpoints get a line too.
- On skill start (Phase 1 step 8): first line matches this ticket → resume at the
  first incomplete phase.
- After compaction, `git log` + this ledger outrank recollection.

## Discipline Red Flags — Stop

- Code before test / "test after achieves the same" / "keep as reference"
- "should pass" / "looks right" / "Great!" / "Done!" before running the command
- Proposing a fix before tracing data flow; fix #4 after three failures
- Claiming green off a run from before the last edit
- Trusting a subagent "success" without reading its diff
- Starting a branch/plan/code before the user approved the intent

## General Development Standards

Baseline conventions for all N2I projects. Project-specific AGENTS.md/claude.md overrides on conflict.

### Backend — .NET Vertical-Slice Architecture

#### Entity Scaffold (7 files per entity)

```
Features/<Name>/
  <Name>.cs
  <Name>Dto.cs
  Create<Name>Request.cs
  Update<Name>Request.cs
  <Name>ModelConfiguration.cs
  I<Name>Service.cs
  <Name>Service.cs
```

#### Entity Rules

```csharp
public class MyEntity : IOrganizationEntity, IAuditable
{
  public long Id { get; set; }
  public string? CreatedBy { get; set; }
  public DateTime CreatedOn { get; set; }
  public string? UpdatedBy { get; set; }
  public DateTime? UpdatedOn { get; set; }
  public string OrganizationId { get; set; } = string.Empty;  // CHAR(26) ULID
}
```

#### ModelConfiguration Rules

```csharp
public static void ConfigureMyEntity(this ModelBuilder builder)
{
  builder.Entity<MyEntity>(entity =>
  {
    entity.ToTable("MyEntities");
    entity.HasKey(e => e.Id);
    entity.Property(e => e.OrganizationId).IsRequired().HasMaxLength(26);
    entity.Property(e => e.Name).IsRequired().HasMaxLength(100);
    entity.HasIndex(e => e.OrganizationId);
    entity.HasIndex(e => e.SomeForeignKey);
  });
}
```

#### Service Patterns

Context resolution: check for a shared `IOrganizationContextAccessor` extension
(e.g. `ResolveWriteContext`) before writing a per-service private method — 30 services in
one real codebase each reinvented this before it got caught. See Security rule 3.

```csharp
public class MyEntityService(IUnitOfWork unitOfWork) : IMyEntityService
{
  // var ctx = unitOfWork.ContextAccessor.ResolveWriteContext(explicitOrganizationId);
  // ctx.Role / ctx.UserOrgId / ctx.OrgId — don't hand-roll this locally.
  // Reads: GetOrganizationScoped
  // Writes: stamp OrganizationId
  // Validation: throw N2IException
  // FK validation: server-side, check same org
  // ScopedDictionary for batch name lookups
  // ConfigureAwait(false) on every await
  // _sortColumns static dict — include id, name, createdOn
}
```

#### Controller Pattern

```csharp
[Route("api/<area>/[controller]")]
[ApiController]
public class MyEntityController(IMyEntityService service) : BaseController
{
  [HttpGet]
  [N2IAuthorize(minimumRole: OrganizationRole.ReadOnly)]
  public async Task<IActionResult> GetAll(...) { ... }

  [HttpPost]
  [N2IAuthorize(minimumRole: OrganizationRole.Admin)]
  public async Task<IActionResult> Create(...) { ... }
}
```

- Return `Response { Success, Message, Data }` envelope
- Lists return `PaginatedResponseDto<T>`
- Create returns `CreatedAtAction`
- Catch `N2IException` → 400

#### Wire-Up (3 steps)

1. `Features/FeatureServiceExtensions.cs` → `.AddScoped<IMyService, MyService>()`
2. `Features/ModelBuilderExtensions.cs` → `builder.ConfigureMyEntity();`
3. `Migration/Scripts/YYYYMMDD_HHMMSS_NN_Area_Desc.sql`

#### Database Migration (DbUp)

Dialect from `DB_ENGINE`. **Postgres = default**; SQL Server only when `DB_ENGINE=sqlserver`.

**Postgres** (all current work):

```sql
-- 2026-09-03 Add MyEntities (#NN)
CREATE TABLE IF NOT EXISTS "MyEntities" (
  "Id"              bigint GENERATED BY DEFAULT AS IDENTITY NOT NULL,
  "Name"            varchar(100) NOT NULL,
  "SomeForeignKey"  bigint NOT NULL,
  "OrganizationId"  char(26) NOT NULL,
  "CreatedBy"       varchar(450) NOT NULL,
  "CreatedOn"       timestamptz NOT NULL DEFAULT now(),
  "UpdatedBy"       varchar(450),
  "UpdatedOn"       timestamptz,
  CONSTRAINT "PK_MyEntities" PRIMARY KEY ("Id"),
  CONSTRAINT "FK_MyEntities_Organizations" FOREIGN KEY ("OrganizationId")
    REFERENCES "Organizations" ("Id") ON DELETE CASCADE,
  CONSTRAINT "FK_MyEntities_SomeParent" FOREIGN KEY ("SomeForeignKey")
    REFERENCES "SomeParents" ("Id")
);
CREATE INDEX IF NOT EXISTS "IX_MyEntities_OrganizationId" ON "MyEntities" ("OrganizationId");
CREATE INDEX IF NOT EXISTS "IX_MyEntities_SomeForeignKey" ON "MyEntities" ("SomeForeignKey");
```

- Quoted PascalCase identifiers, no schema prefix (EF maps `MyEntity`→`"MyEntities"`)
- `bigint GENERATED BY DEFAULT AS IDENTITY`; `varchar(n)`/`text`; `timestamptz DEFAULT now()`; `boolean`; `numeric(p,s)`
- `IF NOT EXISTS` on table/index/column — idempotent. No `GO`.
- DbUp `NoTransactionStrategy`: destructive bulk-data scripts wrap own `BEGIN;`/`COMMIT;`
- Migrator: `DeployChanges.To.PostgresqlDatabase(...)`, `dotnet run --project backend/Migration`

**SQL Server** (legacy only, `DB_ENGINE=sqlserver`):

```sql
CREATE TABLE dbo.MyEntities (
  Id              BIGINT IDENTITY(1,1) NOT NULL,
  Name            NVARCHAR(100) NOT NULL,
  SomeForeignKey  BIGINT NOT NULL,
  OrganizationId  CHAR(26) NOT NULL,
  CreatedBy       NVARCHAR(100) NULL,
  CreatedOn       DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
  UpdatedBy       NVARCHAR(100) NULL,
  UpdatedOn       DATETIME2 NULL,
  CONSTRAINT PK_MyEntities PRIMARY KEY (Id),
  CONSTRAINT FK_MyEntities_Organizations FOREIGN KEY (OrganizationId)
    REFERENCES dbo.Organizations(Id) ON DELETE CASCADE,
  CONSTRAINT FK_MyEntities_SomeParent FOREIGN KEY (SomeForeignKey)
    REFERENCES dbo.SomeParents(Id)
);
CREATE INDEX IX_MyEntities_OrganizationId ON dbo.MyEntities(OrganizationId);
CREATE INDEX IX_MyEntities_SomeForeignKey ON dbo.MyEntities(SomeForeignKey);
GO
```

- `dbo.` schema, `IDENTITY(1,1)`, `NVARCHAR` for text, `DATETIME2 DEFAULT GETUTCDATE()`, end batches with `GO`

Both:
- Filename: `YYYYMMDD_HHMMSS_NN_<Area>_<Description>.sql`
- OrganizationId CHAR(26) + FK ON DELETE CASCADE + index — always
- Non-org FKs: no CASCADE
- Never edit shipped scripts

### Frontend — Angular Patterns

#### File Structure

```
features/<area>/<entity>/
  components/
    <entity>-list.component.ts
    <entity>-form.component.ts
models/
  <entity>.model.ts
  index.ts
services/
  <entity>.service.ts
  index.ts
<area>.routes.ts
```

#### Service Pattern

```typescript
@Injectable({ providedIn: 'root' })
export class MyEntityService extends BaseService<Response<any>> {
  private readonly base = '<area>/MyEntity';
  getAll(pageIndex = 1, pageSize = 20, ...): Observable<...> { ... }
  getById(id: number): Observable<...> { ... }
  create(request: ...): Observable<...> { ... }
  update(id: number, request: ...): Observable<...> { ... }
  remove(id: number): Observable<...> { ... }
}
```

#### Component Patterns

**List:**
- Use `app-data-table` — never raw `p-table`
- Sync page/sort/filter to URL query params
- Load parent dropdown options on init
- Edit: load full entity by ID before dialog

**Form:**
- `@Input() visible` / `@Output() visibleChange`
- `@Output() save, cancel, delete`
- Reactive forms with `FormBuilder`
- `ConfirmationService` for delete
- Cascading dropdowns: parent change → reset children
- `appendTo="body"` on every overlay in dialog
- Dialog responsive: `[style]="{ width: '95vw' }"` + breakpoints
- Dates: `{{ date | userTimezoneDate }}`

**Rich UI:**

| Data type | Use instead |
|---|---|
| Calendar events | `@fullcalendar/angular` |
| Hierarchical/tree | PrimeNG `p-tree` or `p-treeTable` |
| Grid data | Custom grid or `p-table` with spans |

#### Mobile-First (non-negotiable)

- Single column default; `md:` breakpoint for multi-column
- Full-width inputs, ≥44px tap targets
- No horizontal overflow
- Test at ~360px viewport

### Unit Testing

```csharp
public class MyEntityServiceTests
{
  private static (Mock<IUnitOfWork> uow, MyEntityService service) Setup(
    List<MyEntity>? entities = null)
  {
    var uow = new Mock<IUnitOfWork>();
    var accessor = new OrganizationContextAccessor { TargetOrganizationId = "org1" };
    uow.Setup(u => u.ContextAccessor).Returns(accessor);
    uow.Setup(u => u.CommitAsync()).ReturnsAsync(1);
    return (uow, new MyEntityService(uow.Object));
  }

  [Fact] async Task Create_ValidRequest_ReturnsDto() { ... }
  [Fact] async Task Create_EmptyName_Throws() { ... }
  [Fact] async Task Create_FkNotFound_Throws() { ... }
  [Fact] async Task GetAll_ReturnsOrgScopedResults() { ... }
}
```

Minimum per service: create happy path, create invalid (name + each FK), GetAll org-scoped, business rule violations.

### C# Code Quality

- 2-space indent
- Private fields: `_camelCase`; public: `PascalCase`
- Primary constructors preferred
- No `.Result` / `.Wait()` — always async
- `ConfigureAwait(false)` on every await
- Remove unused params, unused imports
- Return empty collections, not null

### Security (non-negotiable)

1. Every entity `: IOrganizationEntity`. Every query org-scoped. Every write stamps `OrganizationId`.
2. Never trust client-supplied identity/role/org. Derive from JWT.
3. Cross-org: `organizationId` param only for `>= SuperOrgManager` — on writes too, not just reads (reads get this free from `GetOrganizationScoped`; writes need an explicit check, centralized as a `ContextAccessor` extension, not inlined per-service). Never forward the *resolved* org id into a nested service call's `explicitOrganizationId` param — forward the original through instead.
4. FK validation server-side in service.
5. When correct behaviour not obvious → **ask, don't guess.**

### Common Mistakes to Avoid

- `int` instead of `long` for IDs
- Wrong SQL dialect for `DB_ENGINE` (Postgres: quoted PascalCase, `varchar`/`timestamptz`, no `GO`; SQL Server: `dbo.`, `NVARCHAR`, `GO`)
- Missing `ConfigureAwait(false)`
- FK validation only in controller
- Missing `appendTo="body"` on overlays in dialogs
- Fixed-width dialogs
- Forgetting wire-up steps
- Forgetting barrel exports
- Forgetting route swap from placeholder to real component
- Naming entity `Task` (conflicts with `System.Threading.Tasks.Task`)
- Shipping without updating migration docs (when in migration mode)
- Writing a local `ResolveContext`/`ResolveOrg` per service instead of using/adding a shared `ContextAccessor` extension
- Calling a scalar context helper and separately re-deriving role/userOrgId in the same method (double throw-check)
- Trusting an audit/dedup ticket's stated file count without re-grepping the actual pattern first
- Bulk sed/regex edits across many files bleeding into unrelated helper methods that reuse the same variable names — rebuild after every batch
- Folding a bug found mid-audit into a "pure refactor" ticket's scope instead of filing it separately

---

## Memory Integration

Use Qwen's built-in memory system. Save observations at milestones:

| Milestone | What to record |
|---|---|
| Plan approved | Key decisions, scope, approach |
| Entity/feature implemented | What built, files created, key design choices |
| Validation pass | Build/test status, issues found and fixed |
| Handover | Summary of changes, what to test |
| Feedback received | User findings, issues reported |
| Fix applied | What fixed and how |
| Shipped / CI green | Final status, branch pushed, CI result |

Search Qwen memory at skill start to surface prior work on same ticket/feature.
The `.n2i-dev-cycle/progress.md` ledger is the durable fallback when memory is unavailable.

---

## Project-Specific Overrides

All project-specific input comes from the repo you're in, nothing cross-repo:
1. `.n2i-dev-cycle/config` — settings (loaded in Dynamic Context).
2. `.n2i-dev-cycle/notes.md` in the repo, if present — personal gotchas (gitignored).
3. Active project's AGENTS.md/claude.md — team overrides, wins on conflict.
