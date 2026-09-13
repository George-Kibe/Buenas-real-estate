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

- djoser owns the auth routes; `DJOSER["SERIALIZERS"]` points at
  `apps/users/serializers.py`. Changing `UserSerializer` changes `auth/users/me/`.
- djoser pins `social-auth-app-django<6.0.0`. Do not bump that package past 5.9.0
  without also replacing djoser.
- Profile responses are wrapped in a `Profile` key by `apps/profiles/renderers.py`.
  Client code must unwrap it.
- `PropertySerializer` is read-only in places (several `SerializerMethodField`s), so
  **writes must use `PropertyCreateSerializer`**. Writing through `PropertySerializer`
  silently discards the data.

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
make lint && make test        # backend
cd client && npm run lint && npx tsc --noEmit && npm run build
```

`next build` is the check that matters most on the frontend — it catches Server/Client
Component boundary mistakes that lint and `tsc` both miss.

## Known rough edges

Pre-existing issues, not regressions. Fix them when you touch the surrounding code:

- `apps/properties/views.py::PropertySearchAPIView` indexes `request.data` directly, so
  a missing key is a `KeyError` → 500 rather than a 400.
- `PropertyViewsAPIView` and `upload_property_image` are defined but not routed.
- `apps/properties/serializers.py` calls `.url` on image fields unconditionally; a
  listing with a cleared photo raises `ValueError`.
- `apps/ratings/views.py::create_agent_review` computes the "already reviewed" check
  against the agent's own pkid rather than the rater's, so it never matches.
- `Property.price` is `max_digits=8, decimal_places=2`, capping a listing at
  **999,999.99**. No Kenyan property costs under 1M KES, so realistic listings are
  rejected with "Ensure that there are no more than 8 digits in total." Widening it
  needs a migration and a decision about currency units.
- `PropertyCreateSerializer` declares `country` explicitly, which drops the model's
  `default="KE"` and makes the field required on create.
- `apps/profiles/renderers.py` looks for an `errors` key, but DRF uses `detail`, so
  error responses from profile endpoints get wrapped as `{"Profile": {"detail": ...}}`.
- There are no API-level tests — the suite covers models only.
