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
│   ├── common/              Abstract TimeStampedUUIDModel + shared Celery tasks
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
| GET | `profile/agents/all/` | ✔ | Every agent |
| GET | `profile/top-agents/all/` | ✔ | Agents flagged `top_agent` |

Profile responses are wrapped in a `Profile` key by `apps/profiles/renderers.py`.

### Properties

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| GET | `properties/all/` | — | Paginated list, 12 per page |
| GET | `properties/details/<slug>/` | — | One listing (increments its view count) |
| GET | `properties/agents/` | ✔ | Your own listings |
| POST | `properties/create/` | ✔ | Create a listing |
| PUT | `properties/update/<slug>/` | ✔ | Update your listing |
| DELETE | `properties/delete/<slug>/` | ✔ | Delete your listing |
| POST | `properties/search/` | — | Structured search by bracketed price/bed/bath |

The list endpoint accepts `search` (country, city), `advert_type`, `property_type`,
`price`, `price__gt`, `price__lt`, `ordering=created_at|-created_at`, `page` and
`page_size`.

### Enquiries and ratings

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| POST | `enquiries/` | — | Submit an enquiry; the email is queued to Celery |
| POST | `ratings/<profile_id>/` | ✔ | Review an agent (1–5 plus a comment) |

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

make test              # pytest with coverage
make lint              # flake8 + black --check + isort --check
make black             # reformat
make isort             # sort imports

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
pytest --cov=.                   # locally, against a running Postgres
```

The suite uses `pytest-django` with `factory_boy` factories in `tests/factories.py`,
registered as fixtures in `conftest.py` (so `UserFactory` becomes `user_factory`).
Coverage settings live in `pyproject.toml`.

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
