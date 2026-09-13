"""Development settings: local Docker stack, console email, verbose errors."""

from .base import *  # noqa: F401,F403
from .base import env

# --- Email ---
# Defaults to the console backend, so mail is printed to the container log.
MAILERS = mailer_config(  # noqa: F405
    env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
)
DOMAIN = env("DOMAIN", default="localhost:3000")

# --- Database ---
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases
# The postgresql backend talks to psycopg 3 when it is installed.
DATABASES = {
    "default": {
        "ENGINE": env("POSTGRES_ENGINE", default="django.db.backends.postgresql"),
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("PG_HOST"),
        "PORT": env("PG_PORT"),
    }
}

# --- Celery ---
CELERY_BROKER_URL = env("CELERY_BROKER")
CELERY_RESULT_BACKEND = env("CELERY_BACKEND")
CELERY_TIMEZONE = TIME_ZONE  # noqa: F405
# Run tasks inline when no worker is available (tests, bare `runserver`).
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
