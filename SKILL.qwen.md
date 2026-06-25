---
name: n2i-dev-cycle
description: Full development lifecycle — ticket/prompt to shipped code. Handles planning, implementation, validation, feedback loops, and CI fixes across N2I projects. Invoke with a ticket number, prompt, or document reference.
type: skill
---

# N2I Development Cycle (Qwen Variant)

Full-lifecycle development skill. Phases: Ingest → Branch → Plan → Implement → Validate → Handover → Feedback → Ship.

## Dynamic Context

Resolve at runtime via shell commands. Values substituted inline — no shell variable persistence across tool calls.

- **Backend:** `find . -maxdepth 3 \( -name '*.slnx' -o -name '*.sln' \) 2>/dev/null | head -1`
- **Frontend:** `find . -maxdepth 3 -name angular.json -not -path '*/node_modules/*' 2>/dev/null | head -1` (fallback: `package.json`)
- **Current branch:** `git branch --show-current`
- **Git remote:** `git remote get-url origin`
- **Forge:** derive from remote URL (gitlab/github). CLI: `glab` or `gh` if available.
- **Migration docs:** source `.n2i-dev-cycle.env` if present, read `MIGRATION_DOC` filename.
- **Config:** read `.n2i-dev-cycle.env` for `BRANCH_PREFIX`, `DEFAULT_SCOPE`, `FORGE` override.
- **Project overrides:** read `projects.local.md` if present.

> If a `FORGE` override is set in config, it wins over remote-URL detection.

## Input Parsing

`$ARGUMENTS` determines the mode:

| Input | Mode | Action |
|---|---|---|
| `#17` or `17` (bare number) | **Ticket** | `glab issue view` or `gh issue view` → extract title, description, acceptance criteria. If no CLI, ask user to paste ticket. |
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

## Phase 1 — Ingest & Understand

1. **Detect project** from dynamic context. Read project AGENTS.md or claude.md if present. If migration doc configured, read it (plus `docs/phase3-porting-guide.md` if present). If BACKEND=none and FRONTEND=none → ask for project context.

2. **Fetch requirements** based on input mode.

3. **Search Qwen memory** for prior work on this ticket/topic. Surface relevant context.

4. **Summarize understanding** in 3-5 bullets:
   - What needs to be built/changed
   - Which entities/features involved
   - Key constraints or dependencies
   - Prior work found in memory (if any)

---

## Phase 2 — Branch Management

1. Resolve `BRANCH_PREFIX`: config value → else derive from `git config user.name` initials → else `dev/`.

2. Check current branch vs ticket/task:
   - Ticket mode: expected pattern `<BRANCH_PREFIX><ticket-number>-<slug>`
   - If current branch matches → proceed
   - If `main` or doesn't match → suggest branch name, ask user: create, modify, or "I'll do it myself"
   - Never force-create or switch without explicit approval.

---

## Phase 3 — Plan & Approve

Structured implementation plan. Format:

### Requirements Summary
- Bullet list of what ticket/prompt asks for

### Implementation Plan

**Backend:**
- Entities to create/modify (fields, FKs, rules)
- Services to create/modify (methods, validation)
- Controllers to create/modify (endpoints, auth)
- Migration scripts needed
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

**Wait for user approval before proceeding.**

---

## Phase 4 — Implement

Execute approved plan. Order:

1. Backend entity (7-file scaffold if new)
2. Migration script (DbUp SQL)
3. Wire-up (DI + ModelBuilder)
4. Controller (if new)
5. Unit tests
6. Frontend models + service
7. Frontend components
8. Route + nav wiring

**Save Qwen memory observation** after each major milestone.

If something breaks — STOP, reassess, inform user, re-plan. No blind pushes.

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

---

## Phase 5 — Validate

Loop until green.

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

### Memory
- Save Qwen memory observation with key details.

---

## Phase 7 — Feedback Loop

User reports findings. For each:

1. Acknowledge
2. Diagnose root cause
3. Fix
4. Re-validate (Phase 5)
5. Report what changed

If starting new session with `"fix: [details]"`:
- Search Qwen memory for prior context
- Read recent git log
- Pick up from where things left off

Repeat until user satisfied.

---

## Phase 8 — Ship & CI

Only on explicit user request:

1. Push to remote (confirm exact command with user)
2. CI failure handling:
   - gitlab: `glab ci trace`
   - github: `gh run view --log`
   - No CLI: ask user to paste CI error output
   - Fix → re-validate → push
3. If in migration mode: update migration doc status table before pushing

**Save Qwen memory observation** with final status.

---

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
    entity.HasIndex(e => e.SomeForeignKey);
  });
}
```

#### Service Patterns

```csharp
public class MyEntityService(IUnitOfWork unitOfWork) : IMyEntityService
{
  private (OrganizationRole userRole, string userOrganizationId) ResolveContext(
    string? explicitOrganizationId) { ... }
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

```sql
CREATE TABLE dbo.MyEntities (
  Id              BIGINT IDENTITY(1,1) NOT NULL,
  Name            NVARCHAR(100) NOT NULL,
  SomeForeignKey  BIGINT NOT NULL,
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

- Filename: `YYYYMMDD_HHMMSS_NN_<Area>_<Description>.sql`
- OrganizationId CHAR(27) + FK ON DELETE CASCADE + index — always
- Non-org FKs: no CASCADE
- NVARCHAR for text
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
3. Cross-org: `organizationId` param only for `>= SuperOrgManager`.
4. FK validation server-side in service.
5. When correct behaviour not obvious → **ask, don't guess.**

### Common Mistakes to Avoid

- `int` instead of `long` for IDs
- `VARCHAR` instead of `NVARCHAR` in SQL
- Missing `ConfigureAwait(false)`
- FK validation only in controller
- Missing `appendTo="body"` on overlays in dialogs
- Fixed-width dialogs
- Forgetting wire-up steps
- Forgetting barrel exports
- Forgetting route swap from placeholder to real component
- Naming entity `Task` (conflicts with `System.Threading.Tasks.Task`)
- Shipping without updating migration docs (when in migration mode)

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

---

## Project-Specific Overrides

After loading general standards:
1. If `projects.local.md` exists in skill dir, read for repo-specific overrides.
2. Always read active project's AGENTS.md or claude.md for overrides (wins on conflict).
