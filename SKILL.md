---
name: n2i-dev-cycle
description: Full development lifecycle — ticket/prompt to shipped code. Handles planning, implementation, validation, feedback loops, and CI fixes across N2I projects. Invoke with a ticket number, prompt, or document reference.
allowed-tools: Bash, Read, Edit, Write, Agent, Grep, Glob, mcp__plugin_claude-mem_mcp-search__observation_add, mcp__plugin_claude-mem_mcp-search__observation_search, mcp__plugin_claude-mem_mcp-search__memory_search
---

# N2I Development Cycle

Full-lifecycle development skill. Phases: Ingest → Branch → Plan → Implement → Validate → Handover → Feedback → Ship.

## Dynamic Context

- Backend: !`SLN=$(find . -maxdepth 3 \( -name '*.slnx' -o -name '*.sln' \) 2>/dev/null | head -1); if [ -n "$SLN" ]; then echo "SLN=$SLN; BACKEND=$(dirname "$SLN"); PROJECT=$(basename "$SLN" | sed 's/\.[^.]*$//')"; else echo "BACKEND=none"; fi`
- Frontend: !`NG=$(find . -maxdepth 3 -name angular.json -not -path '*/node_modules/*' 2>/dev/null | head -1); if [ -n "$NG" ]; then echo "FRONTEND=$(dirname "$NG")"; else PKG=$(find . -maxdepth 3 -name package.json -not -path '*/node_modules/*' 2>/dev/null | head -1); [ -n "$PKG" ] && echo "FRONTEND=$(dirname "$PKG")" || echo "FRONTEND=none"; fi`
- Current branch: !`git branch --show-current 2>/dev/null || echo "not-a-repo"`
- Git remote: !`git remote get-url origin 2>/dev/null || echo "no-remote"`
- Forge: !`URL=$(git remote get-url origin 2>/dev/null); case "$URL" in *gitlab*) F=gitlab;; *github*) F=github;; *) F=unknown;; esac; CLI=none; if [ "$F" = gitlab ] && command -v glab >/dev/null 2>&1; then CLI=glab; elif [ "$F" = github ] && command -v gh >/dev/null 2>&1; then CLI=gh; elif command -v glab >/dev/null 2>&1; then CLI=glab; elif command -v gh >/dev/null 2>&1; then CLI=gh; fi; echo "FORGE=$F; FORGE_CLI=$CLI"`
- Migration docs: !`c=$(find . -maxdepth 2 -name '.n2i-dev-cycle.env' 2>/dev/null | head -1); [ -n "$c" ] && . "$c" 2>/dev/null; if [ -n "${MIGRATION_DOC:-}" ]; then d=$(find . -maxdepth 3 -name "$MIGRATION_DOC" 2>/dev/null | head -1); [ -n "$d" ] && echo "MIGRATION_DOCS=$d" || echo "MIGRATION_DOCS=none"; else echo "MIGRATION_DOCS=none"; fi`
- Config: !`f=$(find . -maxdepth 2 -name '.n2i-dev-cycle.env' -not -path '*/node_modules/*' 2>/dev/null | head -1); if [ -n "$f" ]; then . "$f" 2>/dev/null; echo "CONFIG=$f; BRANCH_PREFIX=${BRANCH_PREFIX:-unset}; DEFAULT_SCOPE=${DEFAULT_SCOPE:-unset}; FORGE_OVERRIDE=${FORGE:-unset}"; else echo "CONFIG=none (see .n2i-dev-cycle.env.example)"; fi`

> **Note:** values above are *detected context*, not exported shell variables. In later
> Bash steps, substitute the literal detected path/value (or re-`source .n2i-dev-cycle.env`
> and re-derive `SLN`/`FRONTEND`) — do not rely on `$SLN`, `$FRONTEND`, `$FORGE_CLI`, etc.
> persisting across tool calls.
> If a `FORGE` override is set in config, it wins over remote-URL detection.

## Input Parsing

`$ARGUMENTS` determines the mode:

| Input | Mode | Action |
|---|---|---|
| `#17` or `17` (bare number) | **Ticket** | `$FORGE_CLI issue view <number>` → extract title, description, acceptance criteria. If `FORGE_CLI=none`, ask user to paste ticket title/description. |
| `"some description or task"` | **Prompt** | Use as-is for requirements |
| `"review and continue migration"` | **Migration** | Read `MIGRATION_DOCS` (detected) → find first ⬜ sub-phase → use as requirements. If `MIGRATION_DOCS=none`, ask user for the migration doc path. |
| `@path/to/doc.md` | **Document** | Read file → extract requirements |
| `"fix: [details]"` or `"feedback: [details]"` | **Feedback** | Skip to Phase 7 (Feedback Loop). Search memory for prior context. |

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

## Phase 1 — Ingest & Understand

1. **Detect project** from dynamic context above. Read project CLAUDE.md if present
   (try `CLAUDE.md`, then `claude.md` in repo root). If `MIGRATION_DOCS` found, read it
   (plus `docs/phase3-porting-guide.md` if present).
   If BACKEND=none and FRONTEND=none → ask user for project context.

2. **Fetch requirements** based on input mode (see Input Parsing above).

3. **Search memory** for prior work on this ticket/topic:
   - Use `observation_search` with ticket number or key terms
   - Use `memory_search` for related past decisions
   - Surface relevant context to avoid re-deriving

4. **Summarize understanding** to user in 3-5 bullets:
   - What needs to be built/changed
   - Which entities/features are involved
   - Key constraints or dependencies
   - Prior work found in memory (if any)

---

## Phase 2 — Branch Management

1. Resolve `BRANCH_PREFIX`: config value → else derive from git user
   (`git config user.name` initials, lowercased) → else `dev/`.

2. Check current branch vs ticket/task:
   - If ticket mode: expected branch pattern is `<BRANCH_PREFIX><ticket-number>-<slug>`
     (e.g. with prefix `mb/` → `mb/17-add-user-name-to-kashaf-pdf`)
   - If current branch matches ticket → proceed
   - If current branch is `main` or doesn't match:
     - Suggest branch name based on ticket/prompt
     - Ask user: create this branch, modify name, or "I'll create it myself"
     - Wait for confirmation before proceeding

3. Never force-create or switch branches without explicit user approval.

---

## Phase 3 — Plan & Approve

Produce a structured implementation plan. Format:

### Requirements Summary
- Bullet list of what the ticket/prompt asks for

### Implementation Plan

**Backend:**
- Entities to create/modify (list fields, FKs, business rules)
- Services to create/modify (list methods, validation logic)
- Controllers to create/modify (list endpoints, auth levels)
- Migration scripts needed (table creates/alters)
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

**Wait for user approval before proceeding.** User may refine, add, or remove items.

---

## Phase 4 — Implement

Execute the approved plan following the standards below. Order:

1. **Backend entity** (7-file scaffold if new entity)
2. **Migration script** (DbUp SQL)
3. **Wire-up** (DI + ModelBuilder)
4. **Controller** (if new)
5. **Unit tests**
6. **Frontend models + service**
7. **Frontend components** (list, form, report, etc.)
8. **Route + nav wiring**

**Record memory observation** after each major milestone (entity done, frontend done, etc.).

If something goes sideways mid-implementation — STOP, reassess, inform user, re-plan if needed. Don't push through blindly.

### Intra-phase checkpoints (mandatory)

After completing each logical unit, **stop and ask the user to review** before continuing. This keeps human reviewers and AI agents in sync — especially across machines and sessions.

| Checkpoint | After completing |
|---|---|
| Backend scaffold | Entity, DTOs, requests, config, service, controller, migration, DI + wire-up, build clean |
| Backend tests | Unit tests written and passing |
| Frontend models + service | TypeScript interfaces/enums, service class, barrel exports |
| Frontend components | List + form components built, routes swapped, sidebar/nav wired, `ng build` clean |

At each checkpoint, summarize what was built and ask: **"[Unit] done. Want to review before I continue?"** The user may review, request changes, push/commit, or say continue. **Never skip ahead silently.**

---

## Phase 5 — Validate

Run all validation commands. Loop until green.

```bash
# Backend — only if SCOPE includes backend && BACKEND != none
dotnet format "$SLN"
dotnet build "$SLN" -v minimal      # zero new errors
dotnet test "$SLN" -v minimal       # all pass, 0 failed

# Frontend — only if SCOPE includes frontend && FRONTEND != none
cd "$FRONTEND"
npm run build                       # ng build → zero errors
npm test -- --watch=false           # all pass
```

If validation fails:
1. Fix the issue
2. Re-run validation
3. Repeat until all green
4. Never skip or ignore failures

---

## Phase 6 — Handover

Summarize for user:

### What Changed
- Files created/modified (grouped by concern)
- Migration scripts added

### What to Test Locally
- Specific flows to verify (step-by-step)
- Edge cases to check
- Mobile/responsive checks if UI was touched

### Known Limitations
- Anything deferred or out of scope
- Dependencies on other work

### Memory
- Record handover observation with key details for cross-session continuity

---

## Phase 7 — Feedback Loop

User reports findings from local testing. For each finding:

1. **Acknowledge** the issue
2. **Diagnose** root cause
3. **Fix** following same standards
4. **Re-validate** (Phase 5)
5. **Report** what changed

If starting a new session with `"fix: [details]"`:
- Search memory for prior context on this feature/ticket
- Read recent git log to understand current state
- Pick up from where things left off

Repeat until user is satisfied.

---

## Phase 8 — Ship & CI

Only when user explicitly asks to push/ship:

1. **Push** to remote (ask for confirmation with exact command shown)
2. If user reports CI failures, read logs by forge:
   - gitlab: `glab ci trace`
   - github: `gh run view --log` (or `gh run view --log-failed`)
   - `FORGE_CLI=none`: ask user to paste CI error output
   - Fix issues
   - Re-validate locally
   - Push fix
3. If in migration mode: update the configured `MIGRATION_DOC` status table before pushing

**Record memory observation** with final status (shipped, CI green, etc.).

---

## General Development Standards

These are the baseline conventions for all N2I projects. Project-specific CLAUDE.md overrides when conflicts arise.

### Backend — .NET Vertical-Slice Architecture

#### Entity Scaffold (7 files per entity)

```
Features/<Name>/
  <Name>.cs                     // entity : IOrganizationEntity, IAuditable
  <Name>Dto.cs                  // record DTO(s)
  Create<Name>Request.cs        // record
  Update<Name>Request.cs        // record
  <Name>ModelConfiguration.cs   // static Configure<Name>(this ModelBuilder)
  I<Name>Service.cs             // interface
  <Name>Service.cs              // implementation
```

#### Entity Rules

```csharp
public class MyEntity : IOrganizationEntity, IAuditable
{
  public long Id { get; set; }               // always long, never int
  // ... fields ...
  public string? CreatedBy { get; set; }
  public DateTime CreatedOn { get; set; }
  public string? UpdatedBy { get; set; }
  public DateTime? UpdatedOn { get; set; }
  public string OrganizationId { get; set; } = string.Empty;  // CHAR(27) ULID
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
    entity.Property(e => e.OrganizationId).IsRequired().HasMaxLength(27);
    entity.Property(e => e.Name).IsRequired().HasMaxLength(100);
    entity.HasIndex(e => e.OrganizationId);
    entity.HasIndex(e => e.SomeForeignKey);  // for each FK in queries
  });
}
```

#### Service Patterns

```csharp
public class MyEntityService(IUnitOfWork unitOfWork) : IMyEntityService
{
  // 1. ResolveContext — always first
  private (OrganizationRole userRole, string userOrganizationId) ResolveContext(
    string? explicitOrganizationId)
  {
    var userRole = unitOfWork.ContextAccessor.GetCurrentOrganizationRole();
    var userOrganizationId = unitOfWork.ContextAccessor.GetCurrentOrganizationIdOrThrow();
    if (!string.IsNullOrEmpty(explicitOrganizationId) &&
        userRole < OrganizationRole.SuperOrgManager)
      throw new N2IException("Unauthorized: Only super roles can access other organizations.");
    return (userRole, userOrganizationId);
  }

  // 2. Reads: GetOrganizationScoped
  // 3. Writes: stamp OrganizationId
  // 4. Validation: throw N2IException
  // 5. FK validation: always server-side, check same org
  // 6. ScopedDictionary for batch name lookups (avoid N+1)
  // 7. ConfigureAwait(false) on every await
  // 8. _sortColumns static dict — always include id, name, createdOn
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
  public async Task<IActionResult> GetAll(
    [FromQuery] int pageIndex = 1, [FromQuery] int pageSize = 20,
    [FromQuery] string? sortBy = null, [FromQuery] string? sortOrder = null,
    [FromQuery] string? organizationId = null) { ... }

  [HttpPost]
  [N2IAuthorize(minimumRole: OrganizationRole.Admin)]
  public async Task<IActionResult> Create(
    [FromBody] CreateMyEntityRequest request,
    [FromQuery] string? organizationId = null)
  {
    try { ... }
    catch (N2IException ex) { return Result(ex); }
  }
}
```

- Return `Response { Success, Message, Data }` envelope
- Lists return `PaginatedResponseDto<T>`
- Create returns `CreatedAtAction`
- Always catch `N2IException` → 400

#### Wire-Up (3 steps, every entity)

1. `Features/FeatureServiceExtensions.cs` → `.AddScoped<IMyService, MyService>()`
2. `Features/ModelBuilderExtensions.cs` → `builder.ConfigureMyEntity();`
3. `Migration/Scripts/YYYYMMDD_HHMMSS_NN_Area_Desc.sql` → new DbUp script

#### Database Migration (DbUp)

```sql
CREATE TABLE dbo.MyEntities (
  Id              BIGINT IDENTITY(1,1) NOT NULL,
  Name            NVARCHAR(100) NOT NULL,
  SomeForeignKey  BIGINT NOT NULL,
  OptionalFk      BIGINT NULL,
  OrganizationId  CHAR(27) NOT NULL,
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

- Filename: `YYYYMMDD_HHMMSS_NN_<Area>_<Description>.sql` — monotonically increasing
- OrganizationId CHAR(27) + FK ON DELETE CASCADE + index — always
- Non-org FKs: no CASCADE
- NVARCHAR for text, not VARCHAR
- End with `GO`
- Never edit shipped scripts

### Frontend — Angular Patterns

#### File Structure

```
features/<area>/<entity>/
  components/
    <entity>-list.component.ts
    <entity>-form.component.ts
models/
  <entity>.model.ts         // Dto + Create/UpdateRequest interfaces
  index.ts                  // barrel
services/
  <entity>.service.ts       // extends BaseService
  index.ts                  // barrel
<area>.routes.ts            // lazy loadComponent, guards, breadcrumb
```

#### Service Pattern

```typescript
@Injectable({ providedIn: 'root' })
export class MyEntityService extends BaseService<Response<any>> {
  private readonly base = '<area>/MyEntity';

  getAll(pageIndex = 1, pageSize = 20, sortBy?: string, sortOrder?: string,
    ...filters): Observable<Response<PaginatedResponseDto<MyEntityDto>>> {
    const params = new URLSearchParams();
    params.set('pageIndex', pageIndex.toString());
    params.set('pageSize', pageSize.toString());
    // ... set optional params only if truthy
    return this.get(`${this.base}?${params}`) as Observable<...>;
  }
  getById(id: number): Observable<Response<MyEntityDto>> { ... }
  create(request: CreateMyEntityRequest): Observable<Response<MyEntityDto>> { ... }
  update(id: number, request: UpdateMyEntityRequest): Observable<Response<MyEntityDto>> { ... }
  remove(id: number): Observable<Response<void>> { ... }
}
```

#### Component Patterns

**List component:**
- Use `app-data-table` — never raw `p-table`
- Sync page/sort/filter to URL query params
- Load parent dropdown options on init
- Edit: load full entity by ID before opening dialog (for cascading dropdowns)

**Form component:**
- `@Input() visible` / `@Output() visibleChange` (two-way binding)
- `@Output() save, cancel, delete`
- Reactive forms with `FormBuilder`
- `ConfirmationService` for delete confirmation
- Cascading dropdowns: parent change → reset children → reload child options
- `appendTo="body"` on every `p-select`/overlay inside `p-dialog`
- Dialog responsive: `[style]="{ width: '95vw' }"` + `[breakpoints]="{ '960px': '75vw', '640px': '95vw' }"`
- Dates: `{{ date | userTimezoneDate }}`

**Rich UI — think before defaulting to a list:**

| Data type | Use instead |
|---|---|
| Calendar events / schedules | `@fullcalendar/angular` |
| Hierarchical / tree data | PrimeNG `p-tree` or `p-treeTable` |
| Grid data (students × days) | Custom grid or `p-table` with spans |

#### Mobile-First (non-negotiable)

- Single column default; `md:` breakpoint for multi-column
- Full-width inputs, ≥44px tap targets, labels above fields
- No horizontal overflow in lists or dialogs
- Test at ~360px viewport

### Unit Testing

```csharp
public class MyEntityServiceTests
{
  private static (Mock<IUnitOfWork> uow, MyEntityService service) Setup(
    List<MyEntity>? entities = null, List<SomeParent>? parents = null)
  {
    var uow = new Mock<IUnitOfWork>();
    // setup each repo mock + GetOrganizationScoped mock
    var accessor = new OrganizationContextAccessor { TargetOrganizationId = "org1" };
    uow.Setup(u => u.ContextAccessor).Returns(accessor);
    uow.Setup(u => u.CommitAsync()).ReturnsAsync(1);
    return (uow, new MyEntityService(uow.Object));
  }

  [Fact] async Task Create_ValidRequest_ReturnsDto() { ... }
  [Fact] async Task Create_EmptyName_Throws() { ... }
  [Fact] async Task Create_FkNotFound_Throws() { ... }
  [Fact] async Task GetAll_ReturnsOrgScopedResults() { ... }
  // + business rule violation tests
}
```

Minimum per service: create happy path, create invalid (name + each FK), GetAll org-scoped, business rule violations.

### C# Code Quality

- 2-space indent (enforced by `.editorconfig` + `dotnet format`)
- Private fields: `_camelCase`; public: `PascalCase`
- Primary constructors preferred (C# 12+)
- No `.Result` / `.Wait()` — always async
- `ConfigureAwait(false)` on every await in service methods
- Remove unused params (CS9113), unused imports
- Return empty collections, not null

### Security (non-negotiable)

1. Every entity `: IOrganizationEntity`. Every query org-scoped. Every write stamps `OrganizationId`.
2. Never trust client-supplied identity/role/org. Derive from JWT.
3. Cross-org: `organizationId` param honored only for `>= SuperOrgManager`.
4. FK validation server-side in service, not just controller.
5. When correct behaviour is not obvious (auth, roles, tenant isolation, money, deletion) → **ask, don't guess.**

### Common Mistakes to Avoid

- `int` instead of `long` for IDs
- `VARCHAR` instead of `NVARCHAR` in SQL
- Missing `ConfigureAwait(false)`
- FK validation only in controller (must be in service)
- Missing `appendTo="body"` on overlays in dialogs
- Fixed-width dialogs (breaks mobile)
- Forgetting wire-up steps (DI + ModelBuilder)
- Forgetting barrel exports (`models/index.ts`, `services/index.ts`)
- Forgetting route swap from placeholder to real component
- Naming entity `Task` (conflicts with `System.Threading.Tasks.Task`)
- Shipping without updating migration docs (when in migration mode)

---

## Memory Integration

> **Best-effort.** Uses the claude-mem MCP tools (`observation_add`, `observation_search`,
> `memory_search`). If unavailable in the session, skip memory steps silently — never block
> the lifecycle on them.

Record observations at these milestones using `observation_add`:

| Milestone | Type | What to record |
|---|---|---|
| Plan approved | `⚖` (decision) | Key decisions, scope, approach chosen |
| Entity/feature implemented | `◆` (feature) | What was built, files created, key design choices |
| Validation pass | `○` (discovery) | Build/test status, any issues found and fixed |
| Handover | `✓` (change) | Summary of all changes, what to test |
| Feedback received | `○` (discovery) | User findings, issues reported |
| Fix applied | `●` (bugfix) | What was fixed and how |
| Shipped / CI green | `✓` (change) | Final status, branch pushed, CI result |

Also search memory at skill start (`observation_search`, `memory_search`) to surface prior work on same ticket/feature.

---

## Project-Specific Overrides

Detection (Dynamic Context) handles paths generically — no project name needed.
Per-repo notes (known repos, migration doc names, legacy paths) live in a gitignored
local file, **not** in this public skill.

After loading general standards:
1. If `projects.local.md` exists in the skill dir, read it for repo-specific overrides.
2. Always read the active project's own CLAUDE.md for overrides (wins on conflict).

See `projects.local.md.example` for the format.
