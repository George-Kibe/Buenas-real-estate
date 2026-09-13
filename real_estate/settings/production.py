"""Production settings: hardened cookies/HSTS, database and email from the env."""

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

# --- Email ---
# Delivery is made asynchronous by apps.common.tasks.send_email_task, not by
# the email backend itself.
MAILERS = mailer_config(  # noqa: F405
    env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
)
DOMAIN = env("DOMAIN")

# --- Database ---
DATABASES = {
    "default": {
        "ENGINE": env("POSTGRES_ENGINE", default="django.db.backends.postgresql"),
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("PG_HOST"),
        "PORT": env("PG_PORT"),
        "CONN_MAX_AGE": env.int("CONN_MAX_AGE", default=60),
    }
}

# --- Celery ---
CELERY_BROKER_URL = env("CELERY_BROKER")
CELERY_RESULT_BACKEND = env("CELERY_BACKEND")
CELERY_TIMEZONE = TIME_ZONE  # noqa: F405

# --- Security ---
# Terminating TLS at nginx, so trust its forwarded proto header.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=60 * 60 * 24 * 30)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
