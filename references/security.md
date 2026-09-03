# Security (non-negotiable)

Applies to every backend change. Read alongside `backend-standards.md`.

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

## Common Mistakes to Avoid

- `explicitOrganizationId ?? userOrganizationId` on a **write** path with no `SuperOrgManager` role check — copy-pasted from a read path or another service without noticing reads are protected by a shared scoping helper and writes aren't. See rule 3.
- Forwarding a resolved `OrgId` into a nested service call's `explicitOrganizationId`. See rule 3.
