---
name: n2i-dev-cycle
description: Full development lifecycle — ticket/prompt to shipped code. Handles planning, implementation, validation, feedback loops, and CI fixes across N2I projects. Invoke with a ticket number, prompt, or document reference.
allowed-tools: Bash, Read, Edit, Write, Agent, Grep, Glob, mcp__plugin_claude-mem_mcp-search__observation_add, mcp__plugin_claude-mem_mcp-search__observation_search, mcp__plugin_claude-mem_mcp-search__memory_search, mcp__ccd_session_mgmt__set_session_title
---

# N2I Development Cycle

Full-lifecycle development skill. Phases: Ingest → Branch → Plan → Implement → Validate → Handover → Feedback → Ship.

## Dynamic Context

- Backend: !`SLN=$(find . -maxdepth 3 \( -name '*.slnx' -o -name '*.sln' \) 2>/dev/null | head -1); if [ -n "$SLN" ]; then echo "SLN=$SLN; BACKEND=$(dirname "$SLN"); PROJECT=$(basename "$SLN" | sed 's/\.[^.]*$//')"; else echo "BACKEND=none"; fi`
- Frontend: !`NG=$(find . -maxdepth 3 -name angular.json -not -path '*/node_modules/*' 2>/dev/null | head -1); if [ -n "$NG" ]; then echo "FRONTEND=$(dirname "$NG")"; else PKG=$(find . -maxdepth 3 -name package.json -not -path '*/node_modules/*' 2>/dev/null | head -1); [ -n "$PKG" ] && echo "FRONTEND=$(dirname "$PKG")" || echo "FRONTEND=none"; fi`
- Current branch: !`git branch --show-current 2>/dev/null || echo "not-a-repo"`
- Git remote: !`git remote get-url origin 2>/dev/null || echo "no-remote"`
- Forge: !`URL=$(git remote get-url origin 2>/dev/null); case "$URL" in *gitlab*) F=gitlab;; *github*) F=github;; *) F=unknown;; esac; CLI=none; if [ "$F" = gitlab ] && command -v glab >/dev/null 2>&1; then CLI=glab; elif [ "$F" = github ] && command -v gh >/dev/null 2>&1; then CLI=gh; elif command -v glab >/dev/null 2>&1; then CLI=glab; elif command -v gh >/dev/null 2>&1; then CLI=gh; fi; echo "FORGE=$F; FORGE_CLI=$CLI"`
- DB engine: !`f=$(find . -maxdepth 3 -path '*/.n2i-dev-cycle/config' 2>/dev/null | head -1); [ -n "$f" ] && . "$f" 2>/dev/null; E=${DB_ENGINE:-}; if [ -n "$E" ] && [ "$E" != auto ]; then echo "DB_ENGINE=$E (config)"; else FILES=$(grep -rlE 'PostgresqlDatabase\(|SqlServerDatabase\(|\.SqlDatabase\(|UseNpgsql|UseSqlServer' --include='*.cs' . 2>/dev/null | grep -v '/old/'); MIG=$(echo "$FILES" | xargs grep -hoE 'PostgresqlDatabase\(|SqlServerDatabase\(|\.SqlDatabase\(|UseNpgsql|UseSqlServer' 2>/dev/null | sort -u | tr -d '\n'); if echo "$MIG" | grep -qE 'Postgresql|Npgsql'; then echo "DB_ENGINE=postgres (migrator)"; elif echo "$MIG" | grep -qE 'SqlServer|SqlDatabase'; then echo "DB_ENGINE=sqlserver (migrator)"; else P=$(grep -rhi -E 'Npgsql\.EntityFrameworkCore|dbup-postgresql' --include='*.csproj' . 2>/dev/null); S=$(grep -rhi -E 'EntityFrameworkCore\.SqlServer|dbup-sqlserver' --include='*.csproj' . 2>/dev/null); if [ -n "$P" ] && [ -z "$S" ]; then echo "DB_ENGINE=postgres (pkg)"; elif [ -n "$S" ] && [ -z "$P" ]; then echo "DB_ENGINE=sqlserver (pkg)"; else echo "DB_ENGINE=postgres (default; confirm in Phase 1)"; fi; fi; fi`
- Migration docs: !`c=$(find . -maxdepth 3 -path '*/.n2i-dev-cycle/config' 2>/dev/null | head -1); [ -n "$c" ] && . "$c" 2>/dev/null; if [ -n "${MIGRATION_DOC:-}" ]; then d=$(find . -maxdepth 3 -name "$MIGRATION_DOC" 2>/dev/null | head -1); [ -n "$d" ] && echo "MIGRATION_DOCS=$d" || echo "MIGRATION_DOCS=none"; else echo "MIGRATION_DOCS=none"; fi`
- Config: !`f=$(find . -maxdepth 3 -path '*/.n2i-dev-cycle/config' -not -path '*/node_modules/*' 2>/dev/null | head -1); if [ -n "$f" ]; then . "$f" 2>/dev/null; echo "CONFIG=$f; BRANCH_PREFIX=${BRANCH_PREFIX:-unset}; DEFAULT_SCOPE=${DEFAULT_SCOPE:-unset}; FORGE_OVERRIDE=${FORGE:-unset}"; else echo "CONFIG=none (see n2i-dev-cycle.config.example)"; fi`
- E2E: !`E2ECFG=$(find . -maxdepth 3 \( -name 'playwright.config.*' -o -name 'cypress.config.*' \) -not -path '*/node_modules/*' 2>/dev/null | head -1); if [ -n "$E2ECFG" ]; then echo "E2E=$(dirname "$E2ECFG")"; else E2EDIR=$(find . -maxdepth 3 -type d \( -name 'e2e' -o -path '*/tests/e2e' \) -not -path '*/node_modules/*' 2>/dev/null | head -1); [ -n "$E2EDIR" ] && echo "E2E=$E2EDIR" || echo "E2E=none"; fi`

> **Note:** values above are *detected context*, not exported shell variables. In later
> Bash steps, substitute the literal detected path/value (or re-`source` the config file
> and re-derive `SLN`/`FRONTEND`) — do not rely on `$SLN`, `$FRONTEND`, `$FORGE_CLI`, etc.
> persisting across tool calls.
> Per-repo config lives in `.n2i-dev-cycle/config` at the repo root (a gitignored
> `.n2i-dev-cycle/` folder — anything repo-scoped and skill-generated goes there).
> If a `FORGE` override is set in config, it wins over remote-URL detection.
> `DB_ENGINE` resolves as: config value (`postgres`/`sqlserver`) → else migrator call in
> code → else csproj packages → else **default `postgres`**. Postgres is the current
> standard; only legacy apps still on SQL Server set `DB_ENGINE=sqlserver` in their repo's
> `.n2i-dev-cycle/config`. When detection lands on the ambiguous default, confirm with the
> user in Phase 1 before emitting any DDL.

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
   (try `CLAUDE.md`, then `claude.md` in repo root), and `.n2i-dev-cycle/notes.md` if
   present. If `MIGRATION_DOCS` found, read it (plus `docs/phase3-porting-guide.md` if
   present). If BACKEND=none and FRONTEND=none → ask user for project context.

2. **Sync project config** — `.n2i-dev-cycle/config` under the repo root
   (`git rev-parse --show-toplevel`). The `.n2i-dev-cycle/` folder is gitignored and holds
   everything repo-scoped the skill generates (today: `config`; room for a resume/checkpoint
   file later). Skip this whole step if not in a git repo — carry detected values in memory.

   **First run for this repo** (`CONFIG=none`): propose a `config` file from detected values:
   - `DB_ENGINE` — from the detection chain; if it landed on the ambiguous default (both
     Npgsql and SqlServer packages, e.g. KoolHub) ask "Postgres or SQL Server?" first
   - `BRANCH_PREFIX` — config value, else git-user initials if derivable, else omit
   - `MIGRATION_DOC` / `FORGE` — only if already known (migration doc read this run, or
     remote detection was `unknown` and the user named a forge)

   Show the exact file contents and target path (`<root>/.n2i-dev-cycle/config`), plus the
   one `.gitignore` line (`.n2i-dev-cycle/`). Ask once.
   - **Yes** → create the folder + file; append `.n2i-dev-cycle/` to the repo's `.gitignore`
     if missing and tell the user to commit that `.gitignore` change (the only tracked file
     touched).
   - **No** → carry the detected values in memory for this run; don't re-ask this session.

   **Later runs** (config exists): it's the source of truth. If `DB_ENGINE` holds an
   explicit value and code detection now disagrees (e.g. the repo finished migrating to
   Postgres), surface the mismatch and ask whether to update that key. Never rewrite the
   file without consent.

   A `MIGRATION_DOC` describing a legacy SQL Server source does **not** change the target —
   new DDL follows the current `DB_ENGINE`, not the legacy dialect.

3. **Fetch requirements** based on input mode (see Input Parsing above).

4. **Search memory** for prior work on this ticket/topic:
   - Use `observation_search` with ticket number or key terms
   - Use `memory_search` for related past decisions
   - Surface relevant context to avoid re-deriving

5. **Summarize understanding** to user in 3-5 bullets:
   - What needs to be built/changed
   - Which entities/features are involved
   - Key constraints or dependencies
   - Target DB engine (`DB_ENGINE`)
   - Prior work found in memory (if any)

6. **Set session title** via `set_session_title`: `<ticket-number>: <short desc>`
   (e.g. `17: add user name to Kashaf PDF`). Skip silently if the tool is unavailable.

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
- Migration scripts needed (table creates/alters) — note target dialect (`DB_ENGINE`)
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

### Pre-push review

Once green, before Phase 6: ask user "Run engineering:code-review on this diff before pushing?"
Default yes if unsure. Reviewing here — against the local diff, before an MR/PR exists — catches
scope-creep and correctness issues while they're still a `git commit --amend` or a clean follow-up
commit away, instead of a fix-up commit sitting permanently in MR history after the fact. It also
skips triggering a CI run against a state you already know you're about to patch.

- If `engineering:code-review` isn't in the available-skills list this session, say so and skip
  silently — don't block the lifecycle. Offer a manual review pass instead if the user still wants one.
- If accepted and available, invoke it against the diff: `git diff <base-branch>...HEAD` (backend
  and/or frontend paths per SCOPE), not a PR URL — no MR/PR exists yet at this point.
- Fix any findings, then **re-run this Phase 5 validation loop** before moving to Phase 6.
- Optionally ask: "Compress findings into caveman-review one-liners for the MR/PR description?"
  If yes and `caveman:caveman-review` is available, run it over the findings and fold the output
  into Phase 6's handover summary. If not available, skip silently — the raw findings still stand.
  (No MR comment thread exists yet to post to — that's why this differs from posting comments.)

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

### E2E Coverage
Only if `E2E != none`:
- Check existing specs under `E2E` for the flows touched by this change
- If a changed flow has no matching spec, flag it and ask user: "No e2e coverage for
  [flow] — want me to add a spec now, or file it separately?"
- If flows are already covered, note that briefly — no action needed

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

1. **Push** to remote (ask for confirmation with exact command shown). Code review already
   happened at the end of Phase 5, against the local diff — this push should already be clean.
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
    entity.HasIndex(e => e.SomeForeignKey);  // for each FK in queries
  });
}
```

#### Service Patterns

**Context resolution — check for a shared helper before writing a local one.** A real
codebase (KoolHub, ticket #18) hit 30 services that each hand-rolled their own private
`ResolveContext`/`ResolveOrg` method with this exact body, because the reference pattern
below used to show it as step 1 of every new service. Before adding one:

1. Look for an existing `IOrganizationContextAccessor` extension in the project's shared/Kernel
   layer (e.g. `ResolveWriteContext`, `ResolveWriteOrganizationId`) that already does this.
2. If it exists but only returns the scalar org id and this method *also* needs `role`/
   `userOrgId` for a `GetOrganizationScoped` call in the same method, don't call the scalar
   helper **and** separately re-derive role/userOrgId (that's a redundant second throw-check
   per request, and it's the mistake that made 7 of #18's 30 services need fixing). Add a
   tuple-returning sibling once, in the shared layer, and have the scalar helper delegate to
   it — not the other way around, and not a third local copy.
3. Only write a local private method if the project genuinely has no shared helper yet —
   and if so, put it in the shared layer, not the service class, so the next entity doesn't
   reinvent it too.

```csharp
public class MyEntityService(IUnitOfWork unitOfWork) : IMyEntityService
{
  // 1. Context resolution — call the shared ContextAccessor extension, don't hand-roll it:
  //    var ctx = unitOfWork.ContextAccessor.ResolveWriteContext(explicitOrganizationId);
  //    ctx.Role / ctx.UserOrgId / ctx.OrgId — see Security rule 3 for what this replaces.

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

Pick the dialect from `DB_ENGINE`. **Postgres is the default** — only use the SQL Server
form for a repo whose `.n2i-dev-cycle/config` sets `DB_ENGINE=sqlserver`.

**Postgres** (KoolHub / KhatahApp / OrbitApp and all current work):

```sql
-- 2026-09-03 Add MyEntities (#NN)

CREATE TABLE IF NOT EXISTS "MyEntities" (
  "Id"              bigint GENERATED BY DEFAULT AS IDENTITY NOT NULL,
  "Name"            varchar(100) NOT NULL,
  "SomeForeignKey"  bigint NOT NULL,
  "OptionalFk"      bigint,
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

Postgres rules:
- **Quoted PascalCase** identifiers everywhere — tables, columns, constraints, indexes.
  EF maps `MyEntity` → table `"MyEntities"`, property `Name` → column `"Name"`. No snake_case,
  no `dbo.`/`public.` prefix.
- `bigint GENERATED BY DEFAULT AS IDENTITY` for `Id` (not `ALWAYS`, not serial).
- `varchar(n)` / `text` for strings; `timestamptz` for dates with `DEFAULT now()`; `boolean`
  with `DEFAULT true|false`; `numeric(p,s)` for money.
- `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS` —
  scripts are idempotent.
- No `GO`. DbUp runs each script with `NoTransactionStrategy`, so a destructive bulk
  data script wraps its own `BEGIN; ... COMMIT;` (plain single-statement DDL does not need it).
- Constraint/index naming unchanged: `PK_<Table>`, `FK_<Table>_<Ref>`, `IX_<Table>_<Cols>`.
- Migrator: `DeployChanges.To.PostgresqlDatabase(...)`, scripts embedded in the `Migration`
  project; runs on `dotnet run --project backend/Migration`.

**SQL Server** (legacy apps only, `DB_ENGINE=sqlserver`):

```sql
CREATE TABLE dbo.MyEntities (
  Id              BIGINT IDENTITY(1,1) NOT NULL,
  Name            NVARCHAR(100) NOT NULL,
  SomeForeignKey  BIGINT NOT NULL,
  OptionalFk      BIGINT NULL,
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

SQL Server rules: `dbo.` schema, `IDENTITY(1,1)`, `NVARCHAR` for text (not `VARCHAR`),
`DATETIME2 DEFAULT GETUTCDATE()`, end every batch with `GO`.

Both dialects:
- Filename: `YYYYMMDD_HHMMSS_NN_<Area>_<Description>.sql` — monotonically increasing
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
3. Cross-org: `organizationId` param honored only for `>= SuperOrgManager` — **on writes, not just reads.**
   Read paths usually get this for free through a shared scoping helper (e.g. `GetOrganizationScoped(query, userRole, userOrganizationId, explicitOrganizationId)`), which silently ignores `explicitOrganizationId` for non-super roles. Writes have no equivalent by default — resist writing the check inline in every `CreateAsync`:
   ```csharp
   // WRONG — copy-pasted across a real codebase 10 times before anyone noticed:
   var organizationId = explicitOrganizationId ?? userOrganizationId;   // no role check at all
   ```
   ```csharp
   // RIGHT — matches the reference scaffold; centralize as a ContextAccessor extension
   // (e.g. ResolveWriteOrganizationId) if the project doesn't already have one, so new
   // write endpoints can't reintroduce the gap by skipping the inline check:
   if (!string.IsNullOrEmpty(explicitOrganizationId) && userRole < OrganizationRole.SuperOrgManager) {
     throw new KoolException("Unauthorized: Only super roles can access other organizations.");
   }
   var organizationId = explicitOrganizationId ?? userOrganizationId;
   ```
   If the method also needs `role`/`userOrgId` in scope (e.g. to feed `GetOrganizationScoped`
   for a read in the same method as a write), don't call the scalar helper above **and**
   separately re-derive `role`/`userOrgId` — that's the same throw-check running twice per
   request. Add a tuple-returning sibling instead (e.g. `ResolveWriteContext` returning
   `(Role, UserOrgId, OrgId)`) and have the scalar helper delegate to it:
   ```csharp
   public static (OrganizationRole Role, string UserOrgId, string OrgId) ResolveWriteContext(
       this IOrganizationContextAccessor contextAccessor, string? explicitOrganizationId) {
     var userRole = contextAccessor.GetCurrentOrganizationRole();
     var userOrganizationId = contextAccessor.GetCurrentOrganizationIdOrThrow();
     if (!string.IsNullOrEmpty(explicitOrganizationId) && userRole < OrganizationRole.SuperOrgManager) {
       throw new KoolException("Unauthorized: Only super roles can access other organizations.");
     }
     return (userRole, userOrganizationId, explicitOrganizationId ?? userOrganizationId);
   }

   public static string ResolveWriteOrganizationId(
       this IOrganizationContextAccessor contextAccessor, string? explicitOrganizationId) =>
     contextAccessor.ResolveWriteContext(explicitOrganizationId).OrgId;
   ```
   Never forward the *resolved* `OrgId`/`organizationId` into a nested service call's
   `explicitOrganizationId` parameter — forward the original (usually-null)
   `explicitOrganizationId` through instead. Forwarding the resolved value defeats the
   nested call's own role check and is the single most common bug in this whole area.
4. FK validation server-side in service, not just controller.
5. When correct behaviour is not obvious (auth, roles, tenant isolation, money, deletion) → **ask, don't guess.**

### Common Mistakes to Avoid

- `int` instead of `long` for IDs
- Wrong SQL dialect for `DB_ENGINE` — snake_case or `VARCHAR` on Postgres; `varchar`/no-`GO` on SQL Server (should be `NVARCHAR` + `GO`)
- Missing `ConfigureAwait(false)`
- FK validation only in controller (must be in service)
- Missing `appendTo="body"` on overlays in dialogs
- Fixed-width dialogs (breaks mobile)
- Forgetting wire-up steps (DI + ModelBuilder)
- Forgetting barrel exports (`models/index.ts`, `services/index.ts`)
- Forgetting route swap from placeholder to real component
- Naming entity `Task` (conflicts with `System.Threading.Tasks.Task`)
- Shipping without updating migration docs (when in migration mode)
- `explicitOrganizationId ?? userOrganizationId` on a **write** path with no `SuperOrgManager` role check — copy-pasted from a read path or another service without noticing reads are protected by a shared scoping helper and writes aren't. See Security rule 3.
- Reading an EF-generated identity (`entity.Id`) before `CommitAsync()`/`SaveChangesAsync()` — it's `0`/default until the save actually happens. If a later step in the same method needs the real id (e.g. a post-save re-fetch), commit right after the add, not at the end of the method.
- Writing a local `ResolveContext`/`ResolveOrg` per service instead of checking for (or adding) a shared `ContextAccessor` extension first. One real codebase hit 30 services with this exact copy before it got caught. See Security rule 3.
- Calling a scalar context-resolution helper **and** separately re-deriving `role`/`userOrgId` in the same method — the throw-check runs twice per request. Use a tuple-returning variant instead.
- Trusting an audit/dedup ticket's stated file count. Re-grep the actual pattern across the whole tree before planning — "12 services" turned out to be 30 once every shape of the duplicate was searched for, not just the one named in the ticket.
- Bulk regex/sed edits across many similar-but-not-identical files bleeding into unrelated code that happens to reuse the same variable/parameter names for a different purpose (e.g. a private helper's own `userRole` parameter getting overwritten by a blanket find-replace meant for call sites). A visual diff won't catch this reliably — rebuild after every batch, not just at the end.
- Adding a new shared helper without checking whether an existing near-duplicate in the same file/class should collapse into it (delegate) instead of leaving a third copy of the same logic sitting alongside the first two.
- Folding a genuine bug found mid-audit into a "pure refactor, no behavior change" ticket's scope. File it separately, even if it's a one-line fix — mixing concerns makes both harder to review and to revert independently.

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

Detection (Dynamic Context) handles paths generically — no project name needed. Everything
project-specific is read from the repo you're in, nothing from a cross-repo file:

1. `.n2i-dev-cycle/config` — the KEY=VALUE settings (already loaded in Dynamic Context).
2. `.n2i-dev-cycle/notes.md` in the repo, if present — free-text personal gotchas
   (gitignored, this repo only). Read it when it exists; never require it.
3. The repo's own `CLAUDE.md` — team-shared conventions and overrides, wins on conflict.

Repo quirks worth writing down: team-facing ones go in `CLAUDE.md`, personal ones in
`.n2i-dev-cycle/notes.md`. There is no skill-dir roster of repos.
