# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

Buenas Real Estate — a property listing platform. **Django 6.1 REST API** (`apps/`,
`real_estate/`) plus a **Next.js 16 App Router client** (`client/`), run together under
Docker Compose behind nginx.

Read [README.md](README.md) first for the stack table, API reference and commands.

## Running things

Everything goes through `make`, which wraps `docker compose exec`:

```bash
make build      # build + start the whole stack
make test       # pytest with coverage, inside the api container
make lint       # flake8 + black --check + isort --check
make migrate    # apply migrations
```

Never run `docker compose exec` by hand when a make target already exists.

Local verification without Docker is fine for quick checks — the backend needs a
Postgres on `PG_HOST`, and `pytest` needs the `db` fixture on any test that touches the
database.

## Conventions that matter here

### Models

- Every model except `User` extends `apps.common.models.TimeStampedUUIDModel`, which
  gives it **two** keys: `pkid` (BigAutoField, the real primary key and what foreign
  keys use) and `id` (a UUID, what the API exposes). When you write a lookup, be
  deliberate about which one you mean.
- `Model.save()` is **keyword-only** as of Django 6.0. Write `def save(self, **kwargs)`
  and `super().save(**kwargs)`; positional args no longer work.
- `Meta.unique_together` is deprecated. Use `Meta.constraints` with `UniqueConstraint`,
  as `apps/ratings/models.py` does.
- `Property.slug` is generated in `save()` by `django.utils.text.slugify` with a
  numeric suffix for collisions. There is no `django-autoslug` — it was dropped because
  it has not been released since 2023.
- `Property.ref_code` is assigned **once**, on creation. It is the code agents quote, so
  do not regenerate it on update.

### Settings

- Three modules: `base.py` (shared), `development.py`, `production.py`. Anything
  environment-specific belongs in the latter two, read through `django-environ`.
- Never import a settings module directly (`from real_estate.settings.development import
  X`). Use `from django.conf import settings`. Direct imports break under the production
  settings module.
- Email uses the **`MAILERS`** dict, new in Django 6.1. The old `EMAIL_*` settings are
  deprecated and **cannot be mixed with `MAILERS`** — Django raises
  `ImproperlyConfigured` if both are defined.

### Async work

- Queue mail with `apps.common.tasks.send_email_task.delay(...)`. Do not reach for
  `django-celery-email`; it calls `get_connection(backend=...)`, which raises under
  `MAILERS`.
- Task arguments must be JSON-serialisable — they cross a broker.
- Set `CELERY_TASK_ALWAYS_EAGER=True` to run tasks inline when there is no worker.

### API

- **DRF denies by default.** `DEFAULT_PERMISSION_CLASSES` is `IsAuthenticated`, so a
  new view is protected unless it opts out with an explicit
  `permission_classes = [permissions.AllowAny]`. The public ones are the property
  list, property detail, property search and the enquiry form.
- **Reads and writes use different serializers.** `PropertySerializer` is entirely
  read-only (`read_only_fields = fields`); writes go through
  `PropertyCreateSerializer`, which deliberately excludes `user`, `slug`, `ref_code`
  and `views`. Never widen that list — `tests/common/test_schema.py` fails if you do.
  The owner is set in the view with `serializer.save(user=request.user)`.
- **Validation lives on the model.** Non-negative prices, bedrooms, floors, plot area
  and bathrooms are `MinValueValidator`s on the fields, which ModelSerializer copies
  onto the generated serializer. Do not re-implement them as `validate_*` hooks — DRF
  also trims whitespace and rejects blank CharFields before a hook runs, so those end
  up unreachable.
- **Every endpoint must appear in the schema.** Function-based views need an
  `@extend_schema(...)` with `request`, `responses` and `tags`, or drf-spectacular
  drops them silently. A `ListAPIView` whose `get_queryset` touches `request.user`
  also needs a static `queryset = Model.objects.none()` class attribute, which is what
  schema generation reads.
- djoser owns the auth routes; `DJOSER["SERIALIZERS"]` points at
  `apps/users/serializers.py`. Changing `UserSerializer` changes `auth/users/me/`.
- djoser pins `social-auth-app-django<6.0.0`. Do not bump that package past 5.9.0
  without also replacing djoser.
- `profile/me/` and `profile/update/` wrap their body in a `Profile` key
  (`apps/profiles/renderers.py`); error bodies and the agent **list** endpoints are
  not wrapped. Client code must account for both.
- Country fields serialise as the country *name* ("Kenya"), not the ISO code, in
  `PropertySerializer`, `ProfileSerializer` and `UserSerializer` alike. The stored
  value is the code.
- Throttling is on by default (60/min anon, 1000/min user). `conftest.py` clears the
  throttle cache between tests; a new test module that bypasses it will flake.

### Frontend

- App Router only. A route is a folder under `src/app/` with a `page.tsx`.
- `params` and `searchParams` are **Promises** (Next 15+). Always `await` them.
- Server Components fetch through `src/lib/server-api.ts` (plain `fetch`,
  `INTERNAL_API_URL`). Client Components use the axios instance in `src/lib/api.ts`,
  which attaches the JWT and refreshes it on a 401.
- A page that reads `useSearchParams()` must sit inside a `<Suspense>` boundary, or the
  build fails.
- **Do not add `src/app/loading.tsx`.** A root `loading.tsx` wraps every route in
  Suspense, which makes Next stream the response — the status code is then committed
  before the page resolves, so `notFound()` returns **200 instead of 404**. This was
  verified against a production build. Use a local `<Suspense>` inside a page instead,
  the way `properties/page.tsx` wraps its filters.
- Redux holds **auth state only**. Property data is fetched per-render, not cached in
  the store.
- **Never hand-write an API path in a component.** `src/lib/endpoints.ts` has one
  typed function per route; add to it rather than calling `api.post("/...")` inline.
  Server Components use `src/lib/server-api.ts` instead.
- Tailwind v4 is configured in CSS (`src/app/globals.css`, `@theme` block). There is no
  `tailwind.config.js` — do not create one.
- Path alias: `@/*` → `src/*`.

## Pinned-version traps

These versions are deliberate. Verify before bumping:

| Package | Pinned | Why not the latest |
| --- | --- | --- |
| `typescript` | 6.0.3 | `typescript-eslint` does not support the TS 7 native port |
| `eslint` | 9.39.5 | `eslint-plugin-react` (inside eslint-config-next) uses `context.getFilename()`, removed in ESLint 10 |
| `social-auth-app-django` | 5.9.0 | djoser pins `<6.0.0` |

Everything else is the newest release compatible with Django 6.1.1 / React 19.3.0.

## Before you finish

```bash
make lint && make test        # backend — fails under 95% coverage
cd client && npm run lint && npx tsc --noEmit && npm run build
```

After changing a view, serializer or URL, also regenerate the shipped API docs:

```bash
make api-docs                 # docs/openapi.yaml + the Postman collection
make newman                   # run the collection against the live stack
```

`next build` is the check that matters most on the frontend — it catches Server/Client
Component boundary mistakes that lint and `tsc` both miss.

## Open questions

- **`AgentListAPIView` and `TopAgentsListAPIView` require authentication.** On a public
  property portal, browsing agents anonymously is the more usual product choice. Left
  as-is because it is a product decision, not a defect.
- **Enquiries are unauthenticated and only rate-limited.** A captcha or honeypot would
  be the normal next step before this faces the open internet.
- **`Property.tax` is a per-listing decimal defaulting to 0.15.** It reads like a
  system-wide rate that happens to live on each row; worth revisiting if tax rules
  ever vary.
