# Backend Standards — .NET Vertical-Slice Architecture

Baseline conventions for all N2I backend work. Project-specific `CLAUDE.md` overrides on conflict.
Migrations: see `migrations.md`. Security: see `security.md`.

## Entity Scaffold (7 files per entity)

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

## Entity Rules

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

## ModelConfiguration Rules

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

## Service Patterns

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
  //    ctx.Role / ctx.UserOrgId / ctx.OrgId — see security.md rule 3 for what this replaces.

  // 2. Reads: GetOrganizationScoped
  // 3. Writes: stamp OrganizationId
  // 4. Validation: throw N2IException
  // 5. FK validation: always server-side, check same org
  // 6. ScopedDictionary for batch name lookups (avoid N+1)
  // 7. ConfigureAwait(false) on every await
  // 8. _sortColumns static dict — always include id, name, createdOn
}
```

## Controller Pattern

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

## Wire-Up (3 steps, every entity)

1. `Features/FeatureServiceExtensions.cs` → `.AddScoped<IMyService, MyService>()`
2. `Features/ModelBuilderExtensions.cs` → `builder.ConfigureMyEntity();`
3. `Migration/Scripts/YYYYMMDD_HHMMSS_NN_Area_Desc.sql` → new DbUp script (see `migrations.md`)

## Unit Testing

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

## C# Code Quality

- 2-space indent (enforced by `.editorconfig` + `dotnet format`)
- Private fields: `_camelCase`; public: `PascalCase`
- Primary constructors preferred (C# 12+)
- No `.Result` / `.Wait()` — always async
- `ConfigureAwait(false)` on every await in service methods
- Remove unused params (CS9113), unused imports
- Return empty collections, not null

## Common Mistakes to Avoid

- `int` instead of `long` for IDs
- Missing `ConfigureAwait(false)`
- FK validation only in controller (must be in service)
- Forgetting wire-up steps (DI + ModelBuilder)
- Forgetting barrel exports on the frontend side after adding the entity
- Forgetting route swap from placeholder to real component
- Naming entity `Task` (conflicts with `System.Threading.Tasks.Task`)
- Reading an EF-generated identity (`entity.Id`) before `CommitAsync()`/`SaveChangesAsync()` — it's `0`/default until the save actually happens. If a later step in the same method needs the real id (e.g. a post-save re-fetch), commit right after the add, not at the end of the method.
- Writing a local `ResolveContext`/`ResolveOrg` per service instead of checking for (or adding) a shared `ContextAccessor` extension first. One real codebase hit 30 services with this exact copy before it got caught. See `security.md` rule 3.
- Calling a scalar context-resolution helper **and** separately re-deriving `role`/`userOrgId` in the same method — the throw-check runs twice per request. Use a tuple-returning variant instead.
- Trusting an audit/dedup ticket's stated file count. Re-grep the actual pattern across the whole tree before planning — "12 services" turned out to be 30 once every shape of the duplicate was searched for, not just the one named in the ticket.
- Bulk regex/sed edits across many similar-but-not-identical files bleeding into unrelated code that happens to reuse the same variable/parameter names for a different purpose (e.g. a private helper's own `userRole` parameter getting overwritten by a blanket find-replace meant for call sites). A visual diff won't catch this reliably — rebuild after every batch, not just at the end.
- Adding a new shared helper without checking whether an existing near-duplicate in the same file/class should collapse into it (delegate) instead of leaving a third copy of the same logic sitting alongside the first two.
- Folding a genuine bug found mid-audit into a "pure refactor, no behavior change" ticket's scope. File it separately, even if it's a one-line fix — mixing concerns makes both harder to review and to revert independently.
