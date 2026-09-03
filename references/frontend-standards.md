# Frontend Standards — Angular Patterns

Baseline conventions for all N2I frontend work. Project-specific `CLAUDE.md` overrides on conflict.

## File Structure

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

## Service Pattern

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

## Component Patterns

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

## Mobile-First (non-negotiable)

- Single column default; `md:` breakpoint for multi-column
- Full-width inputs, ≥44px tap targets, labels above fields
- No horizontal overflow in lists or dialogs
- Test at ~360px viewport

## Common Mistakes to Avoid

- Missing `appendTo="body"` on overlays in dialogs
- Fixed-width dialogs (breaks mobile)
- Forgetting barrel exports (`models/index.ts`, `services/index.ts`)
- Forgetting the route swap from placeholder to real component
