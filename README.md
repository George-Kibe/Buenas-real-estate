# Buenas Real Estate

A property listing platform for the Kenyan market: a **Django 6.1 REST API** backed by
PostgreSQL, Redis and Celery, with a **Next.js 16 / React 19** client. Everything runs
behind nginx in Docker Compose.

---

## Stack

| Layer | Technology | Version |
| --- | --- | --- |
| API | Django + Django REST Framework | 6.1.1 / 3.18.1 |
| Auth | djoser + Simple JWT | 2.3.4 / 5.5.1 |
| Database | PostgreSQL (via psycopg 3) | 18 / 3.3.5 |
| Tasks | Celery + Redis, monitored by Flower | 5.6.3 / 8 / 2.1.0 |
| Client | Next.js (App Router) + React | 16.3.5 / 19.3.0 |
| Client state | Redux Toolkit + React Redux | 2.12.0 / 9.3.0 |
| Styling | Tailwind CSS | 4.3.3 |
| Language | Python / TypeScript | 3.14 / 6.0.3 |
| API docs | drf-spectacular (OpenAPI 3) | 0.30.0 |
| Proxy | nginx | 1.31 |

---

## Quick start

You need Docker and Docker Compose v2.

```bash
git clone <repo-url> Buenas-real-estate
cd Buenas-real-estate

cp .env.example .env     # then edit SECRET_KEY and SIGNING_KEY
make build               # build images and start every service
make superuser           # create an admin login
```

Once the stack is up:

| URL | What it is |
| --- | --- |
| http://localhost:8080 | The Next.js client (through nginx) |
| http://localhost:8080/api/v1/ | The REST API |
| http://localhost:8080/superadmin/ | Django admin |
| http://localhost:5557 | Flower, the Celery dashboard |

Migrations run automatically on API container start.

> **Upgrading an existing checkout:** the database image moved from PostgreSQL 12 to 18,
> and 18 expects its volume mounted at `/var/lib/postgresql` rather than
> `/var/lib/postgresql/data`. An old `postgres_data` volume will not start against the
> new image — dump the data first, or run `make down-v` to start clean.

---

## Project layout

```
.
├── apps/                    Django applications
│   ├── common/              TimeStampedUUIDModel, Celery tasks, exception handler
│   ├── users/               Custom email-login User model, manager, admin
│   ├── profiles/            Profile per user, created by a post_save signal
│   ├── properties/          Listings, views counter, filtering and search
│   ├── enquiries/           Contact-form enquiries, emailed via Celery
│   └── ratings/             Agent reviews (1–5) with a uniqueness constraint
├── real_estate/
│   ├── settings/            base.py + development.py + production.py
│   ├── celery.py            Celery app, configured from Django settings
│   └── urls.py              API routes under /api/v1/
├── client/                  Next.js 16 App Router frontend
│   └── src/
│       ├── app/             Route folders (page.tsx / layout.tsx)
│       ├── components/      Shared UI
│       ├── lib/             axios client, server fetchers, types, formatting
│       └── store/           Redux Toolkit store and auth slice
├── docker/local/            Dockerfiles and start scripts for api, celery, nginx
├── docs/                    OpenAPI schema + Postman collection and environment
├── scripts/                 build_postman_collection.py
├── tests/                   pytest suite (pytest-django + factory_boy)
└── docker-compose.yml
```

---

## API reference

All routes are prefixed with `/api/v1/`.

### Authentication (djoser + Simple JWT)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `auth/users/` | Register. Login field is **email**; `re_password` is required |
| POST | `auth/jwt/create/` | Sign in — returns `{access, refresh}` |
| POST | `auth/jwt/refresh/` | Exchange a refresh token for a new access token |
| GET | `auth/users/me/` | The signed-in user |

Send the access token as `Authorization: Bearer <token>`.

### Profiles

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| GET | `profile/me/` | ✔ | Your profile |
| PATCH | `profile/update/<username>/` | ✔ | Update your own profile |
| GET | `profile/agents/all/` | ✔ | Every agent (paginated) |
| GET | `profile/top-agents/all/` | ✔ | Agents flagged `top_agent` (paginated) |

`profile/me/` and `profile/update/` wrap their body in a `Profile` key
(`apps/profiles/renderers.py`); error bodies and the list endpoints are not
wrapped.

### Properties

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| GET | `properties/all/` | — | Paginated list, 12 per page |
| GET | `properties/details/<slug>/` | — | One listing (increments its view count) |
| GET | `properties/agents/` | ✔ | Your own listings |
| GET | `properties/views/` | ✔ | Per-IP view records for your listings |
| POST | `properties/create/` | ✔ | Create a listing — returns **201** |
| PUT / PATCH | `properties/update/<slug>/` | ✔ | Replace / partially update your listing |
| POST | `properties/upload-image/<slug>/` | ✔ | Replace photos (multipart) |
| DELETE | `properties/delete/<slug>/` | ✔ | Delete your listing — returns **204** |
| POST | `properties/search/` | — | Structured search by bracketed price/bed/bath |

The list endpoint accepts `search` (country, city, title), `advert_type`,
`property_type`, `price`, `price__gt`, `price__lt`,
`ordering=created_at|price|views` (prefix `-` to reverse), `page` and `page_size`.

`create` and `update` ignore `user`, `slug`, `ref_code` and `views` in the body —
those are server-owned. The owner always comes from the access token.

`search` accepts bracketed strings only: `price` is one of `0+`, `50,000+`,
`100,000+`, `200,000+`, `400,000+`, `600,000+`, `Any`; `bedrooms` and `bathrooms`
are `0+` … `5+` or `Any`. Anything else is a 400.

### Enquiries and ratings

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| POST | `enquiries/` | — | Submit an enquiry; the email is queued to Celery |
| POST | `ratings/<profile_id>/` | ✔ | Review an agent (1–5 plus a comment) — returns **201** |

`profile_id` is an agent profile's UUID. You cannot review yourself, and only
once per agent.

### Conventions

- **Auth defaults to required.** Only `properties/all/`, `properties/details/`,
  `properties/search/` and `enquiries/` are public.
- **Throttled** at 60 requests/minute for anonymous callers and 1000/minute for
  signed-in ones (`THROTTLE_ANON` / `THROTTLE_USER`). Over the limit is a 429.
- **Errors are always JSON**, including unhandled ones, via
  `apps.common.exceptions.api_exception_handler`.

---

## API documentation and clients

The schema is generated from the URLconf by
[drf-spectacular](https://drf-spectacular.readthedocs.io/), so it cannot drift
from the code.

| What | Where |
| --- | --- |
| OpenAPI 3 schema (live) | http://localhost:8080/api/v1/schema/ |
| Swagger UI | http://localhost:8080/api/v1/docs/ |
| ReDoc | http://localhost:8080/api/v1/redoc/ |
| Checked-in schema | [docs/openapi.yaml](docs/openapi.yaml) |
| Postman collection | [docs/buenas-real-estate.postman_collection.json](docs/buenas-real-estate.postman_collection.json) |
| Postman environment | [docs/buenas-real-estate.postman_environment.json](docs/buenas-real-estate.postman_environment.json) |

### Running the collection

Insomnia imports Postman collections directly, so the same two files work in
either client.

```bash
make build       # start the stack
make seed-demo   # create an activated account and sample data
```

`seed-demo` prints the values to paste into your environment:

```
email             = asmith@example.com
password          = Str0ngPassw0rd!42
agentProfileId    = <uuid>
someoneElsesSlug  = agent-owned-show-house
```

Then in Postman: **Import** both files, pick the *Buenas Real Estate — Local*
environment, and hit **Run collection**. *Login* stores the tokens, *Create a
property* stores `propertySlug`, and the detail/update/upload/delete requests
reuse it. The Errors folder asserts the 401/403/404/400 paths.

From the command line:

```bash
make newman      # npx newman run, 31 requests with assertions
```

The collection is generated from
[scripts/build_postman_collection.py](scripts/build_postman_collection.py) —
edit that, then `make postman`. `make api-docs` regenerates both the schema and
the collection.

> The djoser *Register* endpoint creates an **inactive** account and emails an
> activation link, which an API client cannot follow. That is why the collection
> logs in with the seeded account and registers a throwaway random identity.

---

## Local development

### Everyday commands

```bash
make up                # start
make down              # stop
make down-v            # stop and drop volumes (wipes the database)
make show-logs         # follow logs

make migrate           # apply migrations
make makemigrations    # generate migrations after a model change
make superuser         # create an admin user
make estate-db         # psql shell

make seed-demo         # activated demo account + sample data

make test              # pytest with coverage (fails under 95%)
make lint              # flake8 + black --check + isort --check
make black             # reformat
make isort             # sort imports

make schema            # regenerate docs/openapi.yaml
make postman           # regenerate the Postman collection
make api-docs          # both of the above
make newman            # run the collection against the stack

make client-lint       # eslint
make client-build      # next build
```

### Backend outside Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# Point PG_HOST at localhost and run Postgres however you like
python manage.py migrate
python manage.py runserver
```

`DJANGO_SETTINGS_MODULE` defaults to `real_estate.settings.development`.

### Frontend outside Docker

```bash
cd client
npm install
NEXT_PUBLIC_API_URL=http://localhost:8080/api/v1 npm run dev
```

The client reads two environment variables:

- `NEXT_PUBLIC_API_URL` — used by browser code. It points at nginx, so API calls are
  same-origin and never trigger a CORS preflight.
- `INTERNAL_API_URL` — used by Server Components, which run inside the Compose network
  and reach the `api` service directly.

---

## Testing

```bash
make test                        # in Docker
pytest                           # locally, against a running Postgres
```

**156 tests, 100% statement coverage of `apps/`.** The run fails below 95%
(`--cov-fail-under=95` in `pyproject.toml`), so coverage cannot quietly rot.

```
tests/
├── common/       exception handler, Celery email task, seed_demo, schema
├── enquiries/    the public contact form
├── profiles/     profile read/update, agent lists, the Profile wrapper
├── properties/   every route in the app, plus slug/ref_code model behaviour
├── ratings/      agent reviews and the aggregate recalculation
└── users/        djoser auth, JWT lifecycle, UserSerializer
```

The suite uses `pytest-django` with `factory_boy` factories in
`tests/factories.py`, registered as fixtures in `conftest.py` (so `UserFactory`
becomes `user_factory`). `conftest.py` also provides `api_client`, `auth_client`,
`other_client`, `listing` and `agent_profile`, and clears the throttle cache
between tests.

`tests/common/test_schema.py` asserts every endpoint still appears in the
generated OpenAPI schema and that `user`, `slug`, `ref_code` and `views` stay
out of the writable property payload — so a permissions regression fails the
build.

---

## Configuration

Every setting is read from the environment through `django-environ`; see
[.env.example](.env.example) for the full list. The ones worth knowing:

| Variable | Notes |
| --- | --- |
| `SECRET_KEY`, `SIGNING_KEY` | Django's secret and the JWT signing key. Must differ in production |
| `ALLOWED_HOSTS` | Comma-separated |
| `CORS_ALLOWED_ORIGINS` | Comma-separated. Only matters when the client bypasses nginx |
| `POSTGRES_*`, `PG_HOST`, `PG_PORT` | Database connection |
| `EMAIL_*`, `DEFAULT_FROM_EMAIL` | Feed the `MAILERS` setting |
| `CELERY_BROKER`, `CELERY_BACKEND` | Redis URLs |
| `CELERY_TASK_ALWAYS_EAGER` | `True` runs tasks inline, with no worker |
| `THROTTLE_ANON`, `THROTTLE_USER` | DRF rate limits, e.g. `60/min` |

### Email

Django 6.1 replaced the individual `EMAIL_*` settings with a single `MAILERS` dict, and
the old settings are removed in Django 7. This project uses `MAILERS`, and sends mail
off the request thread through `apps.common.tasks.send_email_task` rather than an email
backend that queues for you.

Development defaults to the console backend, so mail is printed to the API container's
log instead of being sent.

---

## Production notes

`real_estate.settings.production` turns on `SECURE_SSL_REDIRECT`, HSTS, secure cookies
and `X_FRAME_OPTIONS = DENY`, and trusts nginx's `X-Forwarded-Proto`. Set
`DJANGO_SETTINGS_MODULE=real_estate.settings.production` and serve through gunicorn:

```bash
gunicorn real_estate.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

The Compose file in this repository is a **development** stack: it mounts the source
tree, runs `manage.py runserver`, and runs the Next.js dev server. Build a separate
production compose file before deploying.
